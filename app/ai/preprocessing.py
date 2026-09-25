import io
import numpy as np
import cv2
from PIL import Image

def preprocess_fundus_image(file_bytes: bytes, target_size=(512, 512)) -> np.ndarray:
    """
    Standardizes fundus image for AI inference:
    1. Loads PIL image in RGB mode
    2. Crops aspect ratio / resizes to target_size
    3. Performs CLAHE (Contrast Limited Adaptive Histogram Equalization) on green channel
    4. Returns normalized float32 array (0.0 to 1.0)
    """
    pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    resized = cv2.resize(cv_img, target_size)
    
    # Enhance green channel (highest contrast for retinal vessels and lesions)
    b, g, r = cv2.split(resized)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    g_enhanced = clahe.apply(g)
    merged = cv2.merge([b, g_enhanced, r])
    
    normalized = merged.astype(np.float32) / 255.0
    return normalized
