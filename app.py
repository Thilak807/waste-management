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
    get_waste_points_rules,
    get_waste_points_map,
    update_waste_point_rule,
    add_waste_point_rule,
    delete_waste_point_rule,
    list_smart_machines,
    get_smart_machine,
    reset_smart_machine,
    update_smart_machine_status,
    ensure_user_gamification,
    get_user_by_qr_token,
    get_user_rewards_profile,
    record_disposal,
    list_rewards_catalog,
    redeem_reward,
    get_leaderboard,
    list_all_disposals,
    add_reward,
    delete_reward,
    toggle_reward,
    get_db,
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
    user_points = 0
    user_level_title = "Seedling"
    qr_token = ""
    user_id = session.get("user_id")
    username = session.get("username")

    if username:
        if not user_id:
            with get_db() as conn:
                u_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
                if u_row:
                    user_id = u_row["id"]
                    session["user_id"] = user_id
        if user_id:
            prof = get_user_rewards_profile(user_id)
            user_points = prof.get("current_balance", 0)
            user_level_title = prof.get("level_title", "Seedling")
            qr_token = prof.get("qr_token", "")

    return {
        "class_names": config.CLASS_NAMES,
        "model_info": model_status(),
        "user_points": user_points,
        "user_level_title": user_level_title,
        "user_qr_token": qr_token,
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
            session["user_id"] = user["id"]
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
    # Ensure visitor has session to explore all master landing page features directly
    if not session.get("user") and not session.get("admin"):
        session["user"] = True
        session["username"] = "user"
        session["user_id"] = 2
    
    history = list_detections(limit=10)
    user_id = session.get("user_id")
    username = session.get("username")
    if not user_id and username:
        with get_db() as conn:
            u_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if u_row:
                user_id = u_row["id"]
                session["user_id"] = user_id

    user_profile = get_user_rewards_profile(user_id) if user_id else None
    smart_machines = list_smart_machines()
    points_rules = get_waste_points_rules(only_active=True)
    registered_users = list_users()
    rewards_catalog = list_rewards_catalog()
    leaderboard = get_leaderboard(20)

    return render_template(
        "index.html",
        history=history,
        model_info=model_status(),
        stats=detection_stats(),
        smart_machines=smart_machines,
        points_rules=points_rules,
        registered_users=registered_users,
        user_profile=user_profile,
        rewards_catalog=rewards_catalog,
        leaderboard=leaderboard,
        current_user_id=user_id,
        current_username=username,
        bin_locations=config.BIN_LOCATIONS,
        map_center=getattr(config, "MAP_DEFAULT_CENTER", {"lat": 12.9716, "lng": 77.5946, "zoom": 17}),
        model_metrics=get_model_metrics(),
    )


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

    # Calculate estimated recyclable items & reward points + cash payout from active rules
    CASH_RATES = {
        "plastic": 2.00,
        "metal": 5.00,
        "glass": 3.50,
        "cardboard": 4.00,
        "paper": 1.50,
        "organic": 1.00,
        "other": 1.00,
        "trash": 0.50,
    }

    rules_map = get_waste_points_map()
    deposit_items = []
    total_est_points = 0
    total_est_weight = 0.0
    total_est_cash = 0.0

    for d in result.get("detections", []):
        cls_name = d.get("class_name", "other").lower()
        rule = rules_map.get(cls_name) or rules_map.get("other", {"points_per_item": 5, "base_weight_kg": 0.05, "display_name": "Recyclable Item", "icon": "🗑️"})
        pts = rule.get("points_per_item", 5)
        w = rule.get("base_weight_kg", 0.05)
        cash = CASH_RATES.get(cls_name, 2.00)
        total_est_points += pts
        total_est_weight += w
        total_est_cash += cash
        deposit_items.append({
            "class_name": cls_name,
            "display_name": rule.get("display_name", cls_name.title()),
            "icon": rule.get("icon", "🗑️"),
            "points": pts,
            "cash_rate": cash,
            "weight_kg": round(w, 3),
            "quantity": 1,
        })

    if not deposit_items and result.get("primary_class"):
        cls_name = result["primary_class"].lower()
        rule = rules_map.get(cls_name) or rules_map.get("other", {"points_per_item": 5, "base_weight_kg": 0.05, "display_name": "Recyclable Item", "icon": "🗑️"})
        pts = rule.get("points_per_item", 5)
        w = rule.get("base_weight_kg", 0.05)
        cash = CASH_RATES.get(cls_name, 2.00)
        total_est_points = pts
        total_est_weight = w
        total_est_cash = cash
        deposit_items.append({
            "class_name": cls_name,
            "display_name": rule.get("display_name", cls_name.title()),
            "icon": rule.get("icon", "🗑️"),
            "points": pts,
            "cash_rate": cash,
            "weight_kg": round(w, 3),
            "quantity": 1,
        })

    smart_machines = list_smart_machines()
    registered_users = list_users()
    waste_points_rules = get_waste_points_rules()

    wants_json = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or (request.accept_mimetypes.best_match(["text/html", "application/json"]) == "application/json")
    )
    if wants_json:
        result["detection_id"] = det_id
        result["upload_url"] = f"uploads/{fname}"
        result["bin_location"] = bin_location
        result["deposit_items"] = deposit_items
        result["total_est_points"] = total_est_points
        result["total_est_weight"] = round(total_est_weight, 3)
        result["total_est_cash"] = round(total_est_cash, 2)
        return jsonify(result)

    history = list_detections(limit=10)
    user_id = session.get("user_id")
    user_profile = get_user_rewards_profile(user_id) if user_id else None

    return render_template(
        "result.html",
        result=result,
        upload_url=f"uploads/{fname}",
        detection_id=det_id,
        bin_location=bin_location,
        model_metrics=get_model_metrics(),
        deposit_items=deposit_items,
        total_est_points=total_est_points,
        total_est_weight=round(total_est_weight, 3),
        total_est_cash=round(total_est_cash, 2),
        smart_machines=smart_machines,
        registered_users=registered_users,
        points_rules=waste_points_rules,
        waste_points_rules=waste_points_rules,
        bin_locations=config.BIN_LOCATIONS,
        map_center=getattr(config, "MAP_DEFAULT_CENTER", {"lat": 12.9716, "lng": 77.5946, "zoom": 17}),
        history=history,
        user_profile=user_profile,
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
    upcycling_products = []
    if record.get("primary_class"):
        rec = get_recommendation(record["primary_class"])
        upcycling_products = rec.get("what_can_be_made", [])
    return render_template(
        "history_detail.html",
        record=record,
        model_metrics=get_model_metrics(),
        upcycling_products=upcycling_products,
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


# ---------------------------------------------------------------------------
# Smart Waste Disposal & Reward System Routes
# ---------------------------------------------------------------------------

@app.route("/rewards")
def rewards():
    """User Rewards & Gamification Dashboard."""
    if not session.get("user") and not session.get("admin"):
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    username = session.get("username")
    if not user_id and username:
        with get_db() as conn:
            u_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if u_row:
                user_id = u_row["id"]
                session["user_id"] = user_id

    profile = get_user_rewards_profile(user_id) if user_id else {}
    catalog = list_rewards_catalog()
    machines = list_smart_machines()
    points_rules = get_waste_points_rules(only_active=True)
    leaderboard = get_leaderboard(10)

    return render_template(
        "rewards.html",
        profile=profile,
        catalog=catalog,
        machines=machines,
        points_rules=points_rules,
        leaderboard=leaderboard,
    )


@app.route("/machine")
def smart_machine_view():
    """Interactive Reverse Vending Machine (RVM) Kiosk interface."""

    machines = list_smart_machines()
    points_rules = get_waste_points_rules(only_active=True)
    users = list_users()
    current_user_id = session.get("user_id")
    current_username = session.get("username")
    user_profile = get_user_rewards_profile(current_user_id) if current_user_id else None

    return render_template(
        "machine.html",
        machines=machines,
        points_rules=points_rules,
        users=users,
        current_user_id=current_user_id,
        current_username=current_username,
        user_profile=user_profile,
    )


@app.route("/leaderboard")
def leaderboard_view():
    """Campus & Community Recycling Leaderboard."""
    leaderboard = get_leaderboard(50)
    return render_template("leaderboard.html", leaderboard=leaderboard)


@app.route("/api/detect", methods=["POST"])
def api_detect():
    """JSON API for detection (used for seamless all-in-one single-page detection)."""
    file = request.files.get("image")
    if not file:
        return jsonify({"success": False, "error": "No image provided"}), 400
    ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        return jsonify({"success": False, "error": "Bad file type. Use JPG, PNG, WEBP."}), 400
    fname = f"{uuid.uuid4().hex}.{ext}"
    path = config.UPLOAD_DIR / fname
    file.save(path)
    
    rec_map = get_recommendations_map()
    result = detect_waste(path, recommendations_map=rec_map, save_result=True)
    
    # Get bin location & metadata
    bin_location = None
    bin_info = None
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

    # Calculate estimated recyclable items & reward points from active rules
    rules_map = get_waste_points_map()
    deposit_items = []
    total_est_points = 0
    total_est_weight = 0.0

    for d in result.get("detections", []):
        cls_name = d.get("class_name", "other").lower()
        rule = rules_map.get(cls_name) or rules_map.get("other", {"points_per_item": 5, "base_weight_kg": 0.05, "display_name": "Recyclable Item", "icon": "🗑️"})
        pts = rule.get("points_per_item", 5)
        w = rule.get("base_weight_kg", 0.05)
        total_est_points += pts
        total_est_weight += w
        deposit_items.append({
            "class_name": cls_name,
            "display_name": rule.get("display_name", cls_name.title()),
            "icon": rule.get("icon", "🗑️"),
            "points": pts,
            "weight_kg": round(w, 3),
            "quantity": 1,
        })

    if not deposit_items and result.get("primary_class"):
        cls_name = result["primary_class"].lower()
        rule = rules_map.get(cls_name) or rules_map.get("other", {"points_per_item": 5, "base_weight_kg": 0.05, "display_name": "Recyclable Item", "icon": "🗑️"})
        pts = rule.get("points_per_item", 5)
        w = rule.get("base_weight_kg", 0.05)
        total_est_points = pts
        total_est_weight = w
        deposit_items.append({
            "class_name": cls_name,
            "display_name": rule.get("display_name", cls_name.title()),
            "icon": rule.get("icon", "🗑️"),
            "points": pts,
            "weight_kg": round(w, 3),
            "quantity": 1,
        })

    result["detection_id"] = det_id
    result["upload_url"] = f"uploads/{fname}"
    result["bin_location"] = bin_location
    result["bin_info"] = bin_info
    result["deposit_items"] = deposit_items
    result["total_est_points"] = total_est_points
    result["total_est_weight"] = round(total_est_weight, 3)
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
        result = detect_waste(save_path, recommendations_map=rec_map, save_result=True)
        
        # Get bin location and map coordinates
        bin_location = None
        bin_type = None
        bin_facility = None
        bin_lat = None
        bin_lng = None
        bin_color = "#34d399"
        bin_icon = "🗑️"
        bin_info = None
        
        if result["primary_class"]:
            bin_info = config.BIN_LOCATIONS.get(result["primary_class"]) or config.BIN_LOCATIONS.get("other")
            if bin_info:
                bin_location = bin_info.get("location")
                bin_type = bin_info.get("bin_type")
                bin_facility = bin_info.get("facility_name")
                bin_lat = bin_info.get("lat")
                bin_lng = bin_info.get("lng")
                bin_color = bin_info.get("color", "#34d399")
                bin_icon = bin_info.get("icon", "🗑️")
        
        # Auto-save live detection to database if valid detection found
        det_id = None
        if result.get("primary_class"):
            det_id = save_detection(
                original_image=f"uploads/{fname}",
                result_image=result["result_image"] or "",
                detections=result["detections"],
                primary_class=result["primary_class"],
                primary_confidence=result["primary_confidence"],
                recommendation=result["primary_recommendation"] or "",
                bin_location=bin_location,
                model_mode="live",
            )

        rules_map = get_waste_points_map()
        deposit_items = []
        total_est_points = 0
        total_est_weight = 0.0

        for d in result.get("detections", []):
            cls_name = d.get("class_name", "other").lower()
            rule = rules_map.get(cls_name) or rules_map.get("other", {"points_per_item": 5, "base_weight_kg": 0.05, "display_name": "Recyclable Item", "icon": "🗑️"})
            pts = rule.get("points_per_item", 5)
            w = rule.get("base_weight_kg", 0.05)
            total_est_points += pts
            total_est_weight += w
            deposit_items.append({
                "class_name": cls_name,
                "display_name": rule.get("display_name", cls_name.title()),
                "icon": rule.get("icon", "🗑️"),
                "points": pts,
                "weight_kg": round(w, 3),
                "quantity": 1,
            })

        if not deposit_items and result.get("primary_class"):
            cls_name = result["primary_class"].lower()
            rule = rules_map.get(cls_name) or rules_map.get("other", {"points_per_item": 5, "base_weight_kg": 0.05, "display_name": "Recyclable Item", "icon": "🗑️"})
            pts = rule.get("points_per_item", 5)
            w = rule.get("base_weight_kg", 0.05)
            total_est_points = pts
            total_est_weight = w
            deposit_items.append({
                "class_name": cls_name,
                "display_name": rule.get("display_name", cls_name.title()),
                "icon": rule.get("icon", "🗑️"),
                "points": pts,
                "weight_kg": round(w, 3),
                "quantity": 1,
            })

        response = {
            "success": True,
            "detection_id": det_id,
            "primary_class": result["primary_class"],
            "confidence": result["primary_confidence"],
            "confidence_pct": round(result["primary_confidence"] * 100, 1) if result["primary_confidence"] else 0,
            "bin_type": bin_type,
            "bin_location": bin_location,
            "bin_facility": bin_facility,
            "bin_lat": bin_lat,
            "bin_lng": bin_lng,
            "bin_color": bin_color,
            "bin_icon": bin_icon,
            "bin_info": bin_info,
            "recommendation": result["primary_recommendation"],
            "what_can_be_made": result.get("what_can_be_made", []),
            "detections": result["detections"],
            "result_image": result.get("result_image"),
            "upload_url": f"uploads/{fname}",
            "deposit_items": deposit_items,
            "total_est_points": total_est_points,
            "total_est_weight": round(total_est_weight, 3),
        }
        
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


@app.route("/api/disposal/deposit", methods=["POST"])
def api_disposal_deposit():
    """Submit a waste disposal transaction from Detection page or Kiosk."""
    data = request.get_json() or {}
    user_id = data.get("user_id") or session.get("user_id")
    qr_token = data.get("qr_token")

    if qr_token:
        u_by_qr = get_user_by_qr_token(qr_token)
        if u_by_qr:
            user_id = u_by_qr["user_id"]

    if not user_id:
        username = session.get("username", "user")
        with get_db() as conn:
            u_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if u_row:
                user_id = u_row["id"]
            else:
                user_id = 2

    with get_db() as conn:
        u_row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        username = u_row["username"] if u_row else "user"

    machine_id = data.get("machine_id", "RVM-01-CAMPUS-NORTH")
    items = data.get("items", [])
    if not items:
        return jsonify({"success": False, "error": "No waste items provided for deposit."}), 400

    detection_id = data.get("detection_id")
    result = record_disposal(
        user_id=user_id,
        username=username,
        machine_id=machine_id,
        items=items,
        detection_id=detection_id,
    )
    if result.get("success"):
        session["user_points"] = result.get("new_balance")
        if not session.get("user_id"):
            session["user_id"] = user_id
            session["username"] = username
    return jsonify(result)


@app.route("/api/rewards/redeem", methods=["POST"])
def api_rewards_redeem():
    """Redeem a reward using accumulated points."""
    data = request.get_json() or {}
    reward_id = data.get("reward_id")
    if not reward_id:
        return jsonify({"success": False, "error": "Missing reward ID."}), 400

    user_id = session.get("user_id")
    username = session.get("username")
    if not user_id and username:
        with get_db() as conn:
            u_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if u_row:
                user_id = u_row["id"]
                session["user_id"] = user_id

    if not user_id:
        return jsonify({"success": False, "error": "Please log in to redeem rewards."}), 401

    result = redeem_reward(user_id=user_id, username=username, reward_id=int(reward_id))
    return jsonify(result)


@app.route("/api/user/qr-lookup")
def api_user_qr_lookup():
    """Look up user profile by QR code token for Smart Machine login."""
    token = request.args.get("token", "").strip()
    if not token:
        return jsonify({"success": False, "error": "No token provided."}), 400
    user = get_user_by_qr_token(token)
    if not user:
        return jsonify({"success": False, "error": "User not found with this QR token."}), 404

    profile = get_user_rewards_profile(user["user_id"])
    return jsonify({
        "success": True,
        "user_id": user["user_id"],
        "username": user["username"],
        "total_points": profile["total_points"],
        "current_balance": profile["current_balance"],
        "level": profile["level_info"]["level"],
        "level_title": profile["level_info"]["title"],
        "streak_days": profile["streak_days"],
        "qr_token": user["qr_token"],
    })


@app.route("/api/smart_machines")
def api_smart_machines():
    """Return live list of smart reverse vending machines."""
    return jsonify({
        "success": True,
        "machines": list_smart_machines(),
    })


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
            session["user_id"] = user["id"]
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
        waste_points_rules=get_waste_points_rules(),
        smart_machines=list_smart_machines(),
        rewards_catalog=list_rewards_catalog(only_active=False),
        recent_disposals=list_all_disposals(limit=30),
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


@app.route("/admin/waste-points", methods=["POST"])
@admin_required
def admin_waste_points():
    action = request.form.get("action", "update")
    if action == "update":
        category_code = request.form.get("category_code")
        pts_item = int(request.form.get("points_per_item", 5))
        pts_kg = float(request.form.get("points_per_kg", 50.0))
        is_active = 1 if request.form.get("is_active") else 0
        display_name = request.form.get("display_name")
        update_waste_point_rule(category_code, pts_item, pts_kg, is_active, display_name)
        flash(f"Updated reward configuration for {display_name or category_code}.", "success")
    elif action == "add":
        try:
            add_waste_point_rule(
                category_code=request.form["category_code"],
                display_name=request.form["display_name"],
                points_per_item=int(request.form.get("points_per_item", 5)),
                points_per_kg=float(request.form.get("points_per_kg", 50.0)),
                base_weight_kg=float(request.form.get("base_weight_kg", 0.05)),
                icon=request.form.get("icon", "🗑️"),
                color=request.form.get("color", "#34d399"),
            )
            flash("Added new waste type and point configuration.", "success")
        except Exception as e:
            flash(f"Error adding waste category: {e}", "error")
    elif action == "delete":
        delete_waste_point_rule(int(request.form["rule_id"]))
        flash("Deleted waste point rule.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/rewards", methods=["POST"])
@admin_required
def admin_rewards():
    action = request.form.get("action", "add")
    if action == "add":
        try:
            add_reward(
                title=request.form["title"],
                description=request.form.get("description", ""),
                category=request.form.get("category", "voucher"),
                points_required=int(request.form["points_required"]),
                reward_value=request.form["reward_value"],
                code_prefix=request.form.get("code_prefix", "ECO"),
                icon=request.form.get("icon", "🎁"),
                stock=int(request.form.get("stock", 100)),
            )
            flash("New reward added to catalog.", "success")
        except Exception as e:
            flash(f"Error adding reward: {e}", "error")
    elif action == "delete":
        delete_reward(int(request.form["reward_id"]))
        flash("Reward removed from catalog.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/machines/reset", methods=["POST"])
@admin_required
def admin_machines_reset():
    m_id = int(request.form.get("machine_id"))
    reset_smart_machine(m_id)
    flash("Smart Reverse Vending Machine has been emptied and reset.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/transactions")
@admin_required
def admin_transactions():
    transactions = list_all_disposals(limit=200)
    return render_template(
        "admin_transactions.html",
        transactions=transactions,
        stats=detection_stats(),
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
