from backend.db import crud
from typing import List
from langchain_core.tools import tool
from backend.db import SessionLocal


@tool("get_outfit", parse_docstring=True)
def get_outfit(outfit_id: str) -> Optional[models.Outfit]:
    """
    Get an outfit by ID.
    
    Args:
        outfit_id (str): ID of the outfit to retrieve.
    
    Returns:
        Optional[models.Outfit]: The outfit if found, otherwise None.
    """
    #Todo implement search logic rather than just getting by ID. 
    db = SessionLocal()
    return crud.get_outfit(db, outfit_id)
