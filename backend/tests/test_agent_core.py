import pytest
from unittest.mock import patch, MagicMock
from backend.agent import agent_core
from backend.db.models import ChatRequest, ChatResponse, ItemResponse

# --- Test stream_graph_updates function ---
@patch("backend.agent.agent_core.agent")
def test_stream_graph_updates_success(mock_agent):
    # Mock the agent response
    mock_message = MagicMock()
    mock_message.content = "Hello! I'm FitFinder, your AI fashion assistant."
    mock_agent.invoke.return_value = {"messages": [mock_message]}
    
    result = agent_core.stream_graph_updates("Hello")
    assert result == "Hello! I'm FitFinder, your AI fashion assistant."
    mock_agent.invoke.assert_called_once()

@patch("backend.agent.agent_core.agent")
def test_stream_graph_updates_error(mock_agent):
    # Mock an exception
    mock_agent.invoke.side_effect = Exception("Agent error")
    
    result = agent_core.stream_graph_updates("Hello")
    assert "I'm sorry, I encountered an error" in result

# --- Test create_agent function ---
def test_create_agent():
    """Test that create_agent returns a valid graph object"""
    graph = agent_core.create_agent()
    assert graph is not None
    # The graph should have the expected nodes
    assert hasattr(graph, 'invoke')

# --- Test initialize_agent_resources function ---
@patch("backend.db.vector_store.init_chroma_collections")
@patch("backend.db.models.Base")
def test_initialize_agent_resources_success(mock_base, mock_vector_store):
    """Test successful initialization of agent resources"""
    mock_base.metadata.create_all = MagicMock()
    
    # Should not raise any exceptions
    agent_core.initialize_agent_resources()
    
    mock_base.metadata.create_all.assert_called_once()
    mock_vector_store.assert_called_once()

@patch("backend.db.vector_store.init_chroma_collections")
@patch("backend.db.models.Base")
def test_initialize_agent_resources_error(mock_base, mock_vector_store):
    """Test error handling in agent resource initialization"""
    mock_base.metadata.create_all.side_effect = Exception("DB error")
    
    # Should not crash, but may log errors
    with pytest.raises(Exception):
        agent_core.initialize_agent_resources()

# NOTE: All the FastAPI endpoint tests have been removed as they no longer apply
# to the Chainlit-based architecture. The original tests were for:
# - chat_endpoint
# - get_item  
# - list_items
# - delete_item
# These functions don't exist in the new agent_core.py structure.
