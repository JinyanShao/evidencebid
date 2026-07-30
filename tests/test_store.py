from pathlib import Path

from app.models import FileCategory, ProjectFile
from app.store import Store


def test_store_persists_project_file_and_blocks(tmp_path: Path):
    store = Store(tmp_path / "data")
    project = store.create_project("Northstar RFP")
    project_file = ProjectFile.create(project.id, "rfp.docx", "stored.docx", FileCategory.RFP, "docx")
    store.save_file(project_file)

    assert store.get_project(project.id) == project
    assert store.list_files(project.id)[0].original_name == "rfp.docx"
