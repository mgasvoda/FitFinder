import os
import shutil

# Import the config for configurable data paths
from backend.config import config

# Paths using configurable data directory
SQLITE_DB_PATH = config.get_sqlite_path()
CHROMA_DB_PATH = config.get_chroma_path()
IMAGES_PATH = config.get_images_path()

def reset_backend_data():
    """
    Deletes the SQLite database file, ChromaDB persistent directory, and image repository.
    Recreates empty images and chroma_db directories.
    """
    # Remove SQLite DB
    if os.path.exists(SQLITE_DB_PATH):
        os.remove(SQLITE_DB_PATH)
        print(f"Deleted SQLite DB: {SQLITE_DB_PATH}")
    else:
        print(f"SQLite DB not found: {SQLITE_DB_PATH}")

    # Remove ChromaDB directory
    if os.path.exists(CHROMA_DB_PATH):
        shutil.rmtree(CHROMA_DB_PATH)
        print(f"Deleted ChromaDB directory: {CHROMA_DB_PATH}")
    else:
        print(f"ChromaDB directory not found: {CHROMA_DB_PATH}")

    # Remove images directory
    if os.path.exists(IMAGES_PATH):
        shutil.rmtree(IMAGES_PATH)
        print(f"Deleted images directory: {IMAGES_PATH}")
    else:
        print(f"Images directory not found: {IMAGES_PATH}")

    # Recreate empty directories using the config methods
    # These methods automatically create directories as needed
    config.get_chroma_path()
    config.get_images_path()
    print("Recreated chroma_db and images directories.")

if __name__ == "__main__":
    reset_backend_data()
