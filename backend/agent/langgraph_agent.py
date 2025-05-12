from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_anthropic import ChatAnthropic
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage

# from backend.agent.tools.outfit_searcher import search_outfits, search_clothing_items
from backend.agent.tools.caption_image import caption_image
from backend.agent.tools.image_storage import store_image
from backend.agent.tools.outfit_searcher import search_clothing_items as search_items
from backend.services.embedding_service import get_text_embedding
from backend.db.models import SessionLocal
from backend.db import crud

from dotenv import load_dotenv
from typing import Optional
from typing import TypedDict, Annotated
import numpy as np

import uuid
import os
import json
import logging


load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info('Loading langgraph_agent module')


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
        logger.info(f"Tool node state update keys: {list(state_update.keys())}")
        
        return state_update


def store_image_step(state: State):
    # expects: state['image_file']
    return store_image(state["image_file"])


def embed_step(state: State):
    logger.info("Embedding...")
    # Debug the state keys to help diagnose issues
    logger.info(f"State keys in embed_step: {list(state.keys())}")
    
    # First try to get the caption directly from state (extracted by CaptionToolNode)
    caption = state.get("caption")
    if caption:
        logger.info(f"Using caption from state: {caption[:50]}...")
    
    # If not found, try to extract from caption_image result
    if not caption:
        caption_result = state.get("caption_image")
        if isinstance(caption_result, dict) and "caption" in caption_result:
            caption = caption_result["caption"]
            logger.info(f"Extracted caption from caption_image dict: {caption[:50]}...")
        elif isinstance(caption_result, str):
            # For backward compatibility with string result
            caption = caption_result
            logger.info(f"Using caption_image string: {caption[:50]}...")
    
    # Last resort - try to extract from messages
    if not caption:
        if state.get("messages") and len(state["messages"]) > 0:
            for msg in state["messages"]:
                if hasattr(msg, "name") and msg.name == "caption_image":
                    try:
                        # Parse the content which should be JSON
                        content = json.loads(msg.content)
                        if isinstance(content, dict) and "caption" in content:
                            caption = content["caption"]
                            logger.info(f"Extracted caption from message content dict: {caption[:50]}...")
                        elif isinstance(content, str):
                            caption = content
                            logger.info(f"Extracted caption string from message content: {caption[:50]}...")
                        break
                    except Exception as e:
                        logger.error(f"Failed to parse caption from message content: {e}")
    
    # Validate we have a caption
    if not caption:
        logger.error("No caption found in state for embedding")
        raise ValueError("No caption found in state for embedding")
    
    # Generate embedding
    logger.info(f"Generating embedding for caption: {caption[:50]}...")
    embedding = get_text_embedding(text=caption)
    
    # Return embedding and caption
    return {'embedding': embedding, 'caption': caption}


def persist_db_step(state: State):
    logger.info('Persisting data to database')
    logger.info(f"State keys in persist_db_step: {list(state.keys())}")
    
    # Get item_id and image_url that were created during the caption step
    item_id = state.get("item_id")
    image_url = state.get("image_url")
    
    # If we don't have them, try to extract from caption_image result
    if (not item_id or not image_url) and "caption_image" in state:
        caption_result = state.get("caption_image")
        if isinstance(caption_result, dict):
            if not item_id and "item_id" in caption_result:
                item_id = caption_result["item_id"]
                logger.info(f"Using item_id from caption_image result: {item_id}")
            
            if not image_url and "image_url" in caption_result:
                image_url = caption_result["image_url"]
                logger.info(f"Using image_url from caption_image result: {image_url}")
    
    # Still missing? Fail loudly
    if not item_id or not image_url:
        raise ValueError("No item_id or image_url found in state for persistence")

    
    # Get caption and embedding from state
    caption = state.get("caption")
    embedding = state.get("embedding")
    
    # Last resort for caption - try to get it from caption_image result
    if not caption and "caption_image" in state:
        caption_result = state.get("caption_image")
        if isinstance(caption_result, dict) and "caption" in caption_result:
            caption = caption_result["caption"]
        elif isinstance(caption_result, str):
            caption = caption_result
        logger.info(f"Using caption from caption_image: {caption[:50] if caption else 'None'}...")
    
    # Validate we have the necessary data
    if not caption:
        logger.warning("No caption found, using placeholder")
        raise ValueError("No caption found in state for persistence")

    if not embedding:
        logger.warning("No embedding found - this will cause search to fail")
        raise ValueError("No embedding found in state for persistence")
    
    logger.info(f"Persisting to DB: item_id={item_id}, caption={caption[:50]}..., image={image_url}")
    db = SessionLocal()

    try:
        crud.create_clothing_item(
            db=db,
            item_id=item_id,
            description=caption,
            image_url=image_url,
            embedding=embedding
        )
        logger.info(f"Successfully created clothing item with ID: {item_id}")
    except Exception as e:
        logger.error(f"Error creating clothing item: {str(e)}")
        raise
    
    return {"item_id": item_id, "image_url": image_url, "caption": caption}


def get_items_step(state: State):
    db = SessionLocal()
    ids = state.get("search_items", [])
    items = crud.get_clothing_items_by_ids(db=db, item_ids=ids)
    return {"items": items}


def format_item_search_response(state: State):
    from backend.agent.formatters import format_item_search_messages
    messages = format_item_search_messages(state.get("items", []) or [])
    return {"messages": messages}


# Instantiate the LangGraph agent with anthropic model
llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    anthropic_api_key=ANTHROPIC_API_KEY
)

tools = [caption_image, search_items]

# --- Build StateGraph for sequential workflow ---
graph_builder = StateGraph(State)

# Define nodes
graph_builder.add_node("chat", lambda state: {"messages": llm.bind_tools(tools).invoke(state['messages'])})
graph_builder.add_node("tools", CaptionToolNode(tools))
graph_builder.add_node("embed", embed_step)
graph_builder.add_node("persist_db", persist_db_step)
graph_builder.add_node("get_items", get_items_step)
graph_builder.add_node("format_items", format_item_search_response)

# Define the initial flow
graph_builder.add_edge(START, "chat")

# Route from chat based on whether tools need to be called
graph_builder.add_conditional_edges(
    "chat", 
    tools_condition,
    {
        "tools": "tools",  # If tools are requested, go to tools node
        END: END  # Otherwise end the conversation
    }
)

# Helper function for better routing logic with logging
def _route_from_tools(state):
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

# Improved conditional edge routing to the proper next node based on tool results
graph_builder.add_conditional_edges(
    'tools',
    _route_from_tools,
    {
        'embed': 'embed',            # If caption_image tool was used, route to embed node
        'get_items': 'get_items',    # If search_items tool was used, route to get_items node
        'chat': 'chat'               # If no recognized tool was used, route back to chat
    }
)

# Define the remaining sequential flows
graph_builder.add_edge("embed", "persist_db")
graph_builder.add_edge('persist_db', 'chat')
graph_builder.add_edge('get_items', 'format_items')
graph_builder.add_edge('format_items', 'chat')

# Add an edge from chat to END when the conversation is complete (END is a special state)
graph_builder.add_edge("chat", END)

# Compile the graph to an executable tool
graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    logger.info(f"Starting graph stream with input: {user_input}")
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        # Log more detailed node transition information
        node_name = next(iter(event))
        logger.info(f"Graph transition: {node_name}")
        logger.debug(f"Graph stream event data: {event}")
        
        # Uncomment this to print responses to the console
        for key, value in event.items():
            if "messages" in value and value["messages"]:
                try:
                    if isinstance(value["messages"], list) and value["messages"]:
                        msg = value["messages"][-1]
                        if hasattr(msg, "content"):
                            logger.info(f"Message: {msg.content[:100]}...")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")


if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
