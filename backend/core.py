from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from backend.agent.tools.image_storage import remove_image
from backend.agent.schemas import ItemResponse
from backend.db import crud, models
from backend.db.models import get_db
from sqlalchemy.orm import Session

import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info('Loading core api router')

# Create FastAPI router
core_router = APIRouter()
# Schemas moved to schemas.py

# POST /api/upload
# @core_router.post("/upload", response_model=UploadResponse)
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

# GET /api/items/{item_id}
@core_router.get("/items/{item_id}", response_model=ItemResponse)
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
@core_router.get("/items", response_model=List[ItemResponse])
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
@core_router.delete("/items/{item_id}")
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
@core_router.on_event("startup")
def init_db():
    """Initialize database tables on application startup."""
    models.create_tables()
    logger.info("Database tables initialized")
