# GUI plan (Textual TUI)

Status: implemented in this branch (Textual TUI).
Modern desktop UI notes (implemented): `docs/PYSIDE6_PLAN.md`.

## Selected stack
- Textual (Python TUI): pure Python, no native binaries, works on Windows/Linux/macOS.
- Rich is pulled by Textual and provides progress bars and colors.

## Current UI behavior
- Header with mode, zone, timestamp, fame/h.
- Scoreboard table with DPS/HPS and horizontal bars scaled by sort.
- History panel with recent fights.
- Role colors (tank/dps/heal) with fallback palette; per-weapon colors when item DBs are present.
- Keys: `q` quit, `b/z/m` modes, `1-4` sort (dps/dmg/hps/heal).

## Integration
- Uses `live_snapshots` / `replay_snapshots` from `albion_dps/pipeline.py`.
- Snapshots are forwarded through a queue to the Textual app.
- No changes to capture or protocol logic; GUI is render-only.

## Testing
- Headless smoke test for the GUI exists.

## Prompts used (history)
1) Add dependency Textual (extra gui), add `gui` CLI subcommand (live/replay).
2) Implement adapter queue and Textual app showing header + table + bars.
3) Add role coloring, fallback palette, and history panel.
4) Fix tests/CI and add GUI smoke test.
5) Update README with GUI section.
