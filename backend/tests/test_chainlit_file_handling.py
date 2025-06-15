"""
Tests for Chainlit file handling functionality
Tests the corrected workflow for processing uploaded images in the chat interface
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import chainlit as cl


class MockElement:
    """Mock Chainlit element (uploaded file)"""
    def __init__(self, path, name="test.jpg"):
        self.path = path
        self.name = name


class MockMessage:
    """Mock Chainlit message"""
    def __init__(self, content="", elements=None):
        self.content = content
        self.elements = elements or []


class MockUser:
    """Mock authenticated user"""
    def __init__(self, identifier="test_user"):
        self.identifier = identifier


@pytest.fixture
def mock_chainlit_dependencies():
    """Mock all Chainlit and related dependencies"""
    with patch("backend.chainlit_app.get_current_user") as mock_get_user, \
         patch("backend.chainlit_app.stream_graph_updates") as mock_stream, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step:
        
        # Setup mocks
        mock_get_user.return_value = MockUser()
        mock_stream.return_value = "Successfully created clothing item from your image!"
        
        # Mock Step context manager
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        
        # Mock Message send method
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        yield {
            "get_user": mock_get_user,
            "stream_updates": mock_stream,
            "cl_message": mock_cl_message,
            "step": mock_step,
            "step_instance": mock_step_instance,
            "message_instance": mock_message_instance
        }


@pytest.mark.asyncio
async def test_message_with_image_attachment(mock_chainlit_dependencies):
    """Test handling of messages with image attachments"""
    from backend.chainlit_app import main
    
    # Setup
    test_image_path = ".files/test-uuid/test-image.jpg"
    element = MockElement(test_image_path)
    message = MockMessage(content="Here's my new shirt", elements=[element])
    
    mocks = mock_chainlit_dependencies
    
    # Execute
    await main(message)
    
    # Verify
    # Should call stream_graph_updates with image path and user notes
    mocks["stream_updates"].assert_called_once()
    call_args = mocks["stream_updates"].call_args[0][0]
    assert test_image_path in call_args
    assert "Here's my new shirt" in call_args
    assert "Please create a clothing item from this image" in call_args
    
    # Should show image processing step
    mocks["step"].assert_called_once_with(name="📸 Processing image...")
    
    # Should send response message
    mocks["cl_message"].assert_called_once()
    mocks["message_instance"].send.assert_called_once()


@pytest.mark.asyncio
async def test_message_with_image_no_text(mock_chainlit_dependencies):
    """Test handling of image-only messages (no text content)"""
    from backend.chainlit_app import main
    
    # Setup
    test_image_path = ".files/test-uuid/test-image.jpg"
    element = MockElement(test_image_path)
    message = MockMessage(content="", elements=[element])  # Empty content
    
    mocks = mock_chainlit_dependencies
    
    # Execute
    await main(message)
    
    # Verify
    # Should call stream_graph_updates with image path only
    mocks["stream_updates"].assert_called_once()
    call_args = mocks["stream_updates"].call_args[0][0]
    assert test_image_path in call_args
    assert "Please create a clothing item from this image" in call_args
    # Should not contain " User notes:" when no text content
    assert "User notes:" not in call_args


@pytest.mark.asyncio
async def test_message_text_only_no_attachments(mock_chainlit_dependencies):
    """Test handling of text-only messages (no attachments)"""
    from backend.chainlit_app import main
    
    # Setup
    message = MockMessage(content="Show me my red dresses", elements=[])
    
    mocks = mock_chainlit_dependencies
    
    # Execute
    await main(message)
    
    # Verify
    # Should call stream_graph_updates with text content directly
    mocks["stream_updates"].assert_called_once_with("Show me my red dresses")
    
    # Should show thinking step, not image processing step
    mocks["step"].assert_called_once_with(name="🤔 Thinking...")
    

@pytest.mark.asyncio
async def test_message_multiple_image_attachments(mock_chainlit_dependencies):
    """Test handling of messages with multiple image attachments"""
    from backend.chainlit_app import main
    
    # Setup
    element1 = MockElement(".files/uuid1/image1.jpg")
    element2 = MockElement(".files/uuid2/image2.jpg")
    message = MockMessage(content="Two items", elements=[element1, element2])
    
    mocks = mock_chainlit_dependencies
    
    # Execute
    await main(message)
    
    # Verify
    # Should process each image (called once per element)
    assert mocks["stream_updates"].call_count == 2
    
    # Check both images were processed
    call_args_list = [call[0][0] for call in mocks["stream_updates"].call_args_list]
    assert any(".files/uuid1/image1.jpg" in args for args in call_args_list)
    assert any(".files/uuid2/image2.jpg" in args for args in call_args_list)


@pytest.mark.asyncio
async def test_image_processing_success(mock_chainlit_dependencies):
    """Test successful image processing workflow"""
    from backend.chainlit_app import main
    
    # Setup
    element = MockElement(".files/test-uuid/test.jpg")
    message = MockMessage(elements=[element])
    
    mocks = mock_chainlit_dependencies
    mocks["stream_updates"].return_value = "Successfully created blue denim jacket!"
    
    # Execute
    await main(message)
    
    # Verify
    mocks["step_instance"].output = "Image processed successfully ✅"
    mocks["cl_message"].assert_called_once_with(content="Successfully created blue denim jacket!")


@pytest.mark.asyncio
async def test_image_processing_empty_response(mock_chainlit_dependencies):
    """Test handling of empty response from image processing"""
    from backend.chainlit_app import main
    
    # Setup
    element = MockElement(".files/test-uuid/test.jpg")
    message = MockMessage(elements=[element])
    
    mocks = mock_chainlit_dependencies
    mocks["stream_updates"].return_value = ""  # Empty response
    
    # Execute
    await main(message)
    
    # Verify error handling
    mocks["step_instance"].output = "Failed to process image ⚠️"
    mocks["cl_message"].assert_called_once()
    call_content = mocks["cl_message"].call_args[1]["content"]
    assert "couldn't process your image" in call_content


@pytest.mark.asyncio
async def test_image_processing_exception(mock_chainlit_dependencies):
    """Test handling of exceptions during image processing"""
    from backend.chainlit_app import main
    
    # Setup
    element = MockElement(".files/test-uuid/test.jpg")
    message = MockMessage(elements=[element])
    
    mocks = mock_chainlit_dependencies
    mocks["stream_updates"].side_effect = Exception("Processing failed")
    
    # Execute
    await main(message)
    
    # Verify error handling
    mocks["cl_message"].assert_called_once()
    call_content = mocks["cl_message"].call_args[1]["content"]
    assert "encountered an error processing your image" in call_content


@pytest.mark.asyncio
async def test_element_without_path_attribute(mock_chainlit_dependencies):
    """Test handling of elements that don't have path attribute"""
    from backend.chainlit_app import main
    
    # Setup - element without path
    element = MagicMock()
    del element.path  # Remove path attribute
    message = MockMessage(elements=[element])
    
    mocks = mock_chainlit_dependencies
    
    # Execute
    await main(message)
    
    # Verify - should not process element without path
    mocks["stream_updates"].assert_not_called()


@pytest.mark.asyncio 
async def test_element_with_none_path(mock_chainlit_dependencies):
    """Test handling of elements with None path"""
    from backend.chainlit_app import main
    
    # Setup
    element = MockElement(None)  # Path is None
    message = MockMessage(elements=[element])
    
    mocks = mock_chainlit_dependencies
    
    # Execute
    await main(message)
    
    # Verify - should not process element with None path
    mocks["stream_updates"].assert_not_called()


@pytest.mark.asyncio
async def test_user_authentication_logging(mock_chainlit_dependencies):
    """Test that user authentication is properly logged"""
    from backend.chainlit_app import main
    
    # Setup
    message = MockMessage(content="test message")
    
    mocks = mock_chainlit_dependencies
    test_user = MockUser("john_doe")
    mocks["get_user"].return_value = test_user
    
    with patch("backend.chainlit_app.logger") as mock_logger:
        # Execute
        await main(message)
        
        # Verify user info is logged
        mock_logger.info.assert_called()
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("User: john_doe" in call for call in log_calls)


@pytest.mark.asyncio
async def test_anonymous_user_handling(mock_chainlit_dependencies):
    """Test handling of anonymous users (no authentication)"""
    from backend.chainlit_app import main
    
    # Setup
    message = MockMessage(content="test message")
    
    mocks = mock_chainlit_dependencies
    mocks["get_user"].return_value = None  # Anonymous user
    
    with patch("backend.chainlit_app.logger") as mock_logger:
        # Execute
        await main(message)
        
        # Verify anonymous user is logged
        mock_logger.info.assert_called()
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Anonymous" in call for call in log_calls) 