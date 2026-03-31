from __future__ import annotations

from albion_dps import __version__
from albion_dps.cli import _resolve_cli_version
from albion_dps.qt.runner import _current_app_version
from albion_dps.versioning import resolve_app_version


def main() -> int:
    versions = {
        "__version__": __version__,
        "cli": _resolve_cli_version(),
        "runner": _current_app_version(),
        "helper": resolve_app_version(),
    }
    unique = {str(value or "").strip() for value in versions.values()}
    if len(unique) != 1:
        print("[qa] FAIL: version surfaces disagree")
        for key, value in versions.items():
            print(f"  - {key}: {value}")
        return 1
    only = next(iter(unique), "")
    if not only:
        print("[qa] FAIL: resolved version is empty")
        return 1
    print(f"[qa] PASS: version surfaces agree on {only}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
