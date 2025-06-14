import chainlit as cl
import logging
import os
from backend.agent.agent_core import stream_graph_updates
from backend.db.models import Base, engine
from backend.db import vector_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database and vector store
Base.metadata.create_all(bind=engine)
vector_store.init_chroma_collections()

@cl.on_chat_start
async def start():
    """Called when a new chat session starts"""
    await cl.Message(
        content="👋 **Welcome to FitFinder!**\n\nI'm your AI fashion assistant. I can help you:\n\n"
                "• **Add clothing items** to your wardrobe\n"
                "• **Find clothing items** based on your preferences\n" 
                "• **Create and suggest** complete outfits\n"
                "• **Answer questions** about fashion and styling\n\n"
                "What would you like to do today? 🌟"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages"""
    try:
        logger.info(f"Received message: {message.content}")
        
        # Show typing indicator with step
        async with cl.Step(name="🤔 Thinking...") as step:
            # Use the existing agent functionality
            response = stream_graph_updates(message.content)
            
            if response:
                step.output = "Agent processed successfully ✅"
                # Send the response back to the user
                await cl.Message(content=response).send()
            else:
                step.output = "No response generated ⚠️"
                await cl.Message(
                    content="I'm sorry, I couldn't process your request. Please try again or rephrase your question."
                ).send()
                
    except Exception as e:
        logger.error(f"Error in chainlit message handler: {e}")
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