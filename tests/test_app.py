from fastapi.testclient import TestClient

from app.main import app


def test_homepage_and_create_project(tmp_path, monkeypatch):
    from app import main
    from app.store import Store

    monkeypatch.setattr(main, "store", Store(tmp_path / "data"))
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "Start with the source" in response.text

    response = client.post("/projects", data={"name": "Test RFP"}, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/projects/")


def test_upload_failure_keeps_project_available(tmp_path, monkeypatch):
    from app import main
    from app.models import FileCategory
    from app.parser import DocumentParseError
    from app.store import Store

    monkeypatch.setattr(main, "store", Store(tmp_path / "data"))
    monkeypatch.setattr(main, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(main, "parse_document", lambda _path: (_ for _ in ()).throw(DocumentParseError("Sample parse error")))
    client = TestClient(app)
    project = main.store.create_project("Failure-safe RFP")

    response = client.post(
        f"/projects/{project.id}/files",
        data={"category": FileCategory.RFP.value},
        files={"upload": ("example.pdf", b"document", "application/pdf")},
        follow_redirects=False,
    )
    assert response.status_code == 303

    page = client.get(f"/projects/{project.id}")
    assert page.status_code == 200
    assert "Sample parse error" in page.text
