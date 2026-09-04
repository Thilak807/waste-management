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
    Run full multi-object detection pipeline on an image.
    Detects and classifies all waste objects in a single scene.
    """
    conf_th = conf if conf is not None else config.CONFIDENCE_THRESHOLD
    iou_th = iou if iou is not None else config.IOU_THRESHOLD

    image_path = Path(image_path)
    original, _ = preprocess_for_yolo(image_path, size=config.IMG_SIZE, denoise=True)
    h, w = original.shape[:2]

    model, mode = get_model()
    detections: List[Dict[str, Any]] = []
    annotated = original.copy()

    if mode == "custom":
        # Direct inference using the custom-trained YOLO model
        results = model.predict(
            source=original,
            conf=conf_th,
            iou=iou_th,
            imgsz=config.IMG_SIZE,
            verbose=False,
        )
        if results and len(results) > 0:
            r0 = results[0]
            for box in r0.boxes:
                cls_id = int(box.cls.item())
                score = float(box.conf.item())
                box_xyxy = [int(v) for v in box.xyxy[0].cpu().numpy()]
                raw_name = r0.names.get(cls_id, str(cls_id)).lower()

                bw = box_xyxy[2] - box_xyxy[0]
                bh = box_xyxy[3] - box_xyxy[1]
                if bw * bh > (w * h * 0.95) or bw < 10 or bh < 10:
                    continue

                # Map class name (e.g. Trash -> other, or direct name)
                waste_class = "other" if raw_name in ["trash", "other"] else raw_name
                rec = get_recommendation(waste_class, recommendations_map)
                bin_info = config.BIN_LOCATIONS.get(waste_class, config.BIN_LOCATIONS.get("other", {}))

                det = {
                    "class_name": waste_class,
                    "raw_label": raw_name,
                    "confidence": round(score, 4),
                    "confidence_pct": round(score * 100, 1),
                    "bbox": {"x1": box_xyxy[0], "y1": box_xyxy[1], "x2": box_xyxy[2], "y2": box_xyxy[3]},
                    "category": rec["category"],
                    "recommendation": rec["recommendation"],
                    "disposal_tips": rec["disposal_tips"],
                    "what_can_be_made": rec.get("what_can_be_made", []),
                    "bin_type": bin_info.get("bin_type", "General Waste Bin"),
                    "bin_location": bin_info.get("location", "Main Gate"),
                    "bin_facility": bin_info.get("facility_name", ""),
                    "bin_lat": bin_info.get("lat"),
                    "bin_lng": bin_info.get("lng"),
                    "bin_color": bin_info.get("color", "#34d399"),
                    "bin_icon": bin_info.get("icon", "🗑️"),
                }
                detections.append(det)
                _draw_box(annotated, det)

    else:
        # Demo mode using pretrained COCO model
        results = model.predict(
            source=original,
            conf=conf_th,
            iou=iou_th,
            imgsz=config.IMG_SIZE,
            verbose=False,
        )
        if results and len(results) > 0:
            r0 = results[0]
            for box in r0.boxes:
                cls_id = int(box.cls.item())
                score = float(box.conf.item())
                box_xyxy = [int(v) for v in box.xyxy[0].cpu().numpy()]
                raw_name = r0.names.get(cls_id, str(cls_id)).lower()

                mapped_class = config.DEMO_COCO_TO_WASTE.get(raw_name)
                if not mapped_class:
                    continue

                bw = box_xyxy[2] - box_xyxy[0]
                bh = box_xyxy[3] - box_xyxy[1]
                if bw * bh > (w * h * 0.90) or bw < 15 or bh < 15:
                    continue

                rec = get_recommendation(mapped_class, recommendations_map)
                bin_info = config.BIN_LOCATIONS.get(mapped_class, config.BIN_LOCATIONS.get("other", {}))

                det = {
                    "class_name": mapped_class,
                    "raw_label": raw_name,
                    "confidence": round(score, 4),
                    "confidence_pct": round(score * 100, 1),
                    "bbox": {"x1": box_xyxy[0], "y1": box_xyxy[1], "x2": box_xyxy[2], "y2": box_xyxy[3]},
                    "category": rec["category"],
                    "recommendation": rec["recommendation"],
                    "disposal_tips": rec["disposal_tips"],
                    "what_can_be_made": rec.get("what_can_be_made", []),
                    "bin_type": bin_info.get("bin_type", "General Waste Bin"),
                    "bin_location": bin_info.get("location", "Main Gate"),
                    "bin_facility": bin_info.get("facility_name", ""),
                    "bin_lat": bin_info.get("lat"),
                    "bin_lng": bin_info.get("lng"),
                    "bin_color": bin_info.get("color", "#34d399"),
                    "bin_icon": bin_info.get("icon", "🗑️"),
                }
                detections.append(det)
                _draw_box(annotated, det)

    # Sort by confidence descending
    detections.sort(key=lambda d: d["confidence"], reverse=True)

    # Compute Multi-Waste Summary
    category_counts: Dict[str, int] = {}
    unique_bins: Dict[str, Dict[str, Any]] = {}
    for d in detections:
        cls = d["class_name"]
        category_counts[cls] = category_counts.get(cls, 0) + 1
        if cls not in unique_bins:
            b_info = config.BIN_LOCATIONS.get(cls, config.BIN_LOCATIONS.get("other", {}))
            unique_bins[cls] = {
                "category": cls,
                "bin_type": b_info.get("bin_type", "General Bin"),
                "location": b_info.get("location", "Campus Center"),
                "facility_name": b_info.get("facility_name", ""),
                "color": b_info.get("color", "#34d399"),
                "icon": b_info.get("icon", "🗑️"),
                "lat": b_info.get("lat"),
                "lng": b_info.get("lng"),
            }

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
        "category_counts": category_counts,
        "unique_categories": list(category_counts.keys()),
        "unique_bins": list(unique_bins.values()),
        "primary_class": primary["class_name"] if primary else None,
        "primary_confidence": primary["confidence"] if primary else None,
        "primary_recommendation": primary["recommendation"] if primary else None,
        "what_can_be_made": primary.get("what_can_be_made", []) if primary else [],
    }


def _draw_box(image: np.ndarray, det: Dict[str, Any]) -> None:
    """Draw bounding box + label on BGR image."""
    colors = {
        "plastic": (248, 189, 56),    # Sky Blue
        "paper": (128, 222, 74),      # Green
        "cardboard": (60, 146, 251),  # Orange
        "glass": (21, 204, 250),      # Yellow
        "metal": (252, 132, 192),     # Purple
        "organic": (153, 211, 52),    # Emerald
        "other": (249, 121, 232),     # Pink
        "trash": (249, 121, 232),
    }
    b = det["bbox"]
    color = colors.get(det["class_name"], (0, 220, 255))
    x1, y1, x2, y2 = b["x1"], b["y1"], b["x2"], b["y2"]
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)

    label = f"{det['class_name'].upper()} {det['confidence_pct']:.0f}%"
    (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.58, 2)
    cv2.rectangle(image, (x1, max(0, y1 - th - 10)), (x1 + tw + 8, y1), color, -1)
    cv2.putText(
        image,
        label,
        (x1 + 4, max(th + 2, y1 - 4)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (10, 25, 15),
        2,
        cv2.LINE_AA,
    )


def detect_from_array(image_bgr: np.ndarray, **kwargs) -> Dict[str, Any]:
    """Save temp array then detect (used for webcam captures)."""
    tmp = config.UPLOAD_DIR / "_capture_temp.jpg"
    cv2.imwrite(str(tmp), image_bgr)
    return detect_waste(tmp, **kwargs)
