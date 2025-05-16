from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.db.models import get_db
from backend.agent.schemas import ChatRequest, ChatResponse
from langfuse.callback import CallbackHandler
from typing import TypedDict, Annotated
from langchain_core.messages import add_messages

from tools import get_clothing_item, create_clothing_item, get_outfit, create_outfit

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

# Agent definition

class State (TypedDict):
    messages: Annotated[list, add_messages]

def create_agent(): 
    checkpointer = InMemorySaver() 

    graph_builder = StateGraph(State)

    tools = [get_clothing_item, create_clothing_item, get_outfit, create_outfit]
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
    graph = graph_builder.compile()
    return graph

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

        agent = create_agent()

        # Prepare initial state for the agent
        state = {
            "messages": [{"role": "user", "content": req.prompt}]
        }

        response = agent.invoke(state, config={"callbacks": [langfuse_handler]})

        # Log the response
        logger.info(f"Agent response: {response}")

        # Return the response
        return ChatResponse(response_text=response)

    except Exception as e:
        logger.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")
