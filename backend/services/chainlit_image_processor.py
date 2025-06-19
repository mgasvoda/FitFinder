"""
Chainlit Image Processing Service
Handles image uploads from Chainlit interface with compression
"""

import os
import logging
import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional
import chainlit as cl

from backend.services.image_compression import compress_clothing_image
from backend.config import config

logger = logging.getLogger(__name__)

# Dynamic path getters
def get_clothing_items_dir():
    """Get clothing items directory path dynamically"""
    return config.get_images_path("clothing_items")

def get_temp_uploads_dir():
    """Get temp uploads directory path dynamically"""
    return config.get_images_path("temp")

def process_chainlit_image(element: cl.File, 
                          item_id: Optional[str] = None,
                          compress: bool = True) -> Tuple[str, str, int]:
    """
    Process an image uploaded through Chainlit interface
    
    Args:
        element: Chainlit file element
        item_id: Optional item ID (generated if not provided)
        compress: Whether to compress the image (default: True)
        
    Returns:
        Tuple of (image_url, item_id, file_size_kb)
    """
    if not element.path:
        raise ValueError("No file path provided in Chainlit element")
    
    # Generate ID if not provided
    if not item_id:
        item_id = str(uuid.uuid4())
    
    # Always use .jpg extension for compressed images
    ext = ".jpg" if compress else Path(element.path).suffix.lower()
    if not ext:
        ext = ".jpg"
    
    # Get directory path dynamically and create the final file path
    clothing_items_dir = get_clothing_items_dir()
    final_path = os.path.join(clothing_items_dir, f"{item_id}{ext}")
    
    try:
        if compress:
            # Compress the uploaded image
            compressed_path, size_kb = compress_clothing_image(element.path, final_path)
            logger.info(f"Compressed chainlit image {item_id}: {size_kb}KB")
        else:
            # Copy without compression
            shutil.copy2(element.path, final_path)
            size_kb = int(os.path.getsize(final_path) / 1024)
            logger.info(f"Saved chainlit image {item_id}: {size_kb}KB (uncompressed)")
        
        # Create relative URL
        relative_url = f"/images/clothing_items/{item_id}{ext}"
        
        return relative_url, item_id, size_kb
        
    except Exception as e:
        logger.error(f"Error processing chainlit image {item_id}: {e}")
        # Clean up any partial files
        if os.path.exists(final_path):
            os.remove(final_path)
        raise ValueError(f"Failed to process image: {str(e)}")

def get_image_info(image_path: str) -> dict:
    """
    Get information about a processed image
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with image information
    """
    if not os.path.exists(image_path):
        return {"exists": False}
    
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            width, height = img.size
            
        file_size_kb = int(os.path.getsize(image_path) / 1024)
        
        return {
            "exists": True,
            "width": width,
            "height": height,
            "size_kb": file_size_kb,
            "format": Path(image_path).suffix.upper().replace(".", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting image info for {image_path}: {e}")
        return {"exists": True, "error": str(e)}

def cleanup_temp_files():
    """
    Clean up temporary files older than 1 hour
    """
    try:
        import time
        current_time = time.time()
        
        for filename in os.listdir(TEMP_UPLOADS_DIR):
            file_path = os.path.join(TEMP_UPLOADS_DIR, filename)
            
            # Check if file is older than 1 hour (3600 seconds)
            if os.path.isfile(file_path) and (current_time - os.path.getmtime(file_path)) > 3600:
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {filename}")
                
    except Exception as e:
        logger.error(f"Error cleaning up temporary files: {e}")

# Example usage for testing
if __name__ == "__main__":
    print("Chainlit Image Processor - Test Mode")
    print("This module processes images uploaded through the Chainlit interface.") 