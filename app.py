"""
Flask application — Waste Detection, Classification & Recycling System.

Run:
  python app.py
Then open http://127.0.0.1:5001
"""

from __future__ import annotations

import uuid
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

import config
from database import (
    add_category,
    add_user,
    clear_all_detections,
    delete_detection,
    delete_user,
    detection_stats,
    get_detection,
    get_recommendations_map,
    init_db,
    list_categories,
    list_dataset_images,
    list_detections,
    list_users,
    register_dataset_image,
    save_detection,
    update_recommendation,
    verify_user,
)
from detection import detect_waste, model_status
from evaluation.evaluate import get_model_metrics
from recommendations import list_all_recommendations

app = Flask(
    __name__,
    template_folder=str(config.BASE_DIR / "frontend" / "templates"),
    static_folder=str(config.BASE_DIR / "frontend" / "static"),
)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            flash("Please log in as admin.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_globals():
    return {
        "class_names": config.CLASS_NAMES,
        "model_info": model_status(),
    }


# ---------------------------------------------------------------------------
# Main user routes
# ---------------------------------------------------------------------------

@app.route("/login")
def login():
    """Landing page with user type selection."""
    return render_template("login.html")


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    """User login page."""
    if request.method == "POST":
        user = verify_user(request.form.get("username", ""), request.form.get("password", ""))
        if user and user["role"] == "user":
            session["user"] = True
            session["username"] = user["username"]
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
        elif user and user["role"] == "admin":
            flash("Please use admin login.", "error")
            return redirect(url_for("user_login"))
        flash("Invalid credentials.", "error")
    return render_template("user_login.html")


@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    """New user registration."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm", "").strip()
        if not username or not password:
            flash("Username and password are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
        else:
            try:
                add_user(username, password, "user")
                flash(f"Account created! Welcome, {username}. Please log in.", "success")
                return redirect(url_for("user_login"))
            except Exception:
                flash("Username already taken. Please choose another.", "error")
    return render_template("register.html")


@app.route("/user/logout")
def user_logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/")
def index():
    # Redirect to login if not authenticated
    if not session.get("user") and not session.get("admin"):
        return redirect(url_for("login"))
    history = list_detections(limit=10)
    return render_template("index.html", history=history)


@app.route("/live_detection")
def live_detection():
    if not session.get("user") and not session.get("admin"):
        return redirect(url_for("login"))
    return render_template("live_detection.html")


@app.route("/bin_locations")
def bin_locations():
    if not session.get("user") and not session.get("admin"):
        return redirect(url_for("login"))
    return render_template(
        "bin_locations.html",
        bin_locations=config.BIN_LOCATIONS,
        map_center=getattr(config, "MAP_DEFAULT_CENTER", {"lat": 12.9716, "lng": 77.5946, "zoom": 17}),
    )


@app.route("/api/bin_locations")
def api_bin_locations():
    """JSON API returning all bin and waste recycling centers with GPS coordinates."""
    return jsonify({
        "success": True,
        "center": getattr(config, "MAP_DEFAULT_CENTER", {"lat": 12.9716, "lng": 77.5946, "zoom": 17}),
        "bins": config.BIN_LOCATIONS,
    })


@app.route("/detect", methods=["POST"])
def detect():
    """Upload / capture image → preprocess → YOLO → recommend → store."""
    file = request.files.get("image")
    if not file or file.filename == "":
        flash("Please choose or capture an image first.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Unsupported file type. Use JPG, PNG, BMP, or WEBP.", "error")
        return redirect(url_for("index"))

    ext = file.filename.rsplit(".", 1)[1].lower()
    fname = f"{uuid.uuid4().hex}.{ext}"
    save_path = config.UPLOAD_DIR / fname
    file.save(save_path)

    rec_map = get_recommendations_map()
    result = detect_waste(save_path, recommendations_map=rec_map, save_result=True)

    # Get bin location based on detected class
    bin_location = None
    if result["primary_class"]:
        bin_info = config.BIN_LOCATIONS.get(result["primary_class"]) or config.BIN_LOCATIONS.get("other")
        if bin_info:
            bin_location = bin_info.get("location")

    det_id = save_detection(
        original_image=f"uploads/{fname}",
        result_image=result["result_image"] or "",
        detections=result["detections"],
        primary_class=result["primary_class"],
        primary_confidence=result["primary_confidence"],
        recommendation=result["primary_recommendation"] or "",
        bin_location=bin_location,
        model_mode=result["model_mode"],
    )

    return render_template(
        "result.html",
        result=result,
        upload_url=f"uploads/{fname}",
        detection_id=det_id,
        bin_location=bin_location,
        model_metrics=get_model_metrics(),
    )


@app.route("/history")
def history():
    if not session.get("user") and not session.get("admin"):
        return redirect(url_for("login"))
    records = list_detections(limit=100)
    return render_template("history.html", records=records)


@app.route("/history/<int:detection_id>")
def history_detail(detection_id: int):
    record = get_detection(detection_id)
    if not record:
        flash("Record not found.", "error")
        return redirect(url_for("history"))
    return render_template(
        "history_detail.html",
        record=record,
        model_metrics=get_model_metrics(),
    )


@app.route("/history/<int:detection_id>/delete", methods=["POST"])
def delete_history_record(detection_id: int):
    if delete_detection(detection_id):
        flash("Record deleted.", "success")
    else:
        flash("Record not found.", "error")
    return redirect(url_for("history"))


@app.route("/history/clear", methods=["POST"])
def clear_history():
    count = clear_all_detections()
    flash(f"Cleared {count} detection records.", "success")
    return redirect(url_for("history"))


@app.route("/api/detect", methods=["POST"])
def api_detect():
    """JSON API for detection (useful for demos / mobile later)."""
    file = request.files.get("image")
    if not file:
        return jsonify({"success": False, "error": "No image"}), 400
    ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "error": "Bad file type"}), 400
    fname = f"{uuid.uuid4().hex}.{ext}"
    path = config.UPLOAD_DIR / fname
    file.save(path)
    result = detect_waste(path, recommendations_map=get_recommendations_map())
    
    # Get bin location
    bin_location = None
    if result["primary_class"]:
        bin_info = config.BIN_LOCATIONS.get(result["primary_class"]) or config.BIN_LOCATIONS.get("other")
        if bin_info:
            bin_location = bin_info["location"]
    
    save_detection(
        original_image=f"uploads/{fname}",
        result_image=result["result_image"] or "",
        detections=result["detections"],
        primary_class=result["primary_class"],
        primary_confidence=result["primary_confidence"],
        recommendation=result["primary_recommendation"] or "",
        bin_location=bin_location,
        model_mode=result["model_mode"],
    )
    result["bin_location"] = bin_location
    return jsonify(result)


@app.route("/api/live_detect", methods=["POST"])
def api_live_detect():
    """JSON API for live detection from base64 image data."""
    data = request.get_json()
    if not data or "image_data" not in data:
        return jsonify({"success": False, "error": "No image data"}), 400
    
    import base64
    import io
    from PIL import Image
    
    try:
        raw_data = data["image_data"]
        # Safe base64 decoding (handle data URL prefix if present)
        if "," in raw_data:
            image_b64 = raw_data.split(",", 1)[1]
        else:
            image_b64 = raw_data
            
        image_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Ensure image is in RGB mode for JPEG encoding / YOLO
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Save temp image for detection
        fname = f"live_{uuid.uuid4().hex}.jpg"
        save_path = config.UPLOAD_DIR / fname
        image.save(save_path, "JPEG", quality=85)
        
        # Run detection
        rec_map = get_recommendations_map()
        result = detect_waste(save_path, recommendations_map=rec_map, save_result=False)
        
        # Get bin location and map coordinates
        bin_location = None
        bin_type = None
        bin_facility = None
        bin_lat = None
        bin_lng = None
        
        if result["primary_class"]:
            bin_info = config.BIN_LOCATIONS.get(result["primary_class"]) or config.BIN_LOCATIONS.get("other")
            if bin_info:
                bin_location = bin_info.get("location")
                bin_type = bin_info.get("bin_type")
                bin_facility = bin_info.get("facility_name")
                bin_lat = bin_info.get("lat")
                bin_lng = bin_info.get("lng")
        
        response = {
            "success": True,
            "primary_class": result["primary_class"],
            "confidence": result["primary_confidence"],
            "confidence_pct": round(result["primary_confidence"] * 100, 1) if result["primary_confidence"] else 0,
            "bin_type": bin_type,
            "bin_location": bin_location,
            "bin_facility": bin_facility,
            "bin_lat": bin_lat,
            "bin_lng": bin_lng,
            "recommendation": result["primary_recommendation"],
            "detections": result["detections"],
        }
        
        # Clean up temp file
        save_path.unlink(missing_ok=True)
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/save_live_detection", methods=["POST"])
def api_save_live_detection():
    """Save a live detection to history."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    
    try:
        det_id = save_detection(
            original_image=data.get("original_image", ""),
            result_image=data.get("result_image", ""),
            detections=data.get("detections", []),
            primary_class=data.get("primary_class"),
            primary_confidence=data.get("primary_confidence"),
            recommendation=data.get("recommendation", ""),
            bin_location=data.get("bin_location"),
            model_mode=data.get("model_mode", "live"),
        )
        return jsonify({"success": True, "detection_id": det_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = verify_user(request.form.get("username", ""), request.form.get("password", ""))
        if user and user["role"] == "admin":
            session["admin"] = True
            session["username"] = user["username"]
            flash("Welcome, admin.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid credentials.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = detection_stats()
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        users=list_users(),
        categories=list_categories(),
        recommendations=list_all_recommendations(get_recommendations_map()),
        dataset_images=list_dataset_images(50),
        model_info=model_status(),
    )


@app.route("/admin/users", methods=["POST"])
@admin_required
def admin_users():
    action = request.form.get("action")
    if action == "add":
        try:
            add_user(request.form["username"], request.form["password"], request.form.get("role", "user"))
            flash("User added.", "success")
        except Exception as e:
            flash(f"Could not add user: {e}", "error")
    elif action == "delete":
        delete_user(int(request.form["user_id"]))
        flash("User deleted (admins protected).", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/categories", methods=["POST"])
@admin_required
def admin_categories():
    try:
        add_category(
            request.form["name"],
            int(request.form["class_id"]),
            request.form.get("description", ""),
        )
        flash("Category added. Also update dataset/data.yaml and retrain for YOLO.", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/recommendations", methods=["POST"])
@admin_required
def admin_recommendations():
    update_recommendation(
        request.form["class_name"],
        request.form["category"],
        request.form["recommendation"],
        request.form.get("disposal_tips", ""),
    )
    flash("Recommendation updated (no model retrain needed).", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/dataset", methods=["POST"])
@admin_required
def admin_dataset():
    file = request.files.get("image")
    class_name = request.form.get("class_name", "plastic")
    split = request.form.get("split", "train")
    if not file or not allowed_file(file.filename):
        flash("Invalid image.", "error")
        return redirect(url_for("admin_dashboard"))

    fname = secure_filename(f"{class_name}_{uuid.uuid4().hex[:8]}_{file.filename}")
    dest_dir = config.IMAGES_DIR / split
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / fname
    file.save(dest)

    # Placeholder full-frame label for the chosen class
    class_id = config.CLASS_TO_ID.get(class_name, 0)
    lbl_dir = config.LABELS_DIR / split
    lbl_dir.mkdir(parents=True, exist_ok=True)
    with open(lbl_dir / f"{dest.stem}.txt", "w", encoding="utf-8") as f:
        f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

    register_dataset_image(fname, class_name, split)
    flash(
        f"Saved to dataset/images/{split}/. Placeholder label created — "
        "replace with real bounding boxes before serious training.",
        "success",
    )
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reports")
@admin_required
def admin_reports():
    return render_template(
        "admin_reports.html",
        stats=detection_stats(),
        records=list_detections(200),
    )


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def create_app():
    init_db()
    return app


if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("Waste Detection & Recycling System")
    print("Open: http://127.0.0.1:5001")
    print("Admin: http://127.0.0.1:5001/admin/login")
    print(f"Default admin -> {config.ADMIN_USERNAME} / {config.ADMIN_PASSWORD}")
    print("Model:", model_status()["note"])
    print("=" * 60)
    # Port 5001 avoids conflict with other local Flask apps on 5000
    app.run(host="0.0.0.0", port=5001, debug=True)
