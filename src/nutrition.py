"""Pantry CRUD, macro targets, and meal suggestion context."""

import json
import os
import tempfile

from .config import PANTRY_FILE
from .strava import get_macro_profile


def _read_pantry() -> dict:
    """Read pantry.json. Returns empty dict on failure."""
    if not PANTRY_FILE.exists():
        return {}
    return json.loads(PANTRY_FILE.read_text())


def _write_pantry(data: dict) -> None:
    """Atomic write: tmp -> fsync -> rename."""
    content = json.dumps(data, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(
        dir=str(PANTRY_FILE.parent),
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(PANTRY_FILE))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def fetch_pantry() -> dict:
    """Return the full pantry inventory."""
    pantry = _read_pantry()
    if not pantry:
        return {"available": False, "reason": "pantry.json not found or empty"}
    return {"available": True, "categories": pantry}


def update_pantry(category: str, items: str, action: str = "add") -> dict:
    """Update pantry inventory.

    Args:
        category: Category name (e.g. "proteins", "vegetables").
        items: JSON array of item strings, e.g. '["ground beef", "salmon"]'.
        action: "add" to append, "remove" to delete, "set" to replace category.
    """
    pantry = _read_pantry()
    try:
        item_list = json.loads(items)
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON for items: {items}"}

    if not isinstance(item_list, list):
        return {"error": "items must be a JSON array of strings"}

    existing = pantry.get(category, [])

    if action == "add":
        # Append, avoiding exact duplicates
        existing_lower = {i.lower() for i in existing}
        for item in item_list:
            if item.lower() not in existing_lower:
                existing.append(item)
                existing_lower.add(item.lower())
        pantry[category] = existing
    elif action == "remove":
        remove_lower = {i.lower() for i in item_list}
        pantry[category] = [i for i in existing if i.lower() not in remove_lower]
    elif action == "set":
        pantry[category] = item_list
    else:
        return {"error": f"Unknown action: {action}. Use add/remove/set."}

    _write_pantry(pantry)
    return {"updated": True, "category": category, "items": pantry[category]}


def fetch_macro_targets() -> dict:
    """Get current macro/calorie targets based on training load."""
    return get_macro_profile()


def suggest_meal() -> dict:
    """Get pantry + macro targets together for meal suggestions."""
    pantry = _read_pantry()
    macros = get_macro_profile()
    return {
        "pantry": pantry if pantry else {"note": "pantry.json not found"},
        "macro_targets": macros,
    }
