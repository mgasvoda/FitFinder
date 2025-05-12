import io
import base64
import pytest
from unittest.mock import patch, MagicMock
from backend.agent.tools import caption_image

# Helper: Fake UploadFile for mocking
class FakeUploadFile:
    def __init__(self, filename, file):
        self.filename = filename
        self.file = file

@pytest.fixture
def fake_image_bytes():
    # 1x1 pixel JPEG
    return base64.b64decode("""
        '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
        HBwgJC4nICIsIxwcKDcpLTAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
        MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA
        AhEBAxEB/8QAFwAAAwEAAAAAAAAAAAAAAAAAAAUGB//EABYQAQEBAAAAAAAAAAAAAAAAAAABAv/EABUBAQEAAAAAAAAAAAAAAAAAAAID/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8A9wD/AP/Z'
    """)

def mock_store_image(upload_file, item_id):
    return (f"/mock/path/{upload_file.filename}", item_id)

def mock_llm_generate(msgs):
    class Response:
        class Gen:
            text = "A mock caption for the clothing item."
        generations = [[Gen()]]
    return Response()

@patch("backend.agent.tools.caption_image.llm")
@patch("backend.agent.tools.caption_image.store_image", side_effect=mock_store_image)
@patch("backend.agent.tools.caption_image.UploadFile", side_effect=FakeUploadFile)
def test_caption_image_local(mock_uploadfile, mock_store, mock_llm, fake_image_bytes, tmp_path):
    # Create a fake local image file
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(fake_image_bytes)
    
    result = caption_image._caption_image_impl(str(img_path))
    assert "caption" in result
    assert result["caption"].startswith("A mock caption")
    assert result["item_id"]
    assert result["image_url"].startswith("/mock/path/")
    assert result["metadata"]["filename"] == "test.jpg"
    assert result["metadata"]["source_path"] == str(img_path)

@patch("backend.agent.tools.caption_image.llm")
@patch("backend.agent.tools.caption_image.store_image", side_effect=mock_store_image)
@patch("backend.agent.tools.caption_image.UploadFile", side_effect=FakeUploadFile)
@patch("requests.get")
def test_caption_image_remote(mock_requests_get, mock_uploadfile, mock_store, mock_llm, fake_image_bytes):
    # Mock requests.get to return fake image bytes
    mock_requests_get.return_value.content = fake_image_bytes
    url = "https://example.com/test.jpg"
    result = caption_image._caption_image_impl(url, "Describe this shirt.")
    assert "caption" in result
    assert result["caption"].startswith("A mock caption")
    assert result["item_id"]
    assert result["image_url"].startswith("/mock/path/")
    assert result["metadata"]["filename"] == "test.jpg"
    assert result["metadata"]["source_path"] == url

@patch("backend.agent.tools.caption_image.llm")
@patch("backend.agent.tools.caption_image.store_image", side_effect=mock_store_image)
@patch("backend.agent.tools.caption_image.UploadFile", side_effect=FakeUploadFile)
def test_caption_image_error_handling(mock_uploadfile, mock_store, mock_llm):
    # Pass a non-existent file path to trigger error
    result = caption_image._caption_image_impl("/nonexistent/path.jpg")
    assert "error" in result
    assert result["caption"].startswith("Error processing image")
    assert result["image_url"] is None
    assert result["item_id"]
