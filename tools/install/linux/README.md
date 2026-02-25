# Linux Bootstrap Installer

One-command setup for Albion Command Desk from a source checkout.

## What it does

1. Detects Python 3.10+ (prefers `python3.12`, `python3.11`, `python3.10`).
2. Creates (or reuses) a virtual environment.
3. Upgrades `pip`.
4. Installs package using selected profile:
   - `capture` (default): tries live backend `.[capture]`.
   - `core`: base package `.` without live capture backend.
   - If capture prerequisites are missing, installer falls back to `core` automatically.
5. Verifies CLI startup.
6. Runs shared smoke checks (CLI import + Qt startup probe).
7. Starts app in `core` mode (unless `--skip-run` is used).
   - If capture extras are ready, installer prints the exact `live` launch command.

## Usage

From repository root:

```bash
bash ./tools/install/linux/install.sh
```

Force base/core install only:

```bash
bash ./tools/install/linux/install.sh --profile core
```

Require strict capture (no fallback to core):

```bash
bash ./tools/install/linux/install.sh --strict-capture
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

- `core` mode does not require packet-capture development headers.
- Default path now attempts `capture` first and auto-falls back to `core` if `libpcap`/toolchain prerequisites are missing.
- Use `--strict-capture` only when you want capture install to fail instead of fallback.
- If capture install fails on Python 3.13, retry with Python 3.11 or 3.12.
- Diagnostic output includes expected primary Linux artifact name:
  `AlbionCommandDesk-vX.Y.Z-x86_64.AppImage`.
