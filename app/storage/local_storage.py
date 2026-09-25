import os
import uuid
from app.core.config import settings
from app.storage.storage_interface import StorageInterface

class LocalStorage(StorageInterface):
    def __init__(self, base_dir: str = None):
        self.base_dir = os.path.abspath(base_dir or settings.MEDIA_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, file_bytes: bytes, filename: str, subfolder: str = "images") -> str:
        folder_path = os.path.join(self.base_dir, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        relative_path = os.path.join(subfolder, unique_name)
        full_path = os.path.join(self.base_dir, relative_path)
        
        with open(full_path, "wb") as f:
            f.write(file_bytes)
            
        return f"/media/{relative_path.replace(os.sep, '/')}"

    def get_file_path(self, relative_path: str) -> str:
        clean_path = relative_path.replace("/media/", "").lstrip("/")
        return os.path.join(self.base_dir, clean_path)

    def delete_file(self, relative_path: str) -> bool:
        full_path = self.get_file_path(relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

storage_service = LocalStorage()
