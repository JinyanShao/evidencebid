from __future__ import annotations

import re
from collections import Counter
from uuid import uuid4

from app.models import ExtractedBlock, FileCategory, ProjectFile, ResponseEntry


QUESTION_STARTERS = ("describe", "provide", "confirm", "explain", "list", "outline", "demonstrate")
STOP_WORDS = {"about", "after", "against", "and", "are", "can", "describe", "evidence", "for", "from", "how", "information", "into", "meet", "must", "of", "or", "provide", "required", "service", "the", "this", "to", "will", "with", "your"}


def build_response_workspace(files: list[ProjectFile], blocks_by_file: dict[str, list[ExtractedBlock]]) -> list[ResponseEntry]:
    questions = _questions(files, blocks_by_file)
    company_blocks = _company_blocks(files, blocks_by_file)
    return [_response_entry(question, company_blocks) for question in questions]


def _questions(files: list[ProjectFile], blocks_by_file: dict[str, list[ExtractedBlock]]) -> list[tuple[ProjectFile, ExtractedBlock, str]]:
    items: list[tuple[ProjectFile, ExtractedBlock, str]] = []
    for project_file in files:
        if project_file.category not in {FileCategory.RFP, FileCategory.ATTACHMENT}:
            continue
        for block in blocks_by_file.get(project_file.id, []):
            for sentence in _sentences(block.text):
                if _is_question(sentence):
                    items.append((project_file, block, sentence))
    return items


def _company_blocks(files: list[ProjectFile], blocks_by_file: dict[str, list[ExtractedBlock]]) -> list[tuple[ProjectFile, ExtractedBlock]]:
    return [
        (project_file, block)
        for project_file in files
        if project_file.category == FileCategory.COMPANY_MATERIAL
        for block in blocks_by_file.get(project_file.id, [])
        if block.text.strip()
    ]


def _response_entry(question: tuple[ProjectFile, ExtractedBlock, str], company_blocks: list[tuple[ProjectFile, ExtractedBlock]]) -> ResponseEntry:
    source_file, source_block, text = question
    matches = _matches(text, company_blocks)
    evidence = [
        {"file_id": project_file.id, "block_id": block.id, "label": f"{project_file.original_name} · {block.source.label}", "text": block.text}
        for project_file, block in matches
    ]
    draft = _draft(evidence)
    return ResponseEntry(
        id=str(uuid4()),
        question=text,
        source_file_id=source_file.id,
        source_block_id=source_block.id,
        source_label=f"{source_file.original_name} · {source_block.source.label}",
        draft=draft,
        status="evidence ready" if evidence else "evidence needed",
        evidence=evidence,
    )


def _matches(question: str, company_blocks: list[tuple[ProjectFile, ExtractedBlock]]) -> list[tuple[ProjectFile, ExtractedBlock]]:
    question_words = _words(question)
    ranked = sorted(
        ((len(question_words & _words(block.text)), project_file, block) for project_file, block in company_blocks),
        key=lambda item: item[0],
        reverse=True,
    )
    return [(project_file, block) for score, project_file, block in ranked[:3] if score > 0]


def _draft(evidence: list[dict[str, str]]) -> str:
    if not evidence:
        return "No matching company material was found. Add or select evidence before responding."
    return "\n\n".join(item["text"] for item in evidence)


def _is_question(sentence: str) -> bool:
    normalized = sentence.strip().lower()
    return sentence.strip().endswith("?") or normalized.startswith(QUESTION_STARTERS)


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", text) if part.strip()]


def _words(text: str) -> set[str]:
    return {word for word, count in Counter(re.findall(r"[a-z0-9][a-z0-9-]+", text.lower())).items() if count and word not in STOP_WORDS}
