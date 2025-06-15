import pytest
from unittest.mock import patch, MagicMock
from backend.agent.tools.get_clothing_items import filter_clothing_items_sqlite, vector_search_chroma
from backend.services.embedding_service import get_text_embedding, get_image_embedding, get_multimodal_embedding

# --- Test for filter_clothing_items_sqlite ---
@patch('backend.agent.tools.get_clothing_items.get_db')
def test_filter_clothing_items_sqlite_basic(mock_get_db):
    # Mock DB session and ClothingItem query
    mock_db = MagicMock()
    mock_item1 = MagicMock(id='item1', description='desc1')
    mock_item2 = MagicMock(id='item2', description='desc2')
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_item1, mock_item2]
    mock_db.query.return_value = mock_query

    # Patch get_db to return our mock_db
    mock_get_db.return_value = iter([mock_db])

    tags = {'color': 'red'}
    ids = filter_clothing_items_sqlite(tags)
    assert len(ids) == 2
    assert ids[0]['id'] == 'item1'
    assert ids[1]['id'] == 'item2'

# --- Test for vector_search_chroma ---
@patch('backend.agent.tools.get_clothing_items.query_embedding')
def test_vector_search_chroma_with_ids(mock_query_embedding):
    # Use proper 512-dimension embedding to match ChromaDB expectation
    embedding = [0.1] * 512
    allowed_ids = ['item1', 'item2']
    mock_result1 = MagicMock(id='item1')
    mock_result2 = MagicMock(id='item2')
    mock_query_embedding.return_value = [mock_result1, mock_result2]
    
    results = vector_search_chroma(embedding, allowed_ids, n_results=2, collection_name="clothing_items")
    assert results == [mock_result1, mock_result2]
    mock_query_embedding.assert_called_once()

# --- Test for vector_search_chroma without IDs ---
@patch('backend.agent.tools.get_clothing_items.query_embedding')
def test_vector_search_chroma_no_ids(mock_query_embedding):
    # Use proper 512-dimension embedding to match ChromaDB expectation
    embedding = [0.1] * 512
    mock_query_embedding.return_value = []
    
    results = vector_search_chroma(embedding, allowed_ids=None, n_results=2, collection_name="clothing_items")
    assert results == []
    mock_query_embedding.assert_called_once()

# --- Test for embedding generation primitives ---
def test_get_text_embedding():
    # Simple test that the function exists and can be imported
    from backend.services.embedding_service import get_text_embedding
    assert callable(get_text_embedding)

def test_get_image_embedding():
    # Simple test that the function exists and can be imported
    from backend.services.embedding_service import get_image_embedding
    assert callable(get_image_embedding)

def test_get_multimodal_embedding():
    # Simple test that the function exists and can be imported
    from backend.services.embedding_service import get_multimodal_embedding
    assert callable(get_multimodal_embedding)
