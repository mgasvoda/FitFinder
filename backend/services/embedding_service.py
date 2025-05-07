import numpy as np
from typing import List, Dict, Any, Optional, Union
import os
import requests
from PIL import Image
from io import BytesIO
import torch
from transformers import CLIPProcessor, CLIPModel
from pathlib import Path
from backend.services.storage_service import get_absolute_path

# Check if CUDA is available
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load CLIP model for embeddings
try:
    model_name = "openai/clip-vit-base-patch32"
    model = CLIPModel.from_pretrained(model_name).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(model_name)
    EMBEDDING_DIM = model.config.text_config.hidden_size  # Usually 512 for CLIP base
    print(f"CLIP model loaded successfully on {DEVICE}")
except Exception as e:
    print(f"Error loading CLIP model: {e}")
    # Fallback to dummy embeddings for development
    EMBEDDING_DIM = 512
    model = None
    processor = None

def get_text_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for text input using CLIP
    
    Args:
        text: The text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    if model is None or processor is None:
        # Return dummy embedding for development
        return [0.0] * EMBEDDING_DIM
    
    try:
        # Process the text input
        inputs = processor(text=text, return_tensors="pt", padding=True, truncation=True).to(DEVICE)
        
        # Generate the embedding
        with torch.no_grad():
            text_features = model.get_text_features(**inputs)
        
        # Normalize the embedding
        text_embedding = text_features / text_features.norm(dim=1, keepdim=True)
        
        # Convert to list and return
        return text_embedding.cpu().numpy()[0].tolist()
    except Exception as e:
        print(f"Error generating text embedding: {e}")
        # Return dummy embedding on error
        return [0.0] * EMBEDDING_DIM

def get_image_embedding(image_input: Union[str, bytes, Image.Image]) -> List[float]:
    """
    Generate an embedding vector for an image using CLIP
    
    Args:
        image_input: Can be a URL, file path, bytes, or PIL Image
        
    Returns:
        List of floats representing the embedding vector
    """
    if model is None or processor is None:
        # Return dummy embedding for development
        return [0.0] * EMBEDDING_DIM
    
    try:
        # Convert input to PIL Image
        if isinstance(image_input, str):
            # Check if it's a URL or file path
            if image_input.startswith(('http://', 'https://')):
                response = requests.get(image_input)
                image = Image.open(BytesIO(response.content))
            else:
                # Check if it's a relative URL from our storage
                if image_input.startswith('/images/'):
                    abs_path = get_absolute_path(image_input)
                    if abs_path:
                        image = Image.open(abs_path)
                    else:
                        raise ValueError(f"Image not found: {image_input}")
                else:
                    # Assume it's a file path
                    image = Image.open(image_input)
        elif isinstance(image_input, bytes):
            image = Image.open(BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            raise ValueError("Unsupported image input type")
        
        # Process the image
        inputs = processor(images=image, return_tensors="pt").to(DEVICE)
        
        # Generate the embedding
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
        
        # Normalize the embedding
        image_embedding = image_features / image_features.norm(dim=1, keepdim=True)
        
        # Convert to list and return
        return image_embedding.cpu().numpy()[0].tolist()
    except Exception as e:
        print(f"Error generating image embedding: {e}")
        # Return dummy embedding on error
        return [0.0] * EMBEDDING_DIM

def get_multimodal_embedding(text: Optional[str] = None, image: Optional[Union[str, bytes, Image.Image]] = None) -> List[float]:
    """
    Generate a combined embedding from text and/or image inputs
    
    Args:
        text: Optional text input
        image: Optional image input (URL, file path, bytes, or PIL Image)
        
    Returns:
        List of floats representing the combined embedding vector
    """
    print("Generating multimodal embedding")

    # Get individual embeddings
    text_embedding = get_text_embedding(text) if text else None
    image_embedding = get_image_embedding(image) if image else None
    
    # Combine embeddings
    if text_embedding and image_embedding:
        # Simple average of the two embeddings
        combined = np.mean([np.array(text_embedding), np.array(image_embedding)], axis=0)
        print("Combined embedding:", combined)
        return combined.tolist()
    elif text_embedding:
        print("Text embedding:", text_embedding)
        return text_embedding
    elif image_embedding:
        print("Image embedding:", image_embedding)
        return image_embedding
    else:
        # Return zeros if no inputs provided
        return [0.0] * EMBEDDING_DIM

def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Compute cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    # Convert to numpy arrays
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Compute cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    # Avoid division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)
