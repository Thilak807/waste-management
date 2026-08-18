"""
Create a few synthetic demo images (colored shapes + text) so students can
smoke-test the pipeline without a camera.

These are NOT real waste photos and will usually NOT trigger COCO detections.
For demo_coco mode, prefer real photos of bottles/books/cups.
For custom training, replace with real annotated waste images.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "dataset" / "samples"
OUT.mkdir(parents=True, exist_ok=True)


def make_card(title: str, color, filename: str):
    img = np.full((480, 640, 3), 235, dtype=np.uint8)
    cv2.rectangle(img, (120, 80), (520, 400), color, -1)
    cv2.putText(img, title, (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
    path = OUT / filename
    cv2.imwrite(str(path), img)
    print("Wrote", path)


if __name__ == "__main__":
    make_card("PLASTIC", (40, 120, 255), "sample_plastic_card.jpg")
    make_card("PAPER", (60, 180, 80), "sample_paper_card.jpg")
    make_card("GLASS", (220, 160, 40), "sample_glass_card.jpg")
    make_card("METAL", (180, 80, 200), "sample_metal_card.jpg")
    print("Done. For live demo, use real bottle/book photos in demo_coco mode.")
