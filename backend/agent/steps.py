"""
Agent step functions for the FitFinder LangGraph agent.
This module contains all the step functions used in the agent's graph.
"""

import logging
import json
import numpy as np
from typing import Optional, TypedDict, Annotated
from langchain_core.messages import ToolMessage
from langgraph.graph.message import add_messages

from backend.agent.tools.image_storage import store_image
from backend.services.embedding_service import get_text_embedding
from backend.db.models import SessionLocal
from backend.db import crud

logger = logging.getLogger(__name__)

# Define the State type for the agent
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    item_id: Optional[str]
    image_url: Optional[str]
    caption: Optional[str]
    embedding: Optional[np.ndarray]
    items: Optional[list]
    search_items: Optional[list]


class CaptionToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        
        outputs = []
        # Initialize state update with messages
        state_update = {}
        
        for tool_call in message.tool_calls:
            name = tool_call["name"]
            result = self.tools_by_name[name].invoke(tool_call["args"])
            
            # Create tool message with the result
            tool_message = ToolMessage(
                content=json.dumps(result),
                name=name,
                tool_call_id=tool_call["id"],
                args=tool_call["args"],
            )
            
            outputs.append(tool_message)
            
            # Special handling for caption_image tool which now returns a dictionary
            if name == "caption_image" and isinstance(result, dict):
                logger.info("Processing caption_image result dictionary...")
                
                # Extract caption from the result
                if "caption" in result:
                    state_update["caption"] = result["caption"]
                    logger.info(f"Extracted caption: {result['caption'][:50] if result['caption'] else 'None'}...")
                
                # Extract image URL and ID
                if "image_url" in result:
                    state_update["image_url"] = result["image_url"]
                    logger.info(f"Extracted image_url: {result['image_url']}")
                
                if "item_id" in result:
                    state_update["item_id"] = result["item_id"]
                    logger.info(f"Extracted item_id: {result['item_id']}")
                
                # Store the entire result under the tool name for compatibility
                state_update[name] = result
            else:
                # For other tools, just add the result directly
                state_update[name] = result
            
            # Log the actual tool result for debugging
            logger.info(f"Tool {name} result type: {type(result).__name__}, preview: {str(result)[:50]}...")
            
        # Add all outputs to messages
        state_update["messages"] = outputs
        
        # Debug log to verify state
        logger.debug(f"State update after tool execution: {state_update}")
        
        return state_update


def store_image_step(state: State):
    """Store an image and return the URL and ID."""
    # This is a placeholder for the actual implementation
    return state


def embed_step(state: State):
    """Generate embeddings for the caption text."""
    logger.info("Running embed_step...")
    
    # Check if we have a caption to embed
    if not state.get("caption"):
        logger.warning("No caption found in state, skipping embedding")
        return state
    
    caption = state["caption"]
    logger.info(f"Generating embedding for caption: {caption[:50]}...")
    
    try:
        # Get embedding for the caption
        embedding = get_text_embedding(caption)
        
        if embedding is None:
            logger.error("Failed to generate embedding, got None")
            return state
            
        logger.info(f"Generated embedding with shape: {len(embedding)}")
        
        # Update state with the embedding
        return {
            **state,
            "embedding": embedding
        }
    except Exception as e:
        logger.error(f"Error generating embedding: {e}", exc_info=True)
        # Return original state on error
        return state


def persist_db_step(state: State):
    """Persist the item to the database with its caption and embedding."""
    logger.info("Running persist_db_step...")
    
    # Check if we have the necessary data
    if not state.get("caption"):
        logger.warning("No caption found in state, skipping database persistence")
        return state
    
    if not state.get("image_url"):
        logger.warning("No image_url found in state, skipping database persistence")
        return state
    
    # Get the data from state
    caption = state["caption"]
    image_url = state["image_url"]
    embedding = state.get("embedding")  # This might be None if embedding failed
    
    logger.info(f"Persisting item with caption: {caption[:50]}...")
    logger.info(f"Image URL: {image_url}")
    logger.info(f"Embedding available: {embedding is not None}")
    
    try:
        # Create a database session
        db = SessionLocal()
        
        try:
            # Create the clothing item in the database
            db_item = crud.create_clothing_item(
                db=db,
                description=caption,
                image_url=image_url,
                embedding=embedding
            )
            
            logger.info(f"Created clothing item in database with ID: {db_item.id}")
            
            # Create a chat history entry for this item
            crud.create_chat_history(
                db=db,
                prompt=f"Processed image: {image_url}",
                response=f"Added item: {caption}",
                image_url=image_url
            )
            
            logger.info("Created chat history entry")
            
            # Update state with the database item ID
            return {
                **state,
                "item_id": db_item.id
            }
        finally:
            # Always close the database session
            db.close()
    except Exception as e:
        logger.error(f"Error persisting to database: {e}")
        raise e

def get_items_step(state: State):
    """Process the search results and prepare them for the response.
    
    This function fetches the full item details from the database based on the item IDs
    returned by the search_items tool and formats them as dictionaries.
    """
    logger.info("Running get_items_step...")
    
    # Get the search results (item IDs) from state
    item_ids = state.get("search_items", [])
    if not item_ids:
        logger.warning("No search_items found in state")
        return state
    
    logger.info(f"Fetching {len(item_ids)} items from database: {item_ids}")
    
    try:
        # Create a database session
        db = SessionLocal()
        
        try:
            # Fetch the items from the database
            db_items = crud.get_clothing_items_by_ids(db=db, item_ids=item_ids)
            logger.info(f"Retrieved {len(db_items)} items from database")
            
            # Convert the items to dictionaries
            items = []
            for item in db_items:
                # Create a clean dictionary with primitive types only
                item_dict = {
                    "id": str(item.id),
                    "description": str(item.description) if item.description else "",
                    "image_url": str(item.image_url) if item.image_url else "",
                    "category": str(item.category) if item.category else None,
                    "color": str(item.color) if item.color else None,
                    "season": str(item.season) if item.season else None,
                    "tags": [str(tag.name) for tag in item.tags] if hasattr(item, 'tags') else []
                }
                items.append(item_dict)
            
            logger.info(f"Converted {len(items)} items to dictionaries")
            
            # Update state with the formatted items
            return {
                **state,
                "items": items
            }
        finally:
            # Always close the database session
            db.close()
    except Exception as e:
        logger.error(f"Error fetching items from database: {e}", exc_info=True)
        # Return original state on error
        return state


def format_item_search_response(state: State):
    """Format the search results for the response."""
    logger.info("Running format_item_search_response...")
    return state


def _route_from_tools(state):
    """Helper function for routing logic based on tool results."""
    logger.info(f"Conditional routing from tools, state keys: {list(state.keys())}")
    
    # Check for caption_image results
    if 'caption_image' in state:
        caption_result = state.get('caption_image')
        # Log appropriate info based on the result type
        if isinstance(caption_result, dict) and 'caption' in caption_result:
            logger.info(f"Routing to embed after caption_image, caption: {caption_result['caption'][:50]}...")
        elif isinstance(caption_result, str):
            # For backward compatibility
            logger.info(f"Routing to embed after caption_image, caption (str): {caption_result[:50]}...")
        else:
            logger.info("Routing to embed after caption_image with unknown format")
        return 'embed'
    # Handle search_items results
    elif state.get('search_items') is not None:
        logger.info(f"Routing to get_items after search_items, items: {state.get('search_items')}")
        return 'get_items'
    # Default route
    else:
        logger.info("No recognized tool output, routing to chat")
        return 'chat'
