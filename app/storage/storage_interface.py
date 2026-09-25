from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageInterface(ABC):
    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str, subfolder: str = "images") -> str:
        """Save file bytes and return public/relative URL or storage path"""
        pass
        
    @abstractmethod
    def get_file_path(self, relative_path: str) -> str:
        """Return absolute path or access location"""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Delete stored file"""
        pass
