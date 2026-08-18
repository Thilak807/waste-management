"""
YOLO waste detection module.

- Loads custom trained weights if available (models/trained_model/best.pt)
- Otherwise uses YOLOv8 pretrained COCO weights in DEMO mode with a clear
  mapping from everyday objects to waste categories (not a custom waste model)
- Draws bounding boxes, applies NMS (via Ultralytics), returns confidence scores
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

import config
from preprocessing import preprocess_for_yolo
from recommendations import get_recommendation

PathLike = Union[str, Path]

# Lazy-loaded model cache
_model = None
_model_mode: Optional[str] = None  # "custom" | "demo_coco"


def model_status() -> Dict[str, Any]:
    """Report whether a custom trained model exists."""
    custom = config.WEIGHTS_PATH.exists()
    return {
        "custom_weights_exist": custom,
        "weights_path": str(config.WEIGHTS_PATH) if custom else None,
        "mode": "custom" if custom else "demo_coco",
        "note": (
            "Using your trained waste YOLO weights."
            if custom
            else (
                "No custom waste model found. Running DEMO mode with COCO-pretrained "
                "YOLOv8 and a class mapping (bottle->plastic, book->paper, etc.). "
                "These are NOT results from a custom-trained waste model. "
                "Train with: python training/train.py"
            )
        ),
    }


def get_model():
    """Load YOLO model once (custom weights preferred)."""
    global _model, _model_mode
    if _model is not None:
        return _model, _model_mode

    from ultralytics import YOLO

    if config.WEIGHTS_PATH.exists():
        _model = YOLO(str(config.WEIGHTS_PATH))
        _model_mode = "custom"
    else:
        _model = YOLO(config.YOLO_BASE_MODEL)
        _model_mode = "demo_coco"
    return _model, _model_mode


def _map_demo_class(coco_name: str) -> Optional[str]:
    return config.DEMO_COCO_TO_WASTE.get(coco_name.lower())


def detect_waste(
    image_path: PathLike,
    conf: float = None,
    iou: float = None,
    save_result: bool = True,
    recommendations_map: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Run full detection pipeline on one image.

    Returns a dict with detections, annotated image path, model mode, etc.
    """
    conf = conf if conf is not None else config.CONFIDENCE_THRESHOLD
    iou = iou if iou is not None else config.IOU_THRESHOLD

    image_path = Path(image_path)
    # Preprocess (denoise); Ultralytics handles letterbox internally
    original, _letterboxed = preprocess_for_yolo(image_path, size=config.IMG_SIZE, denoise=True)

    model, mode = get_model()
    results = model.predict(
        source=original,
        conf=conf,
        iou=iou,  # NMS IoU threshold
        imgsz=config.IMG_SIZE,
        verbose=False,
    )

    detections: List[Dict[str, Any]] = []
    annotated = original.copy()

    if results and len(results) > 0:
        r0 = results[0]
        names = r0.names  # id -> name
        boxes = r0.boxes
        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls_id = int(box.cls.item())
                score = float(box.conf.item())
                xyxy = box.xyxy.cpu().numpy().astype(int).tolist()[0]
                raw_name = names.get(cls_id, str(cls_id))

                if mode == "custom":
                    waste_class = raw_name.lower()
                else:
                    waste_class = _map_demo_class(raw_name)
                    if waste_class is None:
                        continue  # skip non-waste-mapped COCO classes

                rec = get_recommendation(waste_class, recommendations_map)
                det = {
                    "class_name": waste_class,
                    "raw_label": raw_name,
                    "confidence": round(score, 4),
                    "confidence_pct": round(score * 100, 1),
                    "bbox": {"x1": xyxy[0], "y1": xyxy[1], "x2": xyxy[2], "y2": xyxy[3]},
                    "category": rec["category"],
                    "recommendation": rec["recommendation"],
                    "disposal_tips": rec["disposal_tips"],
                }
                detections.append(det)
                _draw_box(annotated, det)

    # Sort by confidence descending
    detections.sort(key=lambda d: d["confidence"], reverse=True)

    result_path = None
    if save_result:
        out_name = f"result_{image_path.stem}.jpg"
        result_path = config.RESULT_DIR / out_name
        cv2.imwrite(str(result_path), annotated)
        result_rel = f"results/{out_name}"
    else:
        result_rel = None

    primary = detections[0] if detections else None
    status = model_status()

    return {
        "success": True,
        "model_mode": mode,
        "model_note": status["note"],
        "original_image": str(image_path),
        "result_image": result_rel,
        "detections": detections,
        "count": len(detections),
        "primary_class": primary["class_name"] if primary else None,
        "primary_confidence": primary["confidence"] if primary else None,
        "primary_recommendation": primary["recommendation"] if primary else None,
    }


def _draw_box(image: np.ndarray, det: Dict[str, Any]) -> None:
    """Draw bounding box + label on BGR image."""
    colors = {
        "plastic": (40, 120, 255),
        "paper": (60, 180, 80),
        "glass": (220, 160, 40),
        "metal": (180, 80, 200),
    }
    b = det["bbox"]
    color = colors.get(det["class_name"], (0, 220, 255))
    x1, y1, x2, y2 = b["x1"], b["y1"], b["x2"], b["y2"]
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

    label = f"{det['class_name'].title()} {det['confidence_pct']:.1f}%"
    (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
    cv2.rectangle(image, (x1, max(0, y1 - th - 8)), (x1 + tw + 4, y1), color, -1)
    cv2.putText(
        image,
        label,
        (x1 + 2, y1 - 4),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def detect_from_array(image_bgr: np.ndarray, **kwargs) -> Dict[str, Any]:
    """Save temp array then detect (used for webcam captures)."""
    tmp = config.UPLOAD_DIR / "_capture_temp.jpg"
    cv2.imwrite(str(tmp), image_bgr)
    return detect_waste(tmp, **kwargs)
