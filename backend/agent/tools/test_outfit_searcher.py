import pytest
from unittest.mock import patch, MagicMock
from backend.agent.tools import outfit_searcher

# --- Test for filter_clothing_items_sqlite ---
def test_filter_clothing_items_sqlite_basic(monkeypatch):
    # Mock DB session and ClothingItem
    mock_db = MagicMock()
    mock_item1 = MagicMock(id='item1')
    mock_item2 = MagicMock(id='item2')
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [mock_item1, mock_item2]
    mock_db.query.return_value = mock_query

    # Patch get_db to return our mock_db
    monkeypatch.setattr(outfit_searcher, 'get_db', lambda: iter([mock_db]))
    monkeypatch.setattr(outfit_searcher.models, 'ClothingItem', MagicMock())

    tags = {'color': 'red'}
    ids = outfit_searcher.filter_clothing_items_sqlite(tags)
    assert ids == ['item1', 'item2']
    mock_query.filter.assert_called()

# --- Test for vector_search_chroma ---
def test_vector_search_chroma_with_ids():
    embedding = [0.1, 0.2, 0.3]
    allowed_ids = ['item1', 'item2']
    mock_result1 = MagicMock(id='item1')
    mock_result2 = MagicMock(id='item2')
    with patch.object(outfit_searcher, 'query_embedding', return_value=[mock_result1, mock_result2]) as mock_query:
        results = outfit_searcher.vector_search_chroma(embedding, allowed_ids, n_results=2, collection_name="clothing_items")
        assert results == [mock_result1, mock_result2]
        mock_query.assert_called_once()
        args, kwargs = mock_query.call_args
        assert kwargs['filter_metadata'] == {'id': {'$in': allowed_ids}}

# --- Test for vector_search_chroma without IDs ---
def test_vector_search_chroma_no_ids():
    embedding = [0.1, 0.2, 0.3]
    with patch.object(outfit_searcher, 'query_embedding', return_value=[]) as mock_query:
        results = outfit_searcher.vector_search_chroma(embedding, allowed_ids=None, n_results=2, collection_name="clothing_items")
        assert results == []
        mock_query.assert_called_once()
        args, kwargs = mock_query.call_args
        assert kwargs['filter_metadata'] is None

# --- Test for embedding generation primitives ---
def test_get_text_embedding():
    with patch.object(outfit_searcher, 'get_text_embedding', return_value=[0.1, 0.2]) as mock_embed:
        result = outfit_searcher.get_text_embedding('test')
        assert result == [0.1, 0.2]
        mock_embed.assert_called_once_with('test')

def test_get_image_embedding():
    with patch.object(outfit_searcher, 'get_image_embedding', return_value=[0.3, 0.4]) as mock_embed:
        result = outfit_searcher.get_image_embedding('img_url')
        assert result == [0.3, 0.4]
        mock_embed.assert_called_once_with('img_url')

def test_get_multimodal_embedding():
    with patch.object(outfit_searcher, 'get_multimodal_embedding', return_value=[0.5, 0.6]) as mock_embed:
        result = outfit_searcher.get_multimodal_embedding('text', 'img_url')
        assert result == [0.5, 0.6]
        mock_embed.assert_called_once_with('text', 'img_url')
