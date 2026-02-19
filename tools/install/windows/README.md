# Windows Bootstrap Installer

One-command setup for Albion Command Desk from source checkout.

## What it does

1. Detects Python 3.10+ (`py -3.12/-3.11/-3.10`, `python`, then common install paths).
2. If Python is missing, attempts `winget install --id Python.Python.3.12 --source winget`.
3. Creates (or reuses) a virtual environment.
4. Upgrades `pip`.
5. Installs package using selected profile:
   - `core` (default): base package `.` without live capture backend.
   - `capture`: tries live backend `.[capture]`; falls back to `core` when capture prerequisites are missing.
6. Verifies CLI startup.
7. Runs shared smoke checks (CLI import + Qt startup probe).
8. Starts app in mode matching selected profile (unless `-SkipRun` is used).

## Usage

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1
```

Install with live capture backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -Profile capture
```

Require strict capture (no fallback to core):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -Profile capture -StrictCapture
```

Install only (do not start app):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -SkipRun
```

Recreate virtual environment before install:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -ForceRecreateVenv
```

Use a specific Python interpreter (CI/controlled runtime):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -Python "C:\Python312\python.exe"
```

CI/non-interactive mode (disables pip prompts and forces no auto-run):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -NonInteractive
```

Set release-version label for artifact contract diagnostics:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -ReleaseVersion 0.2.0 -SkipRun
```

Legacy alias (same as `-Profile core`):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -SkipCaptureExtras
```

## Notes

- Default path (`core`) does not require Npcap SDK.
- Capture profile automatically falls back to `core` when SDK/build prerequisites are missing.
- Use `-StrictCapture` only when you explicitly want capture install to fail instead of fallback.
- If using `-Profile capture`, prefer Python 3.11 or 3.12.
- For local firewalls/AV restrictions, run PowerShell as Administrator.
- If `winget` fails because of source issues, install Python manually from `https://www.python.org/downloads/windows/` and rerun.
- `live` mode checks Npcap Runtime on startup and logs detected install path.
- If Npcap Runtime is missing, install from: `https://npcap.com/#download`.
- Diagnostic output includes expected primary Windows artifact name:
  `AlbionCommandDesk-Setup-vX.Y.Z-x86_64.exe`.
