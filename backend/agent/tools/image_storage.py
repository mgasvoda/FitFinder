from fastapi import UploadFile
import os
import uuid
from backend.services.storage_service import store_clothing_image, store_outfit_image, delete_image, get_absolute_path

def store_image(image: UploadFile, item_id=None):
    """
    Store an uploaded clothing item image
    
    Args:
        image: The uploaded image file
        item_id: Optional item ID (generated if not provided)
        
    Returns:
        Tuple of (image_url, item_id)
    """
    return store_clothing_image(image, item_id)

def store_outfit_image_wrapper(image: UploadFile, outfit_id=None):
    """
    Store an uploaded outfit image
    
    Args:
        image: The uploaded image file
        outfit_id: Optional outfit ID (generated if not provided)
        
    Returns:
        Tuple of (image_url, outfit_id)
    """
    return store_outfit_image(image, outfit_id)

def remove_image(image_url: str):
    """
    Delete an image from storage
    
    Args:
        image_url: The URL of the image to delete
        
    Returns:
        Boolean indicating success
    """
    return delete_image(image_url)

def get_image_path(image_url: str):
    """
    Get the absolute file path for an image URL
    
    Args:
        image_url: The URL of the image
        
    Returns:
        Absolute path to the image file or None if not found
    """
    return get_absolute_path(image_url)
