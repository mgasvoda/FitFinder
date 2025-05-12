from langchain.schema import HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from backend.agent.tools.image_storage import store_image
from fastapi import UploadFile
from pathlib import Path
from typing import Optional

import io
import uuid
import base64
import os
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Instantiate the Claude 3.5 Haiku model
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
llm = ChatAnthropic(model="claude-3-5-haiku-latest", anthropic_api_key=ANTHROPIC_API_KEY)

def _caption_image_impl(image_url: str, prompt: Optional[str] = "Generate a descriptive caption for the clothing item in this image. This caption will be used in an embedding database for future retrieval. Focus only on the main clothing item, disregarding surrounding elements.") -> dict:
    """
    Core logic for captioning an image and saving it. Used for both API and direct unit testing.
    """
    logger.info(f"Captioning image from source: {image_url}")
    item_id = str(uuid.uuid4())  # Generate a unique ID for this item
    
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
            {"type": "text", "text": prompt}
        ]
        
        # Get caption from Claude
        human_msg = HumanMessage(content=content)
        response = llm.generate([[human_msg]])
        caption = response.generations[0][0].text.strip()
        logger.info(f"Generated caption: {caption[:50]}...")
        
        # Return both the caption and the image metadata (no binary data)
        return {
            "caption": caption,
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

@tool("caption_image", parse_docstring=True)
def caption_image(image_url: str, prompt: Optional[str] = "Generate a descriptive caption for the clothing item in this image. This caption will be used in an embedding database for future retrieval. Focus only on the main clothing item, disregarding surrounding elements.") -> dict:
    """
    Begin the workflow for storing a new clothing item. Generates a descriptive caption for an image and saves the image file.

    Args:
        image_url: URL or local path to the image.
        prompt: Optional custom prompt.

    Returns:
        A dictionary containing the caption and image metadata.
    """
    return _caption_image_impl(image_url, prompt)
