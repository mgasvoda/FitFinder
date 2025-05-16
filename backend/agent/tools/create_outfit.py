
from backend.db import crud
from typing import List
from langchain_core.tools import tool
from backend.db.models import SessionLocal
from langgraph.types import interrupt

@tool("create_outfit", parse_docstring=True)
def create_outfit(name: str, list_of_items: List[str], description: str) -> str:
    """
    Create an outfit based on a list of item ids.
    
    Args:
        name (str): Name of the outfit.
        list_of_items (List[str]): List of item IDs to include in the outfit.
        description (str): Description of the outfit.

    Returns:
        str: Confirmation message.
    """
    db = SessionLocal()

    response = interrupt(  
        f"Trying to call `create_outfit` with args {{'name': {name}, 'list_of_items': {list_of_items}, 'description': {description}}}. "
        "Please approve or suggest edits."
    )
    if response["type"] == "accept":
        pass
    elif response["type"] == "edit":
        name = response["args"]["name"]
        list_of_items = response["args"]["list_of_items"]
        description = response["args"]["description"]
    else:
        raise ValueError(f"Unknown response type: {response['type']}")

    crud.create_outfit(db, name=name, description=description, item_ids=list_of_items)

    return f"Successfully created outfit {name}."
    