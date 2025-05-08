from typing import Any, Dict, Optional
from backend.db.models import ClothingItem, ClothingItemResponse
import os

def format_item_search_response(
    item: ClothingItem,
    vector_metadata: Optional[Dict[str, Any]] = None,
    image_base_path: str = "images"
) -> Dict[str, Any]:
    """
    Format a comprehensive clothing item response for the chatbot interface.
    Args:
        item: ClothingItem SQLAlchemy ORM object
        vector_metadata: (optional) Metadata dict from vector DB (Chroma)
        image_base_path: (optional) Base path for images on disk
    Returns:
        dict suitable for chatbot display
    """
    # Prefer vector metadata if available, otherwise fall back to DB fields
    meta = vector_metadata or {}
    
    def get_field(field):
        return meta.get(field) or getattr(item, field, None)

    # Tags may be list of str in metadata or ORM relationship
    tags = meta.get("tags")
    if tags is None and hasattr(item, "tags"):
        tags = [t.name for t in getattr(item, "tags", [])]

    # Compose image URL
    image_url = meta.get("image_url") or getattr(item, "image_url", None)
    if image_url and not image_url.startswith("/images/"):
        # If not already a relative URL, convert to standard format
        ext = os.path.splitext(image_url)[-1] or ".jpg"
        image_url = f"/images/clothing_items/{item.id}{ext}"

    response = {
        "id": get_field("id"),
        "description": get_field("description"),
        "category": get_field("category"),
        "color": get_field("color"),
        "season": get_field("season"),
        "tags": tags or [],
        "image_url": image_url,
    }
    # Optionally include vector similarity score if present
    if "score" in meta:
        response["similarity_score"] = meta["score"]
    return response


def format_item_search_messages(items: list) -> list:
    """
    Format a list of items into a list of LangGraph-compliant messages.
    Each message is a dict with only 'role' and 'content'.
    If no items, return a single assistant message indicating no matches.
    """
    if not items:
        return [{"role": "assistant", "content": "No matching items found."}]
    messages = []
    for item in items:
        resp = format_item_search_response(item)
        # Summarize the item dict into a string for content
        summary = (
            f"Item ID: {resp.get('id')}\n"
            f"Description: {resp.get('description')}\n"
            f"Category: {resp.get('category')}\n"
            f"Color: {resp.get('color')}\n"
            f"Season: {resp.get('season')}\n"
            f"Tags: {', '.join(resp.get('tags', []))}\n"
            f"Image URL: {resp.get('image_url')}"
        )
        if resp.get('similarity_score') is not None:
            summary += f"\nSimilarity Score: {resp['similarity_score']}"
        messages.append({"role": "assistant", "content": summary})
    return messages
