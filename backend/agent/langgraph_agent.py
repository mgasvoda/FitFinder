from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_anthropic import ChatAnthropic
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage

# from backend.agent.tools.outfit_searcher import search_outfits, search_clothing_items
from backend.agent.tools.image_captioner import caption_image
from backend.agent.tools.image_storage import store_image
from backend.services.embedding_service import get_text_embedding
from backend.db.models import SessionLocal
from backend.db import crud

from dotenv import load_dotenv
from typing import Optional
from typing import TypedDict, Annotated
import numpy as np

import uuid
import os
import json


load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    item_id: Optional[str]
    image_url: Optional[str]
    caption: Optional[str]
    embedding: Optional[np.ndarray]


class CaptionToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                    args=tool_call["args"]
                )
            )
        
        #hardcoding caption update temporarily for testing
        return {"messages": outputs, "caption": tool_result, "image_url": tool_call["args"]["image_url"]}

def store_image_step(state: State):
    # expects: state['image_file']
    return store_image(state["image_file"])


def embed_step(state: State):
    print("Embedding...")
    # expects: state['caption'], state['image_url']
    # return get_multimodal_embedding(text=state["caption"], image=state["image_url"])
    return {'embedding': get_text_embedding(text=state["caption"])}


def persist_db_step(state: State):
    print("Persisting to DB via CRUD service...")
    db = SessionLocal()

    if "item_id" not in state.keys():
        item_id = str(uuid.uuid4())
    else:
        item_id = state["item_id"]

    crud.create_clothing_item(
        db=db,
        id=item_id,
        description=state["caption"],
        image_url=state["image_url"],
        embedding=state["embedding"]
    )
    return {"item_id": item_id}


# Instantiate the LangGraph agent with anthropic model
llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    anthropic_api_key=ANTHROPIC_API_KEY
)

tools = [caption_image]

# --- Build StateGraph for sequential workflow ---
graph_builder = StateGraph(State)
graph_builder.add_node("chat", lambda state: {"messages":llm.bind_tools(tools).invoke(state['messages'])})
# graph_builder.add_node("store_image", store_image_step)
# graph_builder.add_node("caption", caption_step)
graph_builder.add_node("tools", CaptionToolNode(tools))
graph_builder.add_node("embed", embed_step)
graph_builder.add_node("persist_db", persist_db_step)

# Add edges for sequential execution
graph_builder.add_edge(START, "chat")
graph_builder.add_edge("tools", "chat") 
graph_builder.add_conditional_edges(
    "chat", tools_condition
)
# graph_builder.add_edge("chat", "store_image")
# graph_builder.add_edge("store_image", "caption")
# graph_builder.add_edge("caption", "embed")
graph_builder.add_edge('tools', 'embed')
graph_builder.add_edge("embed", "persist_db")
graph_builder.add_edge('persist_db', 'chat')
graph_builder.add_edge("chat", END)

# Compile the graph to an executable tool
graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        print(event)
        # for value in event.values():
        #     try:
        #         print("Assistant:", value["messages"].content, flush=True)
        #     except AttributeError:
        #         print("Assistant:", value["messages"][-1]['text'], flush=True)

if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
