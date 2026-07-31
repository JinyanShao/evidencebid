from app.models import ExtractedBlock, FileCategory, ProjectFile, SourceLocation
from app.responses import build_response_workspace


def test_response_workspace_matches_company_evidence():
    rfp_file = ProjectFile.create("project-1", "rfp.pdf", "rfp.pdf", FileCategory.RFP, "pdf")
    company_file = ProjectFile.create("project-1", "capabilities.docx", "capabilities.docx", FileCategory.COMPANY_MATERIAL, "docx")
    rfp_block = ExtractedBlock(
        id="rfp-1",
        kind="page text",
        text="Describe how your service will meet the required availability commitment.",
        source=SourceLocation("Page 2", page=2),
    )
    company_block = ExtractedBlock(
        id="company-1",
        kind="text",
        text="The service platform is operated with a 99.95% monthly availability target.",
        source=SourceLocation("Document"),
    )

    entries = build_response_workspace([rfp_file, company_file], {rfp_file.id: [rfp_block], company_file.id: [company_block]})

    assert len(entries) == 1
    assert entries[0].status == "evidence ready"
    assert entries[0].evidence[0]["file_id"] == company_file.id
    assert "99.95%" in entries[0].draft
