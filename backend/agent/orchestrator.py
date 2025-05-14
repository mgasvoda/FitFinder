"""
Agent orchestration module for the FitFinder application.
This module handles the LangGraph graph construction and execution.
"""

import os
import logging
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langchain_anthropic import ChatAnthropic
from typing import TypedDict, List, Dict, Any

from backend.agent.steps import (
    State, 
    CaptionToolNode, 
    embed_step, 
    persist_db_step, 
    get_items_step, 
    format_item_search_response,
    _route_from_tools
)
from backend.agent.tools.caption_image import caption_image
from backend.agent.tools.outfit_searcher import search_clothing_items as search_items

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Get API key from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- State Definitions ---
class OutfitAgentState(TypedDict):
    messages: List[Any]  # For chat interaction within the outfit agent
    selected_items: List[Dict[str, Any]]  # Items currently in the outfit
    missing_categories: List[str]  # e.g., ["top", "shoes"]
    feedback_log: List[str]  # User refinement requests
    season: str  # Extracted from prompt
    anchor_item_description: str  # Initial user-provided item (e.g. "white pants")
    current_embedding: List[float] # Embedding of anchor item or feedback
    item_candidates: List[str] # Candidate item IDs from SQLite query

# The existing `State` TypedDict from backend.agent.steps will be used for:
# 1. The main orchestrator
# 2. The clothing item agent


# --- Stub Tools for Outfit Designer Agent ---
def get_item_embedding_stub(text: str) -> List[float]:
    logger.info(f"STUB (Outfit Designer Tool): get_item_embedding_stub called with text: {text}")
    return [0.0] * 128 # Example embedding size

def query_sqlite_by_tags_stub(tags: dict) -> List[str]:
    logger.info(f"STUB (Outfit Designer Tool): query_sqlite_by_tags_stub called with tags: {tags}")
    return ["item_id_1", "item_id_2"]

def query_chroma_by_ids_and_embedding_stub(ids: List[str], embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
    logger.info(f"STUB (Outfit Designer Tool): query_chroma_by_ids_and_embedding_stub called with {len(ids)} IDs, embedding, top_k={top_k}")
    return [{"item_id": ids[0] if ids else "stub_item_id", "description": "Stub item from Chroma", "category": "top"}]

def check_outfit_completeness_stub(items: List[Dict[str, Any]]) -> bool:
    logger.info(f"STUB (Outfit Designer Tool): check_outfit_completeness_stub called with {len(items)} items.")
    # Simple stub: complete if 3 items are present
    return len(items) >= 3

# --- Stub Nodes for Outfit Designer Agent ---
def outfit_chat_node_stub(state: OutfitAgentState, llm) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): outfit_chat_node_stub called")
    # This node would interact with an LLM, similar to the clothing item agent's chat node
    # For now, it just acknowledges and perhaps adds a stub message
    # Assume tools are bound to this LLM for the outfit agent context
    outfit_designer_tools = [
        get_item_embedding_stub, 
        query_sqlite_by_tags_stub, 
        query_chroma_by_ids_and_embedding_stub, 
        check_outfit_completeness_stub
    ]
    # Simulate LLM call that might decide to use a tool or respond
    # Here, we'll just create a placeholder response
    response_message = {"role": "assistant", "content": "Outfit Designer STUB: Processing your outfit request."}
    return {"messages": state["messages"] + [response_message]}

def parse_anchor_item_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): parse_anchor_item_node_stub called")
    # Example: Extract season and anchor description from the latest user message
    last_user_message = ""
    for msg in reversed(state['messages']):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get('role') == 'user': # Check for dict form too
            last_user_message = msg.get('content', '')
            break

    return {
        "season": "spring", # Stub value
        "anchor_item_description": last_user_message or "white pants", # Stub value
        "selected_items": [],
        "missing_categories": ["top", "bottom", "shoes"],
        "feedback_log": state.get("feedback_log", []) + [f"Parsed anchor: {last_user_message or 'white pants'}"],
        "current_embedding": get_item_embedding_stub(last_user_message or "white pants")
    }

def query_sqlite_anchor_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): query_sqlite_anchor_node_stub called")
    # Dummy tags based on anchor_item_description or season
    tags = {"description_contains": state["anchor_item_description"], "season": state["season"]}
    item_ids = query_sqlite_by_tags_stub(tags)
    return {"item_candidates": item_ids}

def query_chroma_anchor_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): query_chroma_anchor_node_stub called")
    best_match_items = query_chroma_by_ids_and_embedding_stub(
        state["item_candidates"],
        state["current_embedding"],
        top_k=1
    )
    return {"selected_items": state.get("selected_items", []) + best_match_items if best_match_items else state.get("selected_items", [])}

def update_state_add_anchor_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): update_state_add_anchor_node_stub called")
    # This node would typically update missing_categories based on the added anchor item
    # For simplicity, we assume the anchor item is added and we log it.
    if state.get("selected_items"):
        first_item = state["selected_items"][0]
        category = first_item.get("category", "unknown")
        new_missing = [cat for cat in state.get("missing_categories", []) if cat != category]
        return {"missing_categories": new_missing, "feedback_log": state.get("feedback_log", []) + [f"Added anchor: {first_item.get('description')}"]}
    return {}

def build_outfit_loop_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): build_outfit_loop_node_stub called")
    # This is the main loop. It would try to fill missing categories.
    # For now, it just logs and maybe adds one dummy item if categories are missing.
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
    is_complete = check_outfit_completeness_stub(state.get("selected_items", []))
    if not is_complete:
        logger.info("Outfit not yet complete based on stub check.")
        # Potentially add a message to state['messages'] to ask for more items or indicate it's not done.
    else:
        logger.info("Outfit is complete based on stub check.")
    return {"feedback_log": state.get("feedback_log", []) + [f"Completeness check: {is_complete}"]}

def handle_feedback_node_stub(state: OutfitAgentState) -> Dict[str, Any]:
    logger.info("STUB (Outfit Designer Node): handle_feedback_node_stub called")
    # This node would parse user feedback and modify state (e.g., selected_items, missing_categories)
    # For now, it just logs the feedback.
    last_user_message = ""
    for msg in reversed(state['messages']):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_user_message = msg.content
            break
        elif isinstance(msg, dict) and msg.get('role') == 'user':
            last_user_message = msg.get('content', '')
            break
    return {"feedback_log": state.get("feedback_log", []) + [f"User feedback received (stub handling): {last_user_message}"]}


def should_refine_outfit_condition(state: OutfitAgentState) -> str:
    logger.info("STUB (Outfit Designer Condition): should_refine_outfit_condition called")
    # Based on user feedback or completeness. If not complete, loop. If feedback, refine.
    last_message = state["messages"][-1]
    if hasattr(last_message, 'content') and "swap" in last_message.content.lower(): # Simple feedback check
        logger.info("Routing to handle_feedback_node_stub")
        return "handle_feedback"
    if not check_outfit_completeness_stub(state.get("selected_items", [])) and state.get("missing_categories"):
        logger.info("Outfit not complete, routing to build_outfit_loop_node_stub")
        return "build_outfit"
    logger.info("Outfit complete or no feedback, routing to END (Outfit Designer)")
    # In a real scenario, this might go back to chat for final presentation or END
    return END

# --- Clothing Item Agent Graph ---
def create_clothing_item_agent_graph(llm): # Renamed and takes llm
    """
    Create and configure the LangGraph agent graph for managing clothing items.
    
    Returns:
        StateGraph: The compiled LangGraph graph ready for execution.
    """
    # Tools for clothing item agent
    clothing_item_tools = [caption_image, search_items]
    
    graph_builder = StateGraph(State) # Uses the original State
    
    graph_builder.add_node("chat", lambda state: {"messages": llm.bind_tools(clothing_item_tools).invoke(state['messages'])})
    graph_builder.add_node("tools", CaptionToolNode(clothing_item_tools))
    graph_builder.add_node("embed", embed_step)
    graph_builder.add_node("persist_db", persist_db_step)
    graph_builder.add_node("get_items", get_items_step)
    graph_builder.add_node("format_items", format_item_search_response)
    
    graph_builder.add_edge(START, "chat")
    
    graph_builder.add_conditional_edges(
        "chat", 
        tools_condition,
        {
            "tools": "tools",
            END: END
        }
    )
    
    graph_builder.add_conditional_edges(
        'tools',
        _route_from_tools, # Existing routing logic for these tools
        {
            'embed': 'embed',
            'get_items': 'get_items',
            'chat': 'chat' 
        }
    )
    
    graph_builder.add_edge("embed", "persist_db")
    graph_builder.add_edge('persist_db', 'chat')
    graph_builder.add_edge('get_items', 'format_items')
    graph_builder.add_edge('format_items', 'chat')
    
    # Edge from chat to END is implicitly handled by tools_condition if no tools are called.
    # graph_builder.add_edge("chat", END) # This can lead to premature ending if tools_condition handles it.
    
    return graph_builder.compile()

# --- Outfit Designer Agent Graph ---
def create_outfit_designer_agent_graph(llm):
    """
    Creates the graph for the outfit designer agent.
    """
    graph_builder = StateGraph(OutfitAgentState)

    # Nodes
    graph_builder.add_node("outfit_chat", lambda state: outfit_chat_node_stub(state, llm))
    graph_builder.add_node("parse_anchor", parse_anchor_item_node_stub)
    graph_builder.add_node("query_sqlite_anchor", query_sqlite_anchor_node_stub)
    graph_builder.add_node("query_chroma_anchor", query_chroma_anchor_node_stub)
    graph_builder.add_node("update_state_add_anchor", update_state_add_anchor_node_stub)
    graph_builder.add_node("build_outfit", build_outfit_loop_node_stub)
    graph_builder.add_node("check_completeness", check_completeness_node_stub)
    graph_builder.add_node("handle_feedback", handle_feedback_node_stub)

    # Edges (based on docs/outfit_agent_design.md)
    # Start with parsing the user prompt (initial message handled by orchestrator, then to chat/parse)
    graph_builder.add_edge(START, "parse_anchor") # Start by parsing current state/message for anchor
    graph_builder.add_edge("parse_anchor", "query_sqlite_anchor")
    graph_builder.add_edge("query_sqlite_anchor", "query_chroma_anchor")
    graph_builder.add_edge("query_chroma_anchor", "update_state_add_anchor")
    graph_builder.add_edge("update_state_add_anchor", "build_outfit") # Then start building/checking loop
    
    graph_builder.add_edge("build_outfit", "check_completeness")
    
    # Conditional edge after checking completeness (finalize_or_refine logic)
    graph_builder.add_conditional_edges(
        "check_completeness",
        should_refine_outfit_condition, # Condition to loop, refine, or end
        {
            "handle_feedback": "handle_feedback",
            "build_outfit": "build_outfit", # If not complete, continue building
            END: "outfit_chat" # If complete and no feedback, go to chat for final presentation then END.
        }
    )
    graph_builder.add_edge("handle_feedback", "build_outfit") # After handling feedback, try to build again
    graph_builder.add_edge("outfit_chat", END) # Final chat interaction before ending

    return graph_builder.compile()


# --- Main Orchestrator Graph ---
def route_to_agent(state: State) -> str:
    logger.info("ORCHESTRATOR: route_to_agent called")
    last_message_content = ""
    if state['messages']:
        last_msg = state['messages'][-1]
        if hasattr(last_msg, 'content'): # AIMessage, HumanMessage
            last_message_content = last_msg.content
        elif isinstance(last_msg, dict) and 'content' in last_msg: # Raw dict message
            last_message_content = last_msg['content']

    if any(keyword in last_message_content.lower() for keyword in ["outfit", "wear", "style me"]):
        logger.info("ORCHESTRATOR: Routing to outfit_designer_agent")
        return "outfit_designer_agent"
    else:
        logger.info("ORCHESTRATOR: Routing to clothing_item_agent")
        return "clothing_item_agent"

def call_clothing_item_agent_node(state: State, agent, llm) -> Dict[str, Any]:
    logger.info("ORCHESTRATOR: Calling clothing_item_agent")
    # Ensure the agent receives the full state it expects, esp. messages
    sub_agent_state = {"messages": state.get('messages', [])} # Pass only messages or full state if compatible
    result_state = agent.invoke(sub_agent_state)
    return {"messages": result_state.get("messages", state['messages'])}

def call_outfit_designer_agent_node(state: State, agent, llm) -> Dict[str, Any]:
    logger.info("ORCHESTRATOR: Calling outfit_designer_agent")
    initial_outfit_state = OutfitAgentState(
        messages=state.get('messages', []),
        selected_items=[],
        missing_categories=["top", "bottom", "shoes"], 
        feedback_log=[],
        season="any", 
        anchor_item_description="",
        current_embedding=[],
        item_candidates=[]
    )
    result_outfit_state = agent.invoke(initial_outfit_state)
    return {"messages": result_outfit_state.get("messages", state['messages'])}

def create_main_orchestrator_graph(clothing_item_agent_instance, outfit_designer_agent_instance, llm):
    graph_builder = StateGraph(State) # Main orchestrator uses 'State'

    # Orchestrator's own chat node for initial interaction and routing response
    # For now, a simple pass-through or minimal interaction before routing
    graph_builder.add_node("orchestrator_chat", lambda s: {"messages": s['messages']}) # Simple echo for now

    # Nodes to call sub-agents
    graph_builder.add_node(
        "clothing_item_agent_node", 
        lambda s: call_clothing_item_agent_node(s, clothing_item_agent_instance, llm)
    )
    graph_builder.add_node(
        "outfit_designer_agent_node",
        lambda s: call_outfit_designer_agent_node(s, outfit_designer_agent_instance, llm)
    )

    graph_builder.add_edge(START, "orchestrator_chat")
    
    # Conditional routing from orchestrator_chat
    graph_builder.add_conditional_edges(
        "orchestrator_chat",
        route_to_agent,
        {
            "clothing_item_agent": "clothing_item_agent_node",
            "outfit_designer_agent": "outfit_designer_agent_node"
        }
    )

    # After sub-agents complete, they return messages. Route back to orchestrator_chat or END.
    # For now, let's assume sub-agents update messages and then the orchestrator can END or re-chat.
    # The sub-agents themselves have END states. This orchestrator ends after one routing.
    graph_builder.add_edge("clothing_item_agent_node", END) # Or back to orchestrator_chat if further interaction needed
    graph_builder.add_edge("outfit_designer_agent_node", END)

    return graph_builder.compile()


# --- Instantiate LLM and Agents ---
# Instantiate the LLM (shared across agents)
llm_instance = ChatAnthropic(
    model="claude-3-haiku-20240307", # Using Haiku for potentially faster/cheaper stub operations
    anthropic_api_key=ANTHROPIC_API_KEY
)

clothing_item_agent = create_clothing_item_agent_graph(llm_instance)
outfit_designer_agent = create_outfit_designer_agent_graph(llm_instance)
main_orchestrator = create_main_orchestrator_graph(clothing_item_agent, outfit_designer_agent, llm_instance)


def run_agent(state: dict) -> dict:
    """
    Run the main orchestrator agent with the given initial state.
    
    Args:
        state (dict): The initial state for the agent (expects 'messages' key).
        
    Returns:
        dict: The final state after agent execution.
    """
    logger.info(f"MAIN ORCHESTRATOR: Running with initial state keys: {state.keys()}")
    
    # Ensure state is in the format expected by StateGraph (TypedDict)
    # If state is just a raw dict, ensure 'messages' key exists.
    current_state = State(messages=state.get('messages', []))
    
    try:
        result_state = main_orchestrator.invoke(current_state)
        logger.info(f"MAIN ORCHESTRATOR: Execution completed. Result keys: {result_state.keys()}")
        return result_state
    except Exception as e:
        logger.error(f"Error running main orchestrator: {e}", exc_info=True)
        # Return a state with the error message
        return {"messages": state.get('messages', []) + [{"role": "assistant", "content": f"Error: {e}"}]}
