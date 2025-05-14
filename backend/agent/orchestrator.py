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


# --- CLOTHING ITEM AGENT GRAPH (retains existing logic) ---
def create_clothing_item_agent_graph():
    """
    Create and configure the LangGraph agent graph for clothing item management.
    Returns:
        StateGraph: The compiled LangGraph graph ready for execution.
    """
    llm = ChatAnthropic(
        model="claude-3-7-sonnet-latest",
        anthropic_api_key=ANTHROPIC_API_KEY
    )
    tools = [caption_image, search_items]
    graph_builder = StateGraph(State)
    graph_builder.add_node("chat", lambda state: {"messages": llm.bind_tools(tools).invoke(state['messages'])})
    graph_builder.add_node("tools", CaptionToolNode(tools))
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
        _route_from_tools,
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
    graph_builder.add_edge("chat", END)
    return graph_builder.compile()

# --- OUTFIT DESIGNER AGENT GRAPH (per design doc, stubbed tools) ---
from backend.agent.tools.outfit_tools_stubs import (
    query_sqlite_by_tags,
    query_chroma_by_ids_and_embedding,
    get_item_embedding,
    check_outfit_completeness,
)

def create_outfit_designer_agent_graph():
    """
    Create and configure the LangGraph agent graph for outfit design and management.
    Returns:
        StateGraph: The compiled LangGraph graph ready for execution.
    """
    # State for outfit designer agent
    default_outfit_state = {
        "selected_items": [],
        "missing_categories": [],
        "feedback_log": [],
        "season": None,
        "anchor_item_description": None,
    }
    
    graph_builder = StateGraph(dict)
    # Nodes as described in the design doc (stubbed logic)
    def parse_tags_and_get_embedding(state):
        # Stub: parse tags and get embedding for anchor item
        return state
    def query_sqlite_candidates(state):
        # Stub: query SQLite for anchor item candidates
        return state
    def query_chroma_match(state):
        # Stub: query Chroma for best match
        return state
    def update_outfit_state_add_anchor(state):
        # Stub: update outfit state to add anchor item
        return state
    def add_missing_categories_loop(state):
        # Stub: add missing categories
        return state
    def check_completeness(state):
        # Always call check_outfit_completeness
        state["is_complete"] = check_outfit_completeness(state.get("selected_items", []))
        return state
    def prompt_for_feedback_or_return(state):
        # Stub: prompt for feedback or return
        return state
    def handle_user_feedback(state):
        # Stub: handle user feedback
        return state
    def finalize_or_refine(state):
        # Stub: finalize or re-enter refinement
        return state
    # Add nodes
    graph_builder.add_node("parse_tags_and_get_embedding", parse_tags_and_get_embedding)
    graph_builder.add_node("query_sqlite_candidates", query_sqlite_candidates)
    graph_builder.add_node("query_chroma_match", query_chroma_match)
    graph_builder.add_node("update_outfit_state_add_anchor", update_outfit_state_add_anchor)
    graph_builder.add_node("add_missing_categories_loop", add_missing_categories_loop)
    graph_builder.add_node("check_completeness", check_completeness)
    graph_builder.add_node("prompt_for_feedback_or_return", prompt_for_feedback_or_return)
    graph_builder.add_node("handle_user_feedback", handle_user_feedback)
    graph_builder.add_node("finalize_or_refine", finalize_or_refine)
    # Edges per design doc
    graph_builder.add_edge(START, "parse_tags_and_get_embedding")
    graph_builder.add_edge("parse_tags_and_get_embedding", "query_sqlite_candidates")
    graph_builder.add_edge("query_sqlite_candidates", "query_chroma_match")
    graph_builder.add_edge("query_chroma_match", "update_outfit_state_add_anchor")
    graph_builder.add_edge("update_outfit_state_add_anchor", "add_missing_categories_loop")
    graph_builder.add_edge("add_missing_categories_loop", "check_completeness")
    graph_builder.add_edge("check_completeness", "prompt_for_feedback_or_return")
    graph_builder.add_edge("prompt_for_feedback_or_return", "handle_user_feedback")
    graph_builder.add_edge("handle_user_feedback", "finalize_or_refine")
    graph_builder.add_edge("finalize_or_refine", "check_completeness")  # Loop for refinement
    graph_builder.add_edge("prompt_for_feedback_or_return", END)  # If no feedback, finish
    return graph_builder.compile()

# --- ORCHESTRATOR ---
# Create both graphs
clothing_item_graph = create_clothing_item_agent_graph()
outfit_designer_graph = create_outfit_designer_agent_graph()

def orchestrator_run_agent(state: dict, agent_type: str = "clothing_item") -> dict:
    """
    Run the appropriate agent graph based on agent_type.
    Args:
        state (dict): The initial state for the agent.
        agent_type (str): 'clothing_item' or 'outfit_designer'.
    Returns:
        dict: The final state after agent execution.
    """
    logger.info(f"Running orchestrator for agent_type={agent_type}")
    if agent_type == "outfit_designer":
        return outfit_designer_graph.invoke(state)
    else:
        return clothing_item_graph.invoke(state)

def orchestrator_stream_agent_updates(state: dict, agent_type: str = "clothing_item"):
    """
    Stream updates from the appropriate agent graph based on agent_type.
    Args:
        state (dict): The initial state for the agent.
        agent_type (str): 'clothing_item' or 'outfit_designer'.
    Yields:
        dict: Each update from the agent execution.
    """
    logger.info(f"Streaming orchestrator updates for agent_type={agent_type}")
    if agent_type == "outfit_designer":
        for event in outfit_designer_graph.stream(state):
            yield event
    else:
        for event in clothing_item_graph.stream(state):
            yield event



# Create the graph instance
graph = create_agent_graph()


def run_agent(state: dict) -> dict:
    """
    Run the agent with the given initial state.
    
    Args:
        state (dict): The initial state for the agent.
        
    Returns:
        dict: The final state after agent execution.
    """
    logger.info(f"Running agent with initial state keys: {state.keys()}")
    
    try:
        # Execute the graph with the given state
        result_state = graph.invoke(state)
        logger.info(f"Agent execution completed with result state keys: {result_state.keys()}")
        return result_state
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        raise


def stream_agent_updates(state: dict):
    """
    Stream updates from the agent execution.
    
    Args:
        state (dict): The initial state for the agent.
        
    Yields:
        dict: Each update from the agent execution.
    """
    logger.info(f"Streaming agent updates with initial state keys: {state.keys()}")
    
    try:
        for event in graph.stream(state):
            # Log node transition information
            node_name = next(iter(event))
            logger.info(f"Graph transition: {node_name}")
            logger.debug(f"Graph stream event data: {event}")
            
            # Process and yield the event
            yield event
    except Exception as e:
        logger.error(f"Error streaming agent updates: {e}", exc_info=True)
        raise
