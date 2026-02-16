# macOS Bootstrap Installer

One-command setup for Albion Command Desk from a source checkout.

## What it does

1. Verifies macOS and Xcode Command Line Tools (`xcode-select`, `clang`).
2. Detects Python 3.10+ (prefers `python3.12`, `python3.11`, `python3.10`).
3. Creates (or reuses) a virtual environment.
4. Upgrades `pip`.
5. Installs package using selected profile:
   - `core` (default): base package `.` without live capture backend.
   - `capture`: package with live backend `.[capture]`.
6. Verifies CLI startup.
7. Runs shared smoke checks (CLI import + Qt startup probe).
8. Starts app in mode matching selected profile (unless `--skip-run` is used).

## Usage

From repository root:

```bash
bash ./tools/install/macos/install.sh
```

Install with live capture backend:

```bash
bash ./tools/install/macos/install.sh --profile capture
```

Install only (do not start app):

```bash
bash ./tools/install/macos/install.sh --skip-run
```

Recreate virtual environment before install:

```bash
bash ./tools/install/macos/install.sh --force-recreate-venv
```

Use a specific Python interpreter (CI/controlled runtime):

```bash
bash ./tools/install/macos/install.sh --python "$(command -v python3.12)"
```

## Notes

- If command line tools are missing, run `xcode-select --install`.
- If capture profile fails, use `--profile core` for non-live usage.
- If `--profile capture` fails on Python 3.13, retry with Python 3.11 or 3.12.
