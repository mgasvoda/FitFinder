"""
FitFinder Agent Core - Chainlit Backend
Pure agent functionality without FastAPI dependencies
"""

from backend.agent.tools import get_clothing_items, create_clothing_item, get_outfit, create_outfit
from langfuse.callback import CallbackHandler
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.graph import START
from langchain_anthropic import ChatAnthropic

import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.info('Loading FitFinder agent core')

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Optional: Enable Langfuse tracing
# langfuse_handler = CallbackHandler(
#     public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
#     secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
#     host="https://us.cloud.langfuse.com"
# )

# Define the system prompt
SYSTEM_PROMPT = """You are FitFinder, an AI fashion assistant that helps users manage their wardrobe and create outfits. 
Your capabilities include:
    - Adding new clothing items to the user's wardrobe
    - Retrieving clothing items based on filters
    - Creating and suggesting complete outfits
    - Answering questions about fashion and styling
    
    Always be helpful, friendly, and professional in your responses. If you're unsure about something, 
    ask clarifying questions rather than making assumptions."""

class State(TypedDict):
    messages: Annotated[list, add_messages]

def create_agent(): 
    """Create and configure the LangGraph agent"""
    checkpointer = InMemorySaver() 
    graph_builder = StateGraph(State)

    llm = ChatAnthropic(
        model="claude-3-haiku-20240307", 
        anthropic_api_key=ANTHROPIC_API_KEY,
        temperature=0.1,
    )

    tools = [get_clothing_items, create_clothing_item, get_outfit, create_outfit]
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph_builder.add_node("chatbot", chatbot)

    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge(START, "chatbot")
    
    graph = graph_builder.compile(checkpointer=checkpointer)
    return graph

# Initialize the agent
agent = create_agent()

# Initialize the agent with the system prompt
agent.invoke(
    {"messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": "Hello"}]}, 
    config={"configurable": {"thread_id": 1}}
)

def stream_graph_updates(user_input: str):
    """
    Process user input through the agent and return the response
    
    Args:
        user_input (str): The user's message/query
        
    Returns:
        str: The agent's response
    """
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}, 
            config={"configurable": {"thread_id": 1}}
        )
        
        response = result['messages'][-1].content
        return response
        
    except Exception as e:
        logger.error(f"Error in stream_graph_updates: {e}")
        return "I'm sorry, I encountered an error processing your request. Please try again."

def initialize_agent_resources():
    """Initialize database and vector store resources for the agent"""
    from backend.db.models import Base, engine
    from backend.db import vector_store
    
    logger.info("Initializing agent resources...")
    
    # Initialize database
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")
    
    # Initialize ChromaDB collections
    vector_store.init_chroma_collections()
    logger.info("Vector store initialized")
    
    logger.info("Agent resources initialized successfully")

if __name__ == '__main__':
    """CLI mode for testing the agent directly"""
    initialize_agent_resources()
    
    logger.info("FitFinder Agent CLI Mode Initialized.")
    print("Welcome to FitFinder Agent CLI! Type 'exit' or 'quit' to end.")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        response = stream_graph_updates(user_input)
        print(f"Agent: {response}")
