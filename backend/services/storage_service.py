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

# Allowed image file extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def get_base_image_dir():
    """Get the base images directory path dynamically"""
    return config.get_images_path()

def get_clothing_items_dir():
    """Get the clothing items directory path dynamically"""
    return config.get_images_path("clothing_items")

def get_outfit_images_dir():
    """Get the outfit images directory path dynamically"""
    return config.get_images_path("outfits")

def get_temp_uploads_dir():
    """Get the temp uploads directory path dynamically"""
    return config.get_images_path("temp")

def ensure_directories_exist():
    """Ensure all required directories exist"""
    directories = [
        get_base_image_dir(),
        get_clothing_items_dir(),
        get_outfit_images_dir(),
        get_temp_uploads_dir()
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def validate_image(file: UploadFile) -> bool:
    """Validate that the uploaded file is an image"""
    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Ensure temp directory exists
    temp_uploads_dir = get_temp_uploads_dir()
    
    # Save to temp file for validation
    temp_file_path = os.path.join(temp_uploads_dir, f"temp_{uuid.uuid4()}{ext}")
    
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
    
    # Get directory paths dynamically
    clothing_items_dir = get_clothing_items_dir()
    temp_uploads_dir = get_temp_uploads_dir()
    
    # Create the file path
    file_path = os.path.join(clothing_items_dir, f"{item_id}{ext}")
    
    if compress:
        # Save to temporary file first
        temp_path = os.path.join(temp_uploads_dir, f"temp_{item_id}{ext}")
        
        try:
            # Save original file temporarily
            with open(temp_path, "wb") as f:
                shutil.copyfileobj(image.file, f)
            
            # Compress the image
            compressed_path, size_kb = compress_clothing_image(temp_path, file_path)
            logger.info(f"Image compressed successfully: {size_kb}KB -> {compressed_path}")
            
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
    
    # Get directory path dynamically
    outfit_images_dir = get_outfit_images_dir()
    
    # Create the file path
    file_path = os.path.join(outfit_images_dir, f"{outfit_id}{ext}")
    
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
        base_image_dir = get_base_image_dir()
        absolute_path = os.path.join(base_image_dir, relative_path)
        
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
        base_image_dir = get_base_image_dir()
        absolute_path = os.path.join(base_image_dir, relative_path)
        
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
    clothing_items_dir = get_clothing_items_dir()
    
    for filename in os.listdir(clothing_items_dir):
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
    outfit_images_dir = get_outfit_images_dir()
    
    for filename in os.listdir(outfit_images_dir):
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
