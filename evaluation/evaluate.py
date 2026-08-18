"""
Model evaluation: precision, recall, F1, mAP, confusion matrix charts.

IMPORTANT: Metrics are computed only when you have a trained custom model
and labeled validation data. Demo/COCO mode does not invent accuracy numbers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config


def evaluate_custom_model(weights: Path = None, save_plots: bool = True) -> dict:
    """
    Run Ultralytics validation and save metric plots.

    Returns a dict of REAL metrics from the model on the val set.
    Raises if custom weights or dataset are missing.
    """
    from ultralytics import YOLO

    weights = Path(weights) if weights else config.WEIGHTS_PATH
    if not weights.exists():
        return {
            "available": False,
            "reason": (
                "No custom trained weights at models/trained_model/best.pt. "
                "Train the model first. Demo mode does not produce waste-specific metrics."
            ),
            "metrics": None,
        }

    model = YOLO(str(weights))
    metrics = model.val(
        data=str(config.DATA_YAML),
        imgsz=config.TRAIN_IMG_SIZE,
        plots=True,
        project=str(config.EVAL_DIR),
        name="val_run",
        exist_ok=True,
    )

    precision = float(metrics.box.mp) if hasattr(metrics.box, "mp") else None
    recall = float(metrics.box.mr) if hasattr(metrics.box, "mr") else None
    map50 = float(metrics.box.map50) if hasattr(metrics.box, "map50") else None
    map50_95 = float(metrics.box.map) if hasattr(metrics.box, "map") else None
    f1 = None
    if precision is not None and recall is not None and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)

    result = {
        "available": True,
        "source": "Ultralytics validation on dataset/images/val (REAL metrics)",
        "weights": str(weights),
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "mAP_50": map50,
            "mAP_50_95": map50_95,
        },
    }

    if save_plots and result["metrics"]:
        _plot_metrics_bar(result["metrics"])
        # Confusion matrix if Ultralytics saved one
        cm_candidates = list((config.EVAL_DIR / "val_run").glob("*confusion*.png"))
        result["confusion_matrix_images"] = [str(p) for p in cm_candidates]
        result["metrics_chart"] = str(config.EVAL_DIR / "metrics_summary.png")

    out_json = config.EVAL_DIR / "latest_metrics.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    result["json_path"] = str(out_json)
    return result


def _plot_metrics_bar(metrics: dict) -> Path:
    labels = []
    values = []
    for k, v in metrics.items():
        if v is None:
            continue
        labels.append(k)
        values.append(v)

    plt.figure(figsize=(8, 4.5))
    sns.barplot(x=labels, y=values, hue=labels, palette="viridis", legend=False)
    plt.ylim(0, 1.05)
    plt.title("Waste YOLO — Validation Metrics (trained model)")
    plt.ylabel("Score")
    plt.xticks(rotation=20)
    plt.tight_layout()
    out = config.EVAL_DIR / "metrics_summary.png"
    plt.savefig(out, dpi=140)
    plt.close()
    return out


def plot_sample_predictions(image_paths: list, max_images: int = 4) -> list:
    """
    Run detection on sample images and save side-by-side style annotated outputs.
    Uses whatever model mode is active (custom or demo) — labeled in filename.
    """
    from detection import detect_waste, model_status

    status = model_status()
    saved = []
    for path in image_paths[:max_images]:
        path = Path(path)
        if not path.exists():
            continue
        result = detect_waste(path, save_result=True)
        saved.append(
            {
                "image": str(path),
                "result_image": result["result_image"],
                "detections": result["detections"],
                "model_mode": result["model_mode"],
                "note": status["note"],
            }
        )
    out = config.EVAL_DIR / "sample_predictions.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(saved, f, indent=2)
    return saved


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate trained waste YOLO model")
    parser.add_argument("--samples", nargs="*", help="Optional image paths for sample preds")
    args = parser.parse_args()

    report = evaluate_custom_model()
    print(json.dumps(report, indent=2))

    if args.samples:
        print(plot_sample_predictions(args.samples))


if __name__ == "__main__":
    main()
