from __future__ import annotations

import re
from uuid import uuid4

from app.models import ChecklistItem, ExtractedBlock, FileCategory, ProjectFile


DATE_PATTERN = re.compile(r"\b(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", re.IGNORECASE)
TIME_PATTERN = re.compile(r"\b(?:\d{1,2}:\d{2}\s*(?:CET|CEST|UTC|GMT)?)\b", re.IGNORECASE)

RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("submission", "Submission instruction", ("submit", "submission", "procurement portal", "email", "signed pdf")),
    ("deadline", "Deadline", ("deadline", "due", "by ", "closing date", "no later than")),
    ("attachment", "Required attachment", ("attach", "attachment", "appendix", "schedule", "declaration", "certificate")),
    ("eligibility", "Mandatory requirement", ("must", "mandatory", "required", "shall", "minimum")),
    ("evaluation", "Evaluation criterion", ("evaluation", "scoring", "weighting", "criterion", "points")),
)


def build_checklist(files: list[ProjectFile], blocks_by_file: dict[str, list[ExtractedBlock]]) -> list[ChecklistItem]:
    """Create a reviewable checklist from RFP-source text without making unsupported inferences."""
    items: list[ChecklistItem] = []
    for project_file in files:
        if project_file.category not in {FileCategory.RFP, FileCategory.ATTACHMENT}:
            continue
        for block in blocks_by_file.get(project_file.id, []):
            sentences = _sentences(block.text)
            for sentence in sentences:
                category = _classify(sentence)
                if category is None:
                    continue
                rule_category, title = category
                detail = sentence.strip()
                if rule_category == "deadline" and not (DATE_PATTERN.search(detail) or TIME_PATTERN.search(detail)):
                    continue
                items.append(
                    ChecklistItem(
                        id=str(uuid4()),
                        category=rule_category,
                        title=title,
                        detail=detail,
                        source_file_id=project_file.id,
                        source_block_id=block.id,
                        source_label=f"{project_file.original_name} · {block.source.label}",
                    )
                )
    return _deduplicate(items)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def _classify(sentence: str) -> tuple[str, str] | None:
    value = sentence.lower()
    if (DATE_PATTERN.search(sentence) or TIME_PATTERN.search(sentence)) and any(keyword in value for keyword in ("submit", "submission", "deadline", "due", "by ")):
        return "deadline", "Deadline"
    for category, title, keywords in RULES:
        if any(keyword in value for keyword in keywords):
            return category, title
    return None


def _deduplicate(items: list[ChecklistItem]) -> list[ChecklistItem]:
    seen: set[tuple[str, str]] = set()
    unique: list[ChecklistItem] = []
    for item in items:
        key = (item.category, item.detail.lower())
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique
