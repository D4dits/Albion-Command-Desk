# Linux Bootstrap Installer

One-command setup for Albion Command Desk from a source checkout.

## What it does

1. Detects Python 3.10+ (prefers `python3.12`, `python3.11`, `python3.10`).
2. Creates (or reuses) a virtual environment.
3. Upgrades `pip`.
4. Installs package using selected profile:
   - `core` (default): base package `.` without live capture backend.
   - `capture`: tries live backend `.[capture]`; falls back to `core` when capture prerequisites are missing.
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

Require strict capture (no fallback to core):

```bash
bash ./tools/install/linux/install.sh --profile capture --strict-capture
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

CI/non-interactive mode (disables pip prompts and forces `--skip-run`):

```bash
bash ./tools/install/linux/install.sh --non-interactive
```

Set release-version label for artifact contract diagnostics:

```bash
bash ./tools/install/linux/install.sh --release-version 0.2.0 --skip-run
```

## Notes

- Default path (`core`) does not require packet-capture development headers.
- Capture profile auto-falls back to `core` if `libpcap`/toolchain prerequisites are missing.
- Use `--strict-capture` only when you want capture install to fail instead of fallback.
- If `--profile capture` fails on Python 3.13, retry with Python 3.11 or 3.12.
- Diagnostic output includes expected primary Linux artifact name:
  `AlbionCommandDesk-vX.Y.Z-x86_64.AppImage`.
