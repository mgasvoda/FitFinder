import os
import shutil

# Import the config for configurable data paths
from backend.config import config

# Paths using configurable data directory - functions to get paths dynamically
def get_sqlite_db_path():
    """Get SQLite database path dynamically"""
    return config.get_sqlite_path()

def get_chroma_db_path():
    """Get ChromaDB path dynamically"""
    return config.get_chroma_path()

def get_images_path():
    """Get images path dynamically"""
    return config.get_images_path()

def reset_backend_data():
    """
    Deletes the SQLite database file, ChromaDB persistent directory, and image repository.
    Recreates empty images and chroma_db directories.
    """
    # Get paths dynamically
    sqlite_db_path = get_sqlite_db_path()
    chroma_db_path = get_chroma_db_path()
    images_path = get_images_path()
    
    # Remove SQLite DB
    if os.path.exists(sqlite_db_path):
        os.remove(sqlite_db_path)
        print(f"Deleted SQLite DB: {sqlite_db_path}")
    else:
        print(f"SQLite DB not found: {sqlite_db_path}")

    # Remove ChromaDB directory
    if os.path.exists(chroma_db_path):
        shutil.rmtree(chroma_db_path)
        print(f"Deleted ChromaDB directory: {chroma_db_path}")
    else:
        print(f"ChromaDB directory not found: {chroma_db_path}")

    # Remove images directory
    if os.path.exists(images_path):
        shutil.rmtree(images_path)
        print(f"Deleted images directory: {images_path}")
    else:
        print(f"Images directory not found: {images_path}")

    # Recreate empty directories using the config methods
    # These methods automatically create directories as needed
    config.get_chroma_path()
    config.get_images_path()
    print("Recreated chroma_db and images directories.")

if __name__ == "__main__":
    reset_backend_data()
