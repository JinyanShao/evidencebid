from app.analyzer import build_checklist
from app.models import ExtractedBlock, FileCategory, ProjectFile, SourceLocation


def test_checklist_extracts_deadlines_and_mandatory_requirements():
    project_file = ProjectFile.create("project-1", "rfp.pdf", "rfp.pdf", FileCategory.RFP, "pdf")
    block = ExtractedBlock(
        id="block-1",
        kind="page text",
        text="Submit the signed PDF by 16:00 CET on 18 September 2026. Suppliers must hold ISO 27001 certification.",
        source=SourceLocation("Page 1", page=1),
    )

    items = build_checklist([project_file], {project_file.id: [block]})

    assert {item.category for item in items} == {"deadline", "eligibility"}
    assert all(item.source_file_id == project_file.id for item in items)
    assert all(item.source_block_id == block.id for item in items)
