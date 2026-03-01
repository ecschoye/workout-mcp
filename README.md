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

```json
{
  "workout-mcp": {
    "type": "stdio",
    "command": "python3",
    "args": ["-m", "src.server"],
    "env": {
      "PYTHONPATH": "/home/edvard/workout-mcp"
    }
  }
}
```

## Data files

Reads from `~/.zeroclaw/workspace/work/`:
- `fitness_data/strava_cache.json`
- `fitness_data/sleep_log.md`
- `training_program.md`
- `back_health.md`
- `pantry.json`

Creates:
- `fitness_data/workout_notes.json`

Override paths via `WORKOUT_WORKSPACE_DIR` and `WORKOUT_DATA_DIR` env vars.
