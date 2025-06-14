"""
Chainlit Authentication Module
Provides user/password authentication for the Chainlit interface
"""
import chainlit as cl
from typing import Optional
import hashlib
import secrets
from backend.config import config

# Simple user database (in production, use a real database)
USERS = {
    config.CHAINLIT_ADMIN_USERNAME: {
        "password_hash": hashlib.sha256(config.CHAINLIT_ADMIN_PASSWORD.encode()).hexdigest(),
        "role": "admin",
        "name": "Administrator"
    }
}

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == password_hash

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password
    Returns user info if successful, None otherwise
    """
    if username not in USERS:
        return None
    
    user = USERS[username]
    if not verify_password(password, user["password_hash"]):
        return None
    
    return {
        "username": username,
        "role": user["role"],
        "name": user["name"]
    }

def add_user(username: str, password: str, name: str = None, role: str = "user") -> bool:
    """
    Add a new user to the system
    Returns True if successful, False if user already exists
    """
    if username in USERS:
        return False
    
    USERS[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "name": name or username
    }
    return True

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    Chainlit authentication callback
    Called when a user tries to log in
    """
    user_info = authenticate_user(username, password)
    if user_info:
        return cl.User(
            identifier=user_info["username"],
            metadata={
                "role": user_info["role"], 
                "name": user_info["name"]
            }
        )
    return None

# Optional: Session management
@cl.on_chat_start
async def on_chat_start():
    """Called when a new chat session starts (after authentication)"""
    user = cl.user_session.get("user")
    if user:
        # User is authenticated
        welcome_msg = f"👋 **Welcome, {user.metadata.get('name', user.identifier)}!**\n\n"
        
        if user.metadata.get('role') == 'admin':
            welcome_msg += "🔧 **Admin Access Granted**\n\n"
        
        welcome_msg += (
            "I'm your AI fashion assistant. I can help you:\n\n"
            "• **Add clothing items** to your wardrobe\n"
            "• **Find clothing items** based on your preferences\n" 
            "• **Create and suggest** complete outfits\n"
            "• **Answer questions** about fashion and styling\n\n"
            "What would you like to do today? 🌟"
        )
        
        await cl.Message(content=welcome_msg).send()
    else:
        # This shouldn't happen if auth is working correctly
        await cl.Message(
            content="⚠️ Authentication error. Please refresh and try again."
        ).send()

def get_current_user() -> Optional[cl.User]:
    """Get the currently authenticated user"""
    return cl.user_session.get("user")

def require_admin():
    """Decorator/helper to check if current user is admin"""
    user = get_current_user()
    if not user or user.metadata.get('role') != 'admin':
        raise Exception("Admin access required")
    return user 