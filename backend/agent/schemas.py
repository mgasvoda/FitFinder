from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Schemas for agent API endpoints
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
