"""
End-to-end integration tests for the image upload and processing workflow
Tests the complete pipeline from Chainlit file upload to database storage
"""

import pytest 
import tempfile
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import os
import shutil

# Test image data (1x1 pixel JPEG)
TEST_IMAGE_BASE64 = (
    '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a'
    'HBwgJC4nICIsIxwcKDcpLTAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy'
    'MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA'
    'AhEBAxEB/8QAFwAAAwEAAAAAAAAAAAAAAAAAAAUGB//EABYQAQEBAAAAAAAAAAAAAAAAAAABAv/EABUBAQEAAAAAAAAAAAAAAAAAAAID/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8A9wD/AP/Z'
)


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


@pytest.fixture
def mock_database():
    """Mock database operations"""
    with patch("backend.agent.tools.create_clothing_item.SessionLocal") as mock_session, \
         patch("backend.agent.tools.create_clothing_item.crud") as mock_crud, \
         patch("backend.db.vector_store.upsert_embedding") as mock_upsert:
        
        # Setup database mock
        db_instance = MagicMock()
        mock_session.return_value = db_instance
        
        # Mock created item
        mock_item = MagicMock()
        mock_item.id = "test-item-12345"
        mock_crud.create_clothing_item.return_value = mock_item
        
        yield {
            "session": mock_session,
            "crud": mock_crud,
            "item": mock_item,
            "upsert": mock_upsert,
            "db": db_instance
        }


@pytest.fixture
def mock_ai_services():
    """Mock AI services (Claude, embeddings)"""
    with patch("backend.agent.tools.create_clothing_item.llm") as mock_llm, \
         patch("backend.services.embedding_service.get_text_embedding") as mock_embed:
        
        # Mock Claude response
        mock_response = MagicMock()
        mock_response.generations = [[MagicMock()]]
        mock_response.generations[0][0].text = "A red cotton t-shirt with crew neck\n\nCategory: top"
        mock_llm.generate.return_value = mock_response
        
        # Mock embedding
        mock_embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        yield {
            "llm": mock_llm,
            "embedding": mock_embed
        }


@pytest.fixture
def mock_storage():
    """Mock image storage service"""
    with patch("backend.services.storage_service.store_clothing_image") as mock_store:
        mock_store.return_value = ("/images/clothing_items/test-item-12345.jpg", "test-item-12345")
        yield mock_store


class MockElement:
    def __init__(self, path):
        self.path = path


class MockMessage:
    def __init__(self, content="", elements=None):
        self.content = content
        self.elements = elements or []


@pytest.mark.asyncio
async def test_complete_image_upload_workflow(temp_files_dir, mock_database, mock_ai_services, mock_storage):
    """Test the complete workflow from Chainlit upload to database storage"""
    from backend.chainlit_app import main
    from backend.agent.agent_core import stream_graph_updates
    
    # Setup: Create test image file in temp directory
    test_image_path = temp_files_dir / "test-image.jpg"
    
    # Mock Chainlit components
    with patch("backend.chainlit_app.get_current_user") as mock_user, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step:
        
        # Setup mocks
        mock_user.return_value = MagicMock(identifier="test_user")
        
        # Mock Step context manager
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        
        # Mock Message
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        # Create Chainlit message with image attachment
        element = MockElement(str(test_image_path))
        message = MockMessage(content="Here's my new shirt!", elements=[element])
        
        # Execute the complete workflow
        await main(message)
        
        # Verify the workflow executed correctly
        
        # 1. Should have processed the image
        mock_step.assert_called_with(name="📸 Processing image...")
        
        # 2. Should have called the storage service
        mock_storage.assert_called_once()
        
        # 3. Should have called Claude for image analysis
        mock_ai_services["llm"].generate.assert_called_once()
        
        # 4. Should have generated embedding
        mock_ai_services["embedding"].assert_called_once_with("A red cotton t-shirt with crew neck")
        
        # 5. Should have saved to database
        mock_database["crud"].create_clothing_item.assert_called_once()
        create_args = mock_database["crud"].create_clothing_item.call_args[1]
        assert create_args["description"] == "A red cotton t-shirt with crew neck"
        assert create_args["category"] == "top"
        assert create_args["image_url"] == "/images/clothing_items/test-item-12345.jpg"
        
        # 6. Should have upserted embedding to vector store
        mock_database["upsert"].assert_called_once()
        
        # 7. Should have sent success message to user
        mock_cl_message.assert_called_once()
        mock_message_instance.send.assert_called_once()


@pytest.mark.asyncio 
async def test_workflow_with_ai_failure(temp_files_dir, mock_database, mock_storage):
    """Test workflow when AI processing fails"""
    from backend.chainlit_app import main
    
    # Mock AI failure
    with patch("backend.agent.tools.create_clothing_item.llm") as mock_llm:
        mock_llm.generate.side_effect = Exception("Claude API failed")
        
        # Mock other services
        with patch("backend.services.embedding_service.get_text_embedding") as mock_embed, \
             patch("backend.chainlit_app.get_current_user") as mock_user, \
             patch("chainlit.Message") as mock_cl_message, \
             patch("chainlit.Step") as mock_step:
            
            mock_user.return_value = MagicMock(identifier="test_user")
            mock_embed.return_value = [0.1, 0.2, 0.3]
            
            # Mock Step and Message
            mock_step_instance = AsyncMock()
            mock_step.return_value.__aenter__.return_value = mock_step_instance
            mock_step.return_value.__aexit__.return_value = None
            mock_message_instance = AsyncMock()
            mock_cl_message.return_value = mock_message_instance
            
            # Create test message
            test_image_path = temp_files_dir / "test-image.jpg" 
            element = MockElement(str(test_image_path))
            message = MockMessage(elements=[element])
            
            # Execute
            await main(message)
            
            # Verify error handling
            # Should still attempt to process but handle errors gracefully
            mock_storage.assert_called_once()
            
            # Should still create database entry with error caption
            mock_database["crud"].create_clothing_item.assert_called_once()
            create_args = mock_database["crud"].create_clothing_item.call_args[1]
            assert "Error processing image" in create_args["description"]


@pytest.mark.asyncio
async def test_workflow_with_database_failure(temp_files_dir, mock_ai_services, mock_storage):
    """Test workflow when database operations fail"""
    from backend.chainlit_app import main
    
    # Mock database failure
    with patch("backend.agent.tools.create_clothing_item.SessionLocal") as mock_session:
        mock_session.side_effect = Exception("Database connection failed")
        
        with patch("backend.chainlit_app.get_current_user") as mock_user, \
             patch("chainlit.Message") as mock_cl_message, \
             patch("chainlit.Step") as mock_step:
            
            mock_user.return_value = MagicMock(identifier="test_user")
            
            # Mock Step and Message
            mock_step_instance = AsyncMock()
            mock_step.return_value.__aenter__.return_value = mock_step_instance
            mock_step.return_value.__aexit__.return_value = None
            mock_message_instance = AsyncMock()
            mock_cl_message.return_value = mock_message_instance
            
            # Create test message
            test_image_path = temp_files_dir / "test-image.jpg"
            element = MockElement(str(test_image_path))
            message = MockMessage(elements=[element])
            
            # Execute
            await main(message)
            
            # Verify error is handled gracefully
            # Should still process image and generate caption
            mock_storage.assert_called_once()
            mock_ai_services["llm"].generate.assert_called_once()
            
            # Should send some response to user (may be error message)
            mock_cl_message.assert_called_once()


def test_agent_tool_integration():
    """Test that the create_clothing_item tool integrates properly with the agent"""
    from backend.agent.agent_core import agent
    
    with patch("backend.agent.tools.create_clothing_item.caption_image") as mock_caption, \
         patch("backend.agent.tools.create_clothing_item.embed_step") as mock_embed, \
         patch("backend.agent.tools.create_clothing_item.persist_db_step") as mock_persist:
        
        # Setup mocks
        mock_caption.return_value = {
            "caption": "Blue denim jeans",
            "category": "bottom",
            "item_id": "test-123",
            "image_url": "/images/test.jpg"
        }
        mock_embed.return_value = [0.1, 0.2, 0.3]
        mock_persist.return_value = "test-123"
        
        # Test agent can handle image upload request
        response = agent.invoke({
            "messages": [{"role": "user", "content": "Please create a clothing item from this image: /path/to/test.jpg"}]
        }, config={"configurable": {"thread_id": 1}})
        
        # Verify agent processed the request
        assert response is not None
        assert "messages" in response
        
        # Verify the tool was called
        mock_caption.assert_called_once()
        mock_embed.assert_called_once()
        mock_persist.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_images_workflow(temp_files_dir, mock_database, mock_ai_services, mock_storage):
    """Test workflow with multiple image uploads"""
    from backend.chainlit_app import main
    
    # Create second test image
    test_image2_path = temp_files_dir / "test-image2.jpg"
    test_image2_path.write_bytes(base64.b64decode(TEST_IMAGE_BASE64))
    
    with patch("backend.chainlit_app.get_current_user") as mock_user, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step:
        
        mock_user.return_value = MagicMock(identifier="test_user")
        
        # Mock Step and Message
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        # Create message with multiple images
        element1 = MockElement(str(temp_files_dir / "test-image.jpg"))
        element2 = MockElement(str(test_image2_path))
        message = MockMessage(content="Two new items!", elements=[element1, element2])
        
        # Execute
        await main(message)
        
        # Verify both images were processed
        assert mock_storage.call_count == 2
        assert mock_ai_services["llm"].generate.call_count == 2
        assert mock_database["crud"].create_clothing_item.call_count == 2 