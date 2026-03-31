from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version

_FALLBACK_VERSION = "local-dev"


def resolve_app_version() -> str:
    try:
        return str(package_version("albion-command-desk") or _FALLBACK_VERSION)
    except PackageNotFoundError:
        return _FALLBACK_VERSION
    except Exception:
        return _FALLBACK_VERSION
