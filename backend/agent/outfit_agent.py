import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langgraph.prebuilt import tools_condition
from langgraph.graph.message import add_messages

# Import the outfit tools
from backend.agent.tools.outfit_specific_tools import check_outfit_completeness
from backend.agent.tools.outfit_searcher import search_clothing_items, filter_clothing_items_sqlite, vector_search_chroma
from backend.agent.steps import CaptionToolNode, _route_from_tools

logger = logging.getLogger(__name__)

# --- State Definition for Outfit Agent ---
class OutfitAgentState(TypedDict):
    messages: List[Any]  # For chat interaction within the outfit agent
    selected_items: List[Dict[str, Any]]  # Items currently in the outfit
    missing_categories: List[str]  # e.g., ["top", "shoes"]
    feedback_log: List[str]  # User refinement requests
    search_results: Optional[List[str]]  # Results from search_clothing_items tool
    items: Optional[List[Dict[str, Any]]]  # Formatted items from the database

# --- Tools for Outfit Designer Agent ---
@tool("find_anchor_item")
def find_anchor_item(query: str, season: Optional[str] = None) -> List[str]:
    """
    Find a clothing item to serve as the anchor for an outfit based on a text description.
    
    Args:
        query: Text description of the clothing item to find (e.g., "white pants", "blue dress")
        season: Optional season filter (e.g., "summer", "winter", "fall", "spring")
        
    Returns:
        List of item IDs that match the query
    """
    logger.info(f"Finding anchor item for query: {query}, season: {season}")
    
    # Prepare filter metadata
    filter_metadata = {}
    if season and season.lower() != "any":
        filter_metadata["season"] = season.lower()
    
    # Use the search_clothing_items tool to find matching items
    # Create the arguments dictionary for the tool
    args = {
        "query_text": query,
        "filter_metadata": filter_metadata
    }
    
    # Use invoke method instead of direct call
    item_ids = search_clothing_items.invoke(args)
    
    logger.info(f"Found {len(item_ids)} potential anchor items")
    return item_ids

@tool("find_matching_item")
def find_matching_item(category: str, outfit_description: str, season: Optional[str] = None) -> List[str]:
    """
    Find a clothing item that matches the specified category and complements the current outfit.
    
    Args:
        category: The category of item to find (e.g., "top", "bottom", "shoes")
        outfit_description: Description of the current outfit or style preferences
        season: Optional season filter (e.g., "summer", "winter", "fall", "spring")
        
    Returns:
        List of item IDs that match the criteria
    """
    logger.info(f"Finding {category} to match: {outfit_description}, season: {season}")
    
    # Prepare filter metadata
    filter_metadata = {"category": category}
    if season and season.lower() != "any":
        filter_metadata["season"] = season.lower()
    
    # Use the search_clothing_items tool to find matching items
    # Create the arguments dictionary for the tool
    args = {
        "query_text": outfit_description,
        "filter_metadata": filter_metadata
    }
    
    # Use invoke method instead of direct call
    item_ids = search_clothing_items.invoke(args)
    
    logger.info(f"Found {len(item_ids)} potential {category} items")
    return item_ids

@tool("check_outfit_completeness")
def check_outfit_completeness_tool(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check if an outfit has all the required categories (top, bottom, shoes).
    
    Args:
        items: List of clothing items in the outfit, each with at least a 'category' field
        
    Returns:
        Dictionary with 'complete' boolean and 'missing_categories' list
    """
    logger.info(f"Checking completeness of outfit with {len(items)} items")
    
    # Use the check_outfit_completeness function from outfit_specific_tools
    is_complete = check_outfit_completeness(items)
    
    # Determine which categories are missing
    required_categories = {"top", "bottom", "shoes"}
    present_categories = set()
    
    for item in items:
        category = item.get("category", "").lower()
        if category:
            present_categories.add(category)
    
    missing_categories = list(required_categories - present_categories)
    
    logger.info(f"Outfit completeness: {is_complete}, missing: {missing_categories}")
    return {
        "complete": is_complete,
        "missing_categories": missing_categories
    }

# # --- Nodes for Outfit Designer Agent ---
# def outfit_chat_node(state: OutfitAgentState, llm) -> Dict[str, Any]:
#     logger.info("(Outfit Designer Node): outfit_chat_node called")
    
#     # Define the tools for the outfit agent
    
#     # Bind the tools to the LLM
#     llm_with_tools = llm.bind_tools(outfit_tools)
    
#     # Get the messages from the state
#     messages = state.get("messages", [])
    
#     # Have the LLM process the messages and potentially use tools
#     try:
#         response = llm_with_tools.invoke(messages) # Use original messages for now
#         return {"messages": [response]}
#     except Exception as e:
#         logger.error(f"Error in outfit_chat_node: {str(e)}")
#         # If there's still an error, try with a fresh conversation
#         # This is a fallback to reset the conversation state if needed
#         if len(messages) > 2:  # Only if we have enough context to preserve
#             # Keep only the system message (if any) and the most recent user message
#             reset_messages = []
#             for msg in messages:
#                 if hasattr(msg, 'role'):
#                     if msg.role == 'system':
#                         reset_messages.append(msg)
#                     elif msg.role == 'user' and len(reset_messages) < 2:
#                         reset_messages.append(msg)
            
#             logger.warning("Attempting recovery with reset conversation state")
#             response = llm_with_tools.invoke(reset_messages)
#             return {"messages": [response]}
#         raise  # Re-raise if we can't recover

# Helper functions for the outfit agent
def get_items_step(state: OutfitAgentState) -> Dict[str, Any]:
    """Process search results and fetch the full item details from the database."""
    logger.info("Running get_items_step for outfit agent...")
    
    # Get the search results from state
    search_results = state.get("search_results", [])
    if not search_results:
        logger.warning("No search_results found in state")
        return state
    
    logger.info(f"Processing search results: {search_results}")
    
    # Use the database to get the full item details
    from backend.db.models import SessionLocal
    from backend.db import crud
    
    try:
        # Create a database session
        db = SessionLocal()
        
        try:
            # Fetch the items from the database
            db_items = crud.get_clothing_items_by_ids(db=db, item_ids=search_results)
            logger.info(f"Retrieved {len(db_items)} items from database")
            
            # Convert the items to dictionaries
            items = []
            for item in db_items:
                item_dict = {
                    "id": str(item.id),
                    "description": str(item.description) if item.description else "",
                    "image_url": str(item.image_url) if item.image_url else "",
                    "category": str(item.category) if item.category else None,
                    "color": str(item.color) if item.color else None,
                    "season": str(item.season) if item.season else None,
                    "tags": [str(tag.name) for tag in item.tags] if hasattr(item, 'tags') else []
                }
                items.append(item_dict)
            
            logger.info(f"Processed {len(items)} items for the outfit")
            
            # Update state with the formatted items
            return {**state, "items": items}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching items from database: {e}", exc_info=True)
        return state

def update_outfit_step(state: OutfitAgentState) -> Dict[str, Any]:
    """Update the outfit with the items found in the search."""
    logger.info("Running update_outfit_step...")
    
    # Get the items from state
    items = state.get("items", [])
    if not items:
        logger.warning("No items found in state to update outfit")
        return state
    
    # Get the current selected items
    selected_items = state.get("selected_items", [])
    
    # Add the new items to the outfit
    updated_items = selected_items + items
    
    # Check what categories are now in the outfit
    categories = set()
    for item in updated_items:
        category = item.get("category", "").lower()
        if category:
            categories.add(category)
    
    # Determine what categories are still missing
    required_categories = {"top", "bottom", "shoes"}
    missing_categories = list(required_categories - categories)
    
    logger.info(f"Updated outfit with {len(items)} new items. Missing categories: {missing_categories}")
    
    # Update the state
    return {
        "selected_items": updated_items,
        "missing_categories": missing_categories,
        "feedback_log": state.get("feedback_log", []) + [f"Added {len(items)} items to outfit"]
    }

def outfit_tools_node(state: OutfitAgentState) -> Dict[str, Any]:
    """Process tool calls from the outfit chat node."""
    logger.info("Running outfit_tools_node...")
    
    # Define the tools
    outfit_tools = [find_anchor_item, find_matching_item, check_outfit_completeness_tool]
    
    # Create a tool node to handle the tool calls
    tool_node = CaptionToolNode(outfit_tools)
    
    # Process the tool calls
    result = tool_node(state)
    
    # Check if we have search results from find_anchor_item or find_matching_item
    if "find_anchor_item" in result:
        logger.info(f"Found anchor item search results: {result['find_anchor_item']}")
        result["search_results"] = result["find_anchor_item"]
    elif "find_matching_item" in result:
        logger.info(f"Found matching item search results: {result['find_matching_item']}")
        result["search_results"] = result["find_matching_item"]
    
    return result

# --- Conditional Edge for Outfit Agent ---
def route_from_tools_condition(state: OutfitAgentState) -> str:
    """Determine the next node based on tool results."""
    logger.info(f"Routing from tools, state keys: {list(state.keys())}")
    
    # If we have search results, route to get_items_step
    if state.get("search_results"):
        logger.info("Found search results, routing to get_items")
        return "get_items"
    
    # If we have a check_outfit_completeness result, check if we need to continue building
    if "check_outfit_completeness" in state:
        completeness_result = state.get("check_outfit_completeness", {})
        if not completeness_result.get("complete", False):
            logger.info("Outfit not complete, routing back to chat")
            return "chat"
    
    # Default route back to chat
    logger.info("No specific routing condition met, returning to chat")
    return "chat"

def should_continue_condition(state: OutfitAgentState) -> str:
    """Determine if we should continue building the outfit or end."""
    logger.info("Checking if we should continue building the outfit...")
    
    # Get the selected items
    selected_items = state.get("selected_items", [])
    
    # Check if the outfit is complete
    is_complete = check_outfit_completeness(selected_items)
    
    # If the outfit is complete, we're done
    if is_complete:
        logger.info("Outfit is complete, routing to END")
        return END
    
    # If we have missing categories, continue building
    if state.get("missing_categories"):
        logger.info("Outfit has missing categories, continuing")
        return "chat"
    
    # Default to continuing
    logger.info("Default routing to continue outfit building")
    return "chat"

# --- Outfit Agent Graph Creation ---
def create_outfit_designer_agent_graph(llm):
    """
    Creates the graph for the outfit designer agent using a tool-based approach.
    
    Args:
        llm: The language model to be used by the agent.
        
    Returns:
        The compiled LangGraph for the outfit designer agent.
    """
    # Initialize the graph with the OutfitAgentState
    graph_builder = StateGraph(OutfitAgentState)
    
    # Define the outfit tools
    outfit_tools = [find_anchor_item, find_matching_item, check_outfit_completeness_tool]
    
    # Add nodes to the graph
    # Chat node with tools bound to the LLM
    graph_builder.add_node("chat", lambda state: {"messages": llm.bind_tools(outfit_tools).invoke(state['messages'])})

    # Tool execution node
    graph_builder.add_node("tools", outfit_tools_node)
    
    # Item processing nodes
    graph_builder.add_node("get_items", get_items_step)
    graph_builder.add_node("update_outfit", update_outfit_step)
    
    # Define the edges
    # Start with the chat node
    graph_builder.add_edge(START, "chat")
    
    # Route from chat to tools if tools are called
    graph_builder.add_conditional_edges(
        "chat",
        tools_condition        
    )
    
    # Route from tools based on which tool was called
    graph_builder.add_conditional_edges(
        "tools",
        route_from_tools_condition,
        {
            "get_items": "get_items",
            "chat": "chat"
        }
    )
    
    # After getting items, update the outfit
    graph_builder.add_edge("get_items", "update_outfit")
    
    # After updating the outfit, go back to chat
    graph_builder.add_edge("update_outfit", "chat")
    
    # We don't need this anymore since we're using should_continue_condition directly in the chat node routing
    
    logger.info("Outfit Designer Agent graph created successfully.")
    return graph_builder.compile()

# Alias for consistency if imported elsewhere, though create_outfit_designer_agent_graph is more descriptive
create_outfit_agent_graph = create_outfit_designer_agent_graph
