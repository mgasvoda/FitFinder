import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from backend.agent.tools import image_storage

@pytest.fixture
def fake_upload_file():
    file_content = b"fake image data"
    file_obj = io.BytesIO(file_content)
    return UploadFile(filename="test.jpg", file=file_obj)

@pytest.fixture
def fake_file_path(tmp_path):
    file_path = tmp_path / "test.jpg"
    file_path.write_bytes(b"fake image data")
    return str(file_path)

@patch("backend.agent.tools.image_storage.store_clothing_image")
def test_store_image_with_uploadfile(mock_store, fake_upload_file):
    mock_store.return_value = ("/mock/url/test.jpg", "item123")
    result = image_storage.store_image(fake_upload_file, "item123")
    mock_store.assert_called_once_with(fake_upload_file, "item123")
    assert result == ("/mock/url/test.jpg", "item123")

@patch("backend.agent.tools.image_storage.store_clothing_image")
def test_store_image_with_filepath(mock_store, fake_file_path):
    mock_store.return_value = ("/mock/url/test.jpg", "item456")
    result = image_storage.store_image(fake_file_path, "item456")
    assert result == ("/mock/url/test.jpg", "item456")
    # Ensure the UploadFile was constructed and passed
    args, kwargs = mock_store.call_args
    upload_file = args[0]
    assert isinstance(upload_file, UploadFile)
    assert upload_file.filename == "test.jpg"
    assert args[1] == "item456"

@patch("backend.agent.tools.image_storage.store_clothing_image")
def test_store_image_invalid_path(mock_store):
    with pytest.raises(Exception):
        image_storage.store_image("/nonexistent/path.jpg")

@patch("backend.agent.tools.image_storage.store_outfit_image")
def test_store_outfit_image_wrapper(mock_store):
    fake_file = MagicMock(spec=UploadFile)
    mock_store.return_value = ("/mock/url/outfit.jpg", "outfit789")
    result = image_storage.store_outfit_image_wrapper(fake_file, "outfit789")
    mock_store.assert_called_once_with(fake_file, "outfit789")
    assert result == ("/mock/url/outfit.jpg", "outfit789")

@patch("backend.agent.tools.image_storage.delete_image")
def test_remove_image(mock_delete):
    mock_delete.return_value = True
    assert image_storage.remove_image("/mock/url/test.jpg") is True
    mock_delete.return_value = False
    assert image_storage.remove_image("/mock/url/bad.jpg") is False

@patch("backend.agent.tools.image_storage.get_absolute_path")
def test_get_image_path(mock_get_path):
    mock_get_path.return_value = "/abs/path/test.jpg"
    result = image_storage.get_image_path("/mock/url/test.jpg")
    mock_get_path.assert_called_once_with("/mock/url/test.jpg")
    assert result == "/abs/path/test.jpg"
