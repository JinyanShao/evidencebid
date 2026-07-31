from app.models import ResponseEntry
from app.preflight import can_export, review_responses


def response(*, evidence=True, draft="Supported response"):
    return ResponseEntry(
        id="response-1",
        question="Describe availability.",
        source_file_id="rfp-1",
        source_block_id="block-1",
        source_label="RFP.pdf · Page 1",
        draft=draft,
        status="evidence ready" if evidence else "evidence needed",
        evidence=[{"file_id": "company-1", "block_id": "source-1", "label": "Facts.docx", "text": "99.95%"}] if evidence else [],
    )


def test_preflight_allows_supported_response():
    entries = [response()]
    assert review_responses(entries) == []
    assert can_export(entries)


def test_preflight_blocks_missing_evidence_and_placeholder():
    entries = [response(evidence=False, draft="No matching company material was found. Add or select evidence before responding.")]
    assert len(review_responses(entries)) == 2
    assert not can_export(entries)
