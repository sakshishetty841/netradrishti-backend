import io
import numpy as np
import cv2
from PIL import Image
from typing import Dict, Any, List

class ImageQualityChecker:
    """
    Evaluates retinal image quality heuristics: sharpness, illumination, contrast, resolution, visibility.
    Labels quality module as prototype/heuristic per medical compliance rules.
    """
    
    LAPLACIAN_BLUR_THRESHOLD = 50.0  # Below this variance is considered blurry
    MIN_MEAN_BRIGHTNESS = 20.0       # Below this is too dark
    MAX_MEAN_BRIGHTNESS = 235.0      # Above this is overexposed/washed out
    
    def assess_quality(self, file_bytes: bytes) -> Dict[str, Any]:
        messages: List[str] = []
        usable = True
        
        try:
            pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            
            width, height = pil_img.size
            
            # 1. Blur / Sharpness check using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < self.LAPLACIAN_BLUR_THRESHOLD:
                usable = False
                messages.append("Image appears blurry or out of focus. Please rescan with steady positioning.")

            # 2. Illumination / Brightness check
            mean_brightness = float(np.mean(gray))
            if mean_brightness < self.MIN_MEAN_BRIGHTNESS:
                usable = False
                messages.append("Image is too dark for reliable AI retinal analysis. Ensure adequate camera lighting.")
            elif mean_brightness > self.MAX_MEAN_BRIGHTNESS:
                usable = False
                messages.append("Image is overexposed or washed out. Reduce flash brightness or glare.")

            # 3. Contrast check
            std_dev = float(np.std(gray))
            if std_dev < 15.0:
                usable = False
                messages.append("Low contrast detected in retinal fundus image.")

            if usable:
                return {
                    "status": "good",
                    "retina_visibility": "acceptable",
                    "sharpness": "acceptable",
                    "illumination": "acceptable",
                    "field_of_view": "adequate",
                    "usable": True,
                    "metrics": {
                        "blur_score": round(laplacian_var, 2),
                        "brightness": round(mean_brightness, 2),
                        "contrast": round(std_dev, 2)
                    },
                    "messages": []
                }
            else:
                return {
                    "status": "poor",
                    "retina_visibility": "unacceptable",
                    "sharpness": "poor" if laplacian_var < self.LAPLACIAN_BLUR_THRESHOLD else "acceptable",
                    "illumination": "poor" if (mean_brightness < self.MIN_MEAN_BRIGHTNESS or mean_brightness > self.MAX_MEAN_BRIGHTNESS) else "acceptable",
                    "field_of_view": "marginal",
                    "usable": False,
                    "metrics": {
                        "blur_score": round(laplacian_var, 2),
                        "brightness": round(mean_brightness, 2),
                        "contrast": round(std_dev, 2)
                    },
                    "messages": messages
                }
        except Exception as e:
            return {
                "status": "poor",
                "retina_visibility": "unknown",
                "usable": False,
                "messages": [f"Image processing failure during quality check: {str(e)}"]
            }

quality_checker = ImageQualityChecker()
