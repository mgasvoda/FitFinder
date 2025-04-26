from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.agent.tools.image_captioner import caption_image
from backend.agent.tools.outfit_searcher import search_outfits
from backend.agent.tools.image_storage import store_image

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

# POST /api/upload
@agent_router.post("/upload", response_model=UploadResponse)
def upload_item(image: UploadFile = File(...)):
    # Skeleton: store image, caption, add to DB
    image_url, item_id = store_image(image)
    description = caption_image(image_url)
    # TODO: Save to DB
    return UploadResponse(description=description, image_url=image_url, item_id=item_id)

# POST /api/chat
@agent_router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    # Logging the incoming request
    print(f"Backend received chat request: {req}")
    
    # Skeleton: call agent logic
    # TODO: Integrate LangGraph agent
    response_text = "This is a placeholder response."
    matching_outfits = search_outfits(req.prompt, req.optional_image_url)
    
    # Logging the response
    response = ChatResponse(response_text=response_text, matching_outfits=matching_outfits)
    print(f"Backend sending response: {response}")
    
    return response

# GET /api/items/{item_id}
@agent_router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: str):
    # Skeleton: fetch from DB
    # TODO: Query DB for item
    return ItemResponse(id=item_id, description="desc", image_url="url", tags=["sample"])
