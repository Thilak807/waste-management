"""
Recycling recommendation module.

Kept separate from the YOLO model so recommendations can be updated
without retraining. Extend RECOMMENDATIONS when adding new classes.
"""

from __future__ import annotations

from typing import Dict, Optional

# Default guidance per waste class (admin can override via database)
DEFAULT_RECOMMENDATIONS: Dict[str, Dict[str, str]] = {
    "plastic": {
        "category": "Recyclable – Plastic",
        "recommendation": (
            "Place clean plastic items in the appropriate recycling bin. "
            "Rinse containers, remove caps if required by local rules, and "
            "avoid putting soft films or contaminated plastic in the recycling stream."
        ),
        "disposal_tips": (
            "Do not burn plastic. Soft plastic bags often go to store take-back "
            "programs rather than curbside bins."
        ),
    },
    "paper": {
        "category": "Recyclable – Paper",
        "recommendation": (
            "Keep paper dry and place it in the paper recycling collection. "
            "Remove plastic sleeves, binders, and food-stained paper before recycling."
        ),
        "disposal_tips": (
            "Shredded paper may need a paper bag. Greasy pizza boxes usually "
            "belong in compost or general waste, not paper recycling."
        ),
    },
    "glass": {
        "category": "Recyclable – Glass",
        "recommendation": (
            "Separate glass from general waste and send it to a glass recycling "
            "facility. Empty and rinse bottles and jars; remove lids if needed."
        ),
        "disposal_tips": (
            "Broken glass should be wrapped safely. Ceramics, mirrors, and "
            "light bulbs are often not accepted with bottle glass."
        ),
    },
    "metal": {
        "category": "Recyclable – Metal",
        "recommendation": (
            "Place recyclable metal containers in the appropriate recycling "
            "collection. Rinse cans and crush them if space is limited."
        ),
        "disposal_tips": (
            "Aerosol cans must be empty. Scrap metal and electronics may need "
            "special collection points."
        ),
    },
}


def get_recommendation(class_name: str, custom_map: Optional[Dict] = None) -> Dict[str, str]:
    """
    Map a predicted waste class to recycling guidance.

    Args:
        class_name: Predicted class (e.g. 'plastic').
        custom_map: Optional override dictionary from the database.

    Returns:
        Dict with keys: category, recommendation, disposal_tips.
    """
    key = (class_name or "").strip().lower()
    source = custom_map if custom_map else DEFAULT_RECOMMENDATIONS

    if key in source:
        entry = source[key]
        return {
            "class_name": key,
            "category": entry.get("category", f"Recyclable – {key.title()}"),
            "recommendation": entry.get("recommendation", "Follow local recycling guidelines."),
            "disposal_tips": entry.get("disposal_tips", ""),
        }

    return {
        "class_name": key or "unknown",
        "category": "Unknown / General Waste",
        "recommendation": (
            "Class not recognized in the recommendation database. "
            "Dispose according to local municipal waste rules."
        ),
        "disposal_tips": "Contact your local recycling center for guidance.",
    }


def list_all_recommendations(custom_map: Optional[Dict] = None) -> Dict[str, Dict[str, str]]:
    """Return all recommendations (defaults merged with optional custom overrides)."""
    merged = {k: dict(v) for k, v in DEFAULT_RECOMMENDATIONS.items()}
    if custom_map:
        for k, v in custom_map.items():
            merged[k] = {**merged.get(k, {}), **v}
    return merged
