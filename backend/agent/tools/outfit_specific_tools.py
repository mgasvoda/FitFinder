import logging
from typing import List, Dict, Any

# Import actual implementations
from backend.agent.tools.outfit_searcher import filter_clothing_items_sqlite, vector_search_chroma
from backend.services.embedding_service import get_text_embedding
# Assuming ClothingItem model and Session for check_outfit_completeness, adjust as needed
# Removed unused imports: ClothingItem, SessionLocal

logger = logging.getLogger(__name__)

# --- Tools for Outfit Generation Agent ---

def get_item_embedding(text: str) -> List[float]:
    """Generates an embedding for a given text string."""
    logger.info(f"(Outfit Designer Tool): get_item_embedding called with text: {text}")
    try:
        embedding = get_text_embedding(text)
        if embedding is None:
            logger.error("get_item_embedding: Failed to generate embedding, returned None.")
            # Return a zero vector or raise an error, depending on desired handling
            return [0.0] * 128 # Placeholder for default embedding size if known
        return embedding
    except Exception as e:
        logger.error(f"Error in get_item_embedding: {e}", exc_info=True)
        # Fallback or re-raise
        return [0.0] * 128 # Placeholder

def query_sqlite_by_tags(tags: dict) -> List[str]:
    """Queries SQLite for item IDs based on metadata tags."""
    logger.info(f"(Outfit Designer Tool): query_sqlite_by_tags called with tags: {tags}")
    try:
        return filter_clothing_items_sqlite(tags=tags)
    except Exception as e:
        logger.error(f"Error in query_sqlite_by_tags: {e}", exc_info=True)
        return []

def query_chroma_by_ids_and_embedding(item_ids: List[str], embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
    """Queries Chroma for items matching an embedding, optionally filtered by item IDs."""
    logger.info(f"(Outfit Designer Tool): query_chroma_by_ids_and_embedding called with {len(item_ids)} IDs, embedding, top_k={top_k}")
    try:
        # vector_search_chroma calls query_embedding, which returns List[QueryResult]
        # Each QueryResult has .id, .score, .metadata (Dict[str, Any])
        chroma_query_results = vector_search_chroma(
            embedding=embedding, 
            allowed_ids=item_ids, 
            n_results=top_k,
            collection_name="clothing_items" # Ensure this is the correct collection
        )
        
        formatted_results = []
        if chroma_query_results:
            for result_item in chroma_query_results: # result_item is a QueryResult object
                # Access metadata directly from result_item.metadata
                # The design doc implies `list[item]` where item is a dict.
                item_data = {
                    "item_id": result_item.id,
                    "description": result_item.metadata.get("description", "N/A"), # Ensure 'description' exists in metadata
                    "category": result_item.metadata.get("category", "N/A"),     # Ensure 'category' exists in metadata
                    "score": result_item.score # Optionally include the similarity score
                    # Add other relevant fields from result_item.metadata as needed by the agent
                }
                formatted_results.append(item_data)
        
        return formatted_results

    except Exception as e:
        logger.error(f"Error in query_chroma_by_ids_and_embedding: {e}", exc_info=True)
        return []

def check_outfit_completeness(items: List[Dict[str, Any]]) -> bool:
    logger.info(f"(Outfit Designer Tool): check_outfit_completeness called with {len(items)} items.")
    # Implementation based on design: top, bottom, shoes
    required_categories = {"top", "bottom", "shoes"}
    present_categories = set()
    for item in items:
        category = item.get("category")
        if category:
            present_categories.add(category.lower()) # Normalize to lower case
    
    is_complete = required_categories.issubset(present_categories)
    logger.info(f"Outfit completeness: {is_complete}. Present: {present_categories}, Required: {required_categories}")
    return is_complete
