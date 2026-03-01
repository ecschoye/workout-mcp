"""Configuration — paths, user stats, macro profiles, sport type sets."""

import os
from pathlib import Path

# Repo root — where this package lives
_REPO_ROOT = Path(__file__).resolve().parent.parent

# Default data dir is data/ inside the repo
# Override with WORKOUT_DATA_DIR env var (e.g. Pi uses fitness_data/)
DATA_DIR = Path(os.environ.get("WORKOUT_DATA_DIR", str(_REPO_ROOT / "data")))

STRAVA_CACHE = DATA_DIR / "strava_cache.json"
SLEEP_LOG = DATA_DIR / "sleep_log.md"
SLEEP_RAW_DIR = DATA_DIR / "sleep_raw"
WORKOUT_NOTES = DATA_DIR / "workout_notes.json"
PANTRY_FILE = DATA_DIR / "pantry.json"
TRAINING_PROGRAM = DATA_DIR / "training_program.md"
BACK_HEALTH = DATA_DIR / "back_health.md"

# User stats
USER_STATS = {
    "name": "Edvard",
    "weight_kg": 100,
    "height_cm": 173,
    "age": 25,
    "goal": "mild cut",
}

# Macro profiles — by training load tier
MACRO_PROFILES = {
    "deload": {
        "label": "Deload Week",
        "calories": 2000,
        "protein": 185,
        "carbs": 155,
        "fat": 65,
        "note": "Very low recent activity — lighter targets, keep protein up",
    },
    "rest": {
        "label": "Low Activity Week",
        "calories": 2150,
        "protein": 190,
        "carbs": 175,
        "fat": 65,
        "note": "Below average training load this week",
    },
    "moderate": {
        "label": "Normal Training Week",
        "calories": 2400,
        "protein": 195,
        "carbs": 230,
        "fat": 70,
        "note": "Solid training load — standard targets",
    },
    "heavy": {
        "label": "High Training Week",
        "calories": 2650,
        "protein": 200,
        "carbs": 280,
        "fat": 75,
        "note": "Heavy week — fuel recovery and performance",
    },
}

# Sport type classification
STRENGTH_TYPES = {"weighttraining", "workout", "crossfit"}
CARDIO_TYPES = {"elliptical", "ride", "run", "walk", "swim", "rowing", "stairstepper"}


def get_activity_profile(total_minutes: int, strength_sessions: int) -> dict:
    """Determine macro profile from 7-day training load."""
    if total_minutes >= 180 or strength_sessions >= 3:
        return MACRO_PROFILES["heavy"]
    elif total_minutes >= 90 or strength_sessions >= 2:
        return MACRO_PROFILES["moderate"]
    elif total_minutes >= 30 or strength_sessions >= 1:
        return MACRO_PROFILES["rest"]
    else:
        return MACRO_PROFILES["deload"]
