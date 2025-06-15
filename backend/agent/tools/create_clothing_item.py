from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from fastapi import UploadFile
from pathlib import Path

from backend.db import crud
from backend.db.models import SessionLocal
from backend.services.embedding_service import get_text_embedding
from backend.services.storage_service import store_clothing_image

import io
import uuid
import numpy as np
import logging
import os
import base64

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Instantiate the Claude 3.5 Haiku model
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
llm = ChatAnthropic(model="claude-3-5-haiku-latest", anthropic_api_key=ANTHROPIC_API_KEY)

@tool("Create_clothing_item", parse_docstring=True)
def create_clothing_item(image_url: str) -> dict:
    """
    Creates a new clothing item within FitFinder. Generates a descriptive caption for an image and saves the image file.

    Args:
        image_url: URL or local path to the image.

    Returns:
        A dictionary containing the caption, category, and image metadata.
    """
    item_id = str(uuid.uuid4())

    result = caption_image(image_url, item_id) #image is saved during storage step
    caption = result["caption"]
    category = result["category"]
    saved_image_url = result["image_url"]
    
    embedding = embed_step(caption)
    persist_db_step(caption, saved_image_url, embedding, category, item_id)

    return {'item_id': item_id, 'caption': caption, 'category': category, 'image_url': saved_image_url}


def caption_image(image_url: str, item_id: str) -> dict:
    """
    Begin the workflow for storing a new clothing item. Generates a descriptive caption for an image and saves the image file.

    Args:
        image_url: URL or local path to the image.
        item_id: Item ID.

    Returns:
        A dictionary containing the caption, category, and image metadata.
    """
    logger.info(f"Captioning and categorizing image from source: {image_url}")

    default_prompt = (
        "Generate a descriptive caption for the clothing item in this image. "
        "This caption will be used in an embedding database for future retrieval. "
        "Focus only on the main clothing item, disregarding surrounding elements.\n\n"
        "After the caption, on a new line, identify the category of the item. "
        "The category MUST be one of the following: top, bottom, shoes, accessories."
        "Format the category line like this: 'Category: <chosen_category>'."
    )
    
    try:
        # Load image data
        if image_url.startswith("http://") or image_url.startswith("https://"):
            import requests
            img_bytes = requests.get(image_url).content
            filename = image_url.split("/")[-1]
        else:
            img_bytes = Path(image_url).read_bytes()
            filename = Path(image_url).name
        
        logger.info(f"Successfully loaded image: {filename} ({len(img_bytes)} bytes)")
        
        # Save the image immediately using the store_image function
        # Create a UploadFile object that the storage function expects
        file_obj = io.BytesIO(img_bytes)
        upload_file = UploadFile(
            filename=filename,
            file=file_obj
        )
        
        # Store the image and get the saved URL
        saved_image_url, saved_item_id = store_image(upload_file, item_id)
        logger.info(f"Image saved with ID {saved_item_id} at {saved_image_url}")
        
        # Generate caption using base64-encoded image
        img_base64 = base64.b64encode(img_bytes).decode()
        content = [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}},
            {"type": "text", "text": default_prompt}
        ]
        
        # Get caption and category from Claude
        human_msg = HumanMessage(content=content)
        response = llm.generate([[human_msg]])
        llm_output = response.generations[0][0].text.strip()
        logger.info(f"LLM Output:\n{llm_output}")

        # Parse caption and category
        caption = "Error: Could not parse caption."
        category = "Error: Could not parse category."
        lines = llm_output.split('\n')
        
        if lines:
            caption = lines[0].strip() # First line is caption
            if len(lines) > 1:
                category_line = lines[-1].strip() # Last line should be category
                if category_line.startswith("Category:"):
                    extracted_cat = category_line.replace("Category:", "").strip().lower()
                    # Validate category
                    allowed_categories = ["top", "bottom", "shoes", "accessories"]
                    if extracted_cat in allowed_categories:
                        category = extracted_cat
                    else:
                        logger.warning(f"LLM provided invalid category: '{extracted_cat}'. Falling back to 'accessories'.")
                        category = "accessories" # Fallback category
                else:
                    logger.warning(f"Could not parse category from line: '{category_line}'. Falling back to 'accessories'.")
                    category = "accessories" # Fallback category if parsing fails
            else:
                logger.warning("LLM output did not contain a separate line for category. Falling back to 'accessories'.")
                category = "accessories" # Fallback category
        else:
            logger.error("LLM output was empty.")

        logger.info(f"Generated caption: {caption[:50]}... | Category: {category}")
        
        # Return both the caption and the image metadata (no binary data)
        return {
            "caption": caption,
            "category": category, # Added category
            "item_id": saved_item_id,
            "image_url": saved_image_url,
            "metadata": {
                "filename": filename,
                "source_path": image_url,
            }
        }
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return {
            "caption": "Error processing image: " + str(e),
            "error": str(e),
            "item_id": item_id,
            "image_url": None
        }

def store_image(image, item_id=None):
    """
    Store an uploaded clothing item image
    
    Args:
        image: The uploaded image file or a file path string
        item_id: Optional item ID (generated if not provided)
        
    Returns:
        Tuple of (image_url, item_id)
    """
    
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
                file=file_obj
            )
            
            return store_clothing_image(upload_file, item_id)
        except Exception as e:
            import logging
            logging.error(f"Error converting file path to UploadFile: {e}")
            raise
    else:
        # If it's already a UploadFile, use it directly
        return store_clothing_image(image, item_id)


def embed_step(caption: str):
    """Generate embeddings for the caption text."""
    logger.info("Running embed_step...")
    
    try:
        # Get embedding for the caption
        embedding = get_text_embedding(caption)
        # Update state with the embedding
        return embedding

    except Exception as e:
        logger.error(f"Error generating embedding: {e}", exc_info=True)
        # Return original state on error
        return None

def persist_db_step(caption: str, image_url: str, embedding: np.ndarray, category: str, item_id: str):
    """Persist the item to the database with its caption and embedding."""
    logger.info("Running persist_db_step...")
    
    logger.info(f"Persisting item with caption: {caption[:50]}...")
    logger.info(f"Image URL: {image_url}")
    logger.info(f"Category: {category}") # Log the category
    logger.info(f"Embedding available: {embedding is not None}")
    
    try:
        # Create a database session
        db = SessionLocal()
        
        try:
            # Create the clothing item in the database
            db_item = crud.create_clothing_item(
                db=db,
                item_id=item_id,
                description=caption,
                image_url=image_url,
                embedding=embedding,
                category=category  # Pass category to CRUD function
            )
            
            logger.info(f"Created clothing item in database with ID: {db_item.id}")

            return db_item.id
        finally:
            # Always close the database session
            db.close()

    except Exception as e:
        logger.error(f"Error persisting to database: {e}")
        return None
