"""workout-mcp — FastMCP server for fitness data, training, and nutrition."""

import functools
import json
import traceback

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("workout-mcp")


def _safe_tool(func):
    """Wrap MCP tool functions with error handling that returns JSON diagnostics."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc().split("\n")
            return json.dumps({
                "error": f"{func.__name__} failed: {type(e).__name__}: {e}",
                "traceback_tail": tb[-6:],
            })
    return wrapper


# ---------------------------------------------------------------------------
# Tool 1: fetch_fitness_data
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def fetch_fitness_data() -> str:
    """Fetch fitness data: Strava activities (14 days), 7-day load summary,
    macro profile based on training load, and user stats.
    Use for workout planning, recovery advice, or checking recent activity."""
    from .strava import get_fitness_data
    from .health import get_back_health

    data = get_fitness_data()
    data["back_health"] = get_back_health()
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Tool 2: fetch_macro_targets
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def fetch_macro_targets() -> str:
    """Fetch current macro/calorie targets (calories, protein, carbs, fat)
    based on this week's training load from Strava.
    Use when giving nutrition-aligned recipe suggestions or meal advice."""
    from .nutrition import fetch_macro_targets
    return json.dumps(fetch_macro_targets())


# ---------------------------------------------------------------------------
# Tool 3: fetch_pantry
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def fetch_pantry() -> str:
    """Fetch current pantry/fridge inventory.
    Returns categories (proteins, staples, vegetables, sauces, etc.) with item lists.
    Use when suggesting meals or checking what ingredients are available."""
    from .nutrition import fetch_pantry
    return json.dumps(fetch_pantry())


# ---------------------------------------------------------------------------
# Tool 4: update_pantry
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def update_pantry(category: str, items: str, action: str = "add") -> str:
    """Update pantry inventory.

    Args:
        category: Category name (e.g. "proteins", "sauces_and_condiments", "vegetables").
        items: JSON array of item strings, e.g. '["ground beef", "salmon"]'.
        action: "add" to append items, "remove" to delete items, "set" to replace entire category.
    """
    from .nutrition import update_pantry as _update
    return json.dumps(_update(category, items, action))


# ---------------------------------------------------------------------------
# Tool 5: suggest_meal
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def suggest_meal() -> str:
    """Fetch pantry inventory + macro targets together for meal suggestions.
    Use when the user asks "what should I eat/cook?" to get all context in one call.
    The LLM generates the actual meal suggestion from this data."""
    from .nutrition import suggest_meal as _suggest
    return json.dumps(_suggest())


# ---------------------------------------------------------------------------
# Tool 6: get_training_program
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def get_training_program() -> str:
    """Get the structured training program: Workout A, Workout B, cardio plan
    with phases, HR zones, and current phase. Use for understanding the full
    training plan or answering questions about specific exercises."""
    from .training import get_training_program as _get
    return json.dumps(_get())


# ---------------------------------------------------------------------------
# Tool 7: get_back_health
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def get_back_health() -> str:
    """Get back health and medical history (independently from fitness data).
    Includes medical conditions, contraindications, preferred exercises, red flags.
    Use for exercise safety questions or physiotherapy context."""
    from .health import get_back_health as _get
    return json.dumps(_get())


# ---------------------------------------------------------------------------
# Tool 8: get_sleep_data
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def get_sleep_data(days: int = 7) -> str:
    """Get parsed sleep data from Apple Watch exports.
    Returns bed windows, total sleep hours, awake time, and sleep stages.

    Args:
        days: Number of days to look back (default 7).
    """
    from .sleep import get_sleep_data as _get
    return json.dumps(_get(days))


# ---------------------------------------------------------------------------
# Tool 9: log_workout_notes
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def log_workout_notes(
    activity_name: str,
    notes: str = "",
    rpe: int = 0,
    pain_notes: str = "",
) -> str:
    """Log notes and observations for a workout session.

    Args:
        activity_name: Name of the workout (e.g. "Workout A: Push, Quads & Side Delts").
        notes: General workout notes/observations.
        rpe: Rate of perceived exertion (1-10). 0 = not specified.
        pain_notes: Any pain or discomfort observations.
    """
    from .notes import log_workout_notes as _log
    return json.dumps(_log(activity_name, notes, rpe, pain_notes))


# ---------------------------------------------------------------------------
# Tool 10: get_weekly_summary
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def get_weekly_summary() -> str:
    """Get weekly training summary: sessions by type, total volume,
    adherence vs targets (3 strength + 3 cardio), and activity list.
    Use for progress check-ins or weekly reviews."""
    from .training import get_weekly_summary as _get
    return json.dumps(_get())


# ---------------------------------------------------------------------------
# Tool 11: get_next_workout
# ---------------------------------------------------------------------------
@mcp.tool()
@_safe_tool
def get_next_workout() -> str:
    """Determine the next recommended workout based on A/B rotation,
    rest day logic, and cardio deficit. Considers days since last workout,
    whether strength was done yesterday, and cardio sessions remaining."""
    from .training import get_next_workout as _get
    return json.dumps(_get())


if __name__ == "__main__":
    mcp.run()
