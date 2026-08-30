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
