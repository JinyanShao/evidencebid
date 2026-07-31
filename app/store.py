from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.models import ChecklistItem, ExtractedBlock, FileCategory, ProcessingStatus, Project, ProjectFile, ResponseEntry, SourceLocation


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "store.json"
        if not self.db_path.exists():
            self._write({"projects": [], "files": [], "blocks": {}, "analyses": {}, "responses": {}})

    def _read(self) -> dict:
        data = json.loads(self.db_path.read_text(encoding="utf-8"))
        data.setdefault("analyses", {})
        data.setdefault("responses", {})
        return data

    def _write(self, data: dict) -> None:
        self.db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_project(self, name: str) -> Project:
        project = Project.create(name)
        self.create_project_record(project)
        return project

    def create_project_record(self, project: Project) -> None:
        data = self._read()
        data["projects"].append(asdict(project))
        self._write(data)

    def list_projects(self) -> list[Project]:
        return [Project(**item) for item in self._read()["projects"]]

    def get_project(self, project_id: str) -> Project | None:
        return next((item for item in self.list_projects() if item.id == project_id), None)

    def save_file(self, project_file: ProjectFile) -> None:
        data = self._read()
        data["files"].append({**asdict(project_file), "category": project_file.category.value, "status": project_file.status.value})
        self._write(data)

    def update_file(self, project_file: ProjectFile) -> None:
        data = self._read()
        updated = {**asdict(project_file), "category": project_file.category.value, "status": project_file.status.value}
        data["files"] = [updated if item["id"] == project_file.id else item for item in data["files"]]
        self._write(data)

    def get_file(self, file_id: str) -> ProjectFile | None:
        for item in self._read()["files"]:
            if item["id"] == file_id:
                return ProjectFile(
                    **{**item, "category": FileCategory(item["category"]), "status": ProcessingStatus(item["status"])}
                )
        return None

    def list_files(self, project_id: str) -> list[ProjectFile]:
        items = []
        for item in self._read()["files"]:
            if item["project_id"] == project_id:
                items.append(ProjectFile(**{**item, "category": FileCategory(item["category"]), "status": ProcessingStatus(item["status"])}))
        return items

    def save_blocks(self, file_id: str, blocks: list[ExtractedBlock]) -> None:
        data = self._read()
        data["blocks"][file_id] = [block.to_dict() for block in blocks]
        self._write(data)

    def get_blocks(self, file_id: str) -> list[ExtractedBlock]:
        blocks = self._read()["blocks"].get(file_id, [])
        return [ExtractedBlock(id=item["id"], kind=item["kind"], text=item["text"], source=SourceLocation(**item["source"])) for item in blocks]

    def save_analysis(self, project_id: str, items: list[ChecklistItem]) -> None:
        data = self._read()
        data["analyses"][project_id] = [item.to_dict() for item in items]
        self._write(data)

    def get_analysis(self, project_id: str) -> list[ChecklistItem]:
        return [ChecklistItem(**item) for item in self._read()["analyses"].get(project_id, [])]

    def save_responses(self, project_id: str, entries: list[ResponseEntry]) -> None:
        data = self._read()
        data["responses"][project_id] = [entry.to_dict() for entry in entries]
        self._write(data)

    def get_responses(self, project_id: str) -> list[ResponseEntry]:
        return [ResponseEntry(**item) for item in self._read()["responses"].get(project_id, [])]

    def update_response_draft(self, project_id: str, response_id: str, draft: str) -> bool:
        data = self._read()
        entries = data["responses"].get(project_id, [])
        for entry in entries:
            if entry["id"] == response_id:
                entry["draft"] = draft.strip()
                entry["status"] = "edited"
                self._write(data)
                return True
        return False
