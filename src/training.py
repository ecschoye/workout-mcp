"""Parse training program, determine next workout, compute weekly analysis."""

import re
from datetime import datetime, timedelta, timezone

from .config import TRAINING_PROGRAM, STRENGTH_TYPES, CARDIO_TYPES
from .strava import get_activities, compute_load_summary


def _load_program() -> str:
    """Load training_program.md raw text."""
    if not TRAINING_PROGRAM.exists():
        return ""
    return TRAINING_PROGRAM.read_text(errors="replace")


def _parse_workout(text: str, header_pattern: str) -> dict | None:
    """Extract a workout section by header pattern (e.g. 'Workout A')."""
    lines = text.splitlines()
    in_section = False
    section_lines = []
    name = ""

    for line in lines:
        if re.match(rf"^##\s+{header_pattern}", line):
            in_section = True
            name = line.lstrip("# ").strip()
            section_lines.append(line)
            continue
        if in_section:
            if re.match(r"^##\s+", line) and not re.match(rf"^##\s+{header_pattern}", line):
                break
            section_lines.append(line)

    if not section_lines:
        return None

    # Parse exercises
    exercises = []
    for line in section_lines:
        m = re.match(r"^\d+\.\s+(.+?)(?:\s*—\s*(.+))?$", line)
        if m:
            exercises.append({
                "name": m.group(1).strip(),
                "prescription": m.group(2).strip() if m.group(2) else "",
            })

    # Extract duration/sets from first line after header
    duration = ""
    sets = ""
    for line in section_lines[1:3]:
        m = re.match(r"^~?([\dh\s]+min)\s*,?\s*(\d+\s*sets)?", line.strip())
        if m:
            duration = m.group(1).strip() if m.group(1) else ""
            sets = m.group(2).strip() if m.group(2) else ""
            break

    return {
        "name": name,
        "duration": duration,
        "total_sets": sets,
        "exercises": exercises,
    }


def _parse_cardio_plan(text: str) -> dict:
    """Extract cardio plan structure."""
    lines = text.splitlines()
    phases = []
    current_phase = None
    hr_zones = []
    rules = []
    in_rules = False
    in_zones = False
    start_date = None

    for line in lines:
        # Cardio header with start date
        m = re.match(r"^##\s+Cardio.*started\s+(\d{4}-\d{2}-\d{2})", line)
        if m:
            start_date = m.group(1)
            continue

        # HR Zones section
        if re.match(r"^###\s+HR Zones", line):
            in_zones = True
            in_rules = False
            continue

        if in_zones and line.startswith("- "):
            hr_zones.append(line[2:].strip())
            continue

        # Phase headers
        m = re.match(r"^###\s+(Phase\s+\d+:.+?)(?:\s*\((.+?)\))?$", line)
        if m:
            in_zones = False
            in_rules = False
            if current_phase:
                phases.append(current_phase)
            current_phase = {
                "name": m.group(1).strip(),
                "dates": m.group(2).strip() if m.group(2) else "",
                "sessions": [],
            }
            continue

        # Rules section
        if re.match(r"^###\s+Rules", line):
            in_zones = False
            in_rules = True
            if current_phase:
                phases.append(current_phase)
                current_phase = None
            continue

        if in_rules and line.startswith("- "):
            rules.append(line[2:].strip())
            continue

        # Session lines within a phase
        if current_phase and re.match(r"^-\s+Session\s+\d+:", line):
            current_phase["sessions"].append(line.lstrip("- ").strip())

    if current_phase:
        phases.append(current_phase)

    return {
        "start_date": start_date,
        "hr_zones": hr_zones,
        "phases": phases,
        "rules": rules,
    }


def _current_cardio_phase(cardio: dict) -> dict | None:
    """Determine which cardio phase is current based on start date."""
    if not cardio.get("start_date"):
        return None
    start = datetime.strptime(cardio["start_date"], "%Y-%m-%d")
    weeks_elapsed = (datetime.now() - start).days // 7
    for phase in cardio.get("phases", []):
        # Parse week range from dates string like "Weeks 1-4, Feb 24 - Mar 23"
        m = re.match(r"Weeks?\s+(\d+)-(\d+)", phase.get("dates", ""))
        if m:
            w_start = int(m.group(1))
            w_end = int(m.group(2))
            # weeks_elapsed is 0-indexed, phases are 1-indexed
            if w_start - 1 <= weeks_elapsed <= w_end - 1:
                return {**phase, "current_week": weeks_elapsed + 1}
    return None


def get_training_program() -> dict:
    """Return the full structured training program."""
    text = _load_program()
    if not text:
        return {"available": False, "reason": "training_program.md not found"}

    workout_a = _parse_workout(text, "Workout A")
    workout_b = _parse_workout(text, "Workout B")
    cardio = _parse_cardio_plan(text)
    current_phase = _current_cardio_phase(cardio)

    return {
        "available": True,
        "workout_a": workout_a,
        "workout_b": workout_b,
        "cardio": cardio,
        "current_cardio_phase": current_phase,
    }


def get_next_workout() -> dict:
    """Determine the next workout based on A/B alternation and rest logic."""
    activities = get_activities(days=7)
    load = compute_load_summary()

    # Find last strength workout to determine A/B
    strength_workouts = [
        a for a in activities
        if (a.get("sport_type") or "").lower() in STRENGTH_TYPES
    ]
    # Sort by date descending
    strength_workouts.sort(key=lambda a: a.get("start_date", ""), reverse=True)

    last_strength = strength_workouts[0] if strength_workouts else None
    last_was_a = False
    last_was_b = False
    if last_strength:
        name = (last_strength.get("name") or "").lower()
        last_was_a = "workout a" in name
        last_was_b = "workout b" in name

    # Determine next strength workout
    if last_was_a:
        next_strength = "Workout B: Pull, Hams & Arms"
    elif last_was_b:
        next_strength = "Workout A: Push, Quads & Side Delts"
    else:
        next_strength = "Workout A: Push, Quads & Side Delts"

    # Check if rest day needed (trained yesterday?)
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)
    trained_yesterday = any(
        datetime.fromisoformat(a.get("start_date", "1970-01-01T00:00:00+00:00")).date()
        == yesterday.date()
        for a in activities
    )

    # Check cardio deficit
    cardio_target = 3  # sessions/week
    cardio_done = load["cardio_sessions"]
    cardio_deficit = max(0, cardio_target - cardio_done)

    # Get current cardio phase info
    text = _load_program()
    cardio = _parse_cardio_plan(text) if text else {}
    current_phase = _current_cardio_phase(cardio) if cardio else None

    # Days since last workout
    last_activity = None
    if activities:
        sorted_acts = sorted(activities, key=lambda a: a.get("start_date", ""), reverse=True)
        last_activity = sorted_acts[0]

    days_since_last = None
    if last_activity:
        last_date = datetime.fromisoformat(last_activity["start_date"])
        days_since_last = (now - last_date).days

    # Recommendation logic
    if days_since_last is not None and days_since_last >= 3:
        recommendation = f"Priority: {next_strength} (haven't trained in {days_since_last} days)"
    elif trained_yesterday and last_strength and (
        datetime.fromisoformat(last_strength["start_date"]).date() == yesterday.date()
    ):
        if cardio_deficit > 0 and current_phase:
            recommendation = f"Cardio day — {current_phase['name']} (strength yesterday, {cardio_deficit} cardio sessions remaining)"
        else:
            recommendation = "Rest day or light cardio (strength yesterday)"
    elif cardio_deficit >= 2:
        recommendation = f"Cardio priority — {cardio_deficit} sessions behind target"
        if current_phase:
            recommendation += f" ({current_phase['name']})"
    else:
        recommendation = next_strength

    return {
        "next_strength": next_strength,
        "last_strength": {
            "name": last_strength.get("name"),
            "date": last_strength.get("start_date"),
        } if last_strength else None,
        "trained_yesterday": trained_yesterday,
        "days_since_last_workout": days_since_last,
        "cardio_deficit": cardio_deficit,
        "cardio_done_this_week": cardio_done,
        "current_cardio_phase": current_phase,
        "recommendation": recommendation,
    }


def get_weekly_summary() -> dict:
    """Weekly training summary: sessions, volume, adherence."""
    load = compute_load_summary()
    activities = get_activities(days=7)

    # Group by type
    by_type = {}
    for a in activities:
        sport = (a.get("sport_type") or "unknown").lower()
        if sport not in by_type:
            by_type[sport] = {"count": 0, "total_minutes": 0}
        by_type[sport]["count"] += 1
        by_type[sport]["total_minutes"] += a.get("moving_minutes", 0) or 0

    # Adherence against targets
    strength_target = 3
    cardio_target = 3
    strength_adherence = min(1.0, load["strength_sessions"] / strength_target) if strength_target else 1.0
    cardio_adherence = min(1.0, load["cardio_sessions"] / cardio_target) if cardio_target else 1.0

    # Activity list for reference
    activity_list = [
        {
            "name": a.get("name"),
            "type": (a.get("sport_type") or "").lower(),
            "date": a.get("start_date"),
            "minutes": a.get("moving_minutes", 0),
        }
        for a in sorted(activities, key=lambda x: x.get("start_date", ""))
    ]

    return {
        "period": "last 7 days",
        "load_summary": load,
        "by_type": by_type,
        "adherence": {
            "strength": {
                "done": load["strength_sessions"],
                "target": strength_target,
                "pct": round(strength_adherence * 100),
            },
            "cardio": {
                "done": load["cardio_sessions"],
                "target": cardio_target,
                "pct": round(cardio_adherence * 100),
            },
        },
        "activities": activity_list,
    }
