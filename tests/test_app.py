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
    monkeypatch.setattr(main, "parse_document", lambda _path: (_ for _ in ()).throw(DocumentParseError("Parsing failed")))
    client = TestClient(app)
    project = main.store.create_project("Failure-safe RFP")

    response = client.post(
        f"/projects/{project.id}/files",
        data={"category": FileCategory.RFP.value},
        files={"upload": ("proposal.pdf", b"document", "application/pdf")},
        follow_redirects=False,
    )
    assert response.status_code == 303

    page = client.get(f"/projects/{project.id}")
    assert page.status_code == 200
    assert "Parsing failed" in page.text


def test_demo_project_has_inspectable_sources_and_checklist(tmp_path, monkeypatch):
    from app import main
    from app.store import Store

    monkeypatch.setattr(main, "store", Store(tmp_path / "data"))
    client = TestClient(app)

    response = client.get("/demo", follow_redirects=False)
    assert response.status_code == 303
    project_url = response.headers["location"]

    project_page = client.get(project_url)
    assert "Alpine Rail Service Platform" in project_page.text
    assert "Build checklist" in project_page.text

    response = client.post(f"{project_url}/analyze", follow_redirects=True)
    assert response.status_code == 200
    assert "Deadline" in response.text
    assert "Alpine Rail RFP.pdf" in response.text

    response = client.post(f"{project_url}/responses/prepare", follow_redirects=True)
    assert response.status_code == 200
    assert "Evidence-backed drafts" in response.text
    assert "99.95%" in response.text
    assert "Ready to export" in response.text

    export = client.get(f"{project_url}/responses/export.csv")
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert "Evidence sources" in export.content.decode("utf-8-sig")
