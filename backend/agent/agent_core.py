from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional, List, Dict, Any
from backend.agent.tools.image_storage import store_image, remove_image
from backend.agent.orchestrator import run_agent, OutfitAgentState, State
from backend.agent.schemas import ChatRequest, ChatResponse, UploadResponse, ItemResponse
from backend.db import crud, models
from backend.db.models import get_db
from sqlalchemy.orm import Session
from langchain_core.messages import AIMessage, HumanMessage # Keep for type hinting if needed
from backend.agent.utils import get_message_details # Import the new utility

import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info('Loading agent core')

# Create FastAPI router
agent_router = APIRouter()
# Schemas moved to schemas.py

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
    """
    Handle chat requests and interact with the agent.
    
    Args:
        req: The chat request containing prompt and optional image URL
        db: Database session
        
    Returns:
        ChatResponse: The agent's response
    """
    try:
        # Log the incoming request
        logger.info(f"Backend received chat request: {req}")

        # Prepare initial state for the agent
        state = {
            "messages": [{"role": "user", "content": req.prompt}]
        }
        
        # Handle image content if present
        if req.optional_image_url:
            state["image_url"] = req.optional_image_url
            state["image_file"] = req.optional_image_url
        
        logger.info(f"Prepared initial state: {state}")
        
        # Run the agent using the orchestrator
        result_state = run_agent(state)
        logger.info(f"Agent execution completed with state keys: {result_state.keys()}")
        
        # Extract the response text from the agent's messages
        messages = result_state.get("messages", [])
        response_text = "Sorry, I encountered an issue or couldn't find a specific answer."
        
        # Find the last AI message
        if messages:
            for msg_obj in reversed(messages):
                details = get_message_details(msg_obj)
                if details and details["role"] == "assistant":
                    response_text = details["content"]
                    break
        
        # If we still don't have a response, use a fallback (already initialized)
        
        # Extract matching outfits if available
        matching_outfits = result_state.get("items", [])
        
        # If items not found but search_items exists, we need to convert the IDs to dictionaries
        if not matching_outfits and "search_items" in result_state:
            item_ids = result_state.get("search_items", [])
            logger.info(f"Found {len(item_ids)} item IDs in search_items, converting to dictionaries")
            
            try:
                # Create a database session
                db_session = SessionLocal()
                try:
                    # Fetch the items from the database
                    db_items = crud.get_clothing_items_by_ids(db=db_session, item_ids=item_ids)
                    logger.info(f"Retrieved {len(db_items)} items from database")
                    
                    # Convert the items to dictionaries
                    matching_outfits = []
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
                        matching_outfits.append(item_dict)
                finally:
                    db_session.close()
            except Exception as e:
                logger.error(f"Error converting search_items to dictionaries: {e}", exc_info=True)
                # Fallback: create minimal dictionaries with just IDs
                matching_outfits = [{"id": item_id, "description": f"Item {item_id}"} for item_id in item_ids]
        
        # Ensure all items in matching_outfits are dictionaries
        for i, item in enumerate(matching_outfits):
            if not isinstance(item, dict):
                logger.warning(f"Item at index {i} is not a dictionary, converting: {item}")
                if isinstance(item, str):
                    # It's probably an ID string
                    matching_outfits[i] = {"id": item, "description": f"Item {item}"}
                else:
                    # Try to convert to dict if it has attributes
                    try:
                        if hasattr(item, '__dict__'):
                            matching_outfits[i] = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
                        else:
                            matching_outfits[i] = {"id": str(item), "description": str(item)}
                    except Exception as e:
                        logger.error(f"Error converting item to dictionary: {e}")
                        matching_outfits[i] = {"id": "unknown", "description": str(item)}
        
        logger.info(f"Found {len(matching_outfits)} matching outfits")

        # Create a serializable version of the state for debugging
        serializable_state = {}
        for key, value in result_state.items():
            # Skip messages and embedding as they might contain complex objects
            if key in ["messages", "embedding"]:
                continue
                
            # Handle primitive types and lists/dicts
            if isinstance(value, (str, int, float, bool, type(None))):
                serializable_state[key] = value
            else:
                # Try to convert other types to string
                try:
                    serializable_state[key] = str(value)
                except Exception:
                    serializable_state[key] = "<unserializable>"
        
        # Always propagate matching_outfits from result_state if present
        matching_outfits = result_state.get("matching_outfits", [])

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
    """Initialize database tables on application startup."""
    models.create_tables()
    logger.info("Database tables initialized")
