"""Workout notes logging to fitness_data/workout_notes.json."""

import json
import os
import tempfile
from datetime import datetime

from .config import WORKOUT_NOTES

MAX_ENTRIES = 100


def _read_notes() -> list[dict]:
    """Read existing workout notes."""
    if not WORKOUT_NOTES.exists():
        return []
    try:
        return json.loads(WORKOUT_NOTES.read_text())
    except json.JSONDecodeError:
        return []


def _write_notes(entries: list[dict]) -> None:
    """Atomic write of notes list."""
    content = json.dumps(entries, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(
        dir=str(WORKOUT_NOTES.parent),
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(WORKOUT_NOTES))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def log_workout_notes(
    activity_name: str,
    notes: str = "",
    rpe: int = 0,
    pain_notes: str = "",
) -> dict:
    """Log notes for a workout session.

    Args:
        activity_name: Name of the workout (e.g. "Workout A: Push, Quads & Side Delts").
        notes: General workout notes/observations.
        rpe: Rate of perceived exertion (1-10). 0 = not specified.
        pain_notes: Any pain or discomfort observations.
    """
    if rpe and not (1 <= rpe <= 10):
        return {"error": "RPE must be between 1 and 10"}

    entry = {
        "timestamp": datetime.now().isoformat(),
        "activity_name": activity_name,
    }
    if notes:
        entry["notes"] = notes
    if rpe:
        entry["rpe"] = rpe
    if pain_notes:
        entry["pain_notes"] = pain_notes

    entries = _read_notes()
    entries.append(entry)

    # Cap at MAX_ENTRIES, keep most recent
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]

    _write_notes(entries)
    return {"logged": True, "entry": entry, "total_entries": len(entries)}
