# QA-002 Clean Machine Install Tests

Goal: validate that bootstrap install path works on clean Windows/Linux/macOS environments.

## Source of truth

- CI workflow: `.github/workflows/bootstrap-smoke.yml`
- Required jobs (blocker):
  - `windows-core`
  - `linux-core`
  - `macos-core`
- Advisory jobs:
  - `linux-capture-advisory`
  - `macos-capture-advisory`
- Required evidence artifacts:
  - `bootstrap-smoke-windows-core`
  - `bootstrap-smoke-linux-core`
  - `bootstrap-smoke-macos-core`

## Verify latest matrix from CLI

Prerequisites:
- `gh` CLI installed
- `gh auth login` completed

Command:
```
python .\tools\qa\verify_clean_machine_matrix.py
```

Optional explicit run:
```
python .\tools\qa\verify_clean_machine_matrix.py --run-id <ACTIONS_RUN_ID>
```

Exit codes:
- `0` -> required matrix passed
- `1` -> one or more required jobs or evidence artifacts failed/missing/expired
- `2` -> verification could not run (network/auth/API issue)

## CI evidence payload

Each required job uploads a clean-machine evidence bundle containing:
- `bootstrap.log` (bootstrap run output),
- `smoke-report.json` (structured CLI + Qt probe result),
- `update-flow.log` (manifest/update banner contract probe),
- `assets/ux-baseline/*.png` references for release-candidate review.

## Manual local sanity (Windows core profile)

Use only as supplemental check; CI matrix is the release gate:
```
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 `
  -ProjectRoot "$PWD" `
  -VenvPath "$PWD\.venv-qa-clean" `
  -Profile core `
  -ForceRecreateVenv `
  -SkipRun
```
