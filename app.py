from __future__ import annotations

import base64
import json
import os
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
    prompt_1_table1,
    prompt_2_table2,
    prompt_3_tables3_4_5,
    prompt_4_tables6_7,
    prompt_5_tables8_9_10,
)
from openai_client import OpenAIClient, OpenAIConfig
from excel_writer import build_workbook, build_workbook_v2

load_dotenv()

MAX_REFINEMENTS = 3

app = FastAPI(title="Northlake Bid Excel Generator", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Config ──────────────────────────────────────────────────────────────────

def _cfg() -> OpenAIConfig:
    api_key  = os.getenv("OPENAI_API_KEY",  "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    model    = os.getenv("OPENAI_MODEL",    "").strip()
    if not api_key or not base_url or not model:
        raise RuntimeError(
            "Missing OPENAI_API_KEY, OPENAI_BASE_URL, or OPENAI_MODEL in environment/.env"
        )
    return OpenAIConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=float(os.getenv("TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("MAX_TOKENS", "4000")),
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
        filtered = keyword_window(d.text, keywords=keywords, window_lines=4, max_chars=60_000)
        if not filtered.strip():
            filtered = d.text[:30_000]
        out.append(IngestedDoc(filename=d.filename, text=filtered))
    return out


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
        try:
            return json.loads(raw)
        except Exception:
            if attempt >= retries:
                raise HTTPException(
                    status_code=502,
                    detail=f"Model did not return valid JSON. Last response: {raw[:2000]}",
                )
            user = (
                "Your previous response was not valid JSON.\n"
                "Return ONLY valid JSON that matches the schema. No markdown. No extra keys.\n\n"
                + user
            )
    raise HTTPException(
        status_code=502,
        detail=f"Model did not return valid JSON. Last response: {str(last)[:2000]}",
    )


# ─── Pydantic model for chat refinement ──────────────────────────────────────

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
        "version": "0.3.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"ok": True, "status": "running"}


# ── Original endpoint — kept for backwards compatibility ──────────────────────

@app.post("/generate-bid-excel")
async def generate_bid_excel(
    files: List[UploadFile] = File(...),
    project_name: str = Form("Northlake 7-Eleven"),
):
    try:
        cfg = _cfg()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    disable_filter = os.getenv("DISABLE_KEYWORD_FILTER", "false").strip().lower() in (
        "1", "true", "yes", "y"
    )

    docs_full = _ingest(files)
    doc_list  = [d.filename for d in docs_full]
    client    = OpenAIClient(cfg)

    docs1 = _maybe_filter(docs_full, KEYWORDS_PROMPT_1, disable_filter)
    ctx1  = build_context(docs1)
    p1    = prompt_1_table1(project_name, doc_list)
    user1 = p1["user"] + "\n\nDOCUMENT CONTEXT:\n" + ctx1

    docs2 = _maybe_filter(docs_full, KEYWORDS_PROMPT_2, disable_filter)
    ctx2  = build_context(docs2)
    p2    = prompt_2_table2(project_name, doc_list)
    user2 = p2["user"] + "\n\nDOCUMENT CONTEXT:\n" + ctx2

    docs3 = _maybe_filter(docs_full, KEYWORDS_PROMPT_3, disable_filter)
    ctx3  = build_context(docs3)
    p3    = prompt_3_tables3_4_5(project_name, doc_list)
    user3 = p3["user"] + "\n\nDOCUMENT CONTEXT:\n" + ctx3

    print("Starting parallel API calls (original endpoint)...")
    out1, out2, out3 = await asyncio.gather(
        _parse_json_or_retry_async(client, p1["system"], user1, retries=1),
        _parse_json_or_retry_async(client, p2["system"], user2, retries=1),
        _parse_json_or_retry_async(client, p3["system"], user3, retries=1),
    )
    print("All API calls completed!")

    xlsx_bytes = build_workbook(out1, out2, out3)
    filename   = f"{project_name.replace(' ', '_')}_Bid_Tables.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── V2 endpoint — all 10 tables, returns JSON + base64 Excel for chat UI ─────

@app.post("/generate-bid-excel-v2")
async def generate_bid_excel_v2(
    files: List[UploadFile] = File(...),
    project_name: str = Form("Northlake Project"),
):
    try:
        cfg = _cfg()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    disable_filter = os.getenv("DISABLE_KEYWORD_FILTER", "false").strip().lower() in (
        "1", "true", "yes", "y"
    )

    docs_full    = _ingest(files)
    doc_list     = [d.filename for d in docs_full]
    client       = OpenAIClient(cfg)
    full_context = build_context(
        _maybe_filter(docs_full, [], disable_filter)  # full text, no keyword filter for v2
    )

    # Build all 5 prompts
    p1 = prompt_1_table1(project_name, doc_list)
    p2 = prompt_2_table2(project_name, doc_list)
    p3 = prompt_3_tables3_4_5(project_name, doc_list)
    p4 = prompt_4_tables6_7(project_name, doc_list)
    p5 = prompt_5_tables8_9_10(project_name, doc_list)

    # Append full document context to each prompt
    u1 = p1["user"] + "\n" + full_context
    u2 = p2["user"] + "\n" + full_context
    u3 = p3["user"] + "\n" + full_context
    u4 = p4["user"] + "\n" + full_context
    u5 = p5["user"] + "\n" + full_context

    # Run all 5 prompts in parallel
    print("Starting parallel extraction for all 10 tables...")
    out1, out2, out3, out4, out5 = await asyncio.gather(
        _parse_json_or_retry_async(client, p1["system"], u1, retries=1),
        _parse_json_or_retry_async(client, p2["system"], u2, retries=1),
        _parse_json_or_retry_async(client, p3["system"], u3, retries=1),
        _parse_json_or_retry_async(client, p4["system"], u4, retries=1),
        _parse_json_or_retry_async(client, p5["system"], u5, retries=1),
    )
    print("All 10 tables extracted successfully!")

    # Merge all outputs
    all_tables = {
        "meta":    out1.get("meta",    {}),
        "header":  out1.get("header",  {}),
        "table1":  out1.get("table1",  {}),
        "table2":  out2.get("table2",  {}),
        "table3":  out3.get("table3",  {}),
        "table4":  out3.get("table4",  {}),
        "table5":  out3.get("table5",  {}),
        "table6":  out4.get("table6",  {}),
        "table7":  out4.get("table7",  {}),
        "table8":  out5.get("table8",  {}),
        "table9":  out5.get("table9",  {}),
        "table10": out5.get("table10", {}),
        "assumptions_or_gaps": (
            out1.get("assumptions_or_gaps", [])
            + out2.get("assumptions_or_gaps", [])
            + out3.get("assumptions_or_gaps", [])
            + out4.get("assumptions_or_gaps", [])
            + out5.get("assumptions_or_gaps", [])
        ),
    }

    xlsx_bytes = build_workbook_v2(all_tables)
    filename   = f"{project_name.replace(' ', '_')}_Inspection_Testing_Summary.xlsx"

    return {
        "extraction":       all_tables,
        "document_context": full_context[:30000],  # capped for chat refinement turns
        "excel_base64":     base64.b64encode(xlsx_bytes).decode(),
        "filename":         filename,
    }


# ── Refinement / chat endpoint ────────────────────────────────────────────────

@app.post("/refine-extraction")
async def refine_extraction(req: RefineRequest):
    """
    Conversational refinement — up to MAX_REFINEMENTS turns.
    UI tracks turn count and blocks further calls after limit.
    """
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
You have already extracted data from project documents into a structured JSON.
The user will give you specific correction instructions.
Return the COMPLETE updated JSON with corrections applied.
Return ONLY valid JSON. No markdown fences. No explanation outside the JSON.

Current extraction:
{json.dumps(req.current_extraction, indent=2)}

Document context (for reference):
{req.document_context[:15000]}
"""

    # Flatten conversation history into a single user message
    history_text = "\n\n".join(
        f"[{m.role.upper()}]: {m.content}" for m in req.conversation_history
    )
    flat_user = history_text + f"\n\n[USER]: {req.user_message}"

    raw = await asyncio.to_thread(client.chat_json, system=system, user=flat_user)
    try:
        updated = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="Model returned invalid JSON during refinement.",
        )

    xlsx_bytes = build_workbook_v2(updated)

    return {
        "extraction":           updated,
        "excel_base64":         base64.b64encode(xlsx_bytes).decode(),
        "refinements_used":     user_turns + 1,
        "refinements_remaining": MAX_REFINEMENTS - (user_turns + 1),
    }