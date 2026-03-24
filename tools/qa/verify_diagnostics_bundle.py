from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path


REQUIRED_ENTRIES = {
    "summary.json",
    "scanner.log.txt",
    "market.diagnostics.txt",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Albion Command Desk diagnostics bundle structure.")
    parser.add_argument("bundle", help="Path to diagnostics zip bundle")
    args = parser.parse_args(argv)

    bundle_path = Path(args.bundle).expanduser().resolve()
    if not bundle_path.exists():
        print(f"[qa] FAIL: bundle not found: {bundle_path}")
        return 1

    with zipfile.ZipFile(bundle_path, "r") as archive:
        names = set(archive.namelist())
        missing = sorted(REQUIRED_ENTRIES - names)
        if missing:
            print(f"[qa] FAIL: missing entries: {', '.join(missing)}")
            return 2
        summary = json.loads(archive.read("summary.json").decode("utf-8"))
        if "app_version" not in summary or "scanner" not in summary or "market" not in summary:
            print("[qa] FAIL: summary.json missing required keys")
            return 3

    print(f"[qa] OK: diagnostics bundle verified: {bundle_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
