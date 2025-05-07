from pathlib import Path
import base64
import os
from typing import Optional
from langchain.schema import HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

# Instantiate the Claude 3.5 Haiku model
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
llm = ChatAnthropic(model="claude-3-5-haiku-latest", anthropic_api_key=ANTHROPIC_API_KEY)

@tool("caption_image", parse_docstring=True)
def caption_image(image_url: str, prompt: Optional[str] = "Describe the clothing and style in this image.") -> str:
    """
    Generate a descriptive caption for an image using Claude 3.5 Haiku.

    Args:
        image_url: URL or local path to the image.
        prompt: Optional custom prompt.

    Returns:
        A generated caption.
    """
    # Load image data
    if image_url.startswith("http://") or image_url.startswith("https://"):
        import requests
        img_bytes = requests.get(image_url).content
    else:
        img_bytes = Path(image_url).read_bytes()
    img_base64 = base64.b64encode(img_bytes).decode()

    # Compose a human message embedding the image
    content = [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(img_bytes).decode()}"}},
        {"type": "text", "text": prompt}
    ]

    # Proper HumanMessage with structured multimodal input
    human_msg = HumanMessage(content=content)


    # Call the model
    response = llm.generate([[human_msg]])
    caption = response.generations[0][0].text.strip()
    return caption
