from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from .vector_store import upsert_embedding, delete_embedding, query_embedding
from backend.services.embedding_service import get_text_embedding, get_image_embedding

import numpy as np
import uuid
from . import models

# Clothing Item CRUD operations
def create_clothing_item(
    db: Session,
    description: str,
    image_url: str,
    category: Optional[str] = None,
    color: Optional[str] = None,
    season: Optional[str] = None,
    tags: Optional[List[str]] = None,
    item_id: Optional[str] = None,
    embedding: Optional[np.ndarray] = None
) -> models.ClothingItem:
    """Create a new clothing item in the database"""
    # Use provided ID or generate new one
    if not item_id:
        item_id = str(uuid.uuid4())
    
    # Create the item
    db_item = models.ClothingItem(
        id=item_id,
        description=description,
        image_url=image_url,
        category=category,
        color=color,
        season=season
    )
    
    # Add to database
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    # Add tags if provided
    if tags:
        for tag_name in tags:
            # Get or create tag
            tag = get_or_create_tag(db, tag_name)
            db_item.tags.append(tag)
        
        db.commit()
        db.refresh(db_item)
    
    metadata = {
        "description": description,
        "image_url": image_url,
        "category": category,
        "color": color,
        "season": season,
        "tags": tags or []
    }
    upsert_embedding(item_id, embedding, metadata, "clothing_items")
    
    return db_item

def get_clothing_item(db: Session, item_id: str) -> Optional[models.ClothingItem]:
    """Get a clothing item by ID"""
    return db.query(models.ClothingItem).filter(models.ClothingItem.id == item_id).first()

def get_clothing_items_by_ids(db: Session, item_ids: List[str]) -> List[models.ClothingItem]:
    """
    Get all clothing items matching a list of item IDs.
    Args:
        db: SQLAlchemy Session
        item_ids: List of clothing item IDs to retrieve
    Returns:
        List of ClothingItem objects matching the provided IDs (order not guaranteed)
    """
    if not item_ids:
        return []
    return db.query(models.ClothingItem).filter(models.ClothingItem.id.in_(item_ids)).all()

def get_clothing_items(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category: Optional[str] = None,
    season: Optional[str] = None,
    tag: Optional[str] = None
) -> List[models.ClothingItem]:
    """Get multiple clothing items with optional filters"""
    query = db.query(models.ClothingItem)
    
    # Apply filters if provided
    if category:
        query = query.filter(models.ClothingItem.category == category)
    if season:
        query = query.filter(models.ClothingItem.season == season)
    if tag:
        query = query.join(models.ClothingItem.tags).filter(models.Tag.name == tag)
    
    return query.offset(skip).limit(limit).all()

def update_clothing_item(
    db: Session, 
    item_id: str, 
    description: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    season: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Optional[models.ClothingItem]:
    """Update a clothing item"""
    db_item = get_clothing_item(db, item_id)
    if not db_item:
        return None
    
    # Update fields if provided
    if description is not None:
        db_item.description = description
    if category is not None:
        db_item.category = category
    if color is not None:
        db_item.color = color
    if season is not None:
        db_item.season = season
    
    # Update tags if provided
    if tags is not None:
        # Clear existing tags
        db_item.tags = []
        
        # Add new tags
        for tag_name in tags:
            tag = get_or_create_tag(db, tag_name)
            db_item.tags.append(tag)
    
    db.commit()
    db.refresh(db_item)
    
    # Update embedding in vector database
    if description is not None:
        embedding = get_text_embedding(db_item.description)
        metadata = {
            "description": db_item.description,
            "image_url": db_item.image_url,
            "category": db_item.category,
            "color": db_item.color,
            "season": db_item.season,
            "tags": [tag.name for tag in db_item.tags]
        }
        upsert_embedding(item_id, embedding, metadata, "clothing_items")
    
    return db_item

def delete_clothing_item(db: Session, item_id: str) -> bool:
    """Delete a clothing item"""
    db_item = get_clothing_item(db, item_id)
    if not db_item:
        return False
    
    # Delete from database
    db.delete(db_item)
    db.commit()
    
    # Delete from vector database
    delete_embedding(item_id, "clothing_items")
    
    return True

# Tag CRUD operations
def get_or_create_tag(db: Session, name: str) -> models.Tag:
    """Get an existing tag or create a new one"""
    db_tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if db_tag:
        return db_tag
    
    db_tag = models.Tag(name=name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def get_tags(db: Session, skip: int = 0, limit: int = 100) -> List[models.Tag]:
    """Get all tags"""
    return db.query(models.Tag).offset(skip).limit(limit).all()

# Outfit CRUD operations
def create_outfit(
    db: Session,
    name: str,
    description: str,
    item_ids: List[str],
    occasion: Optional[str] = None,
    season: Optional[str] = None
) -> Optional[models.Outfit]:
    """Create a new outfit"""
    # Verify all items exist
    items = []
    for item_id in item_ids:
        item = get_clothing_item(db, item_id)
        if not item:
            # Item not found
            return None
        items.append(item)
    
    # Generate ID
    outfit_id = str(uuid.uuid4())
    
    # Create outfit
    db_outfit = models.Outfit(
        id=outfit_id,
        name=name,
        description=description,
        occasion=occasion,
        season=season
    )
    
    # Add items to outfit
    for item in items:
        db_outfit.items.append(item)
    
    # Add to database
    db.add(db_outfit)
    db.commit()
    db.refresh(db_outfit)
    
    # Create embedding and store in vector database
    embedding = get_text_embedding(f"{name} {description}")
    metadata = {
        "name": name,
        "description": description,
        "occasion": occasion,
        "season": season,
        "item_ids": item_ids
    }
    upsert_embedding(outfit_id, embedding, metadata, "outfits")
    
    return db_outfit

def get_outfit(db: Session, outfit_id: str) -> Optional[models.Outfit]:
    """Get an outfit by ID"""
    return db.query(models.Outfit).filter(models.Outfit.id == outfit_id).first()

def get_outfits(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    occasion: Optional[str] = None,
    season: Optional[str] = None
) -> List[models.Outfit]:
    """Get multiple outfits with optional filters"""
    query = db.query(models.Outfit)
    
    # Apply filters if provided
    if occasion:
        query = query.filter(models.Outfit.occasion == occasion)
    if season:
        query = query.filter(models.Outfit.season == season)
    
    return query.offset(skip).limit(limit).all()

def update_outfit(
    db: Session,
    outfit_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    occasion: Optional[str] = None,
    season: Optional[str] = None,
    item_ids: Optional[List[str]] = None
) -> Optional[models.Outfit]:
    """Update an outfit"""
    db_outfit = get_outfit(db, outfit_id)
    if not db_outfit:
        return None
    
    # Update fields if provided
    if name is not None:
        db_outfit.name = name
    if description is not None:
        db_outfit.description = description
    if occasion is not None:
        db_outfit.occasion = occasion
    if season is not None:
        db_outfit.season = season
    
    # Update items if provided
    if item_ids is not None:
        # Verify all items exist
        items = []
        for item_id in item_ids:
            item = get_clothing_item(db, item_id)
            if not item:
                # Item not found
                return None
            items.append(item)
        
        # Clear existing items
        db_outfit.items = []
        
        # Add new items
        for item in items:
            db_outfit.items.append(item)
    
    db.commit()
    db.refresh(db_outfit)
    
    # Update embedding in vector database
    if name is not None or description is not None:
        embedding = get_text_embedding(f"{db_outfit.name} {db_outfit.description}")
        metadata = {
            "name": db_outfit.name,
            "description": db_outfit.description,
            "occasion": db_outfit.occasion,
            "season": db_outfit.season,
            "item_ids": [item.id for item in db_outfit.items]
        }
        upsert_embedding(outfit_id, embedding, metadata, "outfits")
    
    return db_outfit

def delete_outfit(db: Session, outfit_id: str) -> bool:
    """Delete an outfit"""
    db_outfit = get_outfit(db, outfit_id)
    if not db_outfit:
        return False
    
    # Delete from database
    db.delete(db_outfit)
    db.commit()
    
    # Delete from vector database
    delete_embedding(outfit_id, "outfits")
    
    return True

# Chat history CRUD operations
def create_chat_history(
    db: Session,
    prompt: str,
    response: str,
    image_url: Optional[str] = None
) -> models.ChatHistory:
    """Create a new chat history entry"""
    # Generate ID
    chat_id = str(uuid.uuid4())
    
    # Create chat history
    db_chat = models.ChatHistory(
        id=chat_id,
        prompt=prompt,
        response=response,
        image_url=image_url
    )
    
    # Add to database
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    
    return db_chat

def get_chat_history(db: Session, skip: int = 0, limit: int = 100) -> List[models.ChatHistory]:
    """Get chat history entries"""
    return db.query(models.ChatHistory).order_by(models.ChatHistory.created_at.desc()).offset(skip).limit(limit).all()

# Vector search operations
def search_clothing_items_by_text(
    query_text: str,
    n_results: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Search for clothing items by text query"""
    # Generate embedding for query text
    query_embedding = get_text_embedding(query_text)
    
    # Query vector database
    results = query_embedding(query_embedding, "clothing_items", n_results, filter_metadata)
    
    return [result.dict() for result in results]

def search_clothing_items_by_image(
    image_url: str,
    n_results: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Search for clothing items by image"""
    # Generate embedding for image
    query_embedding = get_image_embedding(image_url)
    
    # Query vector database
    results = query_embedding(query_embedding, "clothing_items", n_results, filter_metadata)
    
    return [result.dict() for result in results]

def search_outfits_by_text(
    query_text: str,
    n_results: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Search for outfits by text query"""
    # Generate embedding for query text
    query_embedding = get_text_embedding(query_text)
    
    # Query vector database
    results = query_embedding(query_embedding, "outfits", n_results, filter_metadata)
    
    return [result.dict() for result in results]
