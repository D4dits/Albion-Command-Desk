# Windows Bootstrap Installer

One-command setup for Albion Command Desk from source checkout.

## What it does

1. Detects Python 3.10+ (prefers `py -3.12`, then `py -3.11`, then `py -3.10`).
2. Creates (or reuses) a virtual environment.
3. Upgrades `pip`.
4. Installs package using selected profile:
   - `core` (default): base package `.` without live capture backend.
   - `capture`: package with live backend `.[capture]`.
5. Verifies CLI startup.
6. Runs shared smoke checks (CLI import + Qt startup probe).
7. Starts app in mode matching selected profile (unless `-SkipRun` is used).

## Usage

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1
```

Install with live capture backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -Profile capture
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

Legacy alias (same as `-Profile core`):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1 -SkipCaptureExtras
```

## Notes

- If packet capture dependencies fail, reinstall with `-Profile core`.
- If using `-Profile capture`, prefer Python 3.11 or 3.12.
- For local firewalls/AV restrictions, run PowerShell as Administrator.
- `live` mode checks Npcap Runtime on startup and logs detected install path.
- If Npcap Runtime is missing, install from: `https://npcap.com/#download`.
