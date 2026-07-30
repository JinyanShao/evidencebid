# EvidenceBid - Stage 1

EvidenceBid is a source-aware RFP workspace. This stage implements only document intake: projects, categorized uploads, PDF/DOCX/XLSX parsing, and readable source locations.

## Scope

- Create a bid project
- Upload and categorize RFP files, RFP attachments, and company material
- Parse DOCX and XLSX files with Docling; extract text PDFs locally without OCR
- Browse extracted text by page, section, table, or worksheet
- Preserve original uploads and show clear processing failures

It does **not** analyse RFP requirements, generate answers, perform OCR, or support scanned PDFs.

## Run locally

```bash
UV_CACHE_DIR=./work/uv-cache uv sync --python /opt/homebrew/bin/python3.11
UV_CACHE_DIR=./work/uv-cache uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

## Test

```bash
UV_CACHE_DIR=./work/uv-cache uv run pytest
```

## Supported files

Text-based PDF, DOCX, and XLSX are supported in this first version. Scanned or password-protected PDFs are rejected with an actionable message. XLSX extraction reads sheet names and cell values; it does not preserve formulas, formatting, or merged-cell layout.
