import io
import os
import cv2
import numpy as np
from PIL import Image
import torch
import torch.nn.functional as F

from app.storage.local_storage import storage_service
from app.core.config import settings

class GradCAM:
    """
    PyTorch Grad-CAM implementation for visual feature attribution in CNN models.
    Registers forward & backward hooks on target layer to extract feature activation gradients.
    """
    def __init__(self, model: torch.nn.Module, target_layer_name: str = None):
        self.model = model
        self.model.eval()
        self.gradients = None
        self.activations = None

        target_layer = self._find_target_layer(target_layer_name)
        if target_layer is not None:
            target_layer.register_forward_hook(self._save_activation)
            target_layer.register_full_backward_hook(self._save_gradient)

    def _find_target_layer(self, layer_name: str = None):
        if layer_name:
            for name, module in self.model.named_modules():
                if name == layer_name:
                    return module
        # Default target layer heuristics for EfficientNet or ResNet
        if hasattr(self.model, "features"): # EfficientNet
            return self.model.features[-1]
        elif hasattr(self.model, "layer4"): # ResNet
            return self.model.layer4[-1]
        else:
            # Fallback to last conv module
            for module in reversed(list(self.model.modules())):
                if isinstance(module, torch.nn.Conv2d):
                    return module
        return None

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate_heatmap(self, input_tensor: torch.Tensor, target_class: int = None) -> np.ndarray:
        self.model.zero_grad()
        output = self.model(input_tensor)

        if target_class is None:
            target_class = output.argmax(dim=1).item()

        score = output[0, target_class]
        score.backward()

        if self.gradients is None or self.activations is None:
            # Return neutral fallback heatmap if hooks failed
            return np.ones((224, 224), dtype=np.float32) * 0.5

        gradients = self.gradients[0]
        activations = self.activations[0]

        weights = torch.mean(gradients, dim=(1, 2), keepdim=True)
        cam = torch.sum(weights * activations, dim=0)
        cam = F.relu(cam)

        cam_np = cam.cpu().numpy()
        if cam_np.max() > 0:
            cam_np = (cam_np - cam_np.min()) / (cam_np.max() - cam_np.min())

        return cam_np

def generate_gradcam_overlay(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    original_bytes: bytes,
    target_class: int = None
) -> dict:
    """
    Computes Grad-CAM map, overlays on raw fundus image bytes, saves file, and returns heatmap URL & explanation.
    """
    try:
        pil_img = Image.open(io.BytesIO(original_bytes)).convert("RGB")
        orig_np = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        h, w, _ = orig_np.shape

        cam_engine = GradCAM(model)
        cam_map = cam_engine.generate_heatmap(input_tensor, target_class=target_class)

        # Resize heatmap to match original image dimensions
        cam_resized = cv2.resize(cam_map, (w, h))
        cam_norm = np.uint8(255 * cam_resized)

        heatmap_color = cv2.applyColorMap(cam_norm, cv2.COLORMAP_JET)

        # Alpha blend original image (70%) with Grad-CAM heatmap (30%)
        overlay = cv2.addWeighted(orig_np, 0.7, heatmap_color, 0.3, 0)

        success, encoded = cv2.imencode(".png", overlay)
        if not success:
            raise ValueError("Failed to encode Grad-CAM image overlay")

        heatmap_bytes = encoded.tobytes()
        heatmap_url = storage_service.save_file(heatmap_bytes, "gradcam_heatmap.png", subfolder="heatmaps")

        explanation_text = (
            "Grad-CAM visual attribution map. Highlighted warm regions (red/orange) show "
            "retinal spatial features that contributed to the model's DR severity prediction. "
            "Note: This is an explainability aid, not proof of a specific diagnostic lesion."
        )

        return {
            "heatmap_url": heatmap_url,
            "explanation": explanation_text,
            "explainability_version": settings.EXPLAINABILITY_VERSION
        }
    except Exception as e:
        return {
            "heatmap_url": "/media/heatmaps/default_heatmap.png",
            "explanation": f"Grad-CAM generation fallback: {str(e)}",
            "explainability_version": settings.EXPLAINABILITY_VERSION
        }
