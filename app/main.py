from __future__ import annotations

import csv
import io
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.analyzer import build_checklist
from app.demo import ensure_demo_project
from app.models import DATA_DIR, FileCategory, ProcessingStatus, ProjectFile
from app.parser import DocumentParseError, SUPPORTED_EXTENSIONS, parse_document
from app.preflight import can_export, review_responses
from app.responses import build_response_workspace
from app.store import Store


BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = DATA_DIR / "uploads"
store = Store(DATA_DIR)

app = FastAPI(title="EvidenceBid")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _project_or_404(project_id: str):
    project = store.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _file_or_404(file_id: str):
    project_file = store.get_file(file_id)
    if project_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return project_file


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"projects": store.list_projects()})


@app.get("/demo")
def open_demo():
    project = ensure_demo_project(store)
    return RedirectResponse(url=f"/projects/{project.id}", status_code=303)


@app.post("/projects")
def create_project(name: str = Form(...)):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Project name is required")
    project = store.create_project(name)
    return RedirectResponse(url=f"/projects/{project.id}", status_code=303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(request: Request, project_id: str):
    project = _project_or_404(project_id)
    responses = store.get_responses(project_id)
    return templates.TemplateResponse(
        request,
        "project.html",
        {
            "project": project,
            "files": store.list_files(project_id),
            "categories": FileCategory,
            "checklist": store.get_analysis(project_id),
            "responses": responses,
            "preflight_issues": review_responses(responses),
            "can_export": can_export(responses),
        },
    )


@app.post("/projects/{project_id}/files")
async def upload_file(
    project_id: str,
    category: FileCategory = Form(...),
    upload: UploadFile = File(...),
):
    _project_or_404(project_id)
    original_name = Path(upload.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=422, detail="Upload a text PDF, DOCX, or XLSX file.")

    project_dir = UPLOAD_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4()}{suffix}"
    target_path = project_dir / stored_name
    with target_path.open("wb") as target:
        shutil.copyfileobj(upload.file, target)

    project_file = ProjectFile.create(project_id, original_name, stored_name, category, suffix.lstrip("."))
    store.save_file(project_file)
    project_file.status = ProcessingStatus.PROCESSING
    store.update_file(project_file)
    try:
        blocks = parse_document(target_path)
    except DocumentParseError as exc:
        project_file.status = ProcessingStatus.FAILED
        project_file.error_message = str(exc)
    else:
        store.save_blocks(project_file.id, blocks)
        project_file.status = ProcessingStatus.READY
        project_file.block_count = len(blocks)
    store.update_file(project_file)
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@app.post("/projects/{project_id}/analyze")
def analyze_project(project_id: str):
    _project_or_404(project_id)
    files = [project_file for project_file in store.list_files(project_id) if project_file.status == ProcessingStatus.READY]
    blocks_by_file = {project_file.id: store.get_blocks(project_file.id) for project_file in files}
    store.save_analysis(project_id, build_checklist(files, blocks_by_file))
    return RedirectResponse(url=f"/projects/{project_id}#checklist", status_code=303)


@app.post("/projects/{project_id}/responses/prepare")
def prepare_responses(project_id: str):
    _project_or_404(project_id)
    files = [project_file for project_file in store.list_files(project_id) if project_file.status == ProcessingStatus.READY]
    blocks_by_file = {project_file.id: store.get_blocks(project_file.id) for project_file in files}
    store.save_responses(project_id, build_response_workspace(files, blocks_by_file))
    return RedirectResponse(url=f"/projects/{project_id}#responses", status_code=303)


@app.post("/projects/{project_id}/responses/{response_id}")
def update_response(project_id: str, response_id: str, draft: str = Form(...)):
    _project_or_404(project_id)
    if not store.update_response_draft(project_id, response_id, draft):
        raise HTTPException(status_code=404, detail="Response entry not found")
    return RedirectResponse(url=f"/projects/{project_id}#responses", status_code=303)


@app.get("/projects/{project_id}/responses/export.csv")
def export_responses(project_id: str):
    project = _project_or_404(project_id)
    entries = store.get_responses(project_id)
    if not can_export(entries):
        raise HTTPException(status_code=409, detail="Resolve blocking preflight issues before exporting")

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Question", "Response draft", "Status", "RFP source", "Evidence sources"])
    for entry in entries:
        writer.writerow(
            [
                entry.question,
                entry.draft,
                entry.status,
                entry.source_label,
                " | ".join(item["label"] for item in entry.evidence),
            ]
        )
    filename = f"{''.join(character if character.isalnum() else '-' for character in project.name).strip('-') or 'evidencebid'}-responses.csv"
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/projects/{project_id}/files/{file_id}", response_class=HTMLResponse)
def file_detail(request: Request, project_id: str, file_id: str):
    project = _project_or_404(project_id)
    project_file = _file_or_404(file_id)
    if project_file.project_id != project.id:
        raise HTTPException(status_code=404, detail="File not found in this project")
    return templates.TemplateResponse(
        request,
        "file.html",
        {"project": project, "file": project_file, "blocks": store.get_blocks(file_id)},
    )


@app.get("/projects/{project_id}/files/{file_id}/download")
def download_original(project_id: str, file_id: str):
    _project_or_404(project_id)
    project_file = _file_or_404(file_id)
    if project_file.project_id != project_id:
        raise HTTPException(status_code=404, detail="File not found in this project")
    if not project_file.stored_name:
        raise HTTPException(status_code=404, detail="The demonstration source has no downloadable original file")
    path = UPLOAD_DIR / project_id / project_file.stored_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Original file is unavailable")
    return FileResponse(path, filename=project_file.original_name)
