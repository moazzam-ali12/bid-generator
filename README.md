# Northlake Qwen → 3-Prompt → 1 Excel (FastAPI)

This project scaffolds an API that:
1) accepts a set of uploaded documents (PDF/DOCX),
2) runs 3 prompts against a Qwen/OpenAI-compatible chat endpoint, and
3) returns one Excel workbook with 3 tabs.

> NOTE: You must provide your own Qwen API base URL + key + model name.
> Many Qwen deployments expose an OpenAI-compatible endpoint at `/v1/chat/completions`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env with your values

uvicorn app:app --reload --port 8000
```

Then open: http://127.0.0.1:8000/docs

## API

POST `/generate-bid-excel`

- `files`: one or more PDFs/DOCX files
- optional: `project_name` (string)

Returns: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

## Output

Workbook contains 3 sheets:
- `01_Geotech_Table1`  (Prompt 1)
- `02_Concrete_Table2` (Prompt 2)
- `03_Rebar_SI_SIP`    (Prompt 3, contains Tables 3–5 stacked)

If you prefer 5 tabs (one per table), see `excel_writer.py` (`SPLIT_TABLES_TO_TABS=True`).

## How it keeps AI honest

Prompts require:
- **strict JSON only**
- `NOT SPECIFIED` when a field isn't found
- a `sources` field per row like `"<filename> p.<page>"` or `"<filename> sheet <id>"`

The server rejects non-JSON responses and retries once with a "repair JSON" instruction.

## Important
Construction drawings can be huge. This scaffold uses keyword-window extraction to reduce context.
For production, consider a proper retrieval step (per-table keyword index or embeddings).

