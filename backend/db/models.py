from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime
import uuid
import os

# SQLAlchemy setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'fitfinder.db')
DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH.replace(os.sep, '/')}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Association tables for many-to-many relationships
item_tag_association = Table(
    "item_tag_association",
    Base.metadata,
    Column("item_id", String, ForeignKey("clothing_items.id")),
    Column("tag_id", Integer, ForeignKey("tags.id"))
)

outfit_item_association = Table(
    "outfit_item_association",
    Base.metadata,
    Column("outfit_id", String, ForeignKey("outfits.id")),
    Column("item_id", String, ForeignKey("clothing_items.id"))
)

# SQLAlchemy ORM Models
class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    items = relationship("ClothingItem", secondary=item_tag_association, back_populates="tags")

class ClothingItem(Base):
    __tablename__ = "clothing_items"
    id = Column(String, primary_key=True, index=True)
    description = Column(Text)
    image_url = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    category = Column(String)  # e.g., "top", "bottom", "dress", "accessory"
    color = Column(String)
    season = Column(String)  # e.g., "summer", "winter", "all"
    tags = relationship("Tag", secondary=item_tag_association, back_populates="items")
    outfits = relationship("Outfit", secondary=outfit_item_association, back_populates="items")

class Outfit(Base):
    __tablename__ = "outfits"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    occasion = Column(String)  # e.g., "casual", "formal", "workout"
    season = Column(String)
    items = relationship("ClothingItem", secondary=outfit_item_association, back_populates="outfits")

class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(String, primary_key=True, index=True)
    prompt = Column(Text)
    response = Column(Text)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

# Pydantic Models for API
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int

    class Config:
        orm_mode = True

class ClothingItemBase(BaseModel):
    description: str
    image_url: str
    category: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None

class ClothingItemCreate(ClothingItemBase):
    tags: Optional[List[str]] = []

class ClothingItemUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    season: Optional[str] = None
    tags: Optional[List[str]] = None

class ClothingItemResponse(ClothingItemBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    tags: List[str]

    class Config:
        orm_mode = True

class OutfitBase(BaseModel):
    name: str
    description: str
    occasion: Optional[str] = None
    season: Optional[str] = None

class OutfitCreate(OutfitBase):
    item_ids: List[str]

class OutfitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    occasion: Optional[str] = None
    season: Optional[str] = None
    item_ids: Optional[List[str]] = None

class OutfitResponse(OutfitBase):
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    items: List[ClothingItemResponse]

    class Config:
        orm_mode = True

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

class VectorEmbedding(BaseModel):
    id: str
    embedding: List[float]
    metadata: Dict[str, Any]

# Helper functions
def create_tables():
    Base.metadata.create_all(bind=engine)

def generate_id():
    return str(uuid.uuid4())

def get_image_path(item_id: str, file_extension: str):
    # Ensure the images directory exists
    os.makedirs("images", exist_ok=True)
    return f"images/{item_id}{file_extension}"
