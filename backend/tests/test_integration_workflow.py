"""
Integration tests for the end-to-end image upload and processing workflow
Tests the complete pipeline from Chainlit file upload to database storage
"""

import pytest
import tempfile
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import shutil

# Test image data (1x1 pixel JPEG)
TEST_IMAGE_BASE64 = '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLTAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFwAAAwEAAAAAAAAAAAAAAAAAAAUGB//EABYQAQEBAAAAAAAAAAAAAAAAAAABAv/EABUBAQEAAAAAAAAAAAAAAAAAAAID/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8A9wD/AP/Z'


@pytest.fixture
def temp_files_dir():
    """Create temporary .files directory structure like Chainlit"""
    temp_dir = tempfile.mkdtemp()
    files_dir = Path(temp_dir) / ".files" / "test-session-uuid"
    files_dir.mkdir(parents=True)
    
    # Create test image file
    test_image = files_dir / "test-image.jpg"
    test_image.write_bytes(base64.b64decode(TEST_IMAGE_BASE64))
    
    yield files_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


class MockElement:
    def __init__(self, path):
        self.path = path


class MockMessage:
    def __init__(self, content="", elements=None):
        self.content = content
        self.elements = elements or []


@pytest.mark.asyncio
async def test_complete_workflow_success(temp_files_dir):
    """Test successful end-to-end workflow from file upload to database"""
    from backend.chainlit_app import main
    
    # Mock all dependencies
    with patch("backend.chainlit_app.get_current_user") as mock_user, \
         patch("backend.chainlit_app.stream_graph_updates") as mock_stream, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step:
        
        # Setup mocks
        mock_user.return_value = MagicMock(identifier="test_user")
        mock_stream.return_value = "Successfully created blue denim jacket (ID: test-123)"
        
        # Mock Step context manager
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        
        # Mock Message
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        # Create test message with image
        test_image_path = temp_files_dir / "test-image.jpg"
        element = MockElement(str(test_image_path))
        message = MockMessage(content="New jacket!", elements=[element])
        
        # Execute
        await main(message)
        
        # Verify workflow
        mock_stream.assert_called_once()
        call_args = mock_stream.call_args[0][0]
        assert str(test_image_path) in call_args
        assert "New jacket!" in call_args
        
        mock_step.assert_called_once_with(name="📸 Processing image...")
        mock_cl_message.assert_called_once()
        mock_message_instance.send.assert_called_once()


def test_create_clothing_item_tool_fixed():
    """Test that create_clothing_item handles dictionary return correctly"""
    from backend.agent.tools.create_clothing_item import create_clothing_item
    
    with patch("backend.agent.tools.create_clothing_item.caption_image") as mock_caption, \
         patch("backend.agent.tools.create_clothing_item.embed_step") as mock_embed, \
         patch("backend.agent.tools.create_clothing_item.persist_db_step") as mock_persist:
        
        # Setup mock returns
        mock_caption.return_value = {
            "caption": "Red cotton shirt",
            "category": "top",
            "item_id": "test-item-123",
            "image_url": "/images/test.jpg"
        }
        mock_embed.return_value = [0.1, 0.2, 0.3]
        mock_persist.return_value = "test-item-123"
        
        # Execute
        result = create_clothing_item("/path/to/test.jpg")
        
        # Verify the fix works (no unpacking error)
        assert result["item_id"] == "test-item-123"
        assert result["caption"] == "Red cotton shirt"
        assert result["category"] == "top"
        assert result["image_url"] == "/images/test.jpg"
        
        # Verify correct parameters passed to persist_db_step
        persist_args = mock_persist.call_args[0]
        assert persist_args[0] == "Red cotton shirt"  # caption
        assert persist_args[1] == "/images/test.jpg"  # saved image URL, not original
        assert persist_args[3] == "top"  # category
        assert persist_args[4] == "test-item-123"  # item_id


def test_regression_dictionary_unpacking():
    """Regression test to ensure dictionary unpacking is handled correctly"""
    from backend.agent.tools.create_clothing_item import create_clothing_item
    
    with patch("backend.agent.tools.create_clothing_item.caption_image") as mock_caption, \
         patch("backend.agent.tools.create_clothing_item.embed_step") as mock_embed, \
         patch("backend.agent.tools.create_clothing_item.persist_db_step") as mock_persist:
        
        # This would have failed before the fix
        mock_caption.return_value = {
            "caption": "Test caption",
            "category": "accessories",
            "item_id": "test-123",
            "image_url": "/images/saved.jpg"
        }
        mock_embed.return_value = [0.1, 0.2]
        mock_persist.return_value = "test-123"
        
        # Should not raise ValueError about unpacking
        try:
            result = create_clothing_item("/test/path.jpg")
            assert result is not None
            assert isinstance(result["item_id"], str)
        except ValueError as e:
            if "unpack" in str(e):
                pytest.fail("Dictionary unpacking error still exists - fix not working")
            else:
                raise


@pytest.mark.asyncio
async def test_chainlit_file_detection():
    """Test that Chainlit correctly detects and processes file attachments"""
    from backend.chainlit_app import main
    
    with patch("backend.chainlit_app.get_current_user"), \
         patch("backend.chainlit_app.stream_graph_updates") as mock_stream, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step:
        
        # Mock setup
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        # Test 1: Message with file attachment
        element = MockElement("/path/to/image.jpg")
        message_with_file = MockMessage(elements=[element])
        
        await main(message_with_file)
        
        # Should call stream_graph_updates with image path
        mock_stream.assert_called_once()
        assert "/path/to/image.jpg" in mock_stream.call_args[0][0]
        
        # Should use image processing step
        mock_step.assert_called_with(name="📸 Processing image...")
        
        # Test 2: Message without file attachment
        mock_stream.reset_mock()
        mock_step.reset_mock()
        
        message_text_only = MockMessage(content="Show me my clothes", elements=[])
        
        await main(message_text_only)
        
        # Should call stream_graph_updates with text content
        mock_stream.assert_called_with("Show me my clothes")
        
        # Should use thinking step
        mock_step.assert_called_with(name="🤔 Thinking...")


def test_uuid_string_generation():
    """Test that item_id is generated as string (not UUID object)"""
    from backend.agent.tools.create_clothing_item import create_clothing_item
    
    with patch("backend.agent.tools.create_clothing_item.caption_image") as mock_caption, \
         patch("backend.agent.tools.create_clothing_item.embed_step"), \
         patch("backend.agent.tools.create_clothing_item.persist_db_step"):
        
        mock_caption.return_value = {
            "caption": "Test",
            "category": "top", 
            "item_id": "generated-id",
            "image_url": "/images/test.jpg"
        }
        
        result = create_clothing_item("/test.jpg")
        
        # Should be string, not UUID object
        assert isinstance(result["item_id"], str)
        assert "-" in result["item_id"]  # UUID format
        assert len(result["item_id"]) == 36  # Standard UUID length 