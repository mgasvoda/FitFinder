# Placeholder for image storage tool
from fastapi import UploadFile
import os
import uuid

def store_image(image: UploadFile):
    # Save image to local filesystem
    ext = os.path.splitext(image.filename)[1]
    item_id = str(uuid.uuid4())
    image_path = f"images/{item_id}{ext}"
    with open(image_path, "wb") as f:
        f.write(image.file.read())
    return image_path, item_id
