"""
Agent orchestration module for the FitFinder application.
This module handles the LangGraph graph construction and execution for the main orchestrator.
"""

import os
import logging
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from typing import Dict, Any

from backend.agent.steps import State
from backend.agent.clothing_agent import create_clothing_item_agent_graph
from backend.agent.outfit_agent import create_outfit_designer_agent_graph, OutfitAgentState
from backend.agent.utils import get_message_details # Import the new utility

load_dotenv()

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def route_to_agent(state: State) -> str:
    last_message = state['messages'][-1]
    content = ""
    if hasattr(last_message, 'content'): 
        content = last_message.content.lower()
    elif isinstance(last_message, dict) and 'content' in last_message: 
        content = str(last_message['content']).lower()
    
    logger.info(f"ORCHESTRATOR: Routing based on content: '{content[:50]}...' ")
    if "outfit" in content or "wear" in content or "style" in content or "dress me" in content:
        logger.info("Routing to outfit_designer_agent")
        return "outfit_designer_agent"
    else:
        logger.info("Routing to clothing_item_agent")
        return "clothing_item_agent"

def call_clothing_item_agent_node(state: State, agent_executor, llm_unused) -> Dict[str, Any]: 
    logger.info("ORCHESTRATOR: Calling clothing_item_agent")
    sub_agent_state = {'messages': state.get('messages', [])} 
    result_state = agent_executor.invoke(sub_agent_state)
    return {"messages": result_state.get("messages", state['messages'])}

def call_outfit_designer_agent_node(state: State, agent_executor, llm_unused) -> Dict[str, Any]: 
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
    result_outfit_state = agent_executor.invoke(initial_outfit_state)
    return {"messages": result_outfit_state.get("messages", state['messages'])}

def create_main_orchestrator_graph(clothing_item_agent_instance, outfit_designer_agent_instance, llm_for_orchestrator_chat_unused):
    graph_builder = StateGraph(State) 

    graph_builder.add_node("orchestrator_chat_router", lambda s: {"messages": s['messages']}) 

    graph_builder.add_node(
        "clothing_item_agent_node", 
        lambda s: call_clothing_item_agent_node(s, clothing_item_agent_instance, None)
    )
    graph_builder.add_node(
        "outfit_designer_agent_node",
        lambda s: call_outfit_designer_agent_node(s, outfit_designer_agent_instance, None)
    )

    graph_builder.add_edge(START, "orchestrator_chat_router")
    
    graph_builder.add_conditional_edges(
        "orchestrator_chat_router",
        route_to_agent,
        {
            "clothing_item_agent": "clothing_item_agent_node",
            "outfit_designer_agent": "outfit_designer_agent_node"
        }
    )

    graph_builder.add_edge("clothing_item_agent_node", END) 
    graph_builder.add_edge("outfit_designer_agent_node", END)
    
    logger.info("Main Orchestrator graph created successfully.")
    return graph_builder.compile()


llm_instance = ChatAnthropic(
    model="claude-3-haiku-20240307", 
    anthropic_api_key=ANTHROPIC_API_KEY,
    max_tokens=2048 
)

clothing_item_agent = create_clothing_item_agent_graph(llm_instance)
outfit_designer_agent = create_outfit_designer_agent_graph(llm_instance)

main_orchestrator = create_main_orchestrator_graph(clothing_item_agent, outfit_designer_agent, llm_instance)


def run_agent(state: dict) -> dict:
    logger.info(f"MAIN ORCHESTRATOR: Running with initial state keys: {list(state.keys()) if isinstance(state, dict) else 'N/A'}")
    
    current_state_messages = []
    if isinstance(state, dict) and 'messages' in state:
        current_state_messages = state['messages']
    elif isinstance(state, list): 
        current_state_messages = state
    else:
        logger.warning("Initial state for run_agent is not a dict with 'messages' or a list of messages. Using empty list.")

    initial_graph_state = State(messages=current_state_messages)
    
    try:
        result_state = main_orchestrator.invoke(initial_graph_state)
        logger.info(f"MAIN ORCHESTRATOR: Execution completed. Result keys: {list(result_state.keys()) if isinstance(result_state, dict) else 'N/A'}")
        return result_state 
    except Exception as e:
        logger.error(f"Error running main orchestrator: {e}", exc_info=True)
        error_message = {"role": "assistant", "content": f"Orchestrator Error: {e}"}
        return {"messages": current_state_messages + [error_message]}

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.info("Orchestrator CLI Chat Mode Initialized.")
    print("Welcome to FitFinder Agent CLI! Type 'exit' or 'quit' to end.")

    chat_history = []

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting chat.")
            break

        if not user_input.strip():
            continue

        # Append user message to history
        chat_history.append({"role": "user", "content": user_input})

        # Prepare state for the agent
        # The run_agent function expects a dict with a 'messages' key
        current_run_state = {"messages": list(chat_history)} # Pass a copy

        try:
            # Call the agent
            result_state = run_agent(current_run_state)
            
            # Extract the last assistant message as the response
            assistant_response = "No response from assistant."
            if result_state and isinstance(result_state.get("messages"), list):
                all_agent_messages = result_state["messages"]
                start_index_for_new_messages = len(chat_history) 
                
                new_messages_from_agent_run = all_agent_messages[start_index_for_new_messages:]

                assistant_message_printed = False
                for msg_obj in new_messages_from_agent_run:
                    chat_history.append(msg_obj) # Add raw message object to history for agent's context
                    details = get_message_details(msg_obj)
                    if details:
                        if details["role"] == "assistant":
                            assistant_response = details["content"]
                            print(f"FitFinder: {assistant_response}")
                            assistant_message_printed = True
                        # elif details["role"] == "user": # Agent should not be adding user messages
                            # logger.warning("Agent added a user message in its response.")
                        # else: # system, tool messages - not typically printed in simple CLI
                            # logger.info(f"Agent internal message ({details['role']}): {details['content'][:100]}")
                    else:
                        logger.warning(f"CLI: Could not parse message from agent: {msg_obj}")
                
                if not assistant_message_printed and new_messages_from_agent_run:
                    # If no specific assistant message was found among new ones (e.g. only tool calls)
                    # but we want to show *something* if the agent did respond.
                    # This might need refinement based on how tool calls / intermediate steps are handled.
                    # For now, if no direct assistant utterance, stick to the default or last known good.
                    # Or, attempt to find last assistant message in the *entire* updated history if appropriate.
                    pass # Keep default "No response..." or let it be updated if a later message is assistant type

                # Fallback: if no new assistant messages were explicitly printed, try to find the *very last* assistant message in all_agent_messages
                if not assistant_message_printed:
                    for msg_obj in reversed(all_agent_messages):
                        details = get_message_details(msg_obj)
                        if details and details["role"] == "assistant":
                            assistant_response = details["content"]
                            print(f"FitFinder: {assistant_response}")
                            assistant_message_printed = True
                            break
                    if not assistant_message_printed:
                         print(f"FitFinder: {assistant_response}") # Print default if still no assistant message

            else:
                print(f"FitFinder: Error or unexpected response format from agent: {result_state}")

        except Exception as e:
            logger.error(f"Error during agent execution in CLI: {e}", exc_info=True)
            print(f"FitFinder: An error occurred: {e}")
            # Optionally, add error to chat_history as an assistant message
            chat_history.append({"role": "assistant", "content": f"Error: {e}"})
