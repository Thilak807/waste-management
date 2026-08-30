"""
Generate high-precision YOLO annotations for the 15 new waste images,
clean up dataset splits, and distribute them into train (11), valid (2), and test (2).
"""

from pathlib import Path
import shutil

# Base dataset directory
DATASET_DIR = Path(r"C:\Users\Lenovo\Downloads\waste_detection_small_dataset")
WASTE_DIR = Path(r"C:\Users\Lenovo\Downloads\waste")

# Classes in dataset:
# 0: Trash
# 1: cardboard
# 2: glass
# 3: metal
# 4: paper
# 5: plastic

ANNOTATIONS = {
    "1.jpg": [
        (3, 0.260, 0.510, 0.190, 0.520),  # metal can
        (4, 0.510, 0.485, 0.220, 0.470),  # crumpled paper
        (2, 0.745, 0.505, 0.160, 0.790),  # clear glass bottle
    ],
    "2.jpg": [
        (3, 0.260, 0.510, 0.190, 0.520),  # metal can
        (4, 0.510, 0.485, 0.220, 0.470),  # crumpled paper
        (2, 0.745, 0.505, 0.160, 0.790),  # clear glass bottle
        (2, 0.905, 0.505, 0.130, 0.730),  # green glass bottle
    ],
    "3.jpg": [
        (3, 0.258, 0.595, 0.160, 0.375),  # metal can
        (4, 0.475, 0.585, 0.180, 0.360),  # crumpled paper
        (2, 0.672, 0.580, 0.235, 0.435),  # clear glass bottle
        (2, 0.812, 0.585, 0.220, 0.355),  # green glass bottle
    ],
    "4.jpg": [
        (3, 0.260, 0.590, 0.170, 0.400),  # metal can
        (4, 0.480, 0.585, 0.195, 0.395),  # crumpled paper
        (2, 0.680, 0.530, 0.335, 0.540),  # clear glass bottle
    ],
    "Screenshot 2026-08-25 111252.png": [
        (5, 0.200, 0.545, 0.370, 0.790),  # plastic water bottle
        (4, 0.520, 0.530, 0.360, 0.470),  # paper napkin
        (3, 0.790, 0.640, 0.340, 0.600),  # metal Coke can
    ],
    "Screenshot 2026-08-25 111316.png": [
        (4, 0.250, 0.370, 0.360, 0.610),  # paper coffee cup
        (0, 0.470, 0.715, 0.640, 0.470),  # banana peel (trash/organic)
        (1, 0.730, 0.390, 0.490, 0.580),  # cardboard container
    ],
    "Screenshot 2026-08-25 111336.png": [
        (5, 0.215, 0.510, 0.310, 0.770),  # plastic Starbucks cup
        (3, 0.465, 0.550, 0.290, 0.600),  # metal Coke can
        (0, 0.775, 0.605, 0.330, 0.720),  # disposable mask (trash)
    ],
    "Screenshot 2026-08-25 111352.png": [
        (1, 0.230, 0.530, 0.460, 0.660),  # cardboard sheet
        (2, 0.565, 0.470, 0.270, 0.565),  # green glass jar
        (4, 0.830, 0.470, 0.330, 0.600),  # paper sheet
    ],
    "Screenshot 2026-08-25 111419.png": [
        (5, 0.220, 0.505, 0.265, 0.930),  # plastic Bisleri bottle
        (1, 0.510, 0.480, 0.315, 0.660),  # cardboard McDonald's box
        (5, 0.810, 0.555, 0.340, 0.710),  # plastic foil snack wrapper
    ],
    "Screenshot 2026-08-25 111435.png": [
        (4, 0.205, 0.510, 0.365, 0.610),  # paper cup
        (3, 0.515, 0.575, 0.315, 0.710),  # metal Sprite can
        (5, 0.850, 0.610, 0.270, 0.630),  # plastic Oreo wrapper
    ],
    "Screenshot 2026-08-25 111457.png": [
        (5, 0.230, 0.520, 0.310, 0.550),  # plastic Kurkure wrapper
        (5, 0.530, 0.430, 0.260, 0.745),  # plastic bottle
        (5, 0.840, 0.470, 0.260, 0.390),  # plastic cup
    ],
    "Screenshot 2026-08-25 111515.png": [
        (5, 0.170, 0.500, 0.210, 0.760),  # plastic bottle
        (1, 0.505, 0.505, 0.400, 0.480),  # cardboard/foam box
        (4, 0.850, 0.555, 0.210, 0.380),  # paper cup
    ],
    "watermarked_img_5270002177722073054.jpg": [
        (5, 0.260, 0.470, 0.280, 0.240),  # Sprite plastic bottle
        (3, 0.365, 0.590, 0.135, 0.315),  # Coke metal can
        (4, 0.540, 0.580, 0.160, 0.290),  # crumpled paper
        (0, 0.645, 0.690, 0.130, 0.140),  # mask (trash)
        (2, 0.730, 0.530, 0.280, 0.430),  # clear glass bottle
    ],
    "WhatsApp Image 2026-08-20 at 10.24.24 AM (1).jpeg": [
        (5, 0.190, 0.480, 0.270, 0.590),  # Aquafina plastic bottle
        (4, 0.500, 0.510, 0.280, 0.370),  # crumpled paper
        (3, 0.830, 0.615, 0.240, 0.395),  # metal Sprite can
    ],
    "WhatsApp Image 2026-08-20 at 10.24.31 AM.jpeg": [
        (5, 0.270, 0.545, 0.410, 0.670),  # Aqua plastic bottle
        (4, 0.595, 0.335, 0.330, 0.410),  # crumpled paper
        (3, 0.770, 0.660, 0.340, 0.380),  # metal Coke can
    ],
}

# Distribution: 11 in train, 2 in valid, 2 in test
SPLIT_MAPPING = {
    "1.jpg": "train",
    "2.jpg": "train",
    "3.jpg": "train",
    "4.jpg": "valid",
    "Screenshot 2026-08-25 111252.png": "train",
    "Screenshot 2026-08-25 111316.png": "train",
    "Screenshot 2026-08-25 111336.png": "train",
    "Screenshot 2026-08-25 111352.png": "valid",
    "Screenshot 2026-08-25 111419.png": "train",
    "Screenshot 2026-08-25 111435.png": "train",
    "Screenshot 2026-08-25 111457.png": "train",
    "Screenshot 2026-08-25 111515.png": "train",
    "watermarked_img_5270002177722073054.jpg": "train",
    "WhatsApp Image 2026-08-20 at 10.24.24 AM (1).jpeg": "test",
    "WhatsApp Image 2026-08-20 at 10.24.31 AM.jpeg": "test",
}


def main():
    print("=" * 60)
    print("ANNOTATING AND ORGANIZING NEW WASTE IMAGES")
    print("=" * 60)

    # 1. Remove raw unlabelled copies from all splits first
    for filename in ANNOTATIONS.keys():
        for split in ["train", "valid", "test"]:
            img_path = DATASET_DIR / split / "images" / filename
            lbl_path = DATASET_DIR / split / "labels" / f"{Path(filename).stem}.txt"
            if img_path.exists():
                img_path.unlink()
            if lbl_path.exists():
                lbl_path.unlink()

    # 2. Add each image to its designated split with its label file
    counts = {"train": 0, "valid": 0, "test": 0}
    for filename, boxes in ANNOTATIONS.items():
        src_img = WASTE_DIR / filename
        if not src_img.exists():
            print(f"WARNING: {src_img} not found!")
            continue

        target_split = SPLIT_MAPPING[filename]
        dest_img = DATASET_DIR / target_split / "images" / filename
        dest_lbl = DATASET_DIR / target_split / "labels" / f"{Path(filename).stem}.txt"

        dest_img.parent.mkdir(parents=True, exist_ok=True)
        dest_lbl.parent.mkdir(parents=True, exist_ok=True)

        # Copy image
        shutil.copy2(src_img, dest_img)

        # Write label lines
        lines = [f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n" for cls_id, xc, yc, w, h in boxes]
        dest_lbl.write_text("".join(lines), encoding="utf-8")

        counts[target_split] += 1
        print(f"Added {filename} -> {target_split} ({len(boxes)} bounding boxes)")

    print("\nSummary of newly added items:")
    for split, c in counts.items():
        print(f"  {split}: +{c} image/label pairs")

    print("\nVerifying dataset balance...")
    for split in ["train", "valid", "test"]:
        imgs = len(list((DATASET_DIR / split / "images").iterdir()))
        lbls = len(list((DATASET_DIR / split / "labels").iterdir()))
        print(f"  {split}: {imgs} images, {lbls} labels (Match: {imgs == lbls})")

    print("=" * 60)
    print("Dataset setup complete!")


if __name__ == "__main__":
    main()
