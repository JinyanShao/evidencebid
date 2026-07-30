from pathlib import Path

import pytest

from app.parser import DocumentParseError, parse_document


def test_rejects_unsupported_file(tmp_path: Path):
    file_path = tmp_path / "input.txt"
    file_path.write_text("not supported", encoding="utf-8")

    with pytest.raises(DocumentParseError, match="Only text PDFs"):
        parse_document(file_path)


def test_rejects_empty_file(tmp_path: Path):
    file_path = tmp_path / "empty.pdf"
    file_path.touch()

    with pytest.raises(DocumentParseError, match="empty"):
        parse_document(file_path)
