# QA-001 Regression Pass

Scope: verify core functional paths after UI/release refactor:
- Meter
- Loot
- Scanner
- Market
- Live capture filtering path
- Replay path

## Run all groups

Windows PowerShell:
```
.\venv\Scripts\python .\tools\qa\run_regression_suite.py
```

## Run a single group

Examples:
```
.\venv\Scripts\python .\tools\qa\run_regression_suite.py --group market
.\venv\Scripts\python .\tools\qa\run_regression_suite.py --group replay
```

Loot-focused checks:
```
.\venv\Scripts\python -m pytest -q tests/test_loot_tracker.py tests/test_loot_tracker_pcaps.py tests/test_loot_export.py tests/test_loot_import.py tests/test_loot_log_writer.py tests/test_qt_loot_state.py tests/test_qml_loot_tab.py
```

## Group mapping

- `meter`: meter aggregation + mode basics
- `meter`: meter aggregation + mode basics (stable subset)
- `loot`: native loot tracker, text import/export, Qt state, QML smoke, and PCAP replay expectations
- `scanner`: packet/protocol decode baseline
- `market`: market engine/state/regression dataset
- `live`: party/self filtering behavior from pcaps
- `replay`: replay pipeline + Qt entry smoke
- `replay`: replay pipeline + Qt entry smoke (isolated temp workspace via `--basetemp`)

## Exit criteria

- all selected groups return PASS
- no regressions in party filtering (`self + party only`)
- no loot regression where party-member loot collapses to local-player-only when PCAP context contains party events
- imported loot logs preserve source classification when `source_kind` is present
- no Qt smoke regressions
