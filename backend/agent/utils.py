import logging
from typing import Dict, Any, Optional

# Import Langchain message types for isinstance checks
try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, ChatMessage, BaseMessage
except ImportError:
    # Fallback if langchain_core.messages is not available or structure changes
    # This is less robust and assumes structure if direct imports fail.
    AIMessage = type('AIMessage', (object,), {})
    HumanMessage = type('HumanMessage', (object,), {})
    SystemMessage = type('SystemMessage', (object,), {})
    ToolMessage = type('ToolMessage', (object,), {})
    ChatMessage = type('ChatMessage', (object,), {})
    BaseMessage = type('BaseMessage', (object,), {})


logger = logging.getLogger(__name__)

def get_message_details(message: Any) -> Optional[Dict[str, str]]:
    """
    Extracts a standardized role and content from various message formats.

    Args:
        message: The message object (can be a Langchain Pydantic model or a dict).

    Returns:
        A dictionary with "role" and "content" keys, or None if not recognized.
        Roles are standardized to: "assistant", "user", "system", "tool".
    """
    role: Optional[str] = None
    content: Optional[str] = None

    try:
        if isinstance(message, dict):
            role_from_dict = message.get("role")
            if role_from_dict == "ai" or role_from_dict == "assistant":
                role = "assistant"
            elif role_from_dict == "human" or role_from_dict == "user":
                role = "user"
            elif role_from_dict in ["system", "tool"]:
                role = role_from_dict
            content = message.get("content", "")
        
        elif isinstance(message, AIMessage):
            role = "assistant"
            content = message.content
        elif isinstance(message, HumanMessage):
            role = "user"
            content = message.content
        elif isinstance(message, SystemMessage):
            role = "system"
            content = message.content
        elif isinstance(message, ToolMessage):
            role = "tool"
            content = message.content # ToolMessage content can be complex, ensure it's stringified if needed by caller
        elif isinstance(message, ChatMessage): # General ChatMessage, has 'role' attribute
            role_from_chat = message.role
            if role_from_chat == "ai":
                role = "assistant"
            elif role_from_chat == "human":
                role = "user"
            else:
                role = role_from_chat # system, tool, or other custom roles
            content = message.content
        elif isinstance(message, BaseMessage): # Fallback for other BaseMessage types
            # Try to infer from 'type' attribute if 'role' is not standard
            if hasattr(message, 'type'):
                if message.type == 'ai': role = 'assistant'
                elif message.type == 'human': role = 'user'
                elif message.type == 'system': role = 'system'
                elif message.type == 'tool': role = 'tool'
            if hasattr(message, 'content'):
                 content = str(message.content)
        elif hasattr(message, 'role') and hasattr(message, 'content'): # Generic object check
            role_attr = getattr(message, 'role')
            if role_attr == "ai": role = "assistant"
            elif role_attr == "human": role = "user"
            else: role = role_attr
            content = str(getattr(message, 'content'))
        elif hasattr(message, 'type') and hasattr(message, 'content'): # e.g. AIMessageChunk sometimes
            type_attr = getattr(message, 'type')
            if type_attr == 'ai': role = 'assistant'
            elif type_attr == 'human': role = 'user'
            elif type_attr == 'system': role = 'system'
            elif type_attr == 'tool': role = 'tool'
            content = str(getattr(message, 'content'))

        if role and content is not None:
            # Ensure content is a string
            if not isinstance(content, str):
                content = str(content)
            return {"role": role, "content": content}
        else:
            # logger.warning(f"Unrecognized message format or missing role/content: {type(message)}")
            return None # Or raise an error, or return a default dict
            
    except AttributeError as e:
        logger.error(f"AttributeError processing message: {message}, Error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing message: {message}, Error: {e}", exc_info=True)
        return None

# Placeholder for other shared functions
