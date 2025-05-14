import logging
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END

from backend.agent.tools.outfit_specific_tools import (
    get_item_embedding,
    query_sqlite_by_tags,
    query_chroma_by_ids_and_embedding,
    check_outfit_completeness
)

logger = logging.getLogger(__name__)

# --- State Definition for Outfit Agent ---
class OutfitAgentState(TypedDict):
    messages: List[Any]  # For chat interaction within the outfit agent
    selected_items: List[Dict[str, Any]]  # Items currently in the outfit
    missing_categories: List[str]  # e.g., ["top", "shoes"]
    feedback_log: List[str]  # User refinement requests
    season: str  # Extracted from prompt
    anchor_item_description: str  # Initial user-provided item (e.g. "white pants")
    current_embedding: List[float] # Embedding of anchor item or feedback
    item_candidates: List[str] # Candidate item IDs from SQLite query

# --- Nodes for Outfit Designer Agent ---
def outfit_chat_node_stub(state: OutfitAgentState, llm) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): outfit_chat_node_stub called")
    # This node would interact with an LLM, similar to the clothing item agent's chat node
    # For now, it just acknowledges and perhaps adds a stub message
    # Assume tools are bound to this LLM for the outfit agent context
    # Here, we'll just create a placeholder response
    response_message = {"role": "assistant", "content": "Outfit Designer STUB: Processing your outfit request."}
    return {"messages": state["messages"] + [response_message]}

def parse_anchor_item_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): parse_anchor_item_node_stub called")
    last_user_message = ""
    for msg in reversed(state.get('messages', [])):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get('role') == 'user':
            last_user_message = msg.get('content', '')
            break
    anchor_desc = last_user_message or "white pants"
    return {
        "season": "spring", 
        "anchor_item_description": anchor_desc,
        "selected_items": [],
        "missing_categories": ["top", "bottom", "shoes"],
        "feedback_log": state.get("feedback_log", []) + [f"Parsed anchor: {anchor_desc}"],
        "current_embedding": get_item_embedding(anchor_desc)
    }

def query_sqlite_anchor_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): query_sqlite_anchor_node_stub called")
    tags = {"description_contains": state["anchor_item_description"], "season": state["season"]}
    item_ids = query_sqlite_by_tags(tags)
    return {"item_candidates": item_ids}

def query_chroma_anchor_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): query_chroma_anchor_node_stub called")
    best_match_items = query_chroma_by_ids_and_embedding(
        state["item_candidates"],
        state["current_embedding"],
        top_k=1
    )
    return {"selected_items": state.get("selected_items", []) + best_match_items if best_match_items else state.get("selected_items", [])}

def update_state_add_anchor_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): update_state_add_anchor_node_stub called")
    if state.get("selected_items"):
        first_item = state["selected_items"][0]
        category = first_item.get("category", "unknown")
        new_missing = [cat for cat in state.get("missing_categories", []) if cat != category]
        return {"missing_categories": new_missing, "feedback_log": state.get("feedback_log", []) + [f"Added anchor: {first_item.get('description')}"]}
    return {}

def build_outfit_loop_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): build_outfit_loop_node_stub called")
    if state.get("missing_categories"):
        cat_to_fill = state["missing_categories"][0]
        dummy_item = {"item_id": f"dummy_{cat_to_fill}", "description": f"Dummy {cat_to_fill}", "category": cat_to_fill}
        new_selected_items = state.get("selected_items", []) + [dummy_item]
        new_missing_categories = state["missing_categories"][1:]
        return {
            "selected_items": new_selected_items,
            "missing_categories": new_missing_categories,
            "feedback_log": state.get("feedback_log", []) + [f"Filled {cat_to_fill} with dummy item"]
        }
    return {}

def check_completeness_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): check_completeness_node_stub called")
    is_complete = check_outfit_completeness(state.get("selected_items", []))
    log_message = f"Completeness check: {is_complete}"
    if not is_complete:
        logger.info("Outfit not yet complete based on check.")
    else:
        logger.info("Outfit is complete based on check.")
    return {"feedback_log": state.get("feedback_log", []) + [log_message]}

def handle_feedback_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): handle_feedback_node_stub called")
    last_user_message = ""
    for msg in reversed(state.get('messages', [])):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get('role') == 'user':
            last_user_message = msg.get('content', '')
            break
    return {"feedback_log": state.get("feedback_log", []) + [f"User feedback received (stub handling): {last_user_message}"]}

# --- Conditional Edge for Outfit Agent ---
def should_refine_outfit_condition(state: OutfitAgentState) -> str:
    logger.info("STUB (Outfit Designer Condition): should_refine_outfit_condition called")
    # Ensure messages list is not empty and last_message is accessible
    if not state.get("messages"): 
        # If no messages, perhaps initial build
        if not check_outfit_completeness(state.get("selected_items", [])) and state.get("missing_categories"):
            logger.info("Outfit not complete, routing to build_outfit_loop_node_stub")
            return "build_outfit"
        logger.info("No messages and outfit complete or no missing categories, routing to END (Outfit Designer)")
        return END # Or a different state if applicable

    last_message = state["messages"][-1]
    # Check content of last_message (human or AI message)
    content_to_check = ""
    if hasattr(last_message, 'content'): # For AIMessage, HumanMessage from Langchain
        content_to_check = last_message.content.lower()
    elif isinstance(last_message, dict) and 'content' in last_message: # For dict messages
        content_to_check = str(last_message['content']).lower()

    if "swap" in content_to_check:
        logger.info("Routing to handle_feedback_node_stub")
        return "handle_feedback"
    if not check_outfit_completeness(state.get("selected_items", [])) and state.get("missing_categories"):
        logger.info("Outfit not complete, routing to build_outfit_loop_node_stub")
        return "build_outfit"
    logger.info("Outfit complete or no feedback, routing to END (Outfit Designer)")
    return END

# --- Outfit Agent Graph Creation ---
def create_outfit_designer_agent_graph(llm):
    """
    Creates the graph for the outfit designer agent.
    """
    graph_builder = StateGraph(OutfitAgentState)

    # Nodes
    # Ensure the callable functions (e.g., outfit_chat_node_stub) are correctly defined above in this file
    graph_builder.add_node("outfit_chat", lambda state: outfit_chat_node_stub(state, llm))
    graph_builder.add_node("parse_anchor", parse_anchor_item_node_stub) # Graph name "parse_anchor" maps to parse_anchor_item_node_stub
    graph_builder.add_node("query_sqlite_anchor", query_sqlite_anchor_node_stub)
    graph_builder.add_node("query_chroma_anchor", query_chroma_anchor_node_stub)
    graph_builder.add_node("update_state_add_anchor", update_state_add_anchor_node_stub)
    graph_builder.add_node("build_outfit", build_outfit_loop_node_stub) # Graph name "build_outfit" maps to build_outfit_loop_node_stub
    graph_builder.add_node("check_completeness", check_completeness_node_stub)
    graph_builder.add_node("handle_feedback", handle_feedback_node_stub)

    # Edges (based on docs/outfit_agent_design.md)
    graph_builder.add_edge(START, "parse_anchor") 
    graph_builder.add_edge("parse_anchor", "query_sqlite_anchor")
    graph_builder.add_edge("query_sqlite_anchor", "query_chroma_anchor")
    graph_builder.add_edge("query_chroma_anchor", "update_state_add_anchor")
    graph_builder.add_edge("update_state_add_anchor", "build_outfit")
    
    graph_builder.add_edge("build_outfit", "check_completeness")
    
    graph_builder.add_conditional_edges(
        "check_completeness",
        should_refine_outfit_condition, 
        {
            "handle_feedback": "handle_feedback",
            "build_outfit": "build_outfit", 
            END: "outfit_chat" 
        }
    )
    graph_builder.add_edge("handle_feedback", "build_outfit") 
    graph_builder.add_edge("outfit_chat", END) 
    
    logger.info("Outfit Designer Agent graph created successfully.")
    return graph_builder.compile()

# Alias for consistency if imported elsewhere, though create_outfit_designer_agent_graph is more descriptive
create_outfit_agent_graph = create_outfit_designer_agent_graph
