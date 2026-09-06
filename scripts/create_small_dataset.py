from pathlib import Path
import shutil
import random

# ============================================================
# SETTINGS
# ============================================================

# Original Roboflow dataset
SOURCE = Path(
    r"C:\Users\Lenovo\Downloads\yolo-v8-trash-detection-EE4016.v3i.yolov8"
)

# New smaller dataset
DEST = Path(
    str(Path(__file__).resolve().parents[1] / "dataset")
)

# Number of images we want
TRAIN_COUNT = 800
VALID_COUNT = 100
TEST_COUNT = 100

# Random seed = same selection every time
RANDOM_SEED = 42

# ============================================================
# IMAGE EXTENSIONS
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}

random.seed(RANDOM_SEED)


# ============================================================
# FIND IMAGE + MATCHING LABEL
# ============================================================

def get_pairs(split):
    """
    Find images and their matching YOLO .txt labels.
    """

    image_dir = SOURCE / split / "images"
    label_dir = SOURCE / split / "labels"

    pairs = []

    if not image_dir.exists():
        print(f"ERROR: Image folder not found: {image_dir}")
        return pairs

    if not label_dir.exists():
        print(f"ERROR: Label folder not found: {label_dir}")
        return pairs

    for image_path in image_dir.iterdir():

        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        label_path = label_dir / f"{image_path.stem}.txt"

        # Only use images that have a matching label
        if label_path.exists():
            pairs.append(
                (image_path, label_path)
            )

    return pairs


# ============================================================
# CREATE FOLDERS
# ============================================================

def create_folders():

    for split in ["train", "valid", "test"]:

        (DEST / split / "images").mkdir(
            parents=True,
            exist_ok=True
        )

        (DEST / split / "labels").mkdir(
            parents=True,
            exist_ok=True
        )


# ============================================================
# COPY DATA
# ============================================================

def copy_pairs(pairs, split, count):

    if len(pairs) < count:

        print(
            f"WARNING: {split} only has "
            f"{len(pairs)} valid image/label pairs."
        )

        count = len(pairs)

    random.shuffle(pairs)

    selected = pairs[:count]

    for image_path, label_path in selected:

        destination_image = (
            DEST
            / split
            / "images"
            / image_path.name
        )

        destination_label = (
            DEST
            / split
            / "labels"
            / label_path.name
        )

        shutil.copy2(
            image_path,
            destination_image
        )

        shutil.copy2(
            label_path,
            destination_label
        )

    print(
        f"{split}: copied {len(selected)} image/label pairs"
    )


# ============================================================
# CREATE DATA.YAML
# ============================================================

def create_yaml():

    yaml_content = f"""path: {DEST.as_posix()}

train: train/images
val: valid/images
test: test/images

nc: 6

names:
  0: Trash
  1: cardboard
  2: glass
  3: metal
  4: paper
  5: plastic
"""

    yaml_path = DEST / "data.yaml"

    yaml_path.write_text(
        yaml_content,
        encoding="utf-8"
    )

    print(
        f"Created: {yaml_path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("CREATING SMALL WASTE DATASET")
    print("=" * 60)

    print(
        f"\nOriginal dataset:\n{SOURCE}"
    )

    print(
        f"\nNew dataset:\n{DEST}"
    )

    print(
        "\nThe original dataset will NOT be modified."
    )

    # --------------------------------------------------------
    # Check source
    # --------------------------------------------------------

    if not SOURCE.exists():

        print(
            "\nERROR: Source dataset does not exist."
        )

        return

    # --------------------------------------------------------
    # Create folders
    # --------------------------------------------------------

    create_folders()

    # --------------------------------------------------------
    # TRAIN
    # --------------------------------------------------------

    print("\nReading training data...")

    train_pairs = get_pairs("train")

    print(
        f"Found {len(train_pairs)} "
        f"valid training image/label pairs."
    )

    copy_pairs(
        train_pairs,
        "train",
        TRAIN_COUNT
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    print("\nReading validation data...")

    valid_pairs = get_pairs("valid")

    print(
        f"Found {len(valid_pairs)} "
        f"valid validation image/label pairs."
    )

    copy_pairs(
        valid_pairs,
        "valid",
        VALID_COUNT
    )

    # --------------------------------------------------------
    # TEST
    # --------------------------------------------------------

    print("\nReading test data...")

    test_pairs = get_pairs("test")

    print(
        f"Found {len(test_pairs)} "
        f"valid test image/label pairs."
    )

    copy_pairs(
        test_pairs,
        "test",
        TEST_COUNT
    )

    # --------------------------------------------------------
    # DATA.YAML
    # --------------------------------------------------------

    create_yaml()

    # --------------------------------------------------------
    # FINISHED
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)

    print(
        "\nSmall dataset created at:"
    )

    print(DEST)

    print("\nStructure:")

    print(
        """
waste_detection_small_dataset/
│
├── data.yaml
│
├── train/
│   ├── images/   800
│   └── labels/   800
│
├── valid/
│   ├── images/   100
│   └── labels/   100
│
└── test/
    ├── images/   100
    └── labels/   100
"""
    )


if __name__ == "__main__":
    main()
