# Linux Bootstrap Installer

One-command setup for Albion Command Desk from a source checkout.

## What it does

1. Detects Python 3.10+ (prefers `python3.12`, `python3.11`, `python3.10`).
2. Creates (or reuses) a virtual environment.
3. Upgrades `pip`.
4. Installs package using selected profile:
   - `core` (default): base package `.` without live capture backend.
   - `capture`: package with live backend `.[capture]`.
5. Verifies CLI startup.
6. Runs shared smoke checks (CLI import + Qt startup probe).
7. Starts app in mode matching selected profile (unless `--skip-run` is used).

## Usage

From repository root:

```bash
bash ./tools/install/linux/install.sh
```

Install with live capture backend:

```bash
bash ./tools/install/linux/install.sh --profile capture
```

Install only (do not start app):

```bash
bash ./tools/install/linux/install.sh --skip-run
```

Recreate virtual environment before install:

```bash
bash ./tools/install/linux/install.sh --force-recreate-venv
```

Use a specific Python interpreter (CI/controlled runtime):

```bash
bash ./tools/install/linux/install.sh --python "$(command -v python3.12)"
```

## Notes

- On some distributions, packet capture dependencies require system libraries/toolchain.
- If capture profile fails, use `--profile core` for non-live usage.
- If `--profile capture` fails on Python 3.13, retry with Python 3.11 or 3.12.
