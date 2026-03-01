"""Read strava_cache.json and compute load summary + macro profile."""

import json
from datetime import datetime, timedelta, timezone

from .config import (
    STRAVA_CACHE, STRENGTH_TYPES, CARDIO_TYPES,
    USER_STATS, get_activity_profile,
)


def load_cache() -> dict:
    """Load the Strava cache file. Returns empty structure on failure."""
    if not STRAVA_CACHE.exists():
        return {"activities": [], "weekly_summary": {}, "fetched_at": None}
    return json.loads(STRAVA_CACHE.read_text())


def get_activities(days: int = 14) -> list[dict]:
    """Get activities from cache, optionally filtered to last N days."""
    cache = load_cache()
    activities = cache.get("activities", [])
    if days < 14:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        activities = [
            a for a in activities
            if datetime.fromisoformat(a["start_date"]) > cutoff
        ]
    return activities


def compute_load_summary() -> dict:
    """Compute 7-day load summary from cached activities."""
    activities = get_activities(days=7)
    total_minutes = 0
    strength_sessions = 0
    cardio_minutes = 0
    cardio_sessions = 0

    for a in activities:
        mins = a.get("moving_minutes", 0) or 0
        sport = (a.get("sport_type") or "").lower()
        total_minutes += mins
        if sport in STRENGTH_TYPES:
            strength_sessions += 1
        if sport in CARDIO_TYPES:
            cardio_minutes += mins
            cardio_sessions += 1

    return {
        "total_minutes": total_minutes,
        "total_sessions": len(activities),
        "strength_sessions": strength_sessions,
        "cardio_minutes": cardio_minutes,
        "cardio_sessions": cardio_sessions,
    }


def get_macro_profile() -> dict:
    """Get macro targets based on 7-day training load."""
    load = compute_load_summary()
    profile = get_activity_profile(load["total_minutes"], load["strength_sessions"])
    return {
        "user": USER_STATS,
        "load_summary": load,
        "targets": profile,
    }


def get_fitness_data() -> dict:
    """Full fitness data payload: activities, load summary, macro profile, back health."""
    cache = load_cache()
    load = compute_load_summary()
    profile = get_activity_profile(load["total_minutes"], load["strength_sessions"])
    return {
        "fetched_at": cache.get("fetched_at"),
        "athlete": cache.get("athlete"),
        "activities": cache.get("activities", []),
        "load_summary": load,
        "macro_profile": profile,
        "user_stats": USER_STATS,
    }
