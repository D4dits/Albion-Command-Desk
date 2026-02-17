# QA-001 Regression Pass

Scope: verify core functional paths after UI/release refactor:
- Meter
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

## Group mapping

- `meter`: meter aggregation + mode basics
- `meter`: meter aggregation + mode basics (stable subset)
- `scanner`: packet/protocol decode baseline
- `market`: market engine/state/regression dataset
- `live`: party/self filtering behavior from pcaps
- `replay`: replay pipeline + Qt entry smoke
- `replay`: replay pipeline + Qt entry smoke (isolated temp workspace via `--basetemp`)

## Exit criteria

- all selected groups return PASS
- no regressions in party filtering (`self + party only`)
- no Qt smoke regressions
