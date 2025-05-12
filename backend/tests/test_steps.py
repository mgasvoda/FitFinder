import pytest
from unittest.mock import patch, MagicMock
from backend.agent import steps

import numpy as np

# --- Test CaptionToolNode ---
def make_tool(name, return_value):
    tool = MagicMock()
    tool.name = name
    tool.invoke.return_value = return_value
    return tool

def make_tool_call(name, args, call_id="id1"):
    return {"name": name, "args": args, "id": call_id}

def test_caption_tool_node_basic():
    tool = make_tool("caption_image", {"caption": "desc", "image_url": "url", "item_id": "id"})
    node = steps.CaptionToolNode([tool])
    message = MagicMock()
    message.tool_calls = [make_tool_call("caption_image", {"foo": "bar"})]
    inputs = {"messages": [message]}
    result = node(inputs)
    assert result["caption"] == "desc"
    assert result["image_url"] == "url"
    assert result["item_id"] == "id"
    assert "caption_image" in result
    assert isinstance(result["messages"], list)

# --- Test store_image_step ---
def test_store_image_step_passthrough():
    state = {"foo": "bar"}
    assert steps.store_image_step(state) == state

# --- Test embed_step ---
@patch("backend.agent.steps.get_text_embedding")
def test_embed_step_success(mock_embed):
    mock_embed.return_value = np.array([1.0, 2.0, 3.0])
    state = {"caption": "desc"}
    result = steps.embed_step(state)
    np.testing.assert_array_equal(result["embedding"], np.array([1.0, 2.0, 3.0]))
    assert result["caption"] == "desc"

@patch("backend.agent.steps.get_text_embedding", side_effect=Exception("fail"))
def test_embed_step_error(mock_embed):
    state = {"caption": "desc"}
    result = steps.embed_step(state)
    assert "embedding" not in result or result["embedding"] is None

# --- Test persist_db_step ---
@patch("backend.agent.steps.SessionLocal")
@patch("backend.agent.steps.crud")
def test_persist_db_step_success(mock_crud, mock_session):
    db = MagicMock()
    mock_session.return_value = db
    item = MagicMock(id="itemid")
    mock_crud.create_clothing_item.return_value = item
    state = {"caption": "desc", "embedding": np.array([1.0, 2.0, 3.0]), "image_url": "url"}
    result = steps.persist_db_step(state)
    assert result["item_id"] == "itemid"
    db.close.assert_called()

@patch("backend.agent.steps.SessionLocal", side_effect=Exception("fail"))
def test_persist_db_step_error(mock_session):
    state = {"caption": "desc", "embedding": np.array([1.0, 2.0, 3.0]), "image_url": "url"}
    result = steps.persist_db_step(state)
    assert "item_id" not in result

# --- Test get_items_step ---
@patch("backend.agent.steps.SessionLocal")
@patch("backend.agent.steps.crud")
def test_get_items_step_success(mock_crud, mock_session):
    db = MagicMock()
    mock_session.return_value = db
    item = MagicMock(id=123, description="desc", image_url="url", category="cat", color="red", season="summer", tags=[MagicMock(name="t1"), MagicMock(name="t2")])
    mock_crud.get_clothing_items_by_ids.return_value = [item]
    state = {"search_items": [123]}
    result = steps.get_items_step(state)
    assert "items" in result
    assert result["items"][0]["id"] == "123"
    db.close.assert_called()

@patch("backend.agent.steps.SessionLocal", side_effect=Exception("fail"))
def test_get_items_step_error(mock_session):
    state = {"search_items": [123]}
    result = steps.get_items_step(state)
    assert "items" not in result or result["items"] == state.get("items")

# --- Test format_item_search_response ---
def test_format_item_search_response_passthrough():
    state = {"foo": "bar"}
    assert steps.format_item_search_response(state) == state

# --- Test _route_from_tools ---
def test_route_from_tools_caption():
    state = {"caption_image": {"caption": "desc"}}
    assert steps._route_from_tools(state) == "embed"

def test_route_from_tools_search():
    state = {"search_items": [1, 2, 3]}
    assert steps._route_from_tools(state) == "get_items"

def test_route_from_tools_default():
    state = {"foo": "bar"}
    assert steps._route_from_tools(state) == "chat"
