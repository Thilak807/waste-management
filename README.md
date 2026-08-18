# Waste Detection, Classification and Recycling System

**Machine Learning + YOLO + Flask** college project for detecting waste (Plastic, Paper, Glass, Metal), showing confidence scores and bounding boxes, and giving recycling guidance.

---

## Honest note about model results (read this)

This project **does not invent accuracy numbers**.

| Mode | When it happens | What you see |
|------|-----------------|--------------|
| **Demo (COCO)** | No file at `models/trained_model/best.pt` | Pretrained YOLOv8 on COCO; everyday objects are **mapped** to waste classes (e.g. bottle → plastic). Labeled clearly in the UI. |
| **Custom trained** | After you train on your annotated waste dataset | Real waste detections + real validation metrics (precision, recall, F1, mAP). |

Always tell examiners which mode you are demonstrating.

---

## Project structure

```
project/
├── app.py                 # Flask entry point
├── config.py              # Paths, classes, thresholds
├── requirements.txt
├── README.md
├── dataset/
│   ├── images/{train,val,test}/
│   ├── labels/{train,val,test}/
│   ├── raw/               # Optional class folders for import
│   └── data.yaml          # YOLO class config
├── models/trained_model/  # best.pt after training
├── preprocessing/         # Resize, normalize, denoise, augment
├── training/train.py      # Train / resume / validate / test
├── detection/             # YOLO inference + NMS + boxes
├── recommendations/       # Recycling text (separate from ML)
├── evaluation/evaluate.py # Metrics + charts
├── database/              # SQLite layer
├── scripts/prepare_dataset.py
├── frontend/
│   ├── templates/
│   └── static/{css,js,uploads,results}/
└── admin/                 # (admin UI via Flask routes)
```

---

## Quick start (demonstration)

### 1. Install

```bash
cd waste_detection_recycling_project
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows CMD
.\.venv\Scripts\activate.bat

pip install -r requirements.txt
```

First run downloads `yolov8n.pt` automatically (needs internet once).

### 2. Run the app

```bash
python app.py
```

Open **http://127.0.0.1:5000**

Admin: **http://127.0.0.1:5000/admin/login**  
Default: `admin` / `admin123`

### 3. Demo flow (no custom training required)

1. Start the app.
2. **Upload** a photo of a plastic bottle, book, wine glass, or metal utensils (COCO-mapped objects), **or** use **Capture Image**.
3. Click **Detect Waste**.
4. See bounding boxes, class, confidence %, recycling guidance.
5. Result is saved in SQLite → appears under **History**.

Banner will say **model mode: demo_coco** until you train.

---

## Dataset preparation

### YOLO label format

One `.txt` per image, same filename:

```
class_id  x_center  y_center  width  height
```

All coordinates are **normalized 0–1**. Class IDs:

| ID | Class   |
|----|---------|
| 0  | plastic |
| 1  | paper   |
| 2  | glass   |
| 3  | metal   |

Example (`bottle001.txt`):

```
0 0.51 0.48 0.32 0.70
```

### Steps

1. Collect photos with different lighting, backgrounds, sizes, angles, and waste conditions.
2. Organize raw images:

```
dataset/raw/plastic/
dataset/raw/paper/
dataset/raw/glass/
dataset/raw/metal/
```

3. Import (creates **placeholder** full-image boxes — replace with real annotations):

```bash
python scripts/prepare_dataset.py --import-raw dataset/raw --split train
```

4. Annotate with **LabelImg**, **Roboflow**, or **CVAT** (YOLO format).
5. Split:

```bash
python scripts/prepare_dataset.py --split-from dataset/images/train --ratios 0.7 0.2 0.1
```

6. Verify:

```bash
python scripts/prepare_dataset.py --verify
```

You can also upload images from **Admin → Add Dataset Image**.

---

## Training commands

```bash
# Verify dataset
python training/train.py --verify-only

# Train (CPU-friendly defaults; use --device 0 for GPU)
python training/train.py --epochs 50 --batch 8 --imgsz 640

# Resume interrupted training
python training/train.py --resume

# Validate only (needs best.pt)
python training/train.py --validate-only

# Test one image
python training/train.py --test path/to/image.jpg
```

After training, `best.pt` is copied to `models/trained_model/best.pt`. Restart Flask; UI switches to **custom** mode.

### Evaluation (real metrics only)

```bash
python evaluation/evaluate.py
python evaluation/evaluate.py --samples path/to/img1.jpg path/to/img2.jpg
```

Outputs go to `evaluation/outputs/` (metrics JSON, bar chart, Ultralytics plots).

---

## How the complete system works

```
User → Capture/Upload
     → Preprocessing (denoise + YOLO letterbox inside Ultralytics)
     → YOLO detection (+ NMS)
     → Waste class + confidence
     → Recommendation module (lookup table / DB)
     → SQLite store
     → Result + History UI
```

Modules stay separate so you can change recycling text without retraining, and retrain YOLO without changing the website.

---

## Concepts explained (simple language)

### What is Machine Learning?
Teaching a computer to find patterns from examples (data) instead of writing fixed rules for every case.

### What is Deep Learning?
A type of ML using **neural networks** with many layers. Good at images, speech, and complex patterns.

### What is Computer Vision?
Making computers understand images/video: detect objects, read text, classify scenes, etc.

### What is YOLO?
**You Only Look Once** — a fast object detection model that looks at the whole image in one pass and predicts boxes + classes.

### Why YOLO is used?
It is **fast** (good for demos and phones), accurate enough for many tasks, and beginner-friendly with libraries like **Ultralytics**.

### What is object detection?
Finding **where** objects are (boxes) and **what** they are (class) in one image. Multiple objects can appear together.

### What is classification?
Assigning a label to something (e.g. “this is plastic”). Detection = location + classification.

### What is a bounding box?
A rectangle around a detected object, usually stored as corner coordinates `(x1,y1,x2,y2)` or YOLO center format.

### What is confidence score?
How sure the model is (0–1 or 0–100%). Example: Plastic 92% means high confidence.

### What is dataset annotation?
Manually marking correct boxes and classes on training images so the model can learn.

### What is preprocessing?
Cleaning/preparing images: resize, normalize, reduce noise, augment. Helps the model train/infer consistently.

### What is training?
Updating model weights using labeled examples so predictions improve.

### What is validation?
Checking the model on a separate labeled set during/after training to tune settings and spot overfitting.

### What is testing?
Final check on unseen images (test set) that were not used to tune the model.

### Precision, Recall, F1-score, mAP
- **Precision**: Of predicted objects, how many were correct?
- **Recall**: Of real objects, how many did we find?
- **F1-score**: Balance of precision and recall.
- **mAP**: Mean Average Precision across classes/IoU thresholds — standard detection score.

### What is Non-Maximum Suppression (NMS)?
When many overlapping boxes detect the same object, NMS keeps the best box and removes duplicates.

---

## Step-by-step code explanation (viva)

1. **`config.py`** — Central settings: class names, paths, confidence/IoU thresholds, training defaults.
2. **`preprocessing/`** — Loads image with OpenCV, optional Gaussian denoise, letterbox resize helpers, augmentations for dataset growth.
3. **`dataset/data.yaml`** — Tells YOLO where images are and what class IDs mean.
4. **`scripts/prepare_dataset.py`** — Import, split, verify dataset.
5. **`training/train.py`** — Loads YOLOv8, trains on `data.yaml`, saves `best.pt` into `models/trained_model/`.
6. **`detection/`** — Loads custom weights if present, else demo COCO model; runs `predict` with `conf` + `iou` (NMS); draws boxes; returns JSON-like dict.
7. **`recommendations/`** — Maps class → recycling text (independent of neural net).
8. **`database/`** — SQLite tables for users, categories, recommendations, detection history.
9. **`app.py`** — Flask routes: home, detect, history, admin.
10. **`frontend/`** — HTML/CSS/JS: upload, camera capture, results, admin forms.
11. **`evaluation/evaluate.py`** — Runs real val metrics only if custom weights exist; plots charts.

### Detection request path
`POST /detect` → save upload → `detect_waste()` → `get_recommendation()` → `save_detection()` → `result.html`.

---

## Sample input / output

**Input:** Photo containing a plastic bottle and a metal fork (demo mode).

**Output (example shape — your numbers will differ):**

```
Plastic — 91.2%   (mapped from COCO "bottle")
Metal   — 88.0%   (mapped from COCO "fork")
```

Plus image with colored boxes, recycling text for the top class, and a history row in SQLite.

After **custom training**, labels come directly from your waste classes (no COCO mapping).

---

## Admin features

- Login / manage users  
- Manage waste categories  
- Update recycling recommendations (no retrain)  
- Upload dataset images  
- View detection reports  
- Reminder to retrain YOLO from terminal after dataset changes  

---

## Mobile / future deployment

The detection logic is in Python modules + a JSON API (`POST /api/detect`). Later you can:

- Export YOLO to **ONNX / TFLite / CoreML** for Android/iOS, or  
- Keep a small Flask/FastAPI server and call it from a mobile app.

---

## Common errors and solutions

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: ultralytics` | Activate venv; `pip install -r requirements.txt` |
| Slow first run | YOLO downloads `yolov8n.pt`; wait / check internet |
| No detections in demo mode | Use objects COCO knows (bottle, book, cup, wine glass, fork…). Real trash piles need **custom training** |
| Camera blocked | Allow browser camera permission, or use Upload |
| `Dataset not ready` when training | Need images + labels in train **and** val |
| CUDA / GPU errors | Train with `--device cpu` |
| Port 5000 in use | Change `app.run(port=5001)` in `app.py` |
| Placeholder labels → poor accuracy | Re-annotate with tight real bounding boxes |
| Import path errors | Always run commands from the **project root** |

---

## 30 likely viva questions (short answers)

1. **What is the aim of your project?** Detect waste in images with YOLO and suggest recycling actions.  
2. **Which algorithm?** YOLO (YOLOv8 via Ultralytics).  
3. **Why YOLO not only CNN classification?** Classification labels the whole image; YOLO finds multiple objects with locations.  
4. **What classes?** Plastic, paper, glass, metal (extendable).  
5. **What is a bounding box?** Rectangle locating an object.  
6. **What is confidence?** Model’s certainty for that detection.  
7. **What is NMS?** Removes duplicate overlapping boxes.  
8. **What is annotation?** Drawing correct boxes/labels for training data.  
9. **Train vs val vs test?** Learn / tune & monitor / final unseen check.  
10. **What is overfitting?** Memorizing train data; poor on new images.  
11. **How do you reduce overfitting?** More varied data, augmentation, early stopping, proper val set.  
12. **What is mAP?** Mean Average Precision for detection quality.  
13. **Precision vs recall?** Correct predictions ratio vs coverage of real objects.  
14. **What preprocessing did you use?** Resize/letterbox, denoise, normalize; augment for training.  
15. **Why separate recommendations module?** Update guidance without retraining the model.  
16. **Which database?** SQLite (local); design can move to Firebase/cloud later.  
17. **What does the Flask app do?** UI + API to run detection and store history.  
18. **How is history stored?** Table `detections` with image paths, class, confidence, time, recommendation.  
19. **Can it detect multiple objects?** Yes — YOLO outputs many boxes per image.  
20. **Demo vs custom mode?** Demo maps COCO classes; custom uses your trained `best.pt`.  
21. **Did you fake accuracy?** No — metrics only from real validation after training.  
22. **How to add a new class?** Update `data.yaml`, annotate data, update recommendations, retrain.  
23. **What is IoU?** Overlap ratio between predicted and true box.  
24. **Backend stack?** Python, Flask, OpenCV, PyTorch, Ultralytics YOLO, SQLite.  
25. **How to run training?** `python training/train.py --epochs 50`.  
26. **What is transfer learning?** Starting from pretrained YOLO weights, fine-tuning on waste data.  
27. **Limitations?** Needs good annotated data; demo mode isn’t real waste training; lighting/occlusion hard.  
28. **Future work?** Mobile deployment, more classes (e-waste, organic), better auth, cloud DB.  
29. **What is deep learning here?** Convolutional neural network inside YOLO learns image features.  
30. **Explain one full user flow.** Upload → preprocess → YOLO+NMS → class+score → recommendation → SQLite → show result/history.

---

## Configuration tips

Edit `config.py` for:

- `CONFIDENCE_THRESHOLD`, `IOU_THRESHOLD`  
- `TRAIN_EPOCHS`, `TRAIN_BATCH`, `TRAIN_DEVICE`  
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`  
- `DEMO_COCO_TO_WASTE` mapping  
- Class list `CLASS_NAMES` (also update `dataset/data.yaml`)

---

## License / academic use

Built as a modular teaching/demo project. Replace demo credentials before any public deployment. Collect and annotate your own dataset for reported accuracy in the project report.
