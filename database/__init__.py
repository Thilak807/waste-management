"""
SQLite database layer for detection history, users, categories, and recommendations.

Designed to be swappable later for Firebase/cloud storage by isolating
all SQL inside this module.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import config


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and seed default data if empty."""
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS waste_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                class_id INTEGER NOT NULL,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                disposal_tips TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_image TEXT NOT NULL,
                result_image TEXT,
                detections_json TEXT NOT NULL,
                primary_class TEXT,
                primary_confidence REAL,
                recommendation TEXT,
                bin_location TEXT,
                model_mode TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS dataset_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                class_name TEXT,
                split TEXT DEFAULT 'train',
                annotated INTEGER DEFAULT 0,
                uploaded_at TEXT NOT NULL
            );

            -- ── Smart Waste Disposal & Reward System Tables ───────────
            CREATE TABLE IF NOT EXISTS waste_points_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_code TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                points_per_item INTEGER NOT NULL DEFAULT 5,
                points_per_kg REAL NOT NULL DEFAULT 50.0,
                base_weight_kg REAL NOT NULL DEFAULT 0.05,
                icon TEXT NOT NULL DEFAULT '🗑️',
                color TEXT NOT NULL DEFAULT '#34d399',
                is_active INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS smart_machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                floor_building TEXT,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'online',
                fill_percentage REAL NOT NULL DEFAULT 15.0,
                capacity_items INTEGER NOT NULL DEFAULT 500,
                total_items_collected INTEGER NOT NULL DEFAULT 0,
                last_emptied_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS disposal_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                waste_category TEXT NOT NULL,
                item_type TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                weight_kg REAL NOT NULL DEFAULT 0.0,
                points_earned INTEGER NOT NULL DEFAULT 0,
                detection_id INTEGER,
                status TEXT NOT NULL DEFAULT 'verified',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                points_required INTEGER NOT NULL,
                reward_value TEXT NOT NULL,
                code_prefix TEXT NOT NULL DEFAULT 'REWARD',
                icon TEXT NOT NULL DEFAULT '🎁',
                stock INTEGER NOT NULL DEFAULT 100,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS redemptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                reward_id INTEGER NOT NULL,
                reward_title TEXT NOT NULL,
                points_spent INTEGER NOT NULL,
                voucher_code TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_gamification (
                user_id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                total_points INTEGER NOT NULL DEFAULT 0,
                current_balance INTEGER NOT NULL DEFAULT 0,
                total_items_recycled INTEGER NOT NULL DEFAULT 0,
                total_weight_kg REAL NOT NULL DEFAULT 0.0,
                streak_days INTEGER NOT NULL DEFAULT 1,
                last_deposit_date TEXT,
                level INTEGER NOT NULL DEFAULT 1,
                level_title TEXT NOT NULL DEFAULT 'Seedling Recycler',
                badges_json TEXT NOT NULL DEFAULT '[]',
                qr_token TEXT UNIQUE NOT NULL
            );
            """
        )

        # Auto-migrate any existing detections table that might be missing bin_location
        cols = [c["name"] for c in conn.execute("PRAGMA table_info(detections)").fetchall()]
        if "bin_location" not in cols:
            conn.execute("ALTER TABLE detections ADD COLUMN bin_location TEXT")

        # Seed admin + demo user (plain demo hash marker — college project simplicity)
        cur = conn.execute("SELECT COUNT(*) AS c FROM users")
        if cur.fetchone()["c"] == 0:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                (config.ADMIN_USERNAME, f"plain:{config.ADMIN_PASSWORD}", "admin", _now()),
            )
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                ("user", "plain:user123", "user", _now()),
            )

        # Ensure all existing users have a corresponding gamification record
        all_users = conn.execute("SELECT id, username FROM users").fetchall()
        for u in all_users:
            g_cur = conn.execute("SELECT user_id FROM user_gamification WHERE user_id = ?", (u["id"],)).fetchone()
            if not g_cur:
                token = f"USER-{u['id']:04d}-{u['username'][:4].upper()}"
                conn.execute(
                    """
                    INSERT INTO user_gamification
                    (user_id, username, total_points, current_balance, total_items_recycled, total_weight_kg, streak_days, level, level_title, badges_json, qr_token)
                    VALUES (?, ?, 50, 50, 5, 0.25, 1, 1, 'Seedling Recycler', '[]', ?)
                    """,
                    (u["id"], u["username"], token),
                )

        # Seed categories
        cur = conn.execute("SELECT COUNT(*) AS c FROM waste_categories")
        if cur.fetchone()["c"] == 0:
            for name, cid in config.CLASS_TO_ID.items():
                conn.execute(
                    "INSERT INTO waste_categories (name, class_id, description, is_active) VALUES (?, ?, ?, 1)",
                    (name, cid, f"{name.title()} waste category"),
                )

        # Seed recommendations
        from recommendations import DEFAULT_RECOMMENDATIONS

        cur = conn.execute("SELECT COUNT(*) AS c FROM recommendations")
        if cur.fetchone()["c"] == 0:
            for cls, data in DEFAULT_RECOMMENDATIONS.items():
                conn.execute(
                    """
                    INSERT INTO recommendations (class_name, category, recommendation, disposal_tips, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (cls, data["category"], data["recommendation"], data["disposal_tips"], _now()),
                )

        # Seed default configurable waste points rules
        cur = conn.execute("SELECT COUNT(*) AS c FROM waste_points_rules")
        if cur.fetchone()["c"] == 0:
            default_rules = [
                ("plastic_bottle", "Plastic Bottle", 5, 50.0, 0.035, "🧴", "#38bdf8"),
                ("plastic_container", "Plastic Container", 7, 60.0, 0.060, "📦", "#60a5fa"),
                ("metal_can", "Metal Can", 10, 80.0, 0.045, "🥫", "#c084fc"),
                ("aluminum_can", "Aluminum Can", 10, 90.0, 0.015, "🥤", "#a855f7"),
                ("paper", "Paper Waste", 3, 30.0, 0.020, "📄", "#4ade80"),
                ("cardboard", "Cardboard Box", 4, 40.0, 0.150, "📦", "#fb923c"),
                ("glass_bottle", "Glass Bottle", 6, 45.0, 0.280, "🍶", "#facc15"),
                ("organic", "Organic / Compost", 2, 20.0, 0.100, "🌿", "#34d399"),
                ("other", "Other Recyclable Waste", 2, 25.0, 0.050, "♻️", "#e879f9"),
            ]
            for code, name, pts, p_kg, w_kg, icon, col in default_rules:
                conn.execute(
                    """
                    INSERT INTO waste_points_rules
                    (category_code, display_name, points_per_item, points_per_kg, base_weight_kg, icon, color, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (code, name, pts, p_kg, w_kg, icon, col, _now()),
                )

        # Seed smart reverse vending machines (RVM)
        cur = conn.execute("SELECT COUNT(*) AS c FROM smart_machines")
        if cur.fetchone()["c"] == 0:
            default_machines = [
                ("RVM-01-CAMPUS-NORTH", "North Campus Smart Reverse Vending Station", "Block B Entrance (North Wing)", "Building B, Ground Floor East", 12.9722, 77.5941, "online", 32.0, 500, 160),
                ("RVM-02-LIBRARY-HUB", "Central Library Eco-Depository Machine", "Library Area & Academic Quad", "Library Ground Floor, South Entrance", 12.9712, 77.5952, "online", 18.0, 400, 72),
                ("RVM-03-SCIENCE-COMPLEX", "Science Complex Glass & Metal Depository", "Block A Entrance (Science Wing)", "Building A, West Walkway", 12.9725, 77.5949, "online", 44.0, 600, 264),
                ("RVM-04-ENG-CANTEEN", "Cafeteria & Food Court Smart RVM", "Cafeteria & Food Court Garden", "Canteen Rear Court, Garden Zone", 12.9705, 77.5950, "online", 58.0, 500, 290),
            ]
            for code, name, loc, bld, lat, lng, st, fill, cap, coll in default_machines:
                conn.execute(
                    """
                    INSERT INTO smart_machines
                    (machine_code, name, location, floor_building, lat, lng, status, fill_percentage, capacity_items, total_items_collected, last_emptied_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (code, name, loc, bld, lat, lng, st, fill, cap, coll, _now()),
                )

        # Seed default reward vouchers catalog
        cur = conn.execute("SELECT COUNT(*) AS c FROM rewards")
        if cur.fetchone()["c"] == 0:
            default_rewards = [
                ("Campus Cafeteria ₹50 Coupon", "Redeemable for snacks, coffee, and meals at any campus canteen counter.", "campus", 500, "₹50 OFF", "CAFE50", "☕", 150),
                ("Green Planet Store ₹100 Voucher", "Valid across sustainable groceries, tote bags, and organic products online.", "voucher", 900, "₹100 Voucher", "ECO100", "🌱", 80),
                ("15% Campus Bookstore Discount", "Get 15% off textbooks, stationery, notebooks, and art supplies.", "discount", 300, "15% OFF", "BOOK15", "📚", 200),
                ("Bamboo Cutlery & Straw Travel Set", "Eco-friendly reusable fork, spoon, knife, chopsticks and straw in a linen pouch.", "product", 600, "Free Item", "BAMBOO", "🥢", 45),
                ("Plant a Native Tree (Certificate)", "Funds planting of a native shade tree on campus with a verified digital certificate.", "donation", 400, "Tree Planted", "TREE", "🌳", 999),
                ("Recycled Insulated Stainless Bottle", "500ml double-wall thermal bottle made with 80% recycled food-grade steel.", "product", 1200, "Free Product", "BOTTLE", "💧", 30),
            ]
            for title, desc, cat, pts, val, prefix, icon, stk in default_rewards:
                conn.execute(
                    """
                    INSERT INTO rewards
                    (title, description, category, points_required, reward_value, code_prefix, icon, stock, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (title, desc, cat, pts, val, prefix, icon, stk, _now()),
                )


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return None
        stored = row["password_hash"]
        # Simple college-demo auth (replace with werkzeug hash in production)
        if stored == f"plain:{password}":
            return dict(row)
        return None


def list_users() -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]


def add_user(username: str, password: str, role: str = "user") -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, f"plain:{password}", role, _now()),
        )
        return int(cur.lastrowid)


def delete_user(user_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))


# ---------------------------------------------------------------------------
# Categories & recommendations
# ---------------------------------------------------------------------------

def list_categories() -> List[Dict[str, Any]]:
    with get_db() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM waste_categories ORDER BY class_id"
        ).fetchall()]


def add_category(name: str, class_id: int, description: str = "") -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO waste_categories (name, class_id, description, is_active) VALUES (?, ?, ?, 1)",
            (name.lower(), class_id, description),
        )
        return int(cur.lastrowid)


def update_recommendation(class_name: str, category: str, recommendation: str, tips: str = "") -> None:
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO recommendations (class_name, category, recommendation, disposal_tips, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(class_name) DO UPDATE SET
                category=excluded.category,
                recommendation=excluded.recommendation,
                disposal_tips=excluded.disposal_tips,
                updated_at=excluded.updated_at
            """,
            (class_name.lower(), category, recommendation, tips, _now()),
        )


def get_recommendations_map() -> Dict[str, Dict[str, str]]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM recommendations").fetchall()
        return {
            r["class_name"]: {
                "category": r["category"],
                "recommendation": r["recommendation"],
                "disposal_tips": r["disposal_tips"] or "",
            }
            for r in rows
        }


# ---------------------------------------------------------------------------
# Detections history
# ---------------------------------------------------------------------------

def save_detection(
    original_image: str,
    result_image: str,
    detections: List[Dict],
    primary_class: Optional[str],
    primary_confidence: Optional[float],
    recommendation: str,
    bin_location: Optional[str] = None,
    model_mode: str = "",
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO detections
            (original_image, result_image, detections_json, primary_class,
             primary_confidence, recommendation, bin_location, model_mode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                original_image,
                result_image,
                json.dumps(detections),
                primary_class,
                primary_confidence,
                recommendation,
                bin_location,
                model_mode,
                _now(),
            ),
        )
        return int(cur.lastrowid)


def list_detections(limit: int = 50) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM detections ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        results = []
        for r in rows:
            item = dict(r)
            item["detections"] = json.loads(item.pop("detections_json"))
            results.append(item)
        return results


def get_detection(detection_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM detections WHERE id = ?", (detection_id,)
        ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["detections"] = json.loads(item.pop("detections_json"))
        return item


def detection_stats() -> Dict[str, Any]:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM detections").fetchone()["c"]
        by_class = conn.execute(
            """
            SELECT primary_class AS class_name, COUNT(*) AS count
            FROM detections
            WHERE primary_class IS NOT NULL
            GROUP BY primary_class
            ORDER BY count DESC
            """
        ).fetchall()
        return {
            "total": total,
            "by_class": [dict(r) for r in by_class],
        }


def delete_detection(detection_id: int) -> bool:
    """Delete a single detection record by ID."""
    with get_db() as conn:
        cur = conn.execute("DELETE FROM detections WHERE id = ?", (detection_id,))
        return cur.rowcount > 0


def clear_all_detections() -> int:
    """Clear all detection records. Returns count of deleted records."""
    with get_db() as conn:
        cur = conn.execute("SELECT COUNT(*) AS c FROM detections")
        count = cur.fetchone()["c"]
        conn.execute("DELETE FROM detections")
        return count


# ---------------------------------------------------------------------------
# Dataset registry (admin)
# ---------------------------------------------------------------------------

def register_dataset_image(filename: str, class_name: str, split: str = "train") -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO dataset_images (filename, class_name, split, annotated, uploaded_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (filename, class_name, split, _now()),
        )
        return int(cur.lastrowid)


def list_dataset_images(limit: int = 100) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM dataset_images ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Smart Waste Disposal & Reward System Functions
# ---------------------------------------------------------------------------

import random
import string


def get_waste_points_rules(only_active: bool = False) -> List[Dict[str, Any]]:
    """Return all configurable waste categories and their point rates."""
    with get_db() as conn:
        sql = "SELECT * FROM waste_points_rules"
        if only_active:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY id ASC"
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]


def get_waste_points_map() -> Dict[str, Dict[str, Any]]:
    """Return dictionary of active waste points rules keyed by category_code."""
    rules = get_waste_points_rules(only_active=True)
    mapping = {r["category_code"]: r for r in rules}
    # Add common aliases for YOLO classes
    if "plastic_bottle" in mapping and "plastic" not in mapping:
        mapping["plastic"] = mapping["plastic_bottle"]
    if "metal_can" in mapping and "metal" not in mapping:
        mapping["metal"] = mapping["metal_can"]
    if "cardboard" in mapping and "paper" in mapping:
        pass
    return mapping


def update_waste_point_rule(
    category_code: str,
    points_per_item: int,
    points_per_kg: float,
    is_active: int = 1,
    display_name: Optional[str] = None,
) -> None:
    """Admin updates points values for a waste category."""
    with get_db() as conn:
        if display_name:
            conn.execute(
                """
                UPDATE waste_points_rules
                SET points_per_item = ?, points_per_kg = ?, is_active = ?, display_name = ?, updated_at = ?
                WHERE category_code = ?
                """,
                (points_per_item, points_per_kg, is_active, display_name, _now(), category_code),
            )
        else:
            conn.execute(
                """
                UPDATE waste_points_rules
                SET points_per_item = ?, points_per_kg = ?, is_active = ?, updated_at = ?
                WHERE category_code = ?
                """,
                (points_per_item, points_per_kg, is_active, _now(), category_code),
            )


def add_waste_point_rule(
    category_code: str,
    display_name: str,
    points_per_item: int = 5,
    points_per_kg: float = 50.0,
    base_weight_kg: float = 0.05,
    icon: str = "🗑️",
    color: str = "#34d399",
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO waste_points_rules
            (category_code, display_name, points_per_item, points_per_kg, base_weight_kg, icon, color, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (category_code.lower().strip(), display_name.strip(), points_per_item, points_per_kg, base_weight_kg, icon, color, _now()),
        )
        return int(cur.lastrowid)


def delete_waste_point_rule(rule_id: int) -> bool:
    with get_db() as conn:
        cur = conn.execute("DELETE FROM waste_points_rules WHERE id = ?", (rule_id,))
        return cur.rowcount > 0


# ── Smart Reverse Vending Machines (RVM) ───────────────────────────────────

def list_smart_machines() -> List[Dict[str, Any]]:
    """Return all smart disposal machines with status and fill percentage."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM smart_machines ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]


def get_smart_machine(machine_code: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM smart_machines WHERE machine_code = ?", (machine_code,)
        ).fetchone()
        return dict(row) if row else None


def reset_smart_machine(machine_id: int) -> bool:
    """Admin empties the reverse vending machine."""
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE smart_machines SET fill_percentage = 0.0, last_emptied_at = ? WHERE id = ?",
            (_now(), machine_id),
        )
        return cur.rowcount > 0


def update_smart_machine_status(machine_id: int, status: str) -> bool:
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE smart_machines SET status = ? WHERE id = ?",
            (status, machine_id),
        )
        return cur.rowcount > 0


# ── User Gamification, Badges & Profile ────────────────────────────────────

def ensure_user_gamification(user_id: int, username: str) -> Dict[str, Any]:
    """Ensure user has a gamification row with valid QR token."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM user_gamification WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not row:
            token = f"USER-{user_id:04d}-{username[:4].upper()}"
            conn.execute(
                """
                INSERT INTO user_gamification
                (user_id, username, total_points, current_balance, total_items_recycled, total_weight_kg, streak_days, level, level_title, badges_json, qr_token)
                VALUES (?, ?, 0, 0, 0, 0.0, 1, 1, 'Seedling Recycler', '[]', ?)
                """,
                (user_id, username, token),
            )
            row = conn.execute(
                "SELECT * FROM user_gamification WHERE user_id = ?", (user_id,)
            ).fetchone()
        return dict(row)


def get_user_by_qr_token(token: str) -> Optional[Dict[str, Any]]:
    """Locate user by their unique QR code token."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM user_gamification WHERE qr_token = ?", (token.strip(),)
        ).fetchone()
        if row:
            return dict(row)
        # Fallback: check by username
        row2 = conn.execute(
            "SELECT * FROM user_gamification WHERE username = ?", (token.strip(),)
        ).fetchone()
        return dict(row2) if row2 else None


def calculate_level(total_points: int) -> Dict[str, Any]:
    """Calculate user level and progress towards next tier."""
    tiers = [
        (1, "Seedling Recycler", 0, 100),
        (2, "Sprout Sorter", 100, 300),
        (3, "Eco Warrior", 300, 600),
        (4, "Green Champion", 600, 1000),
        (5, "Planet Savior", 1000, 999999),
    ]
    for lvl, title, min_pt, next_pt in tiers:
        if total_points < next_pt or lvl == 5:
            progress_pct = 100.0 if lvl == 5 else round(((total_points - min_pt) / (next_pt - min_pt)) * 100, 1)
            return {
                "level": lvl,
                "title": title,
                "min_points": min_pt,
                "next_points": next_pt,
                "progress_pct": max(0.0, min(100.0, progress_pct)),
                "points_to_next": max(0, next_pt - total_points) if lvl < 5 else 0,
            }
    return {"level": 1, "title": "Seedling Recycler", "min_points": 0, "next_points": 100, "progress_pct": 0.0, "points_to_next": 100}


def evaluate_badges(user_id: int, total_items: int, total_points: int, streak_days: int, conn) -> List[Dict[str, Any]]:
    """Determine all earned badges based on recycling statistics."""
    # Count specific categories from transactions
    cur = conn.execute(
        """
        SELECT waste_category, SUM(quantity) as qty
        FROM disposal_transactions
        WHERE user_id = ?
        GROUP BY waste_category
        """,
        (user_id,),
    )
    cat_counts = {r["waste_category"]: (r["qty"] or 0) for r in cur.fetchall()}

    plastic_count = cat_counts.get("plastic", 0) + cat_counts.get("plastic_bottle", 0) + cat_counts.get("plastic_container", 0)
    metal_count = cat_counts.get("metal", 0) + cat_counts.get("metal_can", 0) + cat_counts.get("aluminum_can", 0)
    paper_count = cat_counts.get("paper", 0) + cat_counts.get("cardboard", 0)
    glass_count = cat_counts.get("glass", 0) + cat_counts.get("glass_bottle", 0)

    all_badges = [
        {
            "id": "first_deposit",
            "name": "First Step",
            "icon": "🌱",
            "tier": "bronze",
            "description": "Recycled your first item at a Smart Station",
            "unlocked": total_items >= 1,
            "progress": min(1, total_items),
            "goal": 1,
        },
        {
            "id": "plastic_saver",
            "name": "Plastic Saver",
            "icon": "🥉",
            "tier": "bronze",
            "description": "Recycled 50 plastic bottles / containers",
            "unlocked": plastic_count >= 50,
            "progress": plastic_count,
            "goal": 50,
        },
        {
            "id": "eco_warrior",
            "name": "Eco Warrior",
            "icon": "🥈",
            "tier": "silver",
            "description": "Recycled 100 items across all categories",
            "unlocked": total_items >= 100,
            "progress": total_items,
            "goal": 100,
        },
        {
            "id": "green_champion",
            "name": "Green Champion",
            "icon": "🥇",
            "tier": "gold",
            "description": "Recycled 500 items and helped save the campus ecosystem",
            "unlocked": total_items >= 500,
            "progress": total_items,
            "goal": 500,
        },
        {
            "id": "can_crusher",
            "name": "Can Crusher",
            "icon": "🥫",
            "tier": "silver",
            "description": "Recycled 25 aluminum / metal cans",
            "unlocked": metal_count >= 25,
            "progress": metal_count,
            "goal": 25,
        },
        {
            "id": "packaging_pioneer",
            "name": "Packaging Pioneer",
            "icon": "📦",
            "tier": "bronze",
            "description": "Recycled 25 paper sheets or cardboard boxes",
            "unlocked": paper_count >= 25,
            "progress": paper_count,
            "goal": 25,
        },
        {
            "id": "streak_master",
            "name": "Recycling Streak Master",
            "icon": "🔥",
            "tier": "gold",
            "description": "Reached a 7-day consecutive recycling streak",
            "unlocked": streak_days >= 7,
            "progress": streak_days,
            "goal": 7,
        },
    ]
    return all_badges


def get_user_rewards_profile(user_id: int) -> Dict[str, Any]:
    """Fetch complete gamification profile, stats, badges, and vouchers."""
    with get_db() as conn:
        u_row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        username = u_row["username"] if u_row else f"User_{user_id}"
        gam = ensure_user_gamification(user_id, username)

        # Level calculation
        level_info = calculate_level(gam["total_points"])

        # Badges
        badges = evaluate_badges(
            user_id=user_id,
            total_items=gam["total_items_recycled"],
            total_points=gam["total_points"],
            streak_days=gam["streak_days"],
            conn=conn,
        )

        # Category breakdown
        cat_stats = conn.execute(
            """
            SELECT waste_category, SUM(quantity) as total_qty, SUM(points_earned) as total_pts, ROUND(SUM(weight_kg), 2) as total_wt
            FROM disposal_transactions
            WHERE user_id = ?
            GROUP BY waste_category
            ORDER BY total_qty DESC
            """,
            (user_id,),
        ).fetchall()

        # Recent transactions
        recent_tx = conn.execute(
            """
            SELECT * FROM disposal_transactions
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 10
            """,
            (user_id,),
        ).fetchall()

        # Active vouchers
        vouchers = conn.execute(
            """
            SELECT * FROM redemptions
            WHERE user_id = ?
            ORDER BY id DESC LIMIT 10
            """,
            (user_id,),
        ).fetchall()

        # CO2 offset calculation (approx 0.12 kg CO2 per recyclable item)
        co2_offset = round(gam["total_items_recycled"] * 0.12, 2)

        return {
            **gam,
            "level_info": level_info,
            "badges": badges,
            "unlocked_badges_count": len([b for b in badges if b["unlocked"]]),
            "category_breakdown": [dict(c) for c in cat_stats],
            "recent_transactions": [dict(t) for t in recent_tx],
            "active_vouchers": [dict(v) for v in vouchers],
            "co2_offset_kg": co2_offset,
        }


# ── Waste Disposal Recording ───────────────────────────────────────────────

def record_disposal(
    user_id: int,
    username: str,
    machine_id: str,
    items: List[Dict[str, Any]],
    detection_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Record an atomic waste disposal transaction:
    1. Calculate points from configurable rules.
    2. Insert into disposal_transactions.
    3. Update user points, streak, and level.
    4. Update machine fill level and items collected.
    """
    from datetime import date, timedelta

    rules_map = get_waste_points_map()
    total_points = 0
    total_items = 0
    total_weight = 0.0
    tx_ids = []

    with get_db() as conn:
        for itm in items:
            cat = (itm.get("waste_category") or itm.get("class_name") or "other").lower().strip()
            item_type = itm.get("item_type") or cat.replace("_", " ").title()
            qty = int(itm.get("quantity") or 1)

            # Match rule
            rule = rules_map.get(cat)
            if not rule:
                # Try generic matching (e.g. 'plastic' -> 'plastic_bottle')
                for r_key, r_val in rules_map.items():
                    if r_key.startswith(cat) or cat.startswith(r_key):
                        rule = r_val
                        break
            if not rule:
                rule = rules_map.get("other", {
                    "points_per_item": 5,
                    "points_per_kg": 50.0,
                    "base_weight_kg": 0.05,
                })

            base_unit_wt = float(itm.get("unit_weight_kg") or rule.get("base_weight_kg", 0.05))
            raw_wt = itm.get("weight_kg")
            if raw_wt is not None:
                raw_wt = float(raw_wt)
                if qty > 1 and raw_wt < (base_unit_wt * qty * 0.5):
                    weight = round(raw_wt * qty, 3)
                else:
                    weight = round(raw_wt, 3)
            else:
                weight = round(base_unit_wt * qty, 3)

            pts_per_item = int(rule.get("points_per_item", 5))
            pts_per_kg = float(rule.get("points_per_kg", 50.0))

            # Calculation: item points * quantity + weight bonus
            points = (pts_per_item * qty) + int(weight * pts_per_kg)
            points = max(pts_per_item * qty, points)

            cur = conn.execute(
                """
                INSERT INTO disposal_transactions
                (user_id, username, machine_id, waste_category, item_type, quantity, weight_kg, points_earned, detection_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'verified', ?)
                """,
                (user_id, username, machine_id, cat, item_type, qty, round(weight, 3), points, detection_id, _now()),
            )
            tx_ids.append(int(cur.lastrowid))
            total_points += points
            total_items += qty
            total_weight += weight

        # Update user gamification
        ensure_user_gamification(user_id, username)
        g_row = conn.execute("SELECT * FROM user_gamification WHERE user_id = ?", (user_id,)).fetchone()

        today_str = date.today().isoformat()
        last_date = g_row["last_deposit_date"]
        streak = g_row["streak_days"] or 1

        if last_date:
            try:
                last_d = date.fromisoformat(last_date)
                if last_d == date.today():
                    pass # Already deposited today
                elif last_d == date.today() - timedelta(days=1):
                    streak += 1 # Consecutive day
                else:
                    streak = 1 # Streak broken
            except Exception:
                streak = 1
        else:
            streak = 1

        new_total_pts = g_row["total_points"] + total_points
        new_balance = g_row["current_balance"] + total_points
        new_items = g_row["total_items_recycled"] + total_items
        new_weight = round(g_row["total_weight_kg"] + total_weight, 3)

        lvl_info = calculate_level(new_total_pts)

        conn.execute(
            """
            UPDATE user_gamification
            SET total_points = ?, current_balance = ?, total_items_recycled = ?, total_weight_kg = ?,
                streak_days = ?, last_deposit_date = ?, level = ?, level_title = ?
            WHERE user_id = ?
            """,
            (new_total_pts, new_balance, new_items, new_weight, streak, today_str, lvl_info["level"], lvl_info["title"], user_id),
        )

        # Update Smart Machine stats
        m_row = conn.execute("SELECT * FROM smart_machines WHERE machine_code = ?", (machine_id,)).fetchone()
        if m_row:
            cap = m_row["capacity_items"] or 500
            coll = (m_row["total_items_collected"] or 0) + total_items
            fill = min(100.0, round((coll % cap) / cap * 100.0, 1))
            status = "full" if fill >= 95.0 else m_row["status"]
            conn.execute(
                """
                UPDATE smart_machines
                SET fill_percentage = ?, total_items_collected = ?, status = ?
                WHERE machine_code = ?
                """,
                (fill, coll, status, machine_id),
            )

        # Evaluate badges
        badges = evaluate_badges(user_id, new_items, new_total_pts, streak, conn)
        unlocked = [b for b in badges if b["unlocked"]]

        return {
            "success": True,
            "points_earned": total_points,
            "items_deposited": total_items,
            "total_weight_kg": round(total_weight, 3),
            "new_balance": new_balance,
            "new_total_points": new_total_pts,
            "level": lvl_info["level"],
            "level_title": lvl_info["title"],
            "streak_days": streak,
            "transaction_ids": tx_ids,
            "badges_unlocked": unlocked,
        }


# ── Rewards & Redemptions ──────────────────────────────────────────────────

def list_rewards_catalog(only_active: bool = True) -> List[Dict[str, Any]]:
    with get_db() as conn:
        sql = "SELECT * FROM rewards"
        if only_active:
            sql += " WHERE is_active = 1 AND stock > 0"
        sql += " ORDER BY points_required ASC"
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]


def redeem_reward(user_id: int, username: str, reward_id: int) -> Dict[str, Any]:
    """Redeem a reward using accumulated points."""
    with get_db() as conn:
        reward = conn.execute("SELECT * FROM rewards WHERE id = ?", (reward_id,)).fetchone()
        if not reward:
            return {"success": False, "error": "Reward not found."}
        if reward["stock"] <= 0:
            return {"success": False, "error": "This reward is currently out of stock."}

        ensure_user_gamification(user_id, username)
        user_gam = conn.execute("SELECT * FROM user_gamification WHERE user_id = ?", (user_id,)).fetchone()

        pts_req = reward["points_required"]
        if user_gam["current_balance"] < pts_req:
            return {
                "success": False,
                "error": f"Insufficient points. You need {pts_req} points, but have {user_gam['current_balance']}.",
            }

        # Deduct balance
        new_balance = user_gam["current_balance"] - pts_req
        conn.execute(
            "UPDATE user_gamification SET current_balance = ? WHERE user_id = ?",
            (new_balance, user_id),
        )

        # Decrement reward stock
        conn.execute("UPDATE rewards SET stock = stock - 1 WHERE id = ?", (reward_id,))

        # Generate unique voucher code (e.g. CAFE50-7K9P2X)
        rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        prefix = reward["code_prefix"] or "ECO"
        code = f"{prefix}-{rand_suffix}"

        conn.execute(
            """
            INSERT INTO redemptions
            (user_id, username, reward_id, reward_title, points_spent, voucher_code, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (user_id, username, reward_id, reward["title"], pts_req, code, _now()),
        )

        return {
            "success": True,
            "voucher_code": code,
            "reward_title": reward["title"],
            "reward_value": reward["reward_value"],
            "points_spent": pts_req,
            "new_balance": new_balance,
        }


def add_reward(
    title: str,
    description: str,
    category: str,
    points_required: int,
    reward_value: str,
    code_prefix: str = "REWARD",
    icon: str = "🎁",
    stock: int = 100,
) -> int:
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO rewards
            (title, description, category, points_required, reward_value, code_prefix, icon, stock, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (title, description, category, points_required, reward_value, code_prefix.upper(), icon, stock, _now()),
        )
        return int(cur.lastrowid)


def delete_reward(reward_id: int) -> bool:
    with get_db() as conn:
        cur = conn.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
        return cur.rowcount > 0


def toggle_reward(reward_id: int, is_active: int) -> bool:
    with get_db() as conn:
        cur = conn.execute("UPDATE rewards SET is_active = ? WHERE id = ?", (is_active, reward_id))
        return cur.rowcount > 0


# ── Leaderboard & Transaction History ──────────────────────────────────────

def get_leaderboard(limit: int = 20) -> List[Dict[str, Any]]:
    """Return top recyclers ordered by total points earned."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT user_id, username, total_points, current_balance, total_items_recycled,
                   total_weight_kg, streak_days, level, level_title
            FROM user_gamification
            ORDER BY total_points DESC, total_items_recycled DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def list_all_disposals(limit: int = 100) -> List[Dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM disposal_transactions
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

