
"""
YOLO training pipeline for Waste Detection & Recycling System.

Dataset structure expected:

yolo-v8-trash-detection-EE4016.v3i.yolov8/
├── data.yaml
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/

Usage:

Verify dataset:
    python training/train.py --verify-only

Train model:
    python training/train.py

Train with custom settings:
    python training/train.py --epochs 30 --batch 4 --imgsz 640

Resume training:
    python training/train.py --resume

Validate trained model:
    python training/train.py --validate-only

Test an image:
    python training/train.py --test path/to/image.jpg
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------------

import config


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------

def _get_split_folder(split: str) -> str:
    """
    Convert our logical split names to the actual Roboflow folder names.

    train -> train
    val   -> valid
    test  -> test
    """

    if split == "val":
        return "valid"

    return split


def _count_images(split: str) -> int:
    """
    Count image files inside:

        train/images
        valid/images
        test/images
    """

    actual_split = _get_split_folder(split)

    image_dir = (
        config.DATASET_DIR
        / actual_split
        / "images"
    )

    if not image_dir.exists():
        return 0

    valid_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp",
    }

    return sum(
        1
        for file in image_dir.iterdir()
        if file.is_file()
        and file.suffix.lower() in valid_extensions
    )


def _count_labels(split: str) -> int:
    """
    Count YOLO annotation files inside:

        train/labels
        valid/labels
        test/labels
    """

    actual_split = _get_split_folder(split)

    label_dir = (
        config.DATASET_DIR
        / actual_split
        / "labels"
    )

    if not label_dir.exists():
        return 0

    return len(
        list(label_dir.glob("*.txt"))
    )


# ---------------------------------------------------------------------------
# Dataset verification
# ---------------------------------------------------------------------------

def verify_dataset() -> dict:
    """
    Verify that the Roboflow YOLO dataset is ready for training.

    Returns a dictionary containing:

        data_yaml
        train_images
        val_images
        test_images
        train_labels
        val_labels
        test_labels
        ok
        messages
    """

    report = {
        "data_yaml": config.DATA_YAML.exists(),

        "train_images": _count_images("train"),
        "val_images": _count_images("val"),
        "test_images": _count_images("test"),

        "train_labels": _count_labels("train"),
        "val_labels": _count_labels("val"),
        "test_labels": _count_labels("test"),

        "ok": False,

        "messages": [],
    }

    # -----------------------------------------------------------------------
    # Check data.yaml
    # -----------------------------------------------------------------------

    if not report["data_yaml"]:
        report["messages"].append(
            f"Missing data.yaml: {config.DATA_YAML}"
        )

    # -----------------------------------------------------------------------
    # Check training data
    # -----------------------------------------------------------------------

    if report["train_images"] == 0:
        report["messages"].append(
            "No training images found in train/images/"
        )

    if report["train_labels"] == 0:
        report["messages"].append(
            "No training labels found in train/labels/"
        )

    # -----------------------------------------------------------------------
    # Check validation data
    # -----------------------------------------------------------------------

    if report["val_images"] == 0:
        report["messages"].append(
            "No validation images found in valid/images/"
        )

    if report["val_labels"] == 0:
        report["messages"].append(
            "No validation labels found in valid/labels/"
        )

    # -----------------------------------------------------------------------
    # Check test data
    # -----------------------------------------------------------------------

    if report["test_images"] == 0:
        report["messages"].append(
            "No test images found in test/images/"
        )

    if report["test_labels"] == 0:
        report["messages"].append(
            "No test labels found in test/labels/"
        )

    # -----------------------------------------------------------------------
    # Determine whether dataset is ready
    # -----------------------------------------------------------------------

    report["ok"] = (
        report["data_yaml"]
        and report["train_images"] > 0
        and report["train_labels"] > 0
        and report["val_images"] > 0
        and report["val_labels"] > 0
    )

    if report["ok"]:
        report["messages"].append(
            "Dataset looks ready for training."
        )

    return report


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(
    epochs: int | None = None,
    batch: int | None = None,
    imgsz: int | None = None,
    resume: bool = False,
    device: str | None = None,
) -> Path:
    """
    Train YOLOv8 on the Roboflow waste dataset.

    The trained best.pt and last.pt files are copied to:

        models/trained_model/
    """

    from ultralytics import YOLO

    # Use configuration defaults if command-line values
    # were not supplied.

    epochs = epochs or config.TRAIN_EPOCHS
    batch = batch or config.TRAIN_BATCH
    imgsz = imgsz or config.TRAIN_IMG_SIZE
    device = device or config.TRAIN_DEVICE

    # -----------------------------------------------------------------------
    # Verify dataset
    # -----------------------------------------------------------------------

    report = verify_dataset()

    print()
    print("=" * 70)
    print("DATASET VERIFICATION")
    print("=" * 70)

    print(
        f"Dataset location:\n"
        f"{config.DATASET_DIR}"
    )

    print()

    print(
        f"Training images : {report['train_images']}"
    )

    print(
        f"Training labels : {report['train_labels']}"
    )

    print(
        f"Validation images : {report['val_images']}"
    )

    print(
        f"Validation labels : {report['val_labels']}"
    )

    print(
        f"Test images : {report['test_images']}"
    )

    print(
        f"Test labels : {report['test_labels']}"
    )

    print()

    for message in report["messages"]:
        print(" -", message)

    print()

    # Stop training if dataset is not ready.

    if not report["ok"] and not resume:

        raise SystemExit(
            "\nDataset is not ready for training.\n\n"
            "Make sure the Roboflow dataset contains:\n\n"
            "train/images/\n"
            "train/labels/\n"
            "valid/images/\n"
            "valid/labels/\n"
            "test/images/\n"
            "test/labels/\n"
        )

    # -----------------------------------------------------------------------
    # Model
    # -----------------------------------------------------------------------

    print("=" * 70)
    print("YOLO TRAINING")
    print("=" * 70)

    print(
        f"Base model : {config.YOLO_BASE_MODEL}"
    )

    print(
        f"Epochs     : {epochs}"
    )

    print(
        f"Batch size : {batch}"
    )

    print(
        f"Image size : {imgsz}"
    )

    print(
        f"Device     : {device}"
    )

    print()

    # -----------------------------------------------------------------------
    # Resume training
    # -----------------------------------------------------------------------

    if resume and config.LAST_WEIGHTS_PATH.exists():

        model = YOLO(
            str(config.LAST_WEIGHTS_PATH)
        )

        print(
            f"Resuming training from:\n"
            f"{config.LAST_WEIGHTS_PATH}"
        )

        results = model.train(
            resume=True
        )

    # -----------------------------------------------------------------------
    # Start new training
    # -----------------------------------------------------------------------

    else:

        model = YOLO(
            config.YOLO_BASE_MODEL
        )

        results = model.train(
            data=str(config.DATA_YAML),

            epochs=epochs,

            batch=batch,

            imgsz=imgsz,

            device=device,

            project=str(
                config.BASE_DIR
                / "runs"
                / "detect"
            ),

            name="waste_train",

            exist_ok=True,
        )

    # -----------------------------------------------------------------------
    # Find training output directory
    # -----------------------------------------------------------------------

    run_dir = (
        Path(results.save_dir)
        if hasattr(results, "save_dir")
        else (
            config.BASE_DIR
            / "runs"
            / "detect"
            / "waste_train"
        )
    )

    print()

    print(
        f"Training output:\n"
        f"{run_dir}"
    )

    # -----------------------------------------------------------------------
    # Locate trained weights
    # -----------------------------------------------------------------------

    best = (
        run_dir
        / "weights"
        / "best.pt"
    )

    last = (
        run_dir
        / "weights"
        / "last.pt"
    )

    # Make sure model directory exists.

    config.MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------------------------
    # Copy best model
    # -----------------------------------------------------------------------

    if best.exists():

        shutil.copy2(
            best,
            config.WEIGHTS_PATH
        )

        print(
            f"\nBest model saved to:\n"
            f"{config.WEIGHTS_PATH}"
        )

    else:

        print(
            "\nWARNING: best.pt was not found."
        )

    # -----------------------------------------------------------------------
    # Copy last checkpoint
    # -----------------------------------------------------------------------

    if last.exists():

        shutil.copy2(
            last,
            config.LAST_WEIGHTS_PATH
        )

        print(
            f"Last checkpoint saved to:\n"
            f"{config.LAST_WEIGHTS_PATH}"
        )

    # -----------------------------------------------------------------------
    # Return best model path
    # -----------------------------------------------------------------------

    return config.WEIGHTS_PATH


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(
    weights: Path | None = None
) -> dict:
    """
    Validate the trained YOLO model using the validation dataset.
    """

    from ultralytics import YOLO

    weights = (
        Path(weights)
        if weights
        else config.WEIGHTS_PATH
    )

    if not weights.exists():

        raise SystemExit(
            f"No trained weights found at:\n"
            f"{weights}\n\n"
            f"Train the model first."
        )

    print()
    print("=" * 70)
    print("MODEL VALIDATION")
    print("=" * 70)

    model = YOLO(
        str(weights)
    )

    metrics = model.val(
        data=str(config.DATA_YAML),
        imgsz=config.TRAIN_IMG_SIZE
    )

    summary = {
        "map50": (
            float(metrics.box.map50)
            if hasattr(metrics.box, "map50")
            else None
        ),

        "map50_95": (
            float(metrics.box.map)
            if hasattr(metrics.box, "map")
            else None
        ),

        "precision": (
            float(metrics.box.mp)
            if hasattr(metrics.box, "mp")
            else None
        ),

        "recall": (
            float(metrics.box.mr)
            if hasattr(metrics.box, "mr")
            else None
        ),
    }

    print()

    print(
        "=== Validation metrics ==="
    )

    for key, value in summary.items():

        print(
            f"{key}: {value}"
        )

    print()

    return summary


# ---------------------------------------------------------------------------
# Test image
# ---------------------------------------------------------------------------

def test_image(
    image_path: str,
    weights: Path | None = None
) -> None:
    """
    Run YOLO inference on one image.
    """

    from detection import detect_waste

    result = detect_waste(
        image_path,
        save_result=True
    )

    print()

    print("=" * 70)
    print("IMAGE TEST")
    print("=" * 70)

    print(
        "Mode:",
        result["model_mode"]
    )

    print(
        "Note:",
        result["model_note"]
    )

    print()

    print("Detections:")

    if not result["detections"]:

        print(
            "  No objects detected."
        )

    else:

        for detection in result["detections"]:

            print(
                f"  - "
                f"{detection['class_name']} "
                f"("
                f"{detection['confidence_pct']}%"
                f") "
                f"bbox="
                f"{detection['bbox']}"
            )

    print()

    print(
        "Result image:",
        result["result_image"]
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Train, validate or test "
            "the Waste Detection YOLO model"
        )
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=config.TRAIN_EPOCHS,
        help="Number of training epochs"
    )

    parser.add_argument(
        "--batch",
        type=int,
        default=config.TRAIN_BATCH,
        help="Training batch size"
    )

    parser.add_argument(
        "--imgsz",
        type=int,
        default=config.TRAIN_IMG_SIZE,
        help="Training image size"
    )

    parser.add_argument(
        "--device",
        type=str,
        default=config.TRAIN_DEVICE,
        help="Training device: cpu or GPU number such as 0"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume training from last.pt"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the trained model"
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify the dataset"
    )

    parser.add_argument(
        "--test",
        type=str,
        default=None,
        help="Test one image"
    )

    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Dataset verification only
    # -----------------------------------------------------------------------

    if args.verify_only:

        report = verify_dataset()

        print()

        print(
            "=" * 70
        )

        print(
            "DATASET VERIFICATION RESULT"
        )

        print(
            "=" * 70
        )

        print(
            f"Data YAML      : {report['data_yaml']}"
        )

        print(
            f"Train images   : {report['train_images']}"
        )

        print(
            f"Train labels   : {report['train_labels']}"
        )

        print(
            f"Val images     : {report['val_images']}"
        )

        print(
            f"Val labels     : {report['val_labels']}"
        )

        print(
            f"Test images    : {report['test_images']}"
        )

        print(
            f"Test labels    : {report['test_labels']}"
        )

        print(
            f"Dataset ready  : {report['ok']}"
        )

        print()

        for message in report["messages"]:

            print(
                " -",
                message
            )

        return

    # -----------------------------------------------------------------------
    # Validation only
    # -----------------------------------------------------------------------

    if args.validate_only:

        validate()

        return

    # -----------------------------------------------------------------------
    # Test image
    # -----------------------------------------------------------------------

    if args.test:

        test_image(
            args.test
        )

        return

    # -----------------------------------------------------------------------
    # Train
    # -----------------------------------------------------------------------

    train(
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        resume=args.resume,
        device=args.device
    )

    # -----------------------------------------------------------------------
    # Validate automatically after training
    # -----------------------------------------------------------------------

    if config.WEIGHTS_PATH.exists():

        validate()


# ---------------------------------------------------------------------------
# Program entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
