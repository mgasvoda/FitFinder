import logging
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition

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

logger = logging.getLogger(__name__)

# --- Clothing Item Agent Graph ---
def create_clothing_item_agent_graph(llm):
    """
    Create and configure the LangGraph agent graph for managing clothing items.
    
    Args:
        llm: The language model to be used by the agent.

    Returns:
        StateGraph: The compiled LangGraph graph ready for execution.
    """
    # Tools for clothing item agent
    clothing_item_tools = [caption_image, search_items]
    
    graph_builder = StateGraph(State) # Uses the original State
    
    # Define nodes
    # Bind tools to the LLM for the chat node to decide on tool use
    # The key for the agent's response in the state should be 'messages'
    graph_builder.add_node("chat", lambda state: {"messages": llm.bind_tools(clothing_item_tools).invoke(state['messages'])})
    graph_builder.add_node("tools", CaptionToolNode(clothing_item_tools)) # Generic tool execution node
    graph_builder.add_node("embed", embed_step)
    graph_builder.add_node("persist_db", persist_db_step)
    graph_builder.add_node("get_items", get_items_step)
    graph_builder.add_node("format_items", format_item_search_response)
    
    # Define workflow edges
    graph_builder.add_edge(START, "chat")
    
    # Conditional routing from chat based on tool calls
    graph_builder.add_conditional_edges(
        "chat", 
        tools_condition, # LangGraph's built-in to check if tools were called
        {
            "tools": "tools", # If tools called, go to tools node
            END: END          # If no tools called, end of this agent's turn
        }
    )
    
    # Conditional routing from tools node based on which tool was called
    graph_builder.add_conditional_edges(
        'tools',
        _route_from_tools, # Custom routing logic from backend.agent.steps
        {
            'embed': 'embed',           # Route to embed if caption_image was called (implicitly via _route_from_tools)
            'get_items': 'get_items',   # Route to get_items if search_items was called
            'chat': 'chat'              # Route back to chat if tool output needs reprocessing or error occurred
        }
    )
    
    # Edges from specific processing steps
    graph_builder.add_edge("embed", "persist_db")
    graph_builder.add_edge('persist_db', 'chat') # After persisting, go back to chat for next action/response
    graph_builder.add_edge('get_items', 'format_items')
    graph_builder.add_edge('format_items', 'chat') # After formatting search results, go back to chat
    
    logger.info("Clothing Item Agent graph created successfully.")
    return graph_builder.compile()
