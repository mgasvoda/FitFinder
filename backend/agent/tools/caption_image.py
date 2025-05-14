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

def _caption_image_impl(image_url: str, prompt: Optional[str] = None) -> dict:
    """
    Core logic for captioning an image, determining its category, and saving it.
    """
    logger.info(f"Captioning and categorizing image from source: {image_url}")
    item_id = str(uuid.uuid4())  # Generate a unique ID for this item

    default_prompt = (
        "Generate a descriptive caption for the clothing item in this image. "
        "This caption will be used in an embedding database for future retrieval. "
        "Focus only on the main clothing item, disregarding surrounding elements.\n\n"
        "After the caption, on a new line, identify the category of the item. "
        "The category MUST be one of the following: top, bottom, shoes, accessories."
        "Format the category line like this: 'Category: <chosen_category>'."
    )
    current_prompt = prompt if prompt else default_prompt
    
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
            {"type": "text", "text": current_prompt}
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

@tool("caption_image", parse_docstring=True)
def caption_image(image_url: str, prompt: Optional[str] = None) -> dict:
    """
    Begin the workflow for storing a new clothing item. Generates a descriptive caption for an image and saves the image file.

    Args:
        image_url: URL or local path to the image.
        prompt: Optional custom prompt.

    Returns:
        A dictionary containing the caption, category, and image metadata.
    """
    return _caption_image_impl(image_url, prompt)
