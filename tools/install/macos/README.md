# macOS Bootstrap Installer

One-command setup for Albion Command Desk from a source checkout.

## What it does

1. Verifies macOS and Xcode Command Line Tools (`xcode-select`, `clang`).
2. Detects Python 3.10+ (prefers `python3.12`, `python3.11`, `python3.10`).
3. Creates (or reuses) a virtual environment.
4. Upgrades `pip`.
5. Installs package with capture extras: `.[capture]`.
6. Verifies CLI startup.
7. Starts app in live mode (unless `--skip-run` is used).

## Usage

From repository root:

```bash
bash ./tools/install/macos/install.sh
```

Install only (do not start app):

```bash
bash ./tools/install/macos/install.sh --skip-run
```

Recreate virtual environment before install:

```bash
bash ./tools/install/macos/install.sh --force-recreate-venv
```

## Notes

- If command line tools are missing, run `xcode-select --install`.
- If capture extras fail on Python 3.13, retry with Python 3.11 or 3.12.
