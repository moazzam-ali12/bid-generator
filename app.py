from __future__ import annotations

import base64
import json
import os
import re
import asyncio
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from extract import (
    IngestedDoc,
    extract_text_from_pdf,
    extract_text_from_docx,
    keyword_window,
    build_context,
    KEYWORDS_PROMPT_1,
    KEYWORDS_PROMPT_2,
    KEYWORDS_PROMPT_3,
)
from prompts import (
    prompt_0_cover_page,
    prompt_1_table1,
    prompt_2_table2,
    prompt_3_table3,
    prompt_final_quantities,
)
from openai_client import OpenAIClient, OpenAIConfig
from excel_writer import build_workbook_v2

load_dotenv()

MAX_REFINEMENTS = 3

app = FastAPI(title="Northlake Bid Excel Generator", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Config ──────────────────────────────────────────────────────────────────


def _cfg() -> OpenAIConfig:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not api_key or not base_url or not model:
        raise RuntimeError(
            "Missing OPENAI_API_KEY, OPENAI_BASE_URL, or OPENAI_MODEL in environment/.env"
        )
    return OpenAIConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=float(os.getenv("TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("MAX_TOKENS", "16000")),
        timeout_s=600.0,
    )


# ─── Document Ingestion ───────────────────────────────────────────────────────


def _ingest(files: List[UploadFile]) -> List[IngestedDoc]:
    docs: List[IngestedDoc] = []
    for f in files:
        data = f.file.read()
        name = f.filename or "uploaded"
        lower = name.lower()
        if lower.endswith(".pdf"):
            text = extract_text_from_pdf(data)
        elif lower.endswith(".docx"):
            text = extract_text_from_docx(data)
        else:
            try:
                text = data.decode("utf-8", errors="ignore")
            except Exception:
                text = ""
        docs.append(IngestedDoc(filename=name, text=text))
    return docs


def _maybe_filter(
    docs: List[IngestedDoc], keywords: List[str], disable: bool
) -> List[IngestedDoc]:
    if disable:
        return docs
    out = []
    for d in docs:
        filtered = keyword_window(
            d.text, keywords=keywords, window_lines=4, max_chars=60_000
        )
        if not filtered.strip():
            filtered = d.text[:30_000]
        out.append(IngestedDoc(filename=d.filename, text=filtered))
    return out


# ─── JSON Helpers ─────────────────────────────────────────────────────────────


def _repair_json(text: str) -> str:
    """Fix common GPT JSON formatting mistakes before parsing."""
    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)
    # Fix comma-formatted numbers inside JSON values e.g. 181,000 → 181000
    # Only targets numbers like 181,000 or 1,234,567 (not commas between keys)
    text = re.sub(r"(\d),(\d{3})(?=\s*[,\}\]\n])", r"\1\2", text)
    # Replace Python literals with JSON equivalents
    text = re.sub(r"\bNone\b", "null", text)
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)
    return text


def _is_truncated(text: str) -> bool:
    """Detect if GPT response was cut off mid-JSON."""
    opens = text.count("{") + text.count("[")
    closes = text.count("}") + text.count("]")
    return opens > closes


def _clean_json(raw: str) -> str:
    """Strip markdown fences and leading/trailing noise, then repair common GPT JSON mistakes."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    match = re.search(r"[\[\{]", text)
    if match:
        text = text[match.start() :]
    last = max(text.rfind("}"), text.rfind("]"))
    if last != -1:
        text = text[: last + 1]
    return _repair_json(text.strip())


# ─── JSON Parse + Retry ───────────────────────────────────────────────────────


async def _parse_json_or_retry_async(
    client: OpenAIClient,
    system: str,
    user: str,
    retries: int = 1,
) -> Dict[str, Any]:
    last = None
    for attempt in range(retries + 1):
        raw = await asyncio.to_thread(client.chat_json, system=system, user=user)
        last = raw

        if _is_truncated(_clean_json(raw)):
            raise HTTPException(
                status_code=502,
                detail=(
                    "TRUNCATED: Model response was cut off mid-JSON. "
                    "Increase MAX_TOKENS in your .env (current default: 16000)."
                ),
            )

        try:
            return json.loads(_clean_json(raw))
        except Exception:
            if attempt >= retries:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        f"Model did not return valid JSON after {retries + 1} attempts. "
                        f"Last response: {raw[:500]}"
                    ),
                )
            user = (
                "Your previous response was not valid JSON.\n"
                "Return ONLY valid JSON that matches the schema exactly.\n"
                "No markdown. No backticks. No explanation. Start with { or [.\n\n"
                + user
            )
    raise HTTPException(
        status_code=502,
        detail=f"JSON parse failed. Last response: {str(last)[:500]}",
    )


# ─── Pydantic models ─────────────────────────────────────────────────────────


class RefinementMessage(BaseModel):
    role: str
    content: str


class RefineRequest(BaseModel):
    project_name: str
    document_context: str
    current_extraction: dict
    conversation_history: List[RefinementMessage]
    user_message: str


# ─── Routes ──────────────────────────────────────────────────────────────────


@app.get("/")
def root():
    return {
        "message": "Northlake Bid Excel Generator API",
        "version": "0.5.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"ok": True, "status": "running"}


# ── V2 endpoint — Cover Page + Tables 1-3 + Quantities ───────────────────────


@app.post("/generate-bid-excel-v2")
async def generate_bid_excel_v2(
    files: List[UploadFile] = File(...),
    project_name: str = Form("Northlake Project"),
    user_name: str = Form(""),
    user_company: str = Form(""),
    user_phone: str = Form(""),
    user_email: str = Form(""),
):
    try:
        cfg = _cfg()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    disable_filter = os.getenv("DISABLE_KEYWORD_FILTER", "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "y",
    )

    user_info = {
        "name": user_name,
        "company": user_company,
        "phone": user_phone,
        "email": user_email,
    }

    docs_full = _ingest(files)
    doc_list = [d.filename for d in docs_full]
    client = OpenAIClient(cfg)
    full_context = build_context(_maybe_filter(docs_full, [], disable_filter))

    # Build all 5 prompts
    p0 = prompt_0_cover_page(user_info, project_name, doc_list)
    p1 = prompt_1_table1(user_info, project_name, doc_list)
    p2 = prompt_2_table2(user_info, project_name, doc_list)
    p3 = prompt_3_table3(user_info, project_name, doc_list)
    pf = prompt_final_quantities(user_info, project_name, doc_list)

    ctx = "\n\nDOCUMENT CONTEXT:\n" + full_context

    print("Starting parallel extraction (Cover Page + Tables 1-3 + Quantities)...")
    out0, out1, out2, out3, outf = await asyncio.gather(
        _parse_json_or_retry_async(client, p0["system"], p0["user"] + ctx, retries=1),
        _parse_json_or_retry_async(client, p1["system"], p1["user"] + ctx, retries=1),
        _parse_json_or_retry_async(client, p2["system"], p2["user"] + ctx, retries=1),
        _parse_json_or_retry_async(client, p3["system"], p3["user"] + ctx, retries=1),
        _parse_json_or_retry_async(client, pf["system"], pf["user"] + ctx, retries=1),
    )
    print("All extractions completed!")

    all_tables = {
        "meta": out1.get("meta", {}),
        "header": out1.get("header", {}),
        "cover_page": out0.get("cover_page", {}),
        "table1": out1.get("table1", {}),
        "table2": out2.get("table2", {}),
        "table3": out3.get("table3", {}),
        "quantity_estimation": outf.get("quantity_estimation", {}),
        "assumptions_or_gaps": (
            out0.get("assumptions_or_gaps", [])
            + out1.get("assumptions_or_gaps", [])
            + out2.get("assumptions_or_gaps", [])
            + out3.get("assumptions_or_gaps", [])
            + outf.get("assumptions_or_gaps", [])
        ),
    }

    xlsx_bytes = build_workbook_v2(all_tables)
    filename = f"{project_name.replace(' ', '_')}_Inspection_Testing_Summary.xlsx"

    return {
        "extraction": all_tables,
        "document_context": full_context[:30000],
        "excel_base64": base64.b64encode(xlsx_bytes).decode(),
        "filename": filename,
    }


# ── Refinement / chat endpoint ────────────────────────────────────────────────


@app.post("/refine-extraction")
async def refine_extraction(req: RefineRequest):
    user_turns = sum(1 for m in req.conversation_history if m.role == "user")
    if user_turns >= MAX_REFINEMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_REFINEMENTS} refinements reached. Please start a new session.",
        )

    try:
        cfg = _cfg()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    client = OpenAIClient(cfg)

    system = f"""You are an expert construction document analyst helping refine a bid extraction.
The user will give you specific correction instructions.
Apply the corrections to the current extraction JSON and return the COMPLETE updated JSON.

CRITICAL: Return ONLY valid JSON. No markdown. No backticks. No explanation.
Start your response with {{ and end with }}.

Current extraction:
{json.dumps(req.current_extraction, indent=2)[:12000]}

Document context (for reference):
{req.document_context[:10000]}
"""

    history_text = "\n\n".join(
        f"[{m.role.upper()}]: {m.content}" for m in req.conversation_history
    )
    flat_user = (history_text + f"\n\n[USER]: {req.user_message}").strip()

    raw = await asyncio.to_thread(client.chat_json, system=system, user=flat_user)
    try:
        updated = json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        retry_user = (
            "Your response was not valid JSON. "
            "Return ONLY the JSON object. No markdown. No explanation. "
            "Start with { and end with }.\n\n" + flat_user
        )
        raw2 = await asyncio.to_thread(client.chat_json, system=system, user=retry_user)
        try:
            updated = json.loads(_clean_json(raw2))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=502,
                detail=f"Model returned invalid JSON during refinement. Preview: {raw2[:300]}",
            )

    xlsx_bytes = build_workbook_v2(updated)

    return {
        "extraction": updated,
        "excel_base64": base64.b64encode(xlsx_bytes).decode(),
        "refinements_used": user_turns + 1,
        "refinements_remaining": MAX_REFINEMENTS - (user_turns + 1),
    }
