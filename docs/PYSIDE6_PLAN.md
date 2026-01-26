# PySide6 + QML plan (branch: PySide6)

Goal: a modern, cross-platform desktop UI (Windows/Linux/macOS) with real-time stats,
history cards, copy-to-clipboard, fame totals, and key legend. Passive only (no overlay).

## Selected stack
- PySide6 (Qt6 for Python)
- QML for UI (declarative, modern layout, smooth animations)

Why this stack:
- Native window across OS.
- Fast UI iteration with QML.
- Strong model/view for live data updates.

## Architecture
1) Pipeline produces MeterSnapshot + SessionMeter history (existing logic).
2) Qt bridge layer exposes:
   - Snapshot model (player rows: damage/heal/dps/hps, role colors).
   - History model (entries with copy text).
   - Fame counters and mode/zone labels.
3) QML renders:
   - Header (mode, zone, time, fame, fame/h)
   - Scoreboard list with horizontal bars
   - History cards (copy button)
   - Key legend panel

## Data contract (UI models)
- PlayerRow: name, damage, heal, dps, hps, bar_ratio, role, color
- HistoryRow: label, duration, totals, players, copy_text
- Meta: mode, zone, timestamp, fame_total, fame_per_hour

## Copy format
Single-line, chat-ready:
`battle 00:24 | D4dits dmg 1143 dps 40.1 | SocialFur3 dmg 220 dps 7.7`

## First steps (implementation)
1) Add optional dependency:
   - `pyside6>=6.6` (new extra, e.g. `gui-qt`)
2) Add CLI entry:
   - `albion-dps qt live` / `albion-dps qt replay <pcap>`
3) Create runtime bridge:
   - `albion_dps/qt/runner.py` to connect pipeline -> Qt models
   - `albion_dps/qt/models.py` (QAbstractListModel for players + history)
4) QML scaffold:
   - `albion_dps/qt/ui/Main.qml` with layout placeholders
5) Smoke test:
   - Start Qt app in headless/offscreen mode and feed mock snapshots

## UI layout (initial)
- Top bar: title, mode, zone, time, fame, fame/h
- Center: scoreboard list (left), history panel (right)
- Bottom: key legend

## Notes
- Keep all logic in Python; QML should be purely presentational.
- No game overlay; separate window only.
