#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
VENV_PATH="${PROJECT_ROOT}/venv"
PYTHON_CMD_OVERRIDE=""
SKIP_RUN=0
FORCE_RECREATE_VENV=0
INSTALL_PROFILE="core"

log_info() {
  printf '[ACD install] %s\n' "$1"
}

log_warn() {
  printf '[ACD install] %s\n' "$1" >&2
}

fail() {
  printf '[ACD install] %s\n' "$1" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: ./tools/install/macos/install.sh [options]

Options:
  --project-root <path>      Override repository root path.
  --venv-path <path>         Override virtual environment path.
  --python <path-or-command> Force Python interpreter command/path.
  --profile <core|capture>   Install profile (`core` default, `capture` for live mode).
  --skip-run                 Install only (do not start app).
  --force-recreate-venv      Remove and recreate virtual environment.
  -h, --help                 Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root)
      [[ $# -ge 2 ]] || fail "--project-root requires a value."
      PROJECT_ROOT="$2"
      shift 2
      ;;
    --venv-path)
      [[ $# -ge 2 ]] || fail "--venv-path requires a value."
      VENV_PATH="$2"
      shift 2
      ;;
    --python)
      [[ $# -ge 2 ]] || fail "--python requires a value."
      PYTHON_CMD_OVERRIDE="$2"
      shift 2
      ;;
    --profile)
      [[ $# -ge 2 ]] || fail "--profile requires a value."
      INSTALL_PROFILE="$2"
      shift 2
      ;;
    --skip-run)
      SKIP_RUN=1
      shift
      ;;
    --force-recreate-venv)
      FORCE_RECREATE_VENV=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown option: $1"
      ;;
  esac
done

if [[ "$INSTALL_PROFILE" != "core" && "$INSTALL_PROFILE" != "capture" ]]; then
  fail "Invalid --profile value: ${INSTALL_PROFILE} (expected core|capture)"
fi

[[ -f "${PROJECT_ROOT}/pyproject.toml" ]] || fail "pyproject.toml not found under '${PROJECT_ROOT}'."

if [[ "$(uname -s)" != "Darwin" ]]; then
  fail "This installer is intended for macOS."
fi

if ! xcode-select -p >/dev/null 2>&1; then
  fail "Xcode Command Line Tools are missing. Run: xcode-select --install"
fi

if ! command -v clang >/dev/null 2>&1; then
  fail "clang is missing. Ensure Xcode Command Line Tools are installed."
fi

resolve_python() {
  if [[ -n "$PYTHON_CMD_OVERRIDE" ]]; then
    if ! command -v "$PYTHON_CMD_OVERRIDE" >/dev/null 2>&1 && [[ ! -x "$PYTHON_CMD_OVERRIDE" ]]; then
      fail "Requested Python command/path not found: $PYTHON_CMD_OVERRIDE"
    fi
    local version major minor
    version="$("$PYTHON_CMD_OVERRIDE" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
    if [[ -z "$version" ]]; then
      fail "Could not execute requested Python: $PYTHON_CMD_OVERRIDE"
    fi
    major="${version%%.*}"
    minor="${version##*.}"
    if [[ "$major" != "3" ]] || [[ ! "$minor" =~ ^[0-9]+$ ]] || (( minor < 10 )); then
      fail "Requested Python must be 3.10+ (detected: $version)"
    fi
    printf '%s|%s\n' "$PYTHON_CMD_OVERRIDE" "$version"
    return 0
  fi

  local candidates=(
    "python3.12"
    "python3.11"
    "python3.10"
    "python3"
    "python"
  )
  local cmd version major minor
  for cmd in "${candidates[@]}"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      continue
    fi
    version="$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
    if [[ -z "$version" ]]; then
      continue
    fi
    major="${version%%.*}"
    minor="${version##*.}"
    if [[ "$major" == "3" ]] && [[ "$minor" =~ ^[0-9]+$ ]] && (( minor >= 10 )); then
      printf '%s|%s\n' "$cmd" "$version"
      return 0
    fi
  done
  return 1
}

resolved="$(resolve_python || true)"
[[ -n "$resolved" ]] || fail "Python 3.10+ not found. Install Python and rerun."
PYTHON_CMD="${resolved%%|*}"
PYTHON_VERSION="${resolved##*|}"
log_info "Using Python launcher: ${PYTHON_CMD} (version ${PYTHON_VERSION})"

if [[ "$INSTALL_PROFILE" == "capture" && "$PYTHON_VERSION" == 3.13* ]]; then
  log_warn "Python 3.13 may fail to install capture extras on some systems. Prefer Python 3.11 or 3.12."
fi

if (( FORCE_RECREATE_VENV )) && [[ -d "$VENV_PATH" ]]; then
  log_info "Removing existing virtual environment: ${VENV_PATH}"
  rm -rf "$VENV_PATH"
fi

if [[ ! -d "$VENV_PATH" ]]; then
  log_info "Creating virtual environment"
  "$PYTHON_CMD" -m venv "$VENV_PATH"
else
  log_info "Using existing virtual environment: ${VENV_PATH}"
fi

VENV_PYTHON="${VENV_PATH}/bin/python"
VENV_CLI="${VENV_PATH}/bin/albion-command-desk"
SMOKE_SCRIPT="${PROJECT_ROOT}/tools/install/common/smoke_check.py"
[[ -x "$VENV_PYTHON" ]] || fail "Virtual environment python is missing: ${VENV_PYTHON}"

log_info "Upgrading pip"
"$VENV_PYTHON" -m pip install --upgrade pip

if [[ "$INSTALL_PROFILE" == "capture" ]]; then
  INSTALL_TARGET=".[capture]"
  log_info "Install profile: capture (includes live capture backend)"
else
  INSTALL_TARGET="."
  log_info "Install profile: core (UI + market/scanner/replay, no live capture backend)"
fi

log_info "Installing Albion Command Desk (${INSTALL_TARGET})"
(
  cd "$PROJECT_ROOT"
  "$VENV_PYTHON" -m pip install -e "$INSTALL_TARGET"
)

log_info "Verifying CLI entrypoint"
if [[ -x "$VENV_CLI" ]]; then
  "$VENV_CLI" --version
else
  "$VENV_PYTHON" -m albion_dps.cli --version
fi

[[ -f "$SMOKE_SCRIPT" ]] || fail "Shared smoke check script not found: ${SMOKE_SCRIPT}"
log_info "Running shared install smoke checks"
"$VENV_PYTHON" "$SMOKE_SCRIPT" --project-root "$PROJECT_ROOT"

if (( SKIP_RUN )); then
  log_info "Installation complete. Launch manually with:"
  if [[ "$INSTALL_PROFILE" == "capture" ]]; then
    printf '  %s live\n' "$VENV_CLI"
  else
    printf '  %s core\n' "$VENV_CLI"
    printf '  %s live   # after reinstall with --profile capture\n' "$VENV_CLI"
  fi
  exit 0
fi

if [[ "$INSTALL_PROFILE" == "capture" ]]; then
  log_info "Starting Albion Command Desk (live mode)"
else
  log_info "Starting Albion Command Desk (core mode)"
fi
if [[ -x "$VENV_CLI" ]]; then
  if [[ "$INSTALL_PROFILE" == "capture" ]]; then
    exec "$VENV_CLI" live
  fi
  exec "$VENV_CLI" core
fi
if [[ "$INSTALL_PROFILE" == "capture" ]]; then
  exec "$VENV_PYTHON" -m albion_dps.cli live
fi
exec "$VENV_PYTHON" -m albion_dps.cli core
