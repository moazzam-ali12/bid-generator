\
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Iterable, Dict
from io import BytesIO
import re

from pypdf import PdfReader
from docx import Document as DocxDocument


@dataclass
class IngestedDoc:
    filename: str
    text: str


def extract_text_from_pdf(data: bytes, max_pages: int | None = None) -> str:
    reader = PdfReader(BytesIO(data))
    pages = reader.pages
    if max_pages is not None:
        pages = pages[:max_pages]

    out = []
    for i, page in enumerate(pages, start=1):
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        t = t.strip()
        if t:
            out.append(f"--- PAGE {i} ---\n{t}\n")
        else:
            out.append(f"--- PAGE {i} ---\n[NO EXTRACTABLE TEXT]\n")
    return "\n".join(out)


def extract_text_from_docx(data: bytes) -> str:
    doc = DocxDocument(BytesIO(data))
    paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paras)


def keyword_window(text: str, keywords: List[str], window_lines: int = 3, max_chars: int = 90_000) -> str:
    """
    Simple extraction: keep lines near any keyword. Reduces prompt size.
    """
    if not text.strip():
        return ""

    lines = text.splitlines()
    hits = [False] * len(lines)

    kws = [k.lower() for k in keywords if k.strip()]
    for idx, line in enumerate(lines):
        low = line.lower()
        if any(k in low for k in kws):
            start = max(0, idx - window_lines)
            end = min(len(lines), idx + window_lines + 1)
            for j in range(start, end):
                hits[j] = True

    kept = [ln for ln, h in zip(lines, hits) if h]
    out = "\n".join(kept).strip()
    if len(out) > max_chars:
        out = out[:max_chars] + "\n...[TRUNCATED]..."
    return out


def build_context(docs: List[IngestedDoc]) -> str:
    parts = []
    for d in docs:
        parts.append(f"===== BEGIN DOC: {d.filename} =====\n{d.text}\n===== END DOC: {d.filename} =====\n")
    return "\n".join(parts)


KEYWORDS_PROMPT_1 = [
    "compaction", "proctor", "moisture", "plasticity", "PI", "liquid limit", "select fill",
    "flexible base", "TxDOT", "testing", "field density", "lift", "subgrade",
]
KEYWORDS_PROMPT_2 = [
    "concrete", "PCC", "psi", "f'c", "slump", "air", "cylinder", "testing", "thickness",
    "sidewalk", "pavement", "slab", "grade beam", "footing", "curb", "joint",
]
KEYWORDS_PROMPT_3 = [
    "#", "rebar", "reinforcing", "bar", "stirrups", "dowel", "weld", "fillet", "CJP", "PJP",
    "bolt", "bolting", "CFMF", "cold formed", "light gauge", "SIP", "panel", "connection",
    "special inspection",
]
