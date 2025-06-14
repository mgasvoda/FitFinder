"""
FitFinder Chainlit Chat Interface
Standalone chat application with user authentication
"""

import chainlit as cl
import logging
import os
from backend.agent.agent_core import stream_graph_updates, initialize_agent_resources

# Import authentication module - this registers the auth callbacks
import backend.auth.chainlit_auth
from backend.auth.chainlit_auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database and vector store on app startup
logger.info("Initializing FitFinder Chainlit Chat Interface...")
initialize_agent_resources()
logger.info("FitFinder ready to chat!")

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages"""
    try:
        # Get current authenticated user
        user = get_current_user()
        user_info = f"User: {user.identifier}" if user else "Anonymous"
        
        logger.info(f"Received message from {user_info}: {message.content}")
        
        # Show typing indicator with step
        async with cl.Step(name="🤔 Thinking...") as step:
            # Use the agent functionality directly
            response = stream_graph_updates(message.content)
            
            if response and response.strip():
                step.output = "Agent processed successfully ✅"
                await cl.Message(content=response).send()
            else:
                step.output = "No response generated ⚠️"
                await cl.Message(
                    content="I'm sorry, I couldn't process your request. Please try again or rephrase your question."
                ).send()
                
    except Exception as e:
        user = get_current_user()
        user_info = f"User: {user.identifier}" if user else "Anonymous"
        logger.error(f"Error in chainlit message handler for {user_info}: {e}")
        await cl.Message(
            content="⚠️ I encountered an error processing your request. Please try again in a moment."
        ).send()

if __name__ == "__main__":
    import socket
    
    # Get local IP for logging
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        logger.info(f"Local IP address: {local_ip}")
        logger.info(f"Access from mobile: http://{local_ip}:8001")
    except Exception as e:
        logger.warning(f"Could not determine local IP: {e}")
    
    logger.info("Starting FitFinder Chainlit Chat Interface...")
    # Run with: chainlit run backend/chainlit_app.py --port 8001 