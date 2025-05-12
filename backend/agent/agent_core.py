from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.agent.tools.image_storage import store_image
from backend.agent.langgraph_agent import graph
from backend.agent.tools.caption_image import caption_image
from backend.db import crud, models
from backend.db.models import get_db
from sqlalchemy.orm import Session
from langchain_core.messages import AIMessage

agent_router = APIRouter()

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info('Loading agent core')

# Schemas from architecture doc
class ChatRequest(BaseModel):
    prompt: str
    optional_image_url: Optional[str] = None

class ChatResponse(BaseModel):
    response_text: str
    matching_outfits: Optional[List[Dict[str, Any]]] = None
    raw_response: Optional[Any] = None  # Holds the full structured output from the agent/model

class UploadResponse(BaseModel):
    description: str
    image_url: str
    item_id: str

class ItemResponse(BaseModel):
    id: str
    description: str
    image_url: str
    tags: List[str]
    category: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None

# POST /api/upload
# @agent_router.post("/upload", response_model=UploadResponse)
# def upload_item(image: UploadFile = File(...), db: Session = Depends(get_db)):
#     try:
#         # Store the image
#         image_url, item_id = store_image(image)
        
#         # Generate description using image captioning
#         description = caption_image(image_url)
        
#         # Save to database
#         db_item = crud.create_clothing_item(
#             db=db,
#             description=description,
#             image_url=image_url
#         )
        
#         # Create chat history entry for this upload
#         crud.create_chat_history(
#             db=db,
#             prompt=f"Uploaded image: {image.filename}",
#             response=f"Added item: {description}",
#             image_url=image_url
#         )
        
#         return UploadResponse(description=description, image_url=image_url, item_id=item_id)
#     except Exception as e:
#         logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Failed to upload item: {str(e)}")

# POST /api/chat
@agent_router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        # Logging the incoming request
        logger.info(f"Backend received chat request: {req}")

        # Prepare initial state for the LangGraph agent
        state = {
            "messages": [{"role": "user", "content": req.prompt}]
        }
        
        # Handle image content if present
        # Important: Both image_url AND image_file need to be set
        # The graph needs image_file for the persist_db_step to work
        if req.optional_image_url:
            state["image_url"] = req.optional_image_url
            state["image_file"] = req.optional_image_url
        
        logger.info(f"Prepared initial state: {state}")
        
        # Execute the steps in the graph
        # Instead of using stream, we'll use a different approach to ensure all nodes execute
        try:
            # First we'll execute using a direct invoke call
            logger.info("Executing graph with direct invoke call")
            result_state = {}
            
            # Direct invocation of the graph - this should trigger full execution
            result_state = graph.invoke(state)
            logger.info(f"Direct invoke completed with state keys: {result_state.keys()}")
            
            # If the graph didn't proceed to embed_step and persist_db_step,
            # we'll manually check the conditions and invoke those steps
            if 'caption' in result_state and 'embedding' not in result_state:
                from backend.agent.langgraph_agent import embed_step, persist_db_step
                logger.info("Caption found but embedding missing - manually invoking embed_step")
                # Execute the embedding step with the caption
                embed_result = embed_step(result_state)
                # Update the state with the embedding result
                result_state.update(embed_result)
                
                # Now execute persist_db_step with the updated state
                logger.info("Manually invoking persist_db_step")
                persist_result = persist_db_step(result_state)
                # Update the state with the persistence result
                result_state.update(persist_result)
            
            # Save the final state for response extraction
            final_state = result_state
            
        except Exception as e:
            logger.error(f"Error during graph execution: {e}", exc_info=True)
            # If we encountered an error, try using the stream approach as fallback
            logger.info("Falling back to streaming approach")
            try:
                final_state = {}
                # Stream events and build up the final state
                for event in graph.stream(state, stream_mode=["values"]):
                    if isinstance(event, dict):
                        # For a values stream, each event is the full state
                        final_state = event
                    logger.debug(f"Stream event: {event}")
                logger.info(f"Stream execution complete, state keys: {final_state.keys()}")
            except Exception as stream_err:
                logger.error(f"Error in stream fallback: {stream_err}", exc_info=True)
                final_state = {}
        
        # Extract messages from the final state
        messages = []
        logger.info(f"Final state keys for message extraction: {final_state.keys()}")
        
        # First check common locations for messages
        if "messages" in final_state and final_state["messages"]:
            messages = final_state["messages"]
            logger.info(f"Found {len(messages)} messages in state['messages']")
        elif "chat" in final_state:
            if isinstance(final_state["chat"], dict) and "messages" in final_state["chat"]:
                messages = final_state["chat"]["messages"]
                logger.info(f"Found {len(messages)} messages in state['chat']['messages']")
            elif isinstance(final_state["chat"], list):
                messages = final_state["chat"]
                logger.info(f"Found {len(messages)} messages in state['chat'] list")
        
        # If messages still empty, search all dict values for messages
        if not messages:
            for key, value in final_state.items():
                if key != "__run_info__" and isinstance(value, dict) and "messages" in value:
                    messages = value["messages"]
                    logger.info(f"Found {len(messages)} messages in state['{key}']['messages']")
                    break
                elif key != "__run_info__" and isinstance(value, list) and value and hasattr(value[0], "content"):
                    messages = value
                    logger.info(f"Found {len(messages)} message objects in state['{key}']")
                    break
        
        # Process the messages to extract response text
        response_text = None
        
        if messages:
            logger.info(f"Processing {len(messages)} messages to extract response")
            for message in reversed(messages):
                try:
                    # First handle objects with content attribute (like AIMessage)
                    if hasattr(message, "content"):
                        content = message.content
                        if isinstance(content, str):
                            response_text = content
                            logger.info("Found response in message.content (string)")
                            break
                        elif isinstance(content, list):
                            # Handle content as list of components
                            text_parts = [part.get("text", "") for part in content 
                                          if isinstance(part, dict) and "text" in part]
                            if text_parts:
                                response_text = "\n".join(text_parts).strip()
                                logger.info("Found response in message.content (list of components)")
                                break
                    # Then handle dictionary style messages
                    elif isinstance(message, dict):
                        if 'text' in message:
                            response_text = message['text']
                            logger.info("Found response in message['text']")
                            break
                        elif 'content' in message:
                            content = message['content']
                            if isinstance(content, str):
                                response_text = content
                                logger.info("Found response in message['content'] (string)")
                                break
                            elif isinstance(content, list):
                                text_parts = [part.get("text", "") for part in content 
                                              if isinstance(part, dict) and "text" in part]
                                if text_parts:
                                    response_text = "\n".join(text_parts).strip()
                                    logger.info("Found response in message['content'] (list)")
                                    break
                except Exception as e:
                    logger.warning(f"Error processing message: {e}")
                    continue
        else:
            logger.warning("No messages found in final state")
        
        # Provide a default response if no text was extracted
        if response_text is None:
            response_text = "No response generated."
            logger.warning("No response text extracted from messages")

        # Extract any items or outfits found during search
        matching_items = final_state.get("items", [])
        if matching_items:
            logger.info(f"Found {len(matching_items)} matching items")
            
        # Convert ClothingItem objects to dictionaries
        matching_outfits = []
        for item in matching_items:
            try:
                # Check if item is a SQLAlchemy model object
                if hasattr(item, '__dict__') and hasattr(item, '__table__'):
                    # Create a clean dictionary with primitive types only
                    item_dict = {
                        "id": str(item.id),
                        "description": str(item.description) if item.description else "",
                        "image_url": str(item.image_url) if item.image_url else "",
                        "category": str(item.category) if item.category else None,
                        "color": str(item.color) if item.color else None,
                        "season": str(item.season) if item.season else None,
                    }
                    
                    # Handle tags separately to avoid relationship loading issues
                    try:
                        if hasattr(item, 'tags'):
                            item_dict["tags"] = [str(tag.name) for tag in item.tags]
                        else:
                            item_dict["tags"] = []
                    except Exception as e:
                        logger.warning(f"Error processing tags: {e}")
                        item_dict["tags"] = []
                        
                    matching_outfits.append(item_dict)
                elif isinstance(item, dict):
                    # Item is already a dictionary
                    matching_outfits.append(item)
                else:
                    # Try to convert to dict if it has a __dict__ attribute
                    try:
                        if hasattr(item, '__dict__'):
                            matching_outfits.append({k: v for k, v in item.__dict__.items() 
                                                   if not k.startswith('_')})
                        else:
                            # Last resort: try string representation
                            matching_outfits.append({"description": str(item)})
                    except Exception as e:
                        logger.warning(f"Could not convert item to dict: {e}")
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                # Skip this item if we can't process it

        # Create a serializable version of the final state
        serializable_state = {}
        for key, value in final_state.items():
            # Handle different types of values
            if key == 'items' and isinstance(value, list):
                # We've already processed items into matching_outfits
                serializable_state[key] = matching_outfits
            elif isinstance(value, list):
                # Process lists (might contain SQLAlchemy objects)
                serializable_list = []
                for item in value:
                    if hasattr(item, '__table__'):
                        # SQLAlchemy model
                        try:
                            # Convert to dict with only primitive types
                            item_dict = {}
                            for column in item.__table__.columns:
                                col_name = column.name
                                col_value = getattr(item, col_name, None)
                                item_dict[col_name] = str(col_value) if col_value is not None else None
                            serializable_list.append(item_dict)
                        except Exception as e:
                            logger.warning(f"Error converting list item to dict: {e}")
                            serializable_list.append({"error": "Could not serialize item"})
                    elif isinstance(item, dict):
                        serializable_list.append(item)
                    elif hasattr(item, '__dict__'):
                        try:
                            serializable_list.append({k: v for k, v in item.__dict__.items() 
                                                    if not k.startswith('_')})
                        except Exception as e:
                            logger.warning(f"Error converting object to dict: {e}")
                            serializable_list.append({"error": "Could not serialize item"})
                    else:
                        # Try to convert to string
                        try:
                            serializable_list.append(str(item))
                        except Exception:
                            serializable_list.append("<unserializable>")
                serializable_state[key] = serializable_list
            elif hasattr(value, '__table__'):
                # Single SQLAlchemy model
                try:
                    item_dict = {}
                    for column in value.__table__.columns:
                        col_name = column.name
                        col_value = getattr(value, col_name, None)
                        item_dict[col_name] = str(col_value) if col_value is not None else None
                    serializable_state[key] = item_dict
                except Exception as e:
                    logger.warning(f"Error converting value to dict: {e}")
                    serializable_state[key] = {"error": "Could not serialize item"}
            elif isinstance(value, dict):
                # Handle nested dictionaries
                try:
                    # Simple conversion for now - could be made recursive for deep nesting
                    serializable_dict = {}
                    for k, v in value.items():
                        if hasattr(v, '__table__'):
                            # SQLAlchemy model in dict
                            inner_dict = {}
                            for column in v.__table__.columns:
                                col_name = column.name
                                col_value = getattr(v, col_name, None)
                                inner_dict[col_name] = str(col_value) if col_value is not None else None
                            serializable_dict[k] = inner_dict
                        elif isinstance(v, (str, int, float, bool, type(None))):
                            serializable_dict[k] = v
                        else:
                            serializable_dict[k] = str(v)
                    serializable_state[key] = serializable_dict
                except Exception as e:
                    logger.warning(f"Error processing dictionary: {e}")
                    serializable_state[key] = {"error": "Could not serialize dictionary"}
            elif isinstance(value, (str, int, float, bool, type(None))):
                # Primitive types can be directly serialized
                serializable_state[key] = value
            else:
                # Try to convert other types to string
                try:
                    serializable_state[key] = str(value)
                except Exception:
                    serializable_state[key] = "<unserializable>"
        
        # Create and return the response
        response = ChatResponse(
            response_text=response_text,
            matching_outfits=matching_outfits,
            raw_response=serializable_state
        )
        logger.info(f"Sending response with text: {response_text[:100]}...")
        logger.debug(f"Serialized state keys: {serializable_state.keys()}")
        

        return response
    except Exception as e:
        logger.error(f"Unhandled error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

# GET /api/items/{item_id}
@agent_router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: str, db: Session = Depends(get_db)):
    try:
        # Query DB for item
        db_item = crud.get_clothing_item(db, item_id)
        
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return ItemResponse(
            id=db_item.id,
            description=db_item.description,
            image_url=db_item.image_url,
            tags=[tag.name for tag in db_item.tags],
            category=db_item.category,
            color=db_item.color,
            season=db_item.season
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve item: {str(e)}")

# GET /api/items
@agent_router.get("/items", response_model=List[ItemResponse])
def list_items(
    skip: int = 0, 
    limit: int = 100, 
    category: Optional[str] = None,
    season: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        # Query DB for items with filters
        db_items = crud.get_clothing_items(
            db=db,
            skip=skip,
            limit=limit,
            category=category,
            season=season,
            tag=tag
        )
        
        # Convert to response model
        return [
            ItemResponse(
                id=item.id,
                description=item.description,
                image_url=item.image_url,
                tags=[tag.name for tag in item.tags],
                category=item.category,
                color=item.color,
                season=item.season
            ) for item in db_items
        ]
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve items: {str(e)}")

# DELETE /api/items/{item_id}
@agent_router.delete("/items/{item_id}")
def delete_item(item_id: str, db: Session = Depends(get_db)):
    try:
        # Get the item first to get the image URL
        db_item = crud.get_clothing_item(db, item_id)
        
        if not db_item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Delete the item from the database
        success = crud.delete_clothing_item(db, item_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete item")
        
        # Delete the image file
        remove_image(db_item.image_url)
        
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")

# Initialize database tables
@agent_router.on_event("startup")
def init_db():
    models.create_tables()
