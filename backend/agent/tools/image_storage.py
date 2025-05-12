from fastapi import UploadFile
import os
import uuid
from backend.services.storage_service import store_clothing_image, store_outfit_image, delete_image, get_absolute_path

def store_image(image, item_id=None):
    """
    Store an uploaded clothing item image
    
    Args:
        image: The uploaded image file or a file path string
        item_id: Optional item ID (generated if not provided)
        
    Returns:
        Tuple of (image_url, item_id)
    """
    from fastapi import UploadFile
    import io
    from pathlib import Path
    
    # If image is a string (file path), convert it to a UploadFile object
    if isinstance(image, str):
        try:
            # Get the file name from the path
            file_path = Path(image)
            file_name = file_path.name
            
            # Read the file content
            with open(image, 'rb') as f:
                file_content = f.read()
            
            # Create a file-like object
            file_obj = io.BytesIO(file_content)
            
            # Create a UploadFile object
            upload_file = UploadFile(
                filename=file_name,
                file=file_obj,
                content_type='image/jpeg'  # Assuming JPEG, adjust if needed
            )
            
            return store_clothing_image(upload_file, item_id)
        except Exception as e:
            import logging
            logging.error(f"Error converting file path to UploadFile: {e}")
            raise
    else:
        # If it's already a UploadFile, use it directly
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
