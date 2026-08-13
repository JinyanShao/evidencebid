# EvidenceBid

EvidenceBid is a source-aware RFP workspace. It turns bid documents and company material into a traceable compliance checklist, an evidence-backed response workspace, and an exportable response sheet.

Every checklist item and response draft remains linked to the source material that supports it. Export preflight blocks unsupported drafts, so missing evidence is visible before a response leaves the workspace.

## Current capabilities

- Create a bid project
- Upload and categorize RFP files, RFP attachments, and company material
- Parse DOCX and XLSX files with Docling; extract text PDFs locally without OCR
- Browse extracted text by page, section, table, or worksheet
- Preserve original uploads and show clear processing failures
- Build a source-linked RFP compliance checklist
- Prepare editable response drafts with linked company evidence
- Block unsupported drafts during export preflight
- Export completed response drafts and their source trail as UTF-8 CSV

## Product workflow

1. Start the application.
2. Select **Open demo project** from the home page.
3. Review the RFP and company-source files.
4. Select **Build checklist** to create source-linked submission, deadline, attachment, and mandatory-requirement items.
5. Select **Prepare response drafts** to create editable drafts from matching company-source material.
6. Resolve any export preflight issues, then export the evidence-linked response CSV.

The demo project provides inspectable source material for exploring this workflow without preparing files first.

## Current boundaries

EvidenceBid currently does **not** use an LLM to generate prose. It also does not perform OCR, support scanned or password-protected PDFs, or preserve the customer's original document formatting during export.

These constraints are intentional: the current product prioritizes source traceability, explicit evidence review, and predictable exports over automated prose generation or broad document-format coverage.

## Supported files

Text-based PDF, DOCX, and XLSX files are supported. Scanned or password-protected PDFs are rejected with an actionable message. XLSX extraction reads sheet names and cell values; it does not preserve formulas, formatting, or merged-cell layout.

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
