import pytest
from file_manager import FileManager

def test_upload_file_valid(tmp_path):
    fm = FileManager(str(tmp_path))
    file_path = tmp_path / "test.html"
    file_path.write_text("<html></html>")
    uploaded = fm.upload_file(str(file_path))
    assert uploaded.endswith(".html")

def test_upload_file_invalid_extension(tmp_path):
    fm = FileManager(str(tmp_path))
    file_path = tmp_path / "test.txt"
    file_path.write_text("plain text")
    with pytest.raises(ValueError):
        fm.upload_file(str(file_path))
