from __future__ import annotations

from app.models import ExtractedBlock, FileCategory, ProcessingStatus, Project, ProjectFile, SourceLocation
from app.store import Store


DEMO_PROJECT_NAME = "Alpine Rail Service Platform"


def ensure_demo_project(store: Store) -> Project:
    existing = next((project for project in store.list_projects() if project.is_demo), None)
    if existing:
        return existing

    project = Project.create(DEMO_PROJECT_NAME)
    project.is_demo = True
    store.create_project_record(project)

    rfp_file = ProjectFile.create(project.id, "Alpine Rail RFP.pdf", "", FileCategory.RFP, "pdf")
    rfp_file.status = ProcessingStatus.READY
    rfp_file.block_count = 6
    store.save_file(rfp_file)
    store.save_blocks(
        rfp_file.id,
        [
            ExtractedBlock("demo-001", "title", "Request for Proposal: Passenger Service Platform", SourceLocation("Page 1", page=1)),
            ExtractedBlock("demo-002", "section header", "1. Submission instructions", SourceLocation("Page 1", page=1)),
            ExtractedBlock("demo-003", "page text", "Submit one signed PDF through the procurement portal by 16:00 CET on 18 September 2026.", SourceLocation("Page 1", page=1)),
            ExtractedBlock("demo-004", "section header", "2. Mandatory requirements", SourceLocation("Page 2", page=2)),
            ExtractedBlock("demo-005", "page text", "Suppliers must provide ISO 27001 certification, a 99.9% availability commitment, and two relevant rail-sector references. Attach the completed pricing schedule and the signed declaration of compliance.", SourceLocation("Page 2", page=2)),
            ExtractedBlock("demo-006", "page text", "Describe how your service will meet the required availability commitment and provide evidence of information-security certification.", SourceLocation("Page 3", page=3)),
        ],
    )

    material_file = ProjectFile.create(project.id, "Company capabilities.docx", "", FileCategory.COMPANY_MATERIAL, "docx")
    material_file.status = ProcessingStatus.READY
    material_file.block_count = 2
    store.save_file(material_file)
    store.save_blocks(
        material_file.id,
        [
            ExtractedBlock("demo-101", "section header", "Delivery assurance", SourceLocation("Document", section="Delivery assurance")),
            ExtractedBlock("demo-102", "text", "The service platform is operated with a 99.95% monthly availability target. The company holds ISO 27001 certification.", SourceLocation("Document")),
        ],
    )
    return project
