from abc import ABC, abstractmethod
from typing import Dict, Any

class RetinalScreeningModel(ABC):
    @abstractmethod
    def predict(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Takes raw image bytes, runs preprocessing and model inference.
        Returns dictionary containing:
          - grade: "No DR", "Mild", "Moderate", "Severe", or "Proliferative"
          - confidence: float between 0.0 and 1.0
          - findings: list of strings (e.g. ["Microaneurysms detected", "Soft exudates"])
          - model_version: string tag
        """
        pass
