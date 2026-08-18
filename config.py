"""
Central configuration for the Waste Detection & Recycling System.
Change paths, model settings, and training hyperparameters here.
"""

import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Roboflow Dataset
# ---------------------------------------------------------------------------

DATASET_DIR = Path(
    r"C:\Users\Lenovo\Downloads\waste_detection_small_dataset"
)

# The downloaded dataset contains:
#
# DATASET_DIR/
# ├── data.yaml
# ├── train/
# │   ├── images/
# │   └── labels/
# ├── valid/
# │   ├── images/
# │   └── labels/
# └── test/
#     ├── images/
#     └── labels/
#
# We point IMAGES_DIR and LABELS_DIR to the dataset root because
# train.py expects:
#   IMAGES_DIR / "train"
#   LABELS_DIR / "train"
#
# and similarly for valid/test.

IMAGES_DIR = DATASET_DIR
LABELS_DIR = DATASET_DIR

# YOLO dataset configuration file
DATA_YAML = DATASET_DIR / "data.yaml"


# ---------------------------------------------------------------------------
# Project Output / Model Paths
# ---------------------------------------------------------------------------

MODELS_DIR = BASE_DIR / "models" / "trained_model"

WEIGHTS_PATH = MODELS_DIR / "best.pt"

LAST_WEIGHTS_PATH = MODELS_DIR / "last.pt"


# ---------------------------------------------------------------------------
# Application Paths
# ---------------------------------------------------------------------------

UPLOAD_DIR = BASE_DIR / "frontend" / "static" / "uploads"

RESULT_DIR = BASE_DIR / "frontend" / "static" / "results"

EVAL_DIR = BASE_DIR / "evaluation" / "outputs"

DB_PATH = BASE_DIR / "database" / "waste_detection.db"


# ---------------------------------------------------------------------------
# Create Required Directories
# ---------------------------------------------------------------------------

for _d in (
    UPLOAD_DIR,
    RESULT_DIR,
    EVAL_DIR,
    MODELS_DIR,
):
    _d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Waste Classes
# ---------------------------------------------------------------------------

# These are the main recyclable categories used by the application.

CLASS_NAMES = [
    "plastic",
    "paper",
    "glass",
    "metal",
]

CLASS_TO_ID = {
    name: idx
    for idx, name in enumerate(CLASS_NAMES)
}

ID_TO_CLASS = {
    idx: name
    for idx, name in enumerate(CLASS_NAMES)
}


# ---------------------------------------------------------------------------
# YOLO / Inference Settings
# ---------------------------------------------------------------------------

# YOLOv8 Nano is lightweight and suitable for a college-project PC.

YOLO_BASE_MODEL = "yolov8n.pt"

# Minimum confidence required for a detection.

CONFIDENCE_THRESHOLD = 0.25

# Intersection over Union threshold used for
# Non-Maximum Suppression.

IOU_THRESHOLD = 0.45

# Image size used during inference.

IMG_SIZE = 640


# ---------------------------------------------------------------------------
# Demo Mode
# ---------------------------------------------------------------------------

# These mappings are ONLY for the application's demo mode when
# custom trained weights are not available.
#
# They are NOT the trained waste model.

DEMO_COCO_TO_WASTE = {
    "bottle": "plastic",
    "cup": "plastic",
    "wine glass": "glass",
    "book": "paper",
    "cell phone": "metal",
    "laptop": "metal",
    "tv": "metal",
    "remote": "plastic",
    "keyboard": "plastic",
    "mouse": "plastic",
    "scissors": "metal",
    "fork": "metal",
    "knife": "metal",
    "spoon": "metal",
    "bowl": "glass",
    "vase": "glass",
}


# ---------------------------------------------------------------------------
# Training Settings
# ---------------------------------------------------------------------------

# Number of training epochs.

TRAIN_EPOCHS = 50

# Number of images processed at a time.

TRAIN_BATCH = 8

# Training image size.

TRAIN_IMG_SIZE = 640

# CPU training.
#
# If you have a compatible NVIDIA GPU, this can later be changed
# to:
#
# TRAIN_DEVICE = "0"

TRAIN_DEVICE = "cpu"


# ---------------------------------------------------------------------------
# Flask / Application Settings
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "waste-detection-college-demo-key"
)

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "admin123"
)

# Maximum uploaded image size = 16 MB

MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Allowed image extensions

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "bmp",
    "webp",
}