from typing import Optional, List, Dict, Any
from backend.services.embedding_service import get_text_embedding, get_image_embedding, get_multimodal_embedding
from backend.db.vector_store import query_embedding
from backend.db import crud, models
from backend.db.models import get_db
from sqlalchemy.orm import Session
from langchain_core.tools import tool

def search_outfits(
    query_text: str, 
    optional_image_url: Optional[str] = None,
    n_results: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Search for outfits based on text query and optional image
    
    Args:
        query_text (str): Text query for outfit search
        optional_image_url (Optional[str]): Optional image URL to include in the search
        n_results (int): Maximum number of results to return
        filter_metadata (Optional[Dict[str, Any]]): Optional filter criteria
        
    Returns:
        Optional[List[Dict[str, Any]]]: List of matching outfits with metadata
    """
    try:
        # Generate embedding based on inputs
        if optional_image_url and query_text:
            # Multimodal search (text + image)
            query_embedding = get_multimodal_embedding(query_text, optional_image_url)
        elif optional_image_url:
            # Image-only search
            query_embedding = get_image_embedding(optional_image_url)
        else:
            # Text-only search
            query_embedding = get_text_embedding(query_text)
        
        # Query the vector database
        results = query_embedding(
            query_embedding=query_embedding,
            collection_name="outfits",
            n_results=n_results,
            filter_metadata=filter_metadata
        )
        
        # Format results
        formatted_results = []
        for result in results:
            # Get the full outfit details from SQLite
            db = next(get_db())
            outfit = crud.get_outfit(db, result.id)
            
            if outfit:
                # Format the outfit with its items
                outfit_data = {
                    "id": outfit.id,
                    "name": outfit.name,
                    "description": outfit.description,
                    "occasion": outfit.occasion,
                    "season": outfit.season,
                    "score": result.score,
                    "items": []
                }
                
                # Add items
                for item in outfit.items:
                    item_data = {
                        "id": item.id,
                        "description": item.description,
                        "image_url": item.image_url,
                        "category": item.category,
                        "color": item.color,
                        "tags": [tag.name for tag in item.tags]
                    }
                    outfit_data["items"].append(item_data)
                
                formatted_results.append(outfit_data)
        
        return formatted_results
    
    except Exception as e:
        print(f"Error in outfit search: {e}")


def filter_clothing_items_sqlite(tags: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Filter clothing items in SQLite by tags/metadata and return a list of item IDs.

    Args:
        tags (Optional[Dict[str, Any]]): Dictionary of metadata to filter by (e.g., category, color, user tags).
    
    Returns:
        List[str]: List of matching clothing item IDs.
    """
    db = next(get_db())
    query = db.query(models.ClothingItem)
    if tags:
        for key, value in tags.items():
            if hasattr(models.ClothingItem, key):
                query = query.filter(getattr(models.ClothingItem, key) == value)
            # Add more sophisticated tag filtering as needed (e.g., for many-to-many tags)
    return [item.id for item in query.all()]


def vector_search_chroma(
    embedding: List[float],
    allowed_ids: Optional[List[str]] = None,
    n_results: int = 5,
    collection_name: str = "clothing_items"
) -> List[Any]:
    """
    Perform a vector search in Chroma, optionally restricting to allowed IDs.

    Args:
        embedding (List[float]): The query embedding.
        allowed_ids (Optional[List[str]]): If provided, restrict search to these item IDs.
        n_results (int): Number of results to return.
        collection_name (str): Chroma collection name.

    Returns:
        List[Any]: List of matching items (Chroma results).    
    """
    filter_metadata = {"id": {"$in": allowed_ids}} if allowed_ids else None
    return query_embedding(
        query_embedding=embedding,
        collection_name=collection_name,
        n_results=n_results,
        filter_metadata=filter_metadata
    )


@tool("search_items", parse_docstring=True)
def search_clothing_items(
    query_text: str, 
    optional_image_url: Optional[str] = None,
    n_results: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> Optional[List[str]]:
    """
    Search for individual clothing items based on text query and optional image.

    Args:
        query_text (str): Text query for item search.
        optional_image_url (Optional[str]): Optional image URL to include in the search.
        n_results (int): Maximum number of results to return.
        filter_metadata (Optional[dict]): Optional filter criteria (applied in SQLite first if present).

    Returns:
        Optional[List[str]]: List of matching clothing item IDs.
    """
    try:
        # 1. Filter in SQLite if filter_metadata is provided
        allowed_ids = filter_clothing_items_sqlite(filter_metadata) if filter_metadata else None

        # 2. Generate embedding
        if optional_image_url and query_text:
            embedding = get_multimodal_embedding(query_text, optional_image_url)
        elif optional_image_url:
            embedding = get_image_embedding(optional_image_url)
        else:
            embedding = get_text_embedding(query_text)

        # 3. Vector search in Chroma, restricted to allowed_ids if any
        results = vector_search_chroma(
            embedding=embedding,
            allowed_ids=allowed_ids,
            n_results=n_results,
            collection_name="clothing_items"
        )
        return [result.id for result in results]
    except Exception as e:
        print(f"Error in clothing item search: {e}")
        return None
