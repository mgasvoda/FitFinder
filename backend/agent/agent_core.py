from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.agent.tools.image_captioner import caption_image
from backend.agent.tools.outfit_searcher import search_outfits, search_clothing_items
from backend.agent.tools.image_storage import store_image, remove_image
from backend.db import crud, models
from backend.db.models import get_db
from sqlalchemy.orm import Session
import uuid

agent_router = APIRouter()

# Schemas from architecture doc
class ChatRequest(BaseModel):
    prompt: str
    optional_image_url: Optional[str] = None

class ChatResponse(BaseModel):
    response_text: str
    matching_outfits: Optional[List[Dict[str, Any]]] = None

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
@agent_router.post("/upload", response_model=UploadResponse)
def upload_item(image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Store the image
        image_url, item_id = store_image(image)
        
        # Generate description using image captioning
        description = caption_image(image_url)
        
        # Save to database
        db_item = crud.create_clothing_item(
            db=db,
            description=description,
            image_url=image_url
        )
        
        # Create chat history entry for this upload
        crud.create_chat_history(
            db=db,
            prompt=f"Uploaded image: {image.filename}",
            response=f"Added item: {description}",
            image_url=image_url
        )
        
        return UploadResponse(description=description, image_url=image_url, item_id=item_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload item: {str(e)}")

# POST /api/chat
@agent_router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        # Logging the incoming request
        print(f"Backend received chat request: {req}")
        
        # Search for matching outfits based on the prompt
        matching_outfits = search_outfits(req.prompt, req.optional_image_url)
        
        # TODO: Integrate LangGraph agent for more sophisticated responses
        response_text = f"I found {len(matching_outfits)} outfits that match your request."
        
        # Save chat history
        crud.create_chat_history(
            db=db,
            prompt=req.prompt,
            response=response_text,
            image_url=req.optional_image_url
        )
        
        # Logging the response
        response = ChatResponse(response_text=response_text, matching_outfits=matching_outfits)
        print(f"Backend sending response: {response}")
        
        return response
    except Exception as e:
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
        raise HTTPException(status_code=500, detail=f"Failed to delete item: {str(e)}")

# Initialize database tables
@agent_router.on_event("startup")
def init_db():
    models.create_tables()
