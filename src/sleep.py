"""Parse sleep_log.md and sleep_raw/*.json for sleep data."""

import json
import re
from datetime import datetime, timedelta

from .config import SLEEP_LOG, SLEEP_RAW_DIR


def _parse_sleep_log(days: int = 7) -> list[dict]:
    """Parse sleep_log.md into structured entries."""
    if not SLEEP_LOG.exists():
        return []

    text = SLEEP_LOG.read_text(errors="replace")
    entries = []
    current_date = None
    current = {}

    for line in text.splitlines():
        line = line.strip()
        # Date header: ## 2026-02-28
        m = re.match(r"^##\s+(\d{4}-\d{2}-\d{2})", line)
        if m:
            if current_date and current:
                entries.append({"date": current_date, **current})
            current_date = m.group(1)
            current = {}
            continue

        if not current_date:
            continue

        # Bed: 00:52 - 09:36
        m = re.match(r"^-\s*Bed:\s*(.+)", line)
        if m:
            current["bed_window"] = m.group(1).strip()
            continue

        # Total sleep: 7.0h
        m = re.match(r"^-\s*Total sleep:\s*([\d.]+)h", line)
        if m:
            current["total_hours"] = float(m.group(1))
            continue

        # Awake: 104min
        m = re.match(r"^-\s*Awake:\s*(\d+)min", line)
        if m:
            current["awake_minutes"] = int(m.group(1))
            continue

        # Stages: deep: 68min, core: 241min, rem: 111min
        m = re.match(r"^-\s*Stages:\s*(.+)", line)
        if m:
            stages = {}
            for part in m.group(1).split(","):
                part = part.strip()
                sm = re.match(r"(\w+):\s*(\d+)min", part)
                if sm:
                    stages[sm.group(1)] = int(sm.group(2))
            current["stages"] = stages

    # Don't forget the last entry
    if current_date and current:
        entries.append({"date": current_date, **current})

    # Filter to last N days
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    entries = [e for e in entries if e["date"] >= cutoff]
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def _load_sleep_raw(days: int = 7) -> list[dict]:
    """Load raw sleep JSON exports as fallback."""
    if not SLEEP_RAW_DIR.exists():
        return []

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    entries = []
    for f in sorted(SLEEP_RAW_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            if isinstance(data, list):
                for entry in data:
                    date = entry.get("date", "")
                    if date >= cutoff:
                        entries.append(entry)
            elif isinstance(data, dict):
                date = data.get("date", "")
                if date >= cutoff:
                    entries.append(data)
        except (json.JSONDecodeError, KeyError):
            continue

    return entries[:days]


def get_sleep_data(days: int = 7) -> dict:
    """Get parsed sleep data for the last N days."""
    entries = _parse_sleep_log(days)
    source = "sleep_log.md"

    if not entries:
        entries = _load_sleep_raw(days)
        source = "sleep_raw/" if entries else "none"

    if not entries:
        return {"available": False, "reason": "No sleep data found", "entries": []}

    # Compute averages
    total_hours = [e["total_hours"] for e in entries if "total_hours" in e]
    avg_sleep = round(sum(total_hours) / len(total_hours), 1) if total_hours else None

    return {
        "available": True,
        "source": source,
        "days_covered": len(entries),
        "average_hours": avg_sleep,
        "entries": entries,
    }
