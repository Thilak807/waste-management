import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from detection import detect_waste

test_dir = Path(r"C:\Users\Lenovo\Downloads\waste")

print("=" * 60)
print("VERIFYING INFERENCE ON ALL 15 NEW WASTE IMAGES")
print("=" * 60)

for img_path in sorted(test_dir.iterdir()):
    if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
        continue
    res = detect_waste(img_path, save_result=True)
    dets = [f"{d['class_name'].upper()} {d['confidence_pct']:.0f}%" for d in res["detections"]]
    print(f"{img_path.name:45s} -> {dets}")

print("=" * 60)
