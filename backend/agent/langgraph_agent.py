"""LangGraph Agent Module - Refactored

This module re-exports components from the refactored agent architecture.
It maintains backward compatibility with code that imports from this module.
"""

import logging

# Re-export components from the new modules
from backend.agent.steps import (
    State, 
    CaptionToolNode,
    embed_step,
    persist_db_step,
    get_items_step,
    format_item_search_response,
    _route_from_tools
)

from backend.agent.orchestrator import graph, run_agent, stream_agent_updates

# Re-export tools for backward compatibility
from backend.agent.tools.caption_image import caption_image
from backend.agent.tools.outfit_searcher import search_clothing_items as search_items

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info('Loading langgraph_agent module (refactored)')



# stream_graph_updates function moved to orchestrator.py as stream_agent_updates


# Example usage for testing
if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        # Use the refactored function from orchestrator
        for event in stream_agent_updates({"messages": [{"role": "user", "content": user_input}]}):
            # Process event if needed
            pass
