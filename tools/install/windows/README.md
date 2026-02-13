# Windows Bootstrap Installer

One-command setup for Albion Command Desk from source checkout.

## What it does

1. Detects Python 3.10+ (prefers `py -3.12`, then `py -3.11`, then `py -3.10`).
2. Creates (or reuses) a virtual environment.
3. Upgrades `pip`.
4. Installs package with capture extras: `.[capture]`.
5. Verifies CLI startup.
6. Runs shared smoke checks (CLI import + Qt startup probe).
7. Starts app in live mode (unless `-SkipRun` is used).

## Usage

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install\windows\install.ps1
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

## Notes

- If packet capture dependencies fail, prefer Python 3.11 or 3.12.
- For local firewalls/AV restrictions, run PowerShell as Administrator.
