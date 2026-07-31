from __future__ import annotations

from dataclasses import dataclass

from app.models import ResponseEntry


@dataclass
class PreflightIssue:
    response_id: str | None
    severity: str
    message: str


def review_responses(entries: list[ResponseEntry]) -> list[PreflightIssue]:
    if not entries:
        return [PreflightIssue(None, "blocking", "Prepare response drafts before exporting.")]

    issues: list[PreflightIssue] = []
    for entry in entries:
        if not entry.evidence:
            issues.append(PreflightIssue(entry.id, "blocking", f'No evidence supports: "{entry.question}"'))
        if not entry.draft.strip() or entry.draft.startswith("No matching company material was found"):
            issues.append(PreflightIssue(entry.id, "blocking", f'No usable draft exists for: "{entry.question}"'))
    return issues


def can_export(entries: list[ResponseEntry]) -> bool:
    return not any(issue.severity == "blocking" for issue in review_responses(entries))
