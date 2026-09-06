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

DATASET_DIR = BASE_DIR / "dataset"

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

# These are the main recyclable and waste categories used by the application.

CLASS_NAMES = [
    "plastic",
    "paper",
    "cardboard",
    "glass",
    "metal",
    "organic",
    "other",
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

# YOLOv8 Nano is lightweight and suitable for real-time live detection.

YOLO_BASE_MODEL = "yolov8n.pt"

# Minimum confidence required for a detection (lowered to 0.20 for high responsiveness)

CONFIDENCE_THRESHOLD = 0.20

# Intersection over Union threshold used for
# Non-Maximum Suppression.

IOU_THRESHOLD = 0.45

# Image size used during inference.

IMG_SIZE = 640


# ---------------------------------------------------------------------------
# Demo Mode (COCO Pretrained Classes Mapping)
# ---------------------------------------------------------------------------

# Maps standard COCO 80 object classes into waste categories when
# running live detection or demo testing.

DEMO_COCO_TO_WASTE = {
    # Plastic
    "bottle": "plastic",
    "cup": "plastic",
    "remote": "plastic",
    "keyboard": "plastic",
    "mouse": "plastic",
    "toothbrush": "plastic",
    "hair drier": "plastic",
    "frisbee": "plastic",

    # Paper & Cardboard
    "book": "paper",
    "cardboard": "paper",
    "paper": "paper",

    # Glass
    "wine glass": "glass",
    "vase": "glass",
    "bowl": "glass",

    # Metal & Electronics
    "fork": "metal",
    "knife": "metal",
    "spoon": "metal",
    "scissors": "metal",
    "cell phone": "metal",
    "laptop": "metal",
    "tv": "metal",
    "microwave": "metal",
    "oven": "metal",
    "toaster": "metal",
    "sink": "metal",
    "refrigerator": "metal",
    "clock": "metal",

    # Organic / Food Waste
    "banana": "organic",
    "apple": "organic",
    "sandwich": "organic",
    "orange": "organic",
    "broccoli": "organic",
    "carrot": "organic",
    "hot dog": "organic",
    "pizza": "organic",
    "donut": "organic",
    "cake": "organic",
    "potted plant": "organic",

    # General / Other Waste
    "backpack": "other",
    "handbag": "other",
    "tie": "other",
    "suitcase": "other",
    "umbrella": "other",
    "teddy bear": "other",
    "chair": "other",
    "couch": "other",
    "bed": "other",
    "dining table": "other",
    "toilet": "other",
}


# ---------------------------------------------------------------------------
# Bin & Waste Recycling Centers Configuration (with Coordinates for Map)
# ---------------------------------------------------------------------------

# Default map center coordinates (e.g. campus central quad)
MAP_DEFAULT_CENTER = {
    "lat": 12.9716,
    "lng": 77.5946,
    "zoom": 17,
}

# Maps waste categories to their bin types, locations, GPS coordinates, and descriptions
BIN_LOCATIONS = {
    "plastic": {
        "bin_type": "Plastic Recycling Station",
        "category": "plastic",
        "location": "Block B Entrance (North Wing)",
        "facility_name": "North Campus Plastic Hub",
        "floor_building": "Building B, Ground Floor East",
        "accepted_items": "PET Bottles, milk jugs, shampoo bottles, clean food containers, bottle caps",
        "operating_hours": "24/7 Accessible",
        "lat": 12.9722,
        "lng": 77.5941,
        "color": "#38bdf8",
        "icon": "🧴"
    },
    "paper": {
        "bin_type": "Paper & Cardboard Hub",
        "category": "paper",
        "location": "Library Area & Academic Quad",
        "facility_name": "Central Library Paper Depot",
        "floor_building": "Library Ground Floor, South Entrance",
        "accepted_items": "Newspapers, books, magazines, clean cardboard boxes, printer paper, notebooks",
        "operating_hours": "07:00 AM - 10:00 PM",
        "lat": 12.9712,
        "lng": 77.5952,
        "color": "#4ade80",
        "icon": "📄"
    },
    "cardboard": {
        "bin_type": "Cardboard & Packaging Station",
        "category": "paper",
        "location": "Logistics & Delivery Bay",
        "facility_name": "Campus Logistics Drop-off",
        "floor_building": "Warehouse Block, Bay 2",
        "accepted_items": "Corrugated boxes, shipping cartons, egg trays, paper packaging",
        "operating_hours": "08:00 AM - 08:00 PM",
        "lat": 12.9719,
        "lng": 77.5958,
        "color": "#fb923c",
        "icon": "📦"
    },
    "glass": {
        "bin_type": "Glass Recycling Center",
        "category": "glass",
        "location": "Block A Entrance (Science Wing)",
        "facility_name": "Science Complex Glass Depot",
        "floor_building": "Building A, West Walkway",
        "accepted_items": "Beverage bottles, glass jars, transparent & colored glassware, non-hazardous vials",
        "operating_hours": "24/7 Accessible",
        "lat": 12.9725,
        "lng": 77.5949,
        "color": "#facc15",
        "icon": "🍶"
    },
    "metal": {
        "bin_type": "Metal & E-Waste Facility",
        "category": "metal",
        "location": "Engineering Lab & Parking Area",
        "facility_name": "Engineering Scrap & E-Waste Center",
        "floor_building": "Mech/Electrical Workshop, Bay 1",
        "accepted_items": "Aluminium cans, tin food cans, foil, electronic circuit boards, cables, metal scrap",
        "operating_hours": "08:00 AM - 07:00 PM",
        "lat": 12.9708,
        "lng": 77.5938,
        "color": "#c084fc",
        "icon": "🔩"
    },
    "organic": {
        "bin_type": "Organic Compost Station",
        "category": "organic",
        "location": "Cafeteria & Food Court Garden",
        "facility_name": "Campus Green Composting Center",
        "floor_building": "Canteen Rear Court, Garden Zone",
        "accepted_items": "Food scraps, fruit peels, vegetables, coffee grounds, tea bags, leftover bread",
        "operating_hours": "06:00 AM - 11:00 PM",
        "lat": 12.9705,
        "lng": 77.5950,
        "color": "#34d399",
        "icon": "🌿"
    },
    "other": {
        "bin_type": "General Waste & Sorting Station",
        "category": "other",
        "location": "Main Campus Gate",
        "facility_name": "Main Gate Sorting Facility",
        "floor_building": "Near Security Office & Bus Stop",
        "accepted_items": "Non-recyclable wrappers, mixed household trash, damaged composites, sanitary waste",
        "operating_hours": "24/7 Accessible",
        "lat": 12.9730,
        "lng": 77.5935,
        "color": "#e879f9",
        "icon": "🗑️"
    },
    "trash": {
        "bin_type": "General Waste Bin",
        "category": "other",
        "location": "Main Campus Gate",
        "facility_name": "Main Gate Sorting Facility",
        "floor_building": "Near Security Office & Bus Stop",
        "accepted_items": "Non-recyclable wrappers, mixed household trash",
        "operating_hours": "24/7 Accessible",
        "lat": 12.9730,
        "lng": 77.5935,
        "color": "#e879f9",
        "icon": "🗑️"
    }
}


# ---------------------------------------------------------------------------
# Training Settings
# ---------------------------------------------------------------------------

# Number of training epochs.

TRAIN_EPOCHS = 15

# Number of images processed at a time.

TRAIN_BATCH = 16

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