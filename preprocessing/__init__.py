"""
Image preprocessing for YOLO waste detection.

Operations:
  - Resize to model input size
  - Normalization (0–1 float)
  - Noise reduction (Gaussian blur / bilateral filter)
  - Augmentation helpers for training dataset expansion
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np

PathLike = Union[str, Path]


def load_image(path: PathLike) -> np.ndarray:
    """Load an image in BGR (OpenCV default). Raises if missing/corrupt."""
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img


def resize_image(image: np.ndarray, size: int = 640, keep_aspect: bool = True) -> np.ndarray:
    """
    Resize image for YOLO.

    If keep_aspect=True, letterbox (pad) to square size like YOLO training.
    """
    if not keep_aspect:
        return cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)

    h, w = image.shape[:2]
    scale = size / max(h, w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_LINEAR)

    canvas = np.full((size, size, 3), 114, dtype=np.uint8)  # YOLO gray pad
    top = (size - nh) // 2
    left = (size - nw) // 2
    canvas[top : top + nh, left : left + nw] = resized
    return canvas


def reduce_noise(image: np.ndarray, method: str = "gaussian") -> np.ndarray:
    """Light denoising before detection (optional)."""
    if method == "bilateral":
        return cv2.bilateralFilter(image, d=5, sigmaColor=50, sigmaSpace=50)
    # Default: mild Gaussian blur
    return cv2.GaussianBlur(image, (3, 3), 0)


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Convert uint8 BGR image to float32 RGB in [0, 1]."""
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return rgb.astype(np.float32) / 255.0


def enhance_contrast_adaptive(image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
    """Enhance illumination & local contrast using CLAHE for webcam/low-light frames."""
    if image is None or image.size == 0:
        return image
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)


def preprocess_for_yolo(
    image_or_path: Union[np.ndarray, PathLike],
    size: int = 640,
    denoise: bool = True,
    enhance_light: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Full preprocessing pipeline for inference display / optional tensor use.

    Returns:
        original_bgr: image used for drawing boxes (denoised, original size)
        letterboxed_bgr: resized letterboxed image (model-ready spatial size)
    """
    if isinstance(image_or_path, (str, Path)):
        original = load_image(image_or_path)
    else:
        original = image_or_path.copy()

    if enhance_light:
        original = enhance_contrast_adaptive(original)

    if denoise:
        original = reduce_noise(original)

    letterboxed = resize_image(original, size=size, keep_aspect=True)
    return original, letterboxed


# ---------------------------------------------------------------------------
# Augmentation (for expanding the training set — NOT applied at live inference)
# ---------------------------------------------------------------------------

def augment_flip(image: np.ndarray, horizontal: bool = True) -> np.ndarray:
    return cv2.flip(image, 1 if horizontal else 0)


def augment_brightness(image: np.ndarray, delta: float = 30.0) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] + delta, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def augment_rotation(image: np.ndarray, angle: float = 15.0) -> np.ndarray:
    h, w = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), borderValue=(114, 114, 114))


def save_augmented_variants(
    image_path: PathLike,
    output_dir: PathLike,
    prefix: Optional[str] = None,
) -> list:
    """
    Create simple augmented copies of one image for dataset expansion.
    Returns list of saved file paths.
    """
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = prefix or image_path.stem

    img = load_image(image_path)
    variants = {
        f"{prefix}_flip.jpg": augment_flip(img),
        f"{prefix}_bright.jpg": augment_brightness(img, 35),
        f"{prefix}_dark.jpg": augment_brightness(img, -35),
        f"{prefix}_rot.jpg": augment_rotation(img, 12),
    }

    saved = []
    for name, arr in variants.items():
        out = output_dir / name
        cv2.imwrite(str(out), arr)
        saved.append(out)
    return saved
