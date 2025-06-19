"""
Configuration management for FitFinder Chainlit application
"""
import os
import secrets
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration management for Chainlit-only deployment"""
    
    @classmethod
    def get_data_path_env(cls) -> str:
        """Get DATA_PATH environment variable with dynamic loading"""
        return os.getenv("DATA_PATH", ".")
    
    # Data Storage Configuration
    # In production, this should point to a persistent volume (e.g., /mnt/fitfinder)
    # In development, this defaults to the current directory
    @property
    def DATA_PATH(self) -> str:
        return self.get_data_path_env()
    
    # Chainlit Authentication
    CHAINLIT_AUTH_SECRET: str = os.getenv("CHAINLIT_AUTH_SECRET", secrets.token_urlsafe(32))
    CHAINLIT_ADMIN_USERNAME: str = os.getenv("CHAINLIT_ADMIN_USERNAME", "admin")
    CHAINLIT_ADMIN_PASSWORD: str = os.getenv("CHAINLIT_ADMIN_PASSWORD", "fitfinder2024!")
    
    # Database - now uses configurable data path
    @property
    def DATABASE_URL(self) -> str:
        return os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(self.get_data_path_env(), 'fitfinder.db').replace(os.sep, '/')}")
    
    # AI/ML Service APIs
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Optional: Langfuse tracing (if enabled)
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    
    # Chainlit server settings
    CHAINLIT_HOST: str = os.getenv("CHAINLIT_HOST", "0.0.0.0")
    CHAINLIT_PORT: int = int(os.getenv("CHAINLIT_PORT", 8001))

    @classmethod
    def get_data_path(cls, *paths: str) -> str:
        """
        Get a path relative to the configured data directory.
        Ensures the directory exists.
        
        Args:
            *paths: Path components to join with the data path
            
        Returns:
            Absolute path to the requested location
        """
        full_path = os.path.join(cls.get_data_path_env(), *paths)
        os.makedirs(os.path.dirname(full_path) if paths else full_path, exist_ok=True)
        return full_path

    @classmethod
    def get_sqlite_path(cls) -> str:
        """Get the SQLite database file path"""
        return cls.get_data_path("fitfinder.db")
    
    @classmethod
    def get_chroma_path(cls) -> str:
        """Get the ChromaDB storage directory path"""
        return cls.get_data_path("chroma_db")
    
    @classmethod
    def get_images_path(cls, *paths: str) -> str:
        """Get the images storage directory path"""
        return cls.get_data_path("images", *paths)

# Create config instance
config = Config() 