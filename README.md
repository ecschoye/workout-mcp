# workout-mcp

Standalone MCP server for fitness data, training program, nutrition, and workout tracking.

Reads local data files only — no Strava API calls (existing `strava_cache.py` cron handles that).

## Tools

| Tool | Description |
|------|-------------|
| `fetch_fitness_data()` | Strava activities, load summary, macro profile, back health |
| `fetch_macro_targets()` | Calorie/macro targets based on training load |
| `fetch_pantry()` | Pantry/fridge inventory |
| `update_pantry(category, items, action)` | Add/remove/set pantry items |
| `suggest_meal()` | Pantry + macros for meal suggestions |
| `get_training_program()` | Structured A/B + cardio plan |
| `get_back_health()` | Medical history and contraindications |
| `get_sleep_data(days)` | Apple Watch sleep data |
| `log_workout_notes(activity_name, notes, rpe, pain_notes)` | Save workout observations |
| `get_weekly_summary()` | Sessions, volume, adherence |
| `get_next_workout()` | A/B rotation + rest/cardio logic |

## Install

```bash
pip install -e ~/workout-mcp
```

## Claude Code config (~/.claude.json)

By default, the server reads from `data/` inside the repo. No env vars needed on Mac:

```json
{
  "workout-mcp": {
    "type": "stdio",
    "command": "python3",
    "args": ["-m", "src.server"],
    "env": {
      "PYTHONPATH": "/path/to/workout-mcp"
    }
  }
}
```

On the Pi (where Strava cache cron writes to a different location), override with:

```json
"WORKOUT_DATA_DIR": "/home/edvard/.zeroclaw/workspace/work/fitness_data"
```

## Data files

All data files live in `data/` (or wherever `WORKOUT_DATA_DIR` points):

- `strava_cache.json` — Strava activities (refreshed by cron on Pi)
- `sleep_log.md` — Apple Watch sleep
- `training_program.md` — A/B workout + cardio plan
- `back_health.md` — Medical history
- `pantry.json` — Ingredient inventory (also written by `update_pantry`)
- `workout_notes.json` — Created by `log_workout_notes`
