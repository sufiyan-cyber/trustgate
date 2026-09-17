"""Computer vision utilities for image quality, blur detection, and preprocessing."""
import io
import uuid
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional
from pathlib import Path
from app.config import settings

def load_image_from_bytes(image_bytes: bytes) -> Optional[np.ndarray]:
    """Decodes raw image bytes into an OpenCV BGR numpy array."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None

def is_image_blurry(image_bytes: bytes, threshold: float = 65.0) -> Tuple[bool, float]:
    """
    Computes blurriness using variance of the Laplacian.
    Returns (is_blurry, variance).
    Higher variance indicates sharper edges; below threshold indicates blur.
    """
    img = load_image_from_bytes(image_bytes)
    if img is None:
        return True, 0.0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return (variance < threshold), variance

def assess_image_quality(image_bytes: bytes) -> Tuple[float, dict]:
    """
    Evaluates comprehensive image quality:
    - Sharpness (Laplacian variance)
    - Contrast (standard deviation of intensity)
    - Brightness (mean intensity)
    Returns (quality_score 0.0-1.0, quality_signals).
    """
    img = load_image_from_bytes(image_bytes)
    if img is None:
        return 0.0, {"error": "Invalid image data"}
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))

    # Sharpness factor (scaled: 150+ is crisp)
    sharpness_score = min(1.0, var / 150.0)
    # Brightness factor (ideal: 80 - 180)
    brightness_score = 1.0 - abs(mean_val - 128.0) / 128.0
    # Contrast factor (ideal: > 40)
    contrast_score = min(1.0, std_val / 50.0)

    quality = 0.5 * sharpness_score + 0.3 * contrast_score + 0.2 * brightness_score
    quality = round(max(0.0, min(1.0, quality)), 2)

    return quality, {
        "sharpness_var": round(var, 2),
        "mean_brightness": round(mean_val, 2),
        "contrast_std": round(std_val, 2),
        "is_blurry": var < 65.0
    }

def save_upload_image(image_bytes: bytes, prefix: str = "doc") -> str:
    """Saves uploaded image to the data uploads folder and returns the relative path."""
    filename = f"{prefix}_{uuid.uuid4().hex}.jpg"
    target_path = settings.UPLOAD_DIR / filename
    with open(target_path, "wb") as f:
        f.write(image_bytes)
    return str(target_path)
