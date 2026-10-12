import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from detection import detect_waste

print("=" * 70)
print("TESTING WASTE DETECTION & RECYCLING INFORMATION PIPELINE")
print("=" * 70)

test_imgs = [
    Path("waste_detection_small_dataset/train/images/1.jpg"),
    Path("waste_detection_small_dataset/train/images/Screenshot 2026-08-25 111252.png"),
    Path("waste_detection_small_dataset/train/images/Screenshot 2026-08-25 111316.png"),
    Path("waste_detection_small_dataset/train/images/Screenshot 2026-08-25 111336.png"),
    Path("waste_detection_small_dataset/test/images/cardboard18_jpg.rf.830304af595cbf578f302289d99b42e5.jpg"),
    Path("waste_detection_small_dataset/test/images/plastic103_jpg.rf.27bdbce713a6faeb87d3f18e9c7ce831.jpg"),
    Path("waste_detection_small_dataset/test/images/paper114_jpg.rf.5a16b1e28956ea8b3f2c5f492b4269e8.jpg"),
]

for p in test_imgs:
    if not p.exists():
        continue
    res = detect_waste(p, save_result=True)
    dets = [f"{d['class_name'].upper()} ({d['confidence_pct']:.0f}%)" for d in res["detections"]]
    print(f"\n[Image]: {p.name}")
    print(f"  Count: {res['count']}")
    print(f"  Detections: {dets}")
    print(f"  Unique Waste Info Items ({len(res['unique_waste_items'])}):")
    for u in res["unique_waste_items"]:
        print(f"    - {u['display_name']} -> Category: '{u['category']}', Bin: '{u['segregation_bin']}'")
        print(f"      Current Use: {u['current_use'][:60]}...")
        print(f"      Recycling Method: {u['recycling_method'][:60]}...")
        print(f"      Upcycled Products: {len(u['what_can_be_made'])} ideas")

print("\n" + "=" * 70)
print("TEST COMPLETED SUCCESSFULLY")
print("=" * 70)
