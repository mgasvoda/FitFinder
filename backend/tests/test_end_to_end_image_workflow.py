"""
End-to-end integration tests for the image upload and processing workflow
Tests the complete pipeline from Chainlit file upload to database storage
"""

import pytest 
import tempfile
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, call
import os
import shutil
import uuid

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
def temp_storage_dir():
    """Create temporary storage directory for testing actual file operations"""
    temp_dir = tempfile.mkdtemp()
    storage_dir = Path(temp_dir) / "images" / "clothing_items"
    storage_dir.mkdir(parents=True)
    
    yield temp_dir
    
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
        mock_response.content = "A red cotton t-shirt with crew neck\n\nCategory: top"
        mock_llm.invoke.return_value = mock_response
        
        # Mock embedding
        mock_embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        yield {
            "llm": mock_llm,
            "embedding": mock_embed,
            "response": mock_response
        }


@pytest.fixture
def mock_storage():
    """Mock image storage service"""
    with patch("backend.agent.tools.create_clothing_item.store_image") as mock_store:
        mock_store.return_value = ("/images/clothing_items/test-item-12345.jpg", "test-item-12345")
        yield mock_store


class MockElement:
    def __init__(self, path):
        self.path = path


class MockMessage:
    def __init__(self, content="", elements=None):
        self.content = content
        self.elements = elements or []


@pytest.mark.anyio
async def test_complete_image_upload_workflow(temp_files_dir, mock_database, mock_ai_services, mock_storage):
    """Test the complete workflow from Chainlit upload to database storage"""
    # Setup: Create test image file in temp directory
    test_image_path = temp_files_dir / "test-image.jpg"
    test_image_path.write_bytes(base64.b64decode(TEST_IMAGE_BASE64))  # Create the actual test image file
    
    # Mock all chainlit app dependencies at import time
    with patch("backend.agent.agent_core.initialize_agent_resources") as mock_init_resources, \
         patch("backend.chainlit_app.get_current_user") as mock_user, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step, \
         patch("backend.chainlit_app.process_chainlit_image") as mock_process_image, \
         patch("backend.chainlit_app.get_image_info") as mock_get_info, \
         patch("backend.chainlit_app.stream_graph_updates") as mock_stream_updates:
        
        # Setup mocks
        mock_init_resources.return_value = None
        mock_user.return_value = MagicMock(identifier="test_user")
        
        # Mock image processing
        mock_process_image.return_value = ("/images/clothing_items/test-item-12345.jpg", "test-item-12345", 115)
        mock_get_info.return_value = {"exists": True, "size_kb": 250}
        mock_stream_updates.return_value = "Successfully created clothing item!"
        
        # Mock Step context manager
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        
        # Mock Message
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        # Now import and test the main function
        from backend.chainlit_app import main
        
        # Create Chainlit message with image attachment
        element = MockElement(str(test_image_path))
        message = MockMessage(content="Here's my new shirt!", elements=[element])
        
        # Execute the complete workflow
        await main(message)
        
        # Verify the workflow executed correctly
        
        # 1. Should have processed the image
        mock_step.assert_called()
        mock_process_image.assert_called_once()
        
        # 2. Should have called the agent
        mock_stream_updates.assert_called_once()
        
        # 3. Should have sent message to user
        mock_cl_message.assert_called_once()
        mock_message_instance.send.assert_called_once()


@pytest.mark.anyio
async def test_complete_workflow_no_image_duplication(temp_files_dir, temp_storage_dir):
    """
    Test the complete workflow ensuring no image duplication occurs
    This test uses real file operations to verify image handling
    """
    from backend.services.chainlit_image_processor import process_chainlit_image
    from backend.agent.tools.create_clothing_item import create_clothing_item
    
    # Track all compression calls to ensure no duplication
    compression_calls = []
    
    def mock_compress_track(*args, **kwargs):
        compression_calls.append((args, kwargs))
        # Mock return: output_path, size_kb
        output_path = args[1] if len(args) > 1 else "/mnt/fitfinder/images/clothing_items/test.jpg"
        
        # Actually create the output file so subsequent operations can find it
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Copy the input file to output path to simulate compression
        if len(args) > 0 and os.path.exists(args[0]):
            import shutil
            shutil.copy2(args[0], output_path)
        else:
            # Create a minimal test image if input doesn't exist
            Path(output_path).write_bytes(base64.b64decode(TEST_IMAGE_BASE64))
        
        return output_path, 115
    
    # Setup test image
    test_image_path = temp_files_dir / "test-image.jpg"
    test_image_path.write_bytes(base64.b64decode(TEST_IMAGE_BASE64))  # Create the actual test image file
    
    # Create the clothing items directory
    clothing_items_dir = os.path.join(temp_storage_dir, "images", "clothing_items")
    os.makedirs(clothing_items_dir, exist_ok=True)
    
    with patch("backend.config.Config.get_data_path_env") as mock_data_path, \
         patch("backend.services.chainlit_image_processor.get_clothing_items_dir") as mock_clothing_dir, \
         patch("backend.services.chainlit_image_processor.compress_clothing_image", side_effect=mock_compress_track) as mock_compress, \
         patch("backend.agent.tools.create_clothing_item.llm") as mock_llm, \
         patch("backend.services.embedding_service.get_text_embedding") as mock_embed, \
         patch("backend.agent.tools.create_clothing_item.SessionLocal") as mock_session, \
         patch("backend.agent.tools.create_clothing_item.crud") as mock_crud, \
         patch("backend.db.vector_store.upsert_embedding") as mock_upsert:
        
        # Setup mocks
        mock_data_path.return_value = temp_storage_dir
        mock_clothing_dir.return_value = clothing_items_dir
        
        # Mock Claude response
        mock_response = MagicMock()
        mock_response.content = "A stylish blue denim jacket\n\nCategory: top"
        mock_llm.invoke.return_value = mock_response
        
        # Mock embedding and database
        mock_embed.return_value = [0.1, 0.2, 0.3]
        db_instance = MagicMock()
        mock_session.return_value = db_instance
        mock_item = MagicMock()
        mock_item.id = "test-item-abc123"
        mock_crud.create_clothing_item.return_value = mock_item
        
        # Step 1: Process image through Chainlit (first compression)
        class MockElement:
            def __init__(self, path):
                self.path = path
        
        element = MockElement(str(test_image_path))
        relative_url, item_id, size_kb = process_chainlit_image(element, compress=True)
        
        # Verify first compression happened
        assert len(compression_calls) == 1
        assert relative_url.startswith("/images/clothing_items/")
        assert item_id is not None
        
        # Step 2: Create clothing item using the compressed image URL
        # This should NOT trigger another compression since image is already saved
        result = create_clothing_item(relative_url)
        
        # Verify NO additional compression occurred
        assert len(compression_calls) == 1, f"Expected 1 compression call, got {len(compression_calls)}"
        
        # Verify result contains correct information
        assert result["item_id"] is not None
        assert result["caption"] == "A stylish blue denim jacket"
        assert result["category"] == "top"
        assert result["image_url"] == relative_url  # Should be the same relative URL


@pytest.mark.anyio
async def test_image_reference_consistency_throughout_workflow(temp_files_dir):
    """
    Test that image references remain consistent throughout the entire workflow
    """
    image_references = []  # Track all image references used
    
    def track_image_ref(func_name, ref):
        image_references.append((func_name, ref))
    
    test_image_path = temp_files_dir / "test-image.jpg"
    
    with patch("backend.services.chainlit_image_processor.compress_clothing_image") as mock_compress, \
         patch("backend.agent.tools.create_clothing_item.llm") as mock_llm, \
         patch("backend.services.embedding_service.get_text_embedding") as mock_embed, \
         patch("backend.agent.tools.create_clothing_item.SessionLocal") as mock_session, \
         patch("backend.agent.tools.create_clothing_item.crud") as mock_crud, \
         patch("backend.db.vector_store.upsert_embedding") as mock_upsert, \
         patch("backend.agent.tools.create_clothing_item.store_image") as mock_store, \
         patch("backend.services.storage_service.get_absolute_path") as mock_get_absolute:
        
        # Setup mocks with tracking
        item_id = str(uuid.uuid4())
        expected_relative_url = f"/images/clothing_items/{item_id}.jpg"
        expected_absolute_path = f"/mnt/fitfinder/images/clothing_items/{item_id}.jpg"
        
        mock_compress.return_value = (expected_absolute_path, 115)
        
        # Mock the image existence checks to avoid file I/O errors
        mock_get_absolute.return_value = expected_absolute_path
        
        # Mock Path.read_bytes to simulate reading an image file
        with patch("pathlib.Path.read_bytes") as mock_read_bytes, \
             patch("os.path.exists") as mock_exists:
            mock_read_bytes.return_value = base64.b64decode(TEST_IMAGE_BASE64)
            mock_exists.return_value = True
            
            mock_response = MagicMock()
            mock_response.content = "A red cotton t-shirt\n\nCategory: top"
            mock_llm.invoke.return_value = mock_response
            
            mock_embed.return_value = [0.1, 0.2, 0.3]
            db_instance = MagicMock()
            mock_session.return_value = db_instance
            mock_item = MagicMock()
            mock_item.id = item_id
            mock_crud.create_clothing_item.return_value = mock_item
            
            # Mock store_image to return expected values
            mock_store.return_value = (expected_relative_url, item_id)
            
            # Step 1: Chainlit processing
            from backend.services.chainlit_image_processor import process_chainlit_image
            
            class MockElement:
                def __init__(self, path):
                    self.path = path
            
            element = MockElement(str(test_image_path))
            relative_url, returned_item_id, size_kb = process_chainlit_image(element, item_id=item_id)
            track_image_ref("chainlit_process", relative_url)
            
            # Step 2: Create clothing item
            from backend.agent.tools.create_clothing_item import create_clothing_item
            
            result = create_clothing_item(relative_url)
            track_image_ref("create_clothing_item", result["image_url"])
            
            # Verify image references are consistent
            assert len(image_references) == 2
            chainlit_ref = image_references[0][1]
            create_item_ref = image_references[1][1]
            
            # Both should be the same relative URL
            assert chainlit_ref == create_item_ref
            assert chainlit_ref == expected_relative_url
            assert create_item_ref == expected_relative_url
            
            # Verify database was called with correct image URL
            create_args = mock_crud.create_clothing_item.call_args[1]
            assert create_args["image_url"] == expected_relative_url
            
            # Verify no absolute paths leaked into the database
            assert not create_args["image_url"].startswith("/mnt/")
            assert create_args["image_url"].startswith("/images/")


@pytest.mark.anyio
async def test_workflow_with_existing_image_path(temp_storage_dir):
    """
    Test workflow when given an already processed image path (should not reprocess)
    """
    # Create an existing image file
    storage_dir = Path(temp_storage_dir) / "images" / "clothing_items"
    storage_dir.mkdir(parents=True, exist_ok=True)
    existing_image_path = storage_dir / "existing-item-123.jpg"
    existing_image_path.write_bytes(base64.b64decode(TEST_IMAGE_BASE64))
    
    existing_relative_url = "/images/clothing_items/existing-item-123.jpg"
    
    with patch("backend.config.Config.get_data_path_env", return_value=temp_storage_dir), \
         patch("backend.agent.tools.create_clothing_item.store_image") as mock_store, \
         patch("backend.agent.tools.create_clothing_item.llm") as mock_llm, \
         patch("backend.services.embedding_service.get_text_embedding") as mock_embed, \
         patch("backend.agent.tools.create_clothing_item.SessionLocal") as mock_session, \
         patch("backend.agent.tools.create_clothing_item.crud") as mock_crud, \
         patch("backend.db.vector_store.upsert_embedding") as mock_upsert:
        
        # Setup other mocks
        mock_response = MagicMock()
        mock_response.content = "A green polo shirt\n\nCategory: top"
        mock_llm.invoke.return_value = mock_response
        
        mock_embed.return_value = [0.1, 0.2, 0.3]
        db_instance = MagicMock()
        mock_session.return_value = db_instance
        mock_item = MagicMock()
        mock_item.id = "existing-item-123"
        mock_crud.create_clothing_item.return_value = mock_item
        
        # Test: Create clothing item with existing relative URL
        from backend.agent.tools.create_clothing_item import create_clothing_item
        
        result = create_clothing_item(existing_relative_url)
        
        # Verify: No additional storage should have occurred (image already exists)
        mock_store.assert_not_called()
        
        # Verify: Result uses the existing URL
        assert result["image_url"] == existing_relative_url
        assert result["caption"] == "A green polo shirt"
        assert result["category"] == "top"
        
        # Verify: Database called with existing URL
        create_args = mock_crud.create_clothing_item.call_args[1]
        assert create_args["image_url"] == existing_relative_url


@pytest.mark.anyio
async def test_workflow_with_ai_failure(temp_files_dir, mock_database, mock_storage):
    """Test workflow when AI processing fails"""
    
    # Mock AI failure
    with patch("backend.agent.agent_core.initialize_agent_resources") as mock_init_resources, \
         patch("backend.chainlit_app.stream_graph_updates") as mock_stream_updates, \
         patch("backend.chainlit_app.process_chainlit_image") as mock_process_image, \
         patch("backend.chainlit_app.get_image_info") as mock_get_info, \
         patch("backend.chainlit_app.get_current_user") as mock_user, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step:
        
        mock_init_resources.return_value = None
        mock_stream_updates.side_effect = Exception("AI processing failed")
        
        mock_user.return_value = MagicMock(identifier="test_user")
        mock_process_image.return_value = ("/images/clothing_items/test-item-12345.jpg", "test-item-12345", 115)
        mock_get_info.return_value = {"exists": True, "size_kb": 250}
        
        # Mock Step and Message
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        # Import after mocking
        from backend.chainlit_app import main
        
        # Create test message
        test_image_path = temp_files_dir / "test-image.jpg" 
        element = MockElement(str(test_image_path))
        message = MockMessage(elements=[element])
        
        # Execute
        await main(message)
        
        # Verify error handling
        # Should still attempt to process but handle errors gracefully
        mock_process_image.assert_called_once()
        
        # Should still create message
        mock_cl_message.assert_called_once()


@pytest.mark.anyio
async def test_workflow_with_database_failure(temp_files_dir, mock_ai_services, mock_storage):
    """Test workflow when database operations fail"""
    
    # Mock agent failure to simulate database issues
    with patch("backend.agent.agent_core.initialize_agent_resources") as mock_init_resources, \
         patch("backend.chainlit_app.stream_graph_updates") as mock_stream_updates, \
         patch("backend.chainlit_app.process_chainlit_image") as mock_process_image, \
         patch("backend.chainlit_app.get_image_info") as mock_get_info, \
         patch("backend.chainlit_app.get_current_user") as mock_user, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step:
        
        mock_init_resources.return_value = None
        mock_stream_updates.side_effect = Exception("Database connection failed")
        
        mock_user.return_value = MagicMock(identifier="test_user")
        mock_process_image.return_value = ("/images/clothing_items/test-item-12345.jpg", "test-item-12345", 115)
        mock_get_info.return_value = {"exists": True, "size_kb": 250}
        
        # Mock Step and Message
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        # Import after mocking
        from backend.chainlit_app import main
        
        # Create test message
        test_image_path = temp_files_dir / "test-image.jpg"
        element = MockElement(str(test_image_path))
        message = MockMessage(elements=[element])
        
        # Execute
        await main(message)
        
        # Verify error is handled gracefully
        # Should still process image
        mock_process_image.assert_called_once()
        
        # Should send some response to user (may be error message)
        mock_cl_message.assert_called_once()


def test_agent_tool_integration():
    """Test that the create_clothing_item tool integrates properly with the agent"""
    with patch("backend.agent.agent_core.initialize_agent_resources") as mock_init_resources:
        mock_init_resources.return_value = None
        
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


@pytest.mark.anyio
async def test_multiple_images_workflow(temp_files_dir, mock_database, mock_ai_services, mock_storage):
    """Test workflow with multiple image uploads"""
    # Create second test image
    test_image2_path = temp_files_dir / "test-image2.jpg"
    test_image2_path.write_bytes(base64.b64decode(TEST_IMAGE_BASE64))
    
    with patch("backend.agent.agent_core.initialize_agent_resources") as mock_init_resources, \
         patch("backend.chainlit_app.get_current_user") as mock_user, \
         patch("chainlit.Message") as mock_cl_message, \
         patch("chainlit.Step") as mock_step, \
         patch("backend.chainlit_app.process_chainlit_image") as mock_process_image, \
         patch("backend.chainlit_app.get_image_info") as mock_get_info, \
         patch("backend.chainlit_app.stream_graph_updates") as mock_stream_updates:
        
        mock_init_resources.return_value = None
        mock_user.return_value = MagicMock(identifier="test_user")
        
        # Mock image processing - should be called twice
        mock_process_image.side_effect = [
            ("/images/clothing_items/test-item-1.jpg", "test-item-1", 115),
            ("/images/clothing_items/test-item-2.jpg", "test-item-2", 115)
        ]
        mock_get_info.return_value = {"exists": True, "size_kb": 250}
        mock_stream_updates.return_value = "Successfully created clothing item!"
        
        # Mock Step and Message
        mock_step_instance = AsyncMock()
        mock_step.return_value.__aenter__.return_value = mock_step_instance
        mock_step.return_value.__aexit__.return_value = None
        mock_message_instance = AsyncMock()
        mock_cl_message.return_value = mock_message_instance
        
        # Import after mocking
        from backend.chainlit_app import main
        
        # Create message with multiple images
        element1 = MockElement(str(temp_files_dir / "test-image.jpg"))
        element2 = MockElement(str(test_image2_path))
        message = MockMessage(content="Two new items!", elements=[element1, element2])
        
        # Execute
        await main(message)
        
        # Verify both images were processed
        assert mock_process_image.call_count == 2
        assert mock_stream_updates.call_count == 2
        assert mock_cl_message.call_count == 2 