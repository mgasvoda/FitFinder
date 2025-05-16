from backend.db import crud
from typing import List, Optional
from langchain_core.tools import tool
from backend.db.models import SessionLocal, Outfit


@tool("get_outfit", parse_docstring=True)
def get_outfit(outfit_id: str) -> Optional[Outfit]:
    """
    Get an outfit by ID.
    
    Args:
        outfit_id (str): ID of the outfit to retrieve.
    
    Returns:
        Optional[Outfit]: The outfit if found, otherwise None.
    """
    #Todo implement search logic rather than just getting by ID. 
    db = SessionLocal()
    return crud.get_outfit(db, outfit_id)
