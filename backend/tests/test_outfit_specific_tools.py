import pytest
from unittest.mock import patch, MagicMock
from backend.agent.tools import outfit_specific_tools

# Test get_item_embedding
@patch('backend.agent.tools.outfit_specific_tools.get_text_embedding')
def test_get_item_embedding_success(mock_get_text_embedding):
    mock_get_text_embedding.return_value = [0.1] * 128
    result = outfit_specific_tools.get_item_embedding('test')
    assert result == [0.1] * 128
    mock_get_text_embedding.assert_called_once_with('test')

@patch('backend.agent.tools.outfit_specific_tools.get_text_embedding')
def test_get_item_embedding_none(mock_get_text_embedding):
    mock_get_text_embedding.return_value = None
    result = outfit_specific_tools.get_item_embedding('fail')
    assert result == [0.0] * 128

@patch('backend.agent.tools.outfit_specific_tools.get_text_embedding', side_effect=Exception('err'))
def test_get_item_embedding_exception(mock_get_text_embedding):
    result = outfit_specific_tools.get_item_embedding('error')
    assert result == [0.0] * 128

# Test query_sqlite_by_tags
@patch('backend.agent.tools.outfit_specific_tools.filter_clothing_items_sqlite')
def test_query_sqlite_by_tags_success(mock_filter):
    mock_filter.return_value = ['id1', 'id2']
    tags = {'color': 'blue'}
    result = outfit_specific_tools.query_sqlite_by_tags(tags)
    assert result == ['id1', 'id2']
    mock_filter.assert_called_once_with(tags=tags)

@patch('backend.agent.tools.outfit_specific_tools.filter_clothing_items_sqlite', side_effect=Exception('fail'))
def test_query_sqlite_by_tags_exception(mock_filter):
    tags = {'color': 'red'}
    result = outfit_specific_tools.query_sqlite_by_tags(tags)
    assert result == []

# Test query_chroma_by_ids_and_embedding
@patch('backend.agent.tools.outfit_specific_tools.vector_search_chroma')
def test_query_chroma_by_ids_and_embedding_success(mock_vector_search):
    mock_result = MagicMock()
    mock_result.id = 'item1'
    mock_result.score = 0.9
    mock_result.metadata = {'description': 'desc', 'category': 'top'}
    mock_vector_search.return_value = [mock_result]
    item_ids = ['item1']
    embedding = [0.1] * 128
    top_k = 1
    result = outfit_specific_tools.query_chroma_by_ids_and_embedding(item_ids, embedding, top_k)
    assert result == [{
        'item_id': 'item1',
        'description': 'desc',
        'category': 'top',
        'score': 0.9
    }]
    mock_vector_search.assert_called_once()

@patch('backend.agent.tools.outfit_specific_tools.vector_search_chroma', side_effect=Exception('fail'))
def test_query_chroma_by_ids_and_embedding_exception(mock_vector_search):
    result = outfit_specific_tools.query_chroma_by_ids_and_embedding(['id'], [0.1]*128, 2)
    assert result == []

# Test check_outfit_completeness
@pytest.mark.parametrize('items,expected', [
    ([{'category': 'top'}, {'category': 'bottom'}, {'category': 'shoes'}], True),
    ([{'category': 'top'}, {'category': 'bottom'}], False),
    ([{'category': 'shoes'}, {'category': 'top'}], False),
    ([{'category': 'TOP'}, {'category': 'bottom'}, {'category': 'Shoes'}], True),
    ([{'category': 'top'}, {'category': None}, {'category': 'shoes'}], False),
    ([], False)
])
def test_check_outfit_completeness(items, expected):
    assert outfit_specific_tools.check_outfit_completeness(items) is expected
