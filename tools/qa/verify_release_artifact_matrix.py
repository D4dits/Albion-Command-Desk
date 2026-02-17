from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


DEFAULT_MANIFEST_URL = (
    "https://github.com/D4dits/Albion-Command-Desk/releases/latest/download/manifest.json"
)

EXPECTED_KINDS: dict[str, set[str]] = {
    "windows": {"installer"},
    "linux": {"archive", "bootstrap-script"},
    "macos": {"archive", "bootstrap-script"},
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify release manifest exposes downloadable assets for a target OS."
    )
    parser.add_argument(
        "--manifest-url",
        default=DEFAULT_MANIFEST_URL,
        help="Manifest URL or file:// URI to validate.",
    )
    parser.add_argument(
        "--target-os",
        choices=("windows", "linux", "macos"),
        required=True,
        help="OS key to validate against manifest assets.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="Per-request timeout for manifest/asset probe.",
    )
    return parser.parse_args()


def _fetch_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    request = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


def _filter_assets(manifest: dict[str, Any], target_os: str) -> list[dict[str, Any]]:
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        return []
    return [
        asset
        for asset in assets
        if isinstance(asset, dict) and str(asset.get("os", "")).lower() == target_os
    ]


def _validate_kind(asset: dict[str, Any], target_os: str) -> bool:
    expected = EXPECTED_KINDS[target_os]
    kind = str(asset.get("kind", "")).strip().lower()
    return kind in expected


def _probe_asset_url(url: str, timeout_seconds: float) -> tuple[bool, str]:
    request = urllib.request.Request(
        url=url,
        method="GET",
        headers={"Range": "bytes=0-0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            code = getattr(response, "status", None)
            if code is None:
                return True, "OK (non-HTTP URL scheme)"
            if int(code) not in (200, 206):
                return False, f"HTTP {code}"
            return True, f"HTTP {code}"
    except urllib.error.HTTPError as exc:
        if exc.code == 416:
            return True, "HTTP 416 (empty file response, treated as reachable)"
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # pragma: no cover - environment dependent
        return False, str(exc)


def main() -> int:
    args = _parse_args()
    try:
        manifest = _fetch_json(args.manifest_url, args.timeout_seconds)
    except Exception as exc:
        print(f"[qa] FAIL: unable to fetch manifest: {exc}", file=sys.stderr)
        return 2

    matched = _filter_assets(manifest, args.target_os)
    if not matched:
        print(f"[qa] FAIL: no assets found for os={args.target_os}")
        return 1

    wrong_kind = [asset for asset in matched if not _validate_kind(asset, args.target_os)]
    if wrong_kind:
        print(f"[qa] FAIL: found {len(wrong_kind)} assets with invalid kind for os={args.target_os}")
        for asset in wrong_kind:
            print(
                f"  - {asset.get('name', '<unknown>')} kind={asset.get('kind', '<missing>')}",
                file=sys.stderr,
            )
        return 1

    reachable = False
    for asset in matched:
        name = str(asset.get("name", "<unknown>"))
        url = str(asset.get("url", "")).strip()
        if not url:
            print(f"[qa] FAIL: asset {name} is missing url")
            continue
        ok, detail = _probe_asset_url(url, args.timeout_seconds)
        status = "OK" if ok else "FAIL"
        print(f"[qa] {status}: {name} -> {detail}")
        reachable = reachable or ok

    if not reachable:
        print(f"[qa] FAIL: no reachable assets for os={args.target_os}")
        return 1

    print(f"[qa] PASS: release asset smoke passed for os={args.target_os}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
