# QA-002 Clean Machine Install Tests

Goal: validate that bootstrap install path works on clean Windows/Linux/macOS environments.

## Source of truth

- CI workflow: `.github/workflows/bootstrap-smoke.yml`
- Required jobs (blocker):
  - `windows-core`
  - `linux-core`
  - `macos-core`
- Advisory jobs:
  - `windows-capture-bundle-advisory`
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

Advisory Windows capture-bundle evidence (`bootstrap-smoke-windows-capture-bundle`) should include:
- `bootstrap.log` proving the installer used `Installing prebuilt Windows live capture backend`,
- `smoke-report.json` from the capture-profile install path.

## Manual local sanity (Windows default profile)

Use only as supplemental check; CI matrix is the release gate:
```
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 `
  -ProjectRoot "$PWD" `
  -VenvPath "$PWD\.venv-qa-clean" `
  -ForceRecreateVenv `
  -SkipRun
```

## Manual local sanity (Windows release EXE)

Use on a clean VM to validate real user path (no repo required):
1. Download `AlbionCommandDesk-Setup-vX.Y.Z-x86_64.exe` from release page.
2. Run from PowerShell with log capture:
```
.\AlbionCommandDesk-Setup-vX.Y.Z-x86_64.exe *>&1 | Tee-Object "$HOME\Desktop\acd-install.log"
```
3. Expected result:
   - install completes without auto-start failure,
   - runtime path exists: `%LOCALAPPDATA%\AlbionCommandDesk\runtime\vX.Y.Z`,
   - CLI path exists: `%LOCALAPPDATA%\AlbionCommandDesk\venv\Scripts\albion-command-desk.exe`.

## Manual local sanity (Windows live capture bundle)

Use on a clean VM after installing `Npcap Runtime`:
1. Confirm the release also ships `AlbionCommandDesk-WindowsCapture-vX.Y.Z.zip`.
2. Run the bootstrap installer EXE.
3. Expected result:
   - bootstrap stages the optional Windows capture bundle,
   - `Start` shows `Capture runtime: ready`,
   - `live` is available without installing `Npcap SDK` or Visual C++ build tools.
