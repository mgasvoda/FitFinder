"""
Configuration management for FitFinder Chainlit application
"""
import os
import secrets

class Config:
    """Centralized configuration management for Chainlit-only deployment"""
    
    # Chainlit Authentication
    CHAINLIT_AUTH_SECRET: str = os.getenv("CHAINLIT_AUTH_SECRET", secrets.token_urlsafe(32))
    CHAINLIT_ADMIN_USERNAME: str = os.getenv("CHAINLIT_ADMIN_USERNAME", "admin")
    CHAINLIT_ADMIN_PASSWORD: str = os.getenv("CHAINLIT_ADMIN_PASSWORD", "fitfinder2024!")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fitfinder.db")
    
    # AI/ML Service APIs
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Optional: Langfuse tracing (if enabled)
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    
    # Chainlit server settings
    CHAINLIT_HOST: str = os.getenv("CHAINLIT_HOST", "0.0.0.0")
    CHAINLIT_PORT: int = int(os.getenv("CHAINLIT_PORT", 8001))

# Create config instance
config = Config() 