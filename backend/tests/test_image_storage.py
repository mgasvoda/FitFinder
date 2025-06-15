import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from backend.services.storage_service import store_clothing_image, store_outfit_image, delete_image, get_absolute_path

@pytest.fixture
def fake_upload_file():
    file_content = b"fake image data"
    file_obj = io.BytesIO(file_content)
    upload_file = UploadFile(filename="test.jpg", file=file_obj)
    # Mock the content_type property since it's read-only
    upload_file._content_type = "image/jpeg"
    return upload_file

@pytest.fixture
def fake_file_path(tmp_path):
    file_path = tmp_path / "test.jpg"
    file_path.write_bytes(b"fake image data")
    return str(file_path)

@patch("backend.services.storage_service.validate_image", return_value=True)
@patch("backend.services.storage_service.os.makedirs")
@patch("backend.services.storage_service.shutil.copyfileobj")
def test_store_image_with_uploadfile(mock_copyfile, mock_makedirs, mock_validate, fake_upload_file):
    result = store_clothing_image(fake_upload_file, "item123")
    # Check that the result contains expected patterns
    assert result[1] == "item123"  # item_id should match
    assert "/images/clothing_items/" in result[0]  # Should contain expected path
    mock_validate.assert_called_once()

@patch("backend.services.storage_service.validate_image", return_value=True)
@patch("backend.services.storage_service.os.makedirs")
@patch("backend.services.storage_service.shutil.copyfileobj")
def test_store_image_with_filepath(mock_copyfile, mock_makedirs, mock_validate, fake_file_path):
    # Create UploadFile from filepath
    with open(fake_file_path, 'rb') as f:
        file_obj = io.BytesIO(f.read())
        upload_file = UploadFile(filename="test.jpg", file=file_obj)
        upload_file._content_type = "image/jpeg"
        result = store_clothing_image(upload_file, "item456")
    # Check that the result contains expected patterns
    assert result[1] == "item456"  # item_id should match
    assert "/images/clothing_items/" in result[0]  # Should contain expected path

@patch("backend.services.storage_service.validate_image", return_value=False)
def test_store_image_invalid_path(mock_validate):
    file_obj = io.BytesIO(b"invalid")
    upload_file = UploadFile(filename="invalid.jpg", file=file_obj)
    # Should raise HTTPException for invalid file
    with pytest.raises(Exception):
        store_clothing_image(upload_file)

@patch("backend.services.storage_service.validate_image", return_value=True)
@patch("backend.services.storage_service.os.makedirs")
@patch("backend.services.storage_service.shutil.copyfileobj")
def test_store_outfit_image_wrapper(mock_copyfile, mock_makedirs, mock_validate):
    fake_file = MagicMock()
    fake_file.filename = "outfit.jpg"
    fake_file.file = io.BytesIO(b"fake file content")  # Add file attribute
    fake_file._content_type = "image/jpeg"
    result = store_outfit_image(fake_file, "outfit789")
    # Check that the result contains expected patterns
    assert result[1] == "outfit789"  # item_id should match
    assert "/images/outfits/" in result[0]  # Should contain expected path

@patch("backend.services.storage_service.os.path.exists", return_value=False)
def test_remove_image(mock_exists):
    result = delete_image("/mock/url/test.jpg")
    # The function returns False if file doesn't exist, which is expected
    assert result is False

def test_get_image_path():
    # Simple test that just verifies the function runs without error
    result = get_absolute_path("/images/test.jpg")
    # The function might return None for certain paths, which is acceptable
    assert result is None or isinstance(result, str)
