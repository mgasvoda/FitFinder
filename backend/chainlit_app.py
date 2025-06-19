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

# Import image processing functionality
from backend.services.chainlit_image_processor import process_chainlit_image, get_image_info

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
        
        # Check if message contains file attachments (images)
        if message.elements:
            logger.info(f"Found {len(message.elements)} attachments")
            
            # Show typing indicator with step
            async with cl.Step(name="📸 Processing and compressing image...") as step:
                for element in message.elements:
                    if hasattr(element, 'path') and element.path:
                        logger.info(f"Processing image: {element.path}")
                        try:
                            # Process and compress the uploaded image
                            image_url, item_id, size_kb = process_chainlit_image(element, compress=True)
                            
                            # Get image info for user feedback
                            image_info = get_image_info(element.path)
                            original_size = image_info.get('size_kb', 0) if image_info.get('exists') else 0
                            
                            step_msg = f"Image compressed: {original_size}KB → {size_kb}KB ✅"
                            step.output = step_msg
                            
                            # Use the agent functionality to create clothing item from compressed image
                            user_input = f"Please create a clothing item from this compressed image: {image_url}"
                            if message.content.strip():
                                user_input += f" User notes: {message.content}"
                            
                            response = stream_graph_updates(user_input)
                            
                            if response and response.strip():
                                # Add compression info to the response
                                compression_info = f"\n\n💾 *Image processed: {size_kb}KB (compressed from {original_size}KB)*"
                                full_response = response + compression_info
                                await cl.Message(content=full_response).send()
                            else:
                                step.output = "Failed to process image ⚠️"
                                await cl.Message(
                                    content="I'm sorry, I couldn't process your image. Please try again."
                                ).send()
                                
                        except Exception as e:
                            logger.error(f"Error processing image: {e}")
                            step.output = f"Error processing image: {str(e)}"
                            await cl.Message(
                                content="⚠️ I encountered an error processing your image. Please try again."
                            ).send()
        else:
            # Handle text-only messages
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