import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any, Optional
import numpy as np
from pydantic import BaseModel

# Define the path for ChromaDB persistent storage
CHROMA_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../chroma_db")

# Ensure the directory exists
os.makedirs(CHROMA_DB_PATH, exist_ok=True)

# Initialize ChromaDB client with persistent storage
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

clothing_collection = None
outfit_collection = None

def init_chroma_collections():
    global clothing_collection, outfit_collection
    try:
        clothing_collection = client.get_collection("clothing_items")
    except chromadb.errors.NotFoundError:
        clothing_collection = client.create_collection(
            name="clothing_items",
            metadata={"description": "Clothing item embeddings for similarity search"}
        )
    try:
        outfit_collection = client.get_collection("outfits")
    except chromadb.errors.NotFoundError:
        outfit_collection = client.create_collection(
            name="outfits",
            metadata={"description": "Outfit embeddings for similarity search"}
        )

class QueryResult(BaseModel):
    id: str
    score: float
    metadata: Dict[str, Any]

def upsert_embedding(item_id: str, embedding: List[float], metadata: Dict[str, Any], collection_name: str = "clothing_items"):
    """
    Add or update an embedding in the specified ChromaDB collection
    
    Args:
        item_id: Unique identifier for the item
        embedding: Vector embedding (list of floats)
        metadata: Additional data about the item (e.g., description, image_url)
        collection_name: Name of the collection to store in ("clothing_items" or "outfits")
    """

    print("Upserting embedding...")
    collection = client.get_collection(collection_name)
    
    # Convert embedding to the correct format if needed
    if isinstance(embedding, np.ndarray):
        embedding = embedding.tolist()
    
    # Sanitize metadata: remove keys with None values or empty lists
    cleaned_metadata = {
        k: v for k, v in metadata.items()
        if v is not None and not (isinstance(v, list) and len(v) == 0)
    }
    print(cleaned_metadata)

    # Upsert the embedding
    collection.upsert(
        ids=[item_id],
        embeddings=[embedding],
        metadatas=[cleaned_metadata]
    )
    
    return True

def delete_embedding(item_id: str, collection_name: str = "clothing_items"):
    """Delete an embedding from the specified collection"""
    collection = client.get_collection(collection_name)
    collection.delete(ids=[item_id])
    return True

def query_embedding(
    query_embedding: List[float], 
    collection_name: str = "clothing_items", 
    n_results: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[QueryResult]:
    """
    Query the vector database for similar items
    
    Args:
        query_embedding: Vector embedding to search for
        collection_name: Name of the collection to search in
        n_results: Maximum number of results to return
        filter_metadata: Optional filter to apply to the search
        
    Returns:
        List of QueryResult objects containing id, score, and metadata
    """
    collection = client.get_collection(collection_name)
    
    # Convert embedding to the correct format if needed
    if isinstance(query_embedding, np.ndarray):
        query_embedding = query_embedding.tolist()
    
    # Perform the query
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=filter_metadata
    )
    
    # Format the results
    query_results = []
    if results["ids"] and len(results["ids"][0]) > 0:
        for i in range(len(results["ids"][0])):
            query_results.append(
                QueryResult(
                    id=results["ids"][0][i],
                    score=float(results["distances"][0][i]) if "distances" in results else 1.0,
                    metadata=results["metadatas"][0][i]
                )
            )
    
    return query_results

def get_item_embedding(item_id: str, collection_name: str = "clothing_items") -> Optional[Dict[str, Any]]:
    """Get the embedding and metadata for a specific item"""
    collection = client.get_collection(collection_name)
    
    try:
        result = collection.get(ids=[item_id])
        if result["ids"] and len(result["ids"]) > 0:
            return {
                "id": result["ids"][0],
                "embedding": result["embeddings"][0],
                "metadata": result["metadatas"][0]
            }
        return None
    except Exception:
        return None

def get_all_embeddings(collection_name: str = "clothing_items") -> List[Dict[str, Any]]:
    """Get all embeddings from a collection"""
    collection = client.get_collection(collection_name)
    
    try:
        result = collection.get()
        embeddings = []
        
        if result["ids"]:
            for i in range(len(result["ids"])):
                embeddings.append({
                    "id": result["ids"][i],
                    "embedding": result["embeddings"][i],
                    "metadata": result["metadatas"][i]
                })
        
        return embeddings
    except Exception as e:
        print(f"Error retrieving embeddings: {e}")
        return []
