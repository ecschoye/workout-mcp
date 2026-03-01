"""Load back_health.md as raw text."""

from .config import BACK_HEALTH


def get_back_health() -> dict:
    """Return back health content and status."""
    if not BACK_HEALTH.exists():
        return {"available": False, "reason": "back_health.md not found"}
    content = BACK_HEALTH.read_text(errors="replace").strip()
    if not content:
        return {"available": False, "reason": "back_health.md is empty"}
    return {"available": True, "content": content}
