import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from backend.agent import agent_core
from backend.agent.schemas import ChatRequest, ChatResponse, ItemResponse

# --- Test chat_endpoint ---
@patch("backend.agent.agent_core.run_agent")
def test_chat_endpoint_success(mock_run_agent):
    mock_run_agent.return_value = {
        "messages": [MagicMock(type="ai", content="Hello!")],
        "matching_outfits": [{"id": 1}, {"id": 2}]
    }
    req = ChatRequest(prompt="Hi", optional_image_url=None)
    db = MagicMock()
    resp = agent_core.chat_endpoint(req, db)
    assert isinstance(resp, ChatResponse)
    assert resp.response_text == "Hello!"
    assert resp.matching_outfits == [{"id": 1}, {"id": 2}]

@patch("backend.agent.agent_core.run_agent", side_effect=Exception("fail"))
def test_chat_endpoint_error(mock_run_agent):
    req = ChatRequest(prompt="Hi", optional_image_url=None)
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        agent_core.chat_endpoint(req, db)
    assert exc.value.status_code == 500

# --- Test get_item ---
@patch("backend.agent.agent_core.crud.get_clothing_item")
def test_get_item_success(mock_get):
    class Tag:
        def __init__(self, name):
            self.name = name
    item = MagicMock(
        id="id1", description="desc", image_url="url", tags=[Tag("t1"), Tag("t2")],
        category="cat", color="red", season="summer"
    )
    mock_get.return_value = item
    db = MagicMock()
    resp = agent_core.get_item("id1", db)
    assert isinstance(resp, ItemResponse)
    assert resp.id == "id1"
    assert resp.tags == ["t1", "t2"]

@patch("backend.agent.agent_core.crud.get_clothing_item", return_value=None)
def test_get_item_not_found(mock_get):
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        agent_core.get_item("id1", db)
    assert exc.value.status_code == 404

# --- Test list_items ---
@patch("backend.agent.agent_core.crud.get_clothing_items")
def test_list_items_success(mock_get):
    class Tag:
        def __init__(self, name):
            self.name = name
    item = MagicMock(
        id="id1", description="desc", image_url="url", tags=[Tag("t1")],
        category="cat", color="red", season="summer"
    )
    mock_get.return_value = [item]
    db = MagicMock()
    resp = agent_core.list_items(db=db)
    assert isinstance(resp, list)
    assert isinstance(resp[0], ItemResponse)
    assert resp[0].id == "id1"
    assert resp[0].tags == ["t1"]

@patch("backend.agent.agent_core.crud.get_clothing_items", side_effect=Exception("fail"))
def test_list_items_error(mock_get):
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        agent_core.list_items(db=db)
    assert exc.value.status_code == 500

# --- Test delete_item ---
@patch("backend.agent.agent_core.remove_image")
@patch("backend.agent.agent_core.crud.delete_clothing_item")
@patch("backend.agent.agent_core.crud.get_clothing_item")
def test_delete_item_success(mock_get, mock_delete, mock_remove):
    item = MagicMock(image_url="url")
    mock_get.return_value = item
    mock_delete.return_value = True
    db = MagicMock()
    resp = agent_core.delete_item("id1", db)
    assert resp["message"].startswith("Item deleted")
    mock_remove.assert_called_with("url")

@patch("backend.agent.agent_core.crud.get_clothing_item", return_value=None)
def test_delete_item_not_found(mock_get):
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        agent_core.delete_item("id1", db)
    assert exc.value.status_code == 404

@patch("backend.agent.agent_core.crud.delete_clothing_item", return_value=False)
@patch("backend.agent.agent_core.crud.get_clothing_item")
def test_delete_item_delete_fail(mock_get, mock_delete):
    item = MagicMock(image_url="url")
    mock_get.return_value = item
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        agent_core.delete_item("id1", db)
    assert exc.value.status_code == 500

@patch("backend.agent.agent_core.crud.delete_clothing_item", side_effect=Exception("fail"))
@patch("backend.agent.agent_core.crud.get_clothing_item")
def test_delete_item_error(mock_get, mock_delete):
    item = MagicMock(image_url="url")
    mock_get.return_value = item
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        agent_core.delete_item("id1", db)
    assert exc.value.status_code == 500
