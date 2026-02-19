#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
VENV_PATH="${PROJECT_ROOT}/venv"
PYTHON_CMD_OVERRIDE=""
SKIP_RUN=0
FORCE_RECREATE_VENV=0
INSTALL_PROFILE="core"
STRICT_CAPTURE=0
NON_INTERACTIVE=0
RELEASE_VERSION="${ACD_RELEASE_VERSION:-local-dev}"

log_info() {
  printf '[ACD install] %s\n' "$1"
}

log_warn() {
  printf '[ACD install] %s\n' "$1" >&2
}

log_hint() {
  printf '[ACD install] hint: %s\n' "$1" >&2
}

fail() {
  printf '[ACD install] %s\n' "$1" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: ./tools/install/linux/install.sh [options]

Options:
  --project-root <path>      Override repository root path.
  --venv-path <path>         Override virtual environment path.
  --python <path-or-command> Force Python interpreter command/path.
  --profile <core|capture>   Install profile (`core` default, `capture` for live mode).
  --release-version <ver>    Release version label used for artifact contract diagnostics.
  --skip-run                 Install only (do not start app).
  --non-interactive          Disable pip prompts and force --skip-run (CI mode).
  --force-recreate-venv      Remove and recreate virtual environment.
  --strict-capture           Fail if capture profile cannot be installed.
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
    --release-version)
      [[ $# -ge 2 ]] || fail "--release-version requires a value."
      RELEASE_VERSION="$2"
      shift 2
      ;;
    --skip-run)
      SKIP_RUN=1
      shift
      ;;
    --non-interactive)
      NON_INTERACTIVE=1
      shift
      ;;
    --force-recreate-venv)
      FORCE_RECREATE_VENV=1
      shift
      ;;
    --strict-capture)
      STRICT_CAPTURE=1
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

detect_libpcap() {
  if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists libpcap; then
    printf '%s\n' "available (pkg-config libpcap)"
    return 0
  fi
  if ldconfig -p 2>/dev/null | grep -qi libpcap; then
    printf '%s\n' "available (ldconfig lookup)"
    return 0
  fi
  printf '%s\n' "missing"
  return 1
}

get_primary_artifact_name() {
  printf 'AlbionCommandDesk-v%s-x86_64.AppImage' "$RELEASE_VERSION"
}

show_diagnostics() {
  local compiler_state="missing"
  if command -v gcc >/dev/null 2>&1; then
    compiler_state="available (gcc)"
  elif command -v clang >/dev/null 2>&1; then
    compiler_state="available (clang)"
  fi
  local libpcap_state
  libpcap_state="$(detect_libpcap || true)"
  [[ -n "$libpcap_state" ]] || libpcap_state="missing"

  log_info "Diagnostic summary:"
  log_info "  project_root: ${PROJECT_ROOT}"
  log_info "  venv_path: ${VENV_PATH}"
  log_info "  profile: ${INSTALL_PROFILE}"
  log_info "  expected_primary_artifact: $(get_primary_artifact_name)"
  log_info "  python: ${PYTHON_CMD} (version ${PYTHON_VERSION})"
  if [[ "$compiler_state" == missing ]]; then
    log_warn "  c_compiler: missing (capture profile may fail to build backend)"
    log_hint "For core mode this is expected and safe."
  else
    log_info "  c_compiler: ${compiler_state}"
  fi
  if [[ "$INSTALL_PROFILE" == "capture" ]]; then
    if [[ "$libpcap_state" == "missing" ]]; then
      log_warn "  libpcap: missing"
      log_hint "Install libpcap dev package (e.g. libpcap-dev) before capture profile."
    else
      log_info "  libpcap: ${libpcap_state}"
    fi
  else
    log_info "  libpcap: optional (core mode selected)"
  fi
}

resolved="$(resolve_python || true)"
[[ -n "$resolved" ]] || fail "Python 3.10+ not found. Install Python and rerun."
PYTHON_CMD="${resolved%%|*}"
PYTHON_VERSION="${resolved##*|}"
log_info "Using Python launcher: ${PYTHON_CMD} (version ${PYTHON_VERSION})"

if [[ "$INSTALL_PROFILE" == "capture" && "$PYTHON_VERSION" == 3.13* ]]; then
  log_warn "Python 3.13 may fail to install capture extras on some systems. Prefer Python 3.11 or 3.12."
fi

if (( NON_INTERACTIVE )); then
  export PIP_NO_INPUT=1
  export PIP_DISABLE_PIP_VERSION_CHECK=1
  SKIP_RUN=1
  log_info "Non-interactive mode enabled (pip prompts disabled, --skip-run forced)."
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
show_diagnostics

if [[ "$INSTALL_PROFILE" == "capture" ]]; then
  if [[ "$(detect_libpcap || true)" == "missing" ]]; then
    if (( STRICT_CAPTURE )); then
      fail "Capture profile requested with --strict-capture but libpcap was not detected."
    fi
    log_warn "Capture profile requested, but libpcap was not detected. Falling back to core profile."
    log_hint "Install libpcap-dev and rerun with --profile capture when ready."
    INSTALL_PROFILE="core"
    INSTALL_TARGET="."
  fi
fi

log_info "Installing Albion Command Desk (${INSTALL_TARGET})"
if ! (
  cd "$PROJECT_ROOT"
  "$VENV_PYTHON" -m pip install -e "$INSTALL_TARGET"
); then
  if [[ "$INSTALL_PROFILE" == "capture" && $STRICT_CAPTURE -eq 0 ]]; then
    log_warn "Capture profile install failed; falling back to core profile."
    log_hint "Use --strict-capture if you want this to fail instead of fallback."
    (
      cd "$PROJECT_ROOT"
      "$VENV_PYTHON" -m pip install -e "."
    )
    INSTALL_PROFILE="core"
  else
    fail "Package install failed."
  fi
fi

log_info "Verifying CLI entrypoint"
if [[ -x "$VENV_CLI" ]]; then
  "$VENV_CLI" --version
else
  "$VENV_PYTHON" -m albion_dps.cli --version
fi

[[ -f "$SMOKE_SCRIPT" ]] || fail "Shared smoke check script not found: ${SMOKE_SCRIPT}"
log_info "Running shared install smoke checks"
"$VENV_PYTHON" "$SMOKE_SCRIPT" --project-root "$PROJECT_ROOT" --profile "$INSTALL_PROFILE" --artifact-name "$(get_primary_artifact_name)"

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
