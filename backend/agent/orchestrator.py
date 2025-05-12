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


def create_agent_graph():
    """
    Create and configure the LangGraph agent graph.
    
    Returns:
        StateGraph: The compiled LangGraph graph ready for execution.
    """
    # Instantiate the LLM
    llm = ChatAnthropic(
        model="claude-3-7-sonnet-latest",
        anthropic_api_key=ANTHROPIC_API_KEY
    )
    
    # Define available tools
    tools = [caption_image, search_items]
    
    # Build StateGraph for sequential workflow
    graph_builder = StateGraph(State)
    
    # Define nodes
    graph_builder.add_node("chat", lambda state: {"messages": llm.bind_tools(tools).invoke(state['messages'])})
    graph_builder.add_node("tools", CaptionToolNode(tools))
    graph_builder.add_node("embed", embed_step)
    graph_builder.add_node("persist_db", persist_db_step)
    graph_builder.add_node("get_items", get_items_step)
    graph_builder.add_node("format_items", format_item_search_response)
    
    # Define the initial flow
    graph_builder.add_edge(START, "chat")
    
    # Route from chat based on whether tools need to be called
    graph_builder.add_conditional_edges(
        "chat", 
        tools_condition,
        {
            "tools": "tools",  # If tools are requested, go to tools node
            END: END  # Otherwise end the conversation
        }
    )
    
    # Improved conditional edge routing to the proper next node based on tool results
    graph_builder.add_conditional_edges(
        'tools',
        _route_from_tools,
        {
            'embed': 'embed',            # If caption_image tool was used, route to embed node
            'get_items': 'get_items',    # If search_items tool was used, route to get_items node
            'chat': 'chat'               # If no recognized tool was used, route back to chat
        }
    )
    
    # Define the remaining sequential flows
    graph_builder.add_edge("embed", "persist_db")
    graph_builder.add_edge('persist_db', 'chat')
    graph_builder.add_edge('get_items', 'format_items')
    graph_builder.add_edge('format_items', 'chat')
    
    # Add an edge from chat to END when the conversation is complete (END is a special state)
    graph_builder.add_edge("chat", END)
    
    # Compile the graph to an executable tool
    return graph_builder.compile()


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
