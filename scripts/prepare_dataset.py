"""
Dataset utilities:
  - Organize images by class folders into YOLO structure
  - Split train/val/test
  - Verify pairing of images and labels
  - Create empty label stubs for annotation
  - Helper to convert simple class-folder datasets

YOLO label format (one .txt per image):
  class_id x_center y_center width height   (all normalized 0–1)
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def list_images(folder: Path) -> list:
    return sorted([p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_EXTS])


def verify_dataset() -> dict:
    """Check image/label pairs and report missing files."""
    report = {"splits": {}, "issues": [], "ok": True}
    for split in ("train", "val", "test"):
        img_dir = config.IMAGES_DIR / split
        lbl_dir = config.LABELS_DIR / split
        images = list_images(img_dir) if img_dir.exists() else []
        labels = list(lbl_dir.glob("*.txt")) if lbl_dir.exists() else []
        img_stems = {p.stem for p in images}
        lbl_stems = {p.stem for p in labels}
        missing_labels = sorted(img_stems - lbl_stems)
        orphan_labels = sorted(lbl_stems - img_stems)
        report["splits"][split] = {
            "images": len(images),
            "labels": len(labels),
            "missing_labels": missing_labels[:20],
            "orphan_labels": orphan_labels[:20],
        }
        if missing_labels:
            report["ok"] = False
            report["issues"].append(f"{split}: {len(missing_labels)} images without labels")
        if orphan_labels:
            report["issues"].append(f"{split}: {len(orphan_labels)} labels without images")
    return report


def split_dataset(
    source_images: Path,
    source_labels: Path = None,
    ratios=(0.7, 0.2, 0.1),
    seed: int = 42,
) -> dict:
    """
    Split a flat folder of images (+ optional labels) into train/val/test.

    ratios: (train, val, test) summing to 1.0
    """
    source_images = Path(source_images)
    source_labels = Path(source_labels) if source_labels else source_images
    images = list_images(source_images)
    if not images:
        raise SystemExit(f"No images found in {source_images}")

    random.seed(seed)
    random.shuffle(images)
    n = len(images)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])
    splits = {
        "train": images[:n_train],
        "val": images[n_train : n_train + n_val],
        "test": images[n_train + n_val :],
    }

    counts = {}
    for split, files in splits.items():
        img_out = config.IMAGES_DIR / split
        lbl_out = config.LABELS_DIR / split
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)
        for img in files:
            dest = img_out / img.name
            if img.resolve() != dest.resolve():
                shutil.copy2(img, dest)
            lbl = source_labels / f"{img.stem}.txt"
            if lbl.exists():
                shutil.copy2(lbl, lbl_out / lbl.name)
        counts[split] = len(files)
    return counts


def import_class_folders(raw_root: Path, split: str = "train") -> int:
    """
    Import images from folders named by class:
      raw_root/plastic/*.jpg
      raw_root/paper/*.jpg
      ...

    Creates empty YOLO label stubs (class_id 0.5 0.5 1.0 1.0) as PLACEHOLDERS
    so students know the format — they MUST re-annotate with real boxes for training.
    """
    raw_root = Path(raw_root)
    img_out = config.IMAGES_DIR / split
    lbl_out = config.LABELS_DIR / split
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)

    count = 0
    for class_name, class_id in config.CLASS_TO_ID.items():
        folder = raw_root / class_name
        if not folder.exists():
            continue
        for img in list_images(folder):
            dest_name = f"{class_name}_{img.stem}{img.suffix.lower()}"
            shutil.copy2(img, img_out / dest_name)
            # Placeholder full-image box — replace with real annotations!
            with open(lbl_out / f"{Path(dest_name).stem}.txt", "w", encoding="utf-8") as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
            count += 1
    return count


def create_sample_label(class_id: int, xc=0.5, yc=0.5, w=0.4, h=0.6) -> str:
    """Return one YOLO label line (normalized coordinates)."""
    return f"{class_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n"


def write_readme_stub():
    stub = config.DATASET_DIR / "HOW_TO_ANNOTATE.txt"
    stub.write_text(
        """
HOW TO PREPARE THE DATASET
==========================

1. Collect photos of plastic, paper, glass, and metal waste under different
   lighting, backgrounds, angles, and object sizes.

2. Put raw photos in:
     dataset/raw/plastic/
     dataset/raw/paper/
     dataset/raw/glass/
     dataset/raw/metal/

3. Import (creates placeholder labels — replace with real boxes!):
     python scripts/prepare_dataset.py --import-raw dataset/raw --split train

4. Annotate properly with a tool such as LabelImg or Roboflow.
   Label format (YOLO): each image has a .txt file with lines:
     class_id  x_center  y_center  width  height
   All values except class_id are normalized between 0 and 1.
   Class IDs: 0=plastic, 1=paper, 2=glass, 3=metal

5. Split into train/val/test:
     python scripts/prepare_dataset.py --split-from dataset/images/train --ratios 0.7 0.2 0.1

6. Verify:
     python scripts/prepare_dataset.py --verify

7. Train:
     python training/train.py --epochs 50 --batch 8
""".strip(),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="Dataset preparation helpers")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--import-raw", type=str, help="Path to class-named folders")
    parser.add_argument("--split", type=str, default="train")
    parser.add_argument("--split-from", type=str, help="Flat image folder to split")
    parser.add_argument("--labels-from", type=str, default=None)
    parser.add_argument("--ratios", nargs=3, type=float, default=[0.7, 0.2, 0.1])
    args = parser.parse_args()

    write_readme_stub()

    if args.verify:
        import json
        print(json.dumps(verify_dataset(), indent=2))
        return
    if args.import_raw:
        n = import_class_folders(Path(args.import_raw), split=args.split)
        print(f"Imported {n} images into {args.split} (PLACEHOLDER labels — re-annotate!)")
        return
    if args.split_from:
        counts = split_dataset(Path(args.split_from), args.labels_from, tuple(args.ratios))
        print("Split counts:", counts)
        return
    parser.print_help()


if __name__ == "__main__":
    main()
