import os
import shutil

# Paths (relative to the backend directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DB_PATH = os.path.join(BASE_DIR, 'fitfinder.db')
CHROMA_DB_PATH = os.path.join(BASE_DIR, 'chroma_db')
IMAGES_PATH = os.path.join(BASE_DIR, 'images')

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

    # Recreate empty directories
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    os.makedirs(IMAGES_PATH, exist_ok=True)
    print("Recreated chroma_db and images directories.")

if __name__ == "__main__":
    reset_backend_data()
