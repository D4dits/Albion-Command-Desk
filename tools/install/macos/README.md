# macOS Bootstrap Installer

One-command setup for Albion Command Desk from a source checkout.

## What it does

1. Verifies macOS and Xcode Command Line Tools (`xcode-select`, `clang`).
2. Detects Python 3.10+ (prefers `python3.12`, `python3.11`, `python3.10`).
3. Creates (or reuses) a virtual environment.
4. Upgrades `pip`.
5. Installs package using selected profile:
   - `capture` (default): tries live backend `.[capture]`.
   - `core`: base package `.` without live capture backend.
   - If capture prerequisites are missing, installer falls back to `core` automatically.
6. Verifies CLI startup.
7. Runs shared smoke checks (CLI import + Qt startup probe).
8. Starts app in `core` mode (unless `--skip-run` is used).
   - If capture extras are ready, installer prints the exact `live` launch command.

## Usage

From repository root:

```bash
bash ./tools/install/macos/install.sh
```

Force base/core install only:

```bash
bash ./tools/install/macos/install.sh --profile core
```

Require strict capture (no fallback to core):

```bash
bash ./tools/install/macos/install.sh --strict-capture
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

CI/non-interactive mode (disables pip prompts and forces `--skip-run`):

```bash
bash ./tools/install/macos/install.sh --non-interactive
```

Set release-version label for artifact contract diagnostics:

```bash
bash ./tools/install/macos/install.sh --release-version 0.2.0 --skip-run
```

## Notes

- If command line tools are missing, run `xcode-select --install`.
- `core` mode does not require packet-capture development headers.
- Default path now attempts `capture` first and auto-falls back to `core` if `libpcap`/toolchain prerequisites are missing.
- Use `--strict-capture` only when you want capture install to fail instead of fallback.
- If capture install fails on Python 3.13, retry with Python 3.11 or 3.12.
- Diagnostic output includes expected primary macOS artifact name:
  `AlbionCommandDesk-vX.Y.Z-universal.dmg`.
