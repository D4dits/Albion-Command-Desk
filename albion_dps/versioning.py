from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path

_FALLBACK_VERSION = "local-dev"
_PYPROJECT_PATH = Path(__file__).resolve().parents[1] / "pyproject.toml"


def _read_checkout_version() -> str | None:
    try:
        lines = _PYPROJECT_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    in_project_section = False
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_project_section = line == "[project]"
            continue
        if not in_project_section or not line.startswith("version"):
            continue
        key, _, value = line.partition("=")
        if key.strip() != "version":
            continue
        normalized = value.strip().strip('"').strip("'")
        return normalized or None
    return None


def _read_installed_version() -> str | None:
    try:
        return str(package_version("albion-command-desk") or "").strip() or None
    except PackageNotFoundError:
        return None
    except Exception:
        return None


def resolve_app_version() -> str:
    checkout_version = _read_checkout_version()
    if checkout_version:
        return checkout_version

    installed_version = _read_installed_version()
    if installed_version:
        return installed_version

    return _FALLBACK_VERSION
