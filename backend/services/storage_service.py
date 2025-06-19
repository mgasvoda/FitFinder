# Placeholder for storage service

import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException
from typing import Tuple, List, Dict, Any, Optional
import filetype
from pathlib import Path
import logging

# Import the config for configurable data paths
from backend.config import config
# Import image compression functionality
from backend.services.image_compression import compress_clothing_image

logger = logging.getLogger(__name__)

# Define the base directory for storing images using configurable path
BASE_IMAGE_DIR = config.get_images_path()

# Ensure the base directory exists
os.makedirs(BASE_IMAGE_DIR, exist_ok=True)

# Define subdirectories for different types of images
CLOTHING_ITEMS_DIR = config.get_images_path("clothing_items")
OUTFIT_IMAGES_DIR = config.get_images_path("outfits")
TEMP_UPLOADS_DIR = config.get_images_path("temp")

# Ensure subdirectories exist
for directory in [CLOTHING_ITEMS_DIR, OUTFIT_IMAGES_DIR, TEMP_UPLOADS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Allowed image file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def validate_image(file: UploadFile) -> bool:
    """Validate that the uploaded file is an image"""
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Save to temp file for validation
    temp_file_path = os.path.join(TEMP_UPLOADS_DIR, f"temp_{uuid.uuid4()}{ext}")
    
    try:
        # Read the file content
        file_content = file.file.read()
        
        # Reset file pointer for future operations
        file.file.seek(0)
        
        # Write to temp file
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        # Check if it's a valid image using filetype
        kind = filetype.guess(temp_file_path)
        is_valid = kind is not None and kind.mime.startswith('image/')
        
        # Clean up temp file
        os.remove(temp_file_path)
        
        return is_valid
    except Exception:
        # Clean up temp file if it exists
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return False

def store_clothing_image(image: UploadFile, item_id: Optional[str] = None, 
                        compress: bool = True) -> Tuple[str, str]:
    """
    Store a clothing item image in the filesystem with optional compression
    
    Args:
        image: The uploaded image file
        item_id: Optional item ID (generated if not provided)
        compress: Whether to compress the image (default: True)
        
    Returns:
        Tuple of (image_url, item_id)
    """
    if not validate_image(image):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Generate ID if not provided
    if not item_id:
        item_id = str(uuid.uuid4())
    
    # Always use .jpg extension for compressed images
    ext = ".jpg" if compress else (os.path.splitext(image.filename)[1].lower() if image.filename else ".jpg")
    
    # Create the file path
    file_path = os.path.join(CLOTHING_ITEMS_DIR, f"{item_id}{ext}")
    
    if compress:
        # Save to temporary file first
        temp_path = os.path.join(TEMP_UPLOADS_DIR, f"temp_{item_id}{ext}")
        
        try:
            # Save original file temporarily
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(image.file, f)
            
            # Compress the image
            compressed_path, size_kb = compress_clothing_image(temp_path, file_path)
            logger.info(f"Compressed clothing image {item_id}: {size_kb}KB")
            
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error(f"Error compressing image {item_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to process image")
    else:
        # Save the file without compression
        with open(file_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
    
    # Return the relative URL and item ID
    relative_url = f"/images/clothing_items/{item_id}{ext}"
    
    return relative_url, item_id

def store_outfit_image(image: UploadFile, outfit_id: Optional[str] = None) -> Tuple[str, str]:
    """
    Store an outfit image in the filesystem
    
    Args:
        image: The uploaded image file
        outfit_id: Optional outfit ID (generated if not provided)
        
    Returns:
        Tuple of (image_url, outfit_id)
    """
    if not validate_image(image):
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Generate ID if not provided
    if not outfit_id:
        outfit_id = str(uuid.uuid4())
    
    # Get file extension
    ext = os.path.splitext(image.filename)[1].lower() if image.filename else ".jpg"
    
    # Create the file path
    file_path = os.path.join(OUTFIT_IMAGES_DIR, f"{outfit_id}{ext}")
    
    # Save the file
    with open(file_path, "wb") as f:
        shutil.copyfileobj(image.file, f)
    
    # Return the relative URL and outfit ID
    relative_url = f"/images/outfits/{outfit_id}{ext}"
    
    return relative_url, outfit_id

def delete_image(image_url: str) -> bool:
    """
    Delete an image from the filesystem
    
    Args:
        image_url: The relative URL of the image to delete
        
    Returns:
        Boolean indicating success
    """
    # Convert relative URL to absolute path
    if image_url.startswith("/images/"):
        # Remove the leading "/images/" to get the relative path
        relative_path = image_url[8:]
        absolute_path = os.path.join(BASE_IMAGE_DIR, relative_path)
        
        # Check if file exists
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
            return True
    
    return False

def get_absolute_path(image_url: str) -> Optional[str]:
    """
    Convert a relative image URL to an absolute filesystem path
    
    Args:
        image_url: The relative URL of the image
        
    Returns:
        Absolute path to the image file or None if invalid
    """
    if image_url.startswith("/images/"):
        # Remove the leading "/images/" to get the relative path
        relative_path = image_url[8:]
        absolute_path = os.path.join(BASE_IMAGE_DIR, relative_path)
        
        if os.path.exists(absolute_path):
            return absolute_path
    
    return None

def list_clothing_images() -> List[Dict[str, Any]]:
    """
    List all clothing item images in the filesystem
    
    Returns:
        List of dictionaries with image_url and item_id
    """
    images = []
    
    for filename in os.listdir(CLOTHING_ITEMS_DIR):
        if os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS:
            item_id = os.path.splitext(filename)[0]
            image_url = f"/images/clothing_items/{filename}"
            images.append({"image_url": image_url, "item_id": item_id})
    
    return images

def list_outfit_images() -> List[Dict[str, Any]]:
    """
    List all outfit images in the filesystem
    
    Returns:
        List of dictionaries with image_url and outfit_id
    """
    images = []
    
    for filename in os.listdir(OUTFIT_IMAGES_DIR):
        if os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS:
            outfit_id = os.path.splitext(filename)[0]
            image_url = f"/images/outfits/{filename}"
            images.append({"image_url": image_url, "outfit_id": outfit_id})
    
    return images

def get_image_url(item_id: str):
    # TODO: Implement retrieval
    return f"/images/{item_id}.jpg"

def save_image(image_file):
    # TODO: Implement image save logic
    pass
