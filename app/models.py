from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


class FileCategory(StrEnum):
    RFP = "rfp"
    ATTACHMENT = "attachment"
    COMPANY_MATERIAL = "company_material"


class ProcessingStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class Project:
    id: str
    name: str
    created_at: str

    @classmethod
    def create(cls, name: str) -> "Project":
        return cls(id=str(uuid4()), name=name.strip(), created_at=datetime.now(UTC).isoformat())


@dataclass
class SourceLocation:
    label: str
    page: int | None = None
    sheet: str | None = None
    section: str | None = None


@dataclass
class ExtractedBlock:
    id: str
    kind: str
    text: str
    source: SourceLocation

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        return value


@dataclass
class ProjectFile:
    id: str
    project_id: str
    original_name: str
    stored_name: str
    category: FileCategory
    file_type: str
    status: ProcessingStatus
    created_at: str
    error_message: str | None = None
    block_count: int = 0

    @classmethod
    def create(
        cls,
        project_id: str,
        original_name: str,
        stored_name: str,
        category: FileCategory,
        file_type: str,
    ) -> "ProjectFile":
        return cls(
            id=str(uuid4()),
            project_id=project_id,
            original_name=original_name,
            stored_name=stored_name,
            category=category,
            file_type=file_type,
            status=ProcessingStatus.PENDING,
            created_at=datetime.now(UTC).isoformat(),
        )


DATA_DIR = Path("data")
