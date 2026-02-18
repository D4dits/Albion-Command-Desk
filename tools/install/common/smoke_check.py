from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _check_cli_import() -> tuple[bool, str]:
    try:
        import albion_dps.cli  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment-specific
        return False, f"CLI import failed: {exc}"
    return True, "CLI import OK"


def _check_qt_probe(project_root: Path) -> tuple[bool, str]:
    qml_path = project_root / "albion_dps" / "qt" / "ui" / "Main.qml"
    if not qml_path.exists():
        return False, f"QML file missing: {qml_path}"
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtGui import QGuiApplication
    except Exception as exc:  # pragma: no cover - environment-specific
        return False, f"PySide6 import failed: {exc}"

    app = None
    try:
        app = QGuiApplication.instance() or QGuiApplication([])
    except Exception as exc:  # pragma: no cover - environment-specific
        return False, f"Qt startup probe failed: {exc}"
    finally:
        if app is not None:
            app.quit()

    return True, "Qt startup probe OK"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Albion Command Desk install smoke check")
    parser.add_argument("--project-root", required=True, help="Repository root path")
    parser.add_argument("--profile", choices=("core", "capture"), default="core", help="Install profile context")
    parser.add_argument("--artifact-name", default="", help="Expected primary release artifact name (diagnostic)")
    parser.add_argument(
        "--report-path",
        default="",
        help="Optional JSON report output path for CI evidence",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    if not (project_root / "pyproject.toml").exists():
        print(f"[smoke] Project root invalid: {project_root}", file=sys.stderr)
        return 2

    print(f"[smoke] CONTEXT: profile={args.profile}")
    if args.artifact_name:
        print(f"[smoke] CONTEXT: expected_primary_artifact={args.artifact_name}")

    checks = [
        _check_cli_import,
        lambda: _check_qt_probe(project_root),
    ]

    report: dict[str, object] = {
        "profile": args.profile,
        "artifact_name": args.artifact_name,
        "project_root": str(project_root),
        "checks": [],
    }
    failed = False
    for check in checks:
        ok, message = check()
        prefix = "OK" if ok else "FAIL"
        print(f"[smoke] {prefix}: {message}")
        report["checks"].append({"ok": bool(ok), "message": message})
        if not ok:
            failed = True

    report["passed"] = not failed
    report["exit_code"] = 1 if failed else 0
    if args.report_path.strip():
        report_path = Path(args.report_path).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"[smoke] REPORT: {report_path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
