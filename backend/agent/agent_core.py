from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.models import get_db
from backend.agent.schemas import ChatRequest, ChatResponse
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
logger.info('Loading agent core')

agent_router = APIRouter()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host="https://us.cloud.langfuse.com"
)

# Define the system prompt
SYSTEM_PROMPT = """You are FitFinder, an AI fashion assistant that helps users manage their wardrobe and create outfits. 
Your capabilities include:
    - Adding new clothing items to the user's wardrobe
    - Retrieving clothing items based on filters
    - Creating and suggesting complete outfits
    - Answering questions about fashion and styling
    
    Always be helpful, friendly, and professional in your responses. If you're unsure about something, 
    ask clarifying questions rather than making assumptions."""
# Agent definition

class State (TypedDict):
    messages: Annotated[list, add_messages]

def create_agent(): 
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
    graph = graph_builder.compile(checkpointer=checkpointer, )
    return graph

agent = create_agent()
agent.invoke({"messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": "Hello"}]}, config={
            "configurable": {"thread_id": 1}, 
            "callbacks": [langfuse_handler]
        })

def stream_graph_updates(user_input: str):
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]}, 
        config={
            "configurable": {"thread_id": 1}, 
            "callbacks": [langfuse_handler]
        }
    )
    try:
        print(result['messages'][-1].content)
    except Exception as e:
        print(result)
        print(f"Error in stream_graph_updates: {e}")

# Agent routing for API endpoint
# POST /api/chat
@agent_router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    """
    Handle chat requests and interact with the agent.
    
    Args:
        req: The chat request containing prompt and optional image URL
        db: Database session
        
    Returns:
        ChatResponse: The agent's response
    """
    try:
        # Log the incoming request
        logger.info(f"Backend received chat request: {req}")

        response = stream_graph_updates(req.prompt)
        # Log the response
        logger.info(f"Agent response: {response}")

        # Return the response
        return ChatResponse(response_text=response)

    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")


if __name__ == '__main__':

    from backend.db.models import Base, engine
    from backend.db import vector_store  # Import to initialize ChromaDB collections

    logging.basicConfig(level=logging.INFO)

    # DB init
    Base.metadata.create_all(bind=engine)
    # ChromaDB embedding collections init
    vector_store.init_chroma_collections()
    
    logger.info("Orchestrator CLI Chat Mode Initialized.")
    print("Welcome to FitFinder Agent CLI! Type 'exit' or 'quit' to end.")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
