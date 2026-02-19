from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen


API_BASE = "https://api.github.com"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OS_ORDER = {"windows": 0, "linux": 1, "macos": 2, "unknown": 9}
_ARCH_ORDER = {"x86_64": 0, "arm64": 1, "universal": 2}
_PREFERRED_KIND_BY_OS = {
    "windows": "installer",
    "linux": "archive",
    "macos": "archive",
}
_KIND_FALLBACK_ORDER = {
    "installer": 0,
    "archive": 1,
    "bootstrap-script": 2,
    "asset": 9,
}


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    size: int
    digest: str


def _json_get(url: str, token: str | None = None) -> dict:
    headers = {"User-Agent": "AlbionCommandDesk/manifest-builder"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["Accept"] = "application/vnd.github+json"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _download_sha256(url: str, token: str | None = None) -> str:
    headers = {"User-Agent": "AlbionCommandDesk/manifest-builder"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    digest = hashlib.sha256()
    with urlopen(request, timeout=120) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _asset_os(name: str) -> str:
    lower = name.lower()
    if "windows" in lower or lower.endswith(".exe") or lower.endswith(".msi"):
        return "windows"
    if "linux" in lower or lower.endswith(".appimage"):
        return "linux"
    if lower.endswith(".dmg"):
        return "macos"
    if "macos" in lower or "darwin" in lower or "osx" in lower:
        return "macos"
    return "unknown"


def _asset_arch(name: str) -> str:
    lower = name.lower()
    if "universal" in lower:
        return "universal"
    if "arm64" in lower or "aarch64" in lower:
        return "arm64"
    if "x86_64" in lower or "amd64" in lower or "x64" in lower or "win64" in lower:
        return "x86_64"
    return "x86_64"


def _asset_kind(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".exe") or lower.endswith(".msi") or lower.endswith(".pkg"):
        return "installer"
    if lower.endswith(".ps1") or lower.endswith(".sh"):
        return "bootstrap-script"
    if (
        lower.endswith(".zip")
        or lower.endswith(".tar.gz")
        or lower.endswith(".tgz")
        or lower.endswith(".dmg")
        or lower.endswith(".appimage")
    ):
        return "archive"
    return "asset"


def _normalize_digest(raw_digest: str, url: str, token: str | None) -> str:
    digest = (raw_digest or "").strip().lower()
    if digest.startswith("sha256:"):
        normalized = digest.split(":", 1)[1]
    else:
        normalized = _download_sha256(url, token=token)
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError(f"invalid sha256 digest for asset url={url}")
    return normalized


def _validate_asset_fields(asset: dict) -> None:
    url = str(asset.get("url", "")).strip()
    if not url.startswith("https://"):
        raise ValueError(f"asset url must use https: {url or '<empty>'}")
    digest = str(asset.get("sha256", "")).strip().lower()
    if not _SHA256_RE.fullmatch(digest):
        raise ValueError(f"asset sha256 is invalid for {asset.get('name', '<unknown>')}")
    size = int(asset.get("size", 0) or 0)
    if size <= 0:
        raise ValueError(f"asset size must be > 0 for {asset.get('name', '<unknown>')}")
    if not str(asset.get("name", "")).strip():
        raise ValueError("asset name is empty")


def _asset_sort_key(asset: dict) -> tuple[int, int, int, str]:
    os_name = str(asset.get("os", "unknown")).lower()
    arch = str(asset.get("arch", "x86_64")).lower()
    kind = str(asset.get("kind", "asset")).lower()
    preferred_kind = _PREFERRED_KIND_BY_OS.get(os_name, "")
    preferred_rank = 0 if preferred_kind and kind == preferred_kind else 1
    return (
        _OS_ORDER.get(os_name, _OS_ORDER["unknown"]),
        _ARCH_ORDER.get(arch, 9),
        preferred_rank * 10 + _KIND_FALLBACK_ORDER.get(kind, _KIND_FALLBACK_ORDER["asset"]),
        str(asset.get("name", "")),
    )


def _parse_assets(release: dict, token: str | None) -> list[dict]:
    output: list[dict] = []
    for asset in release.get("assets", []) or []:
        name = str(asset.get("name", "")).strip()
        url = str(asset.get("browser_download_url", "")).strip()
        size = int(asset.get("size", 0) or 0)
        if not name or not url or size <= 0:
            continue
        digest = _normalize_digest(str(asset.get("digest", "")), url, token)
        output.append(
            {
                "os": _asset_os(name),
                "arch": _asset_arch(name),
                "kind": _asset_kind(name),
                "name": name,
                "url": url,
                "sha256": digest,
                "size": size,
            }
        )
    for parsed in output:
        _validate_asset_fields(parsed)
    output.sort(key=_asset_sort_key)
    return output


def validate_manifest_strategy(manifest: dict) -> tuple[list[str], list[str]]:
    assets = manifest.get("assets", []) or []
    blockers: list[str] = []
    warnings: list[str] = []

    def has_asset(os_name: str, kind: str, arch: str | None = None) -> bool:
        for asset in assets:
            if asset.get("os") != os_name:
                continue
            if asset.get("kind") != kind:
                continue
            if arch is not None and asset.get("arch") != arch:
                continue
            return True
        return False

    if not has_asset("windows", "installer", "x86_64"):
        blockers.append("Missing required Windows x86_64 installer asset.")

    if not has_asset("linux", "archive") and not has_asset("linux", "bootstrap-script"):
        warnings.append(
            "No Linux archive/bootstrap asset attached (core install still possible via repository bootstrap script)."
        )

    if not has_asset("macos", "archive") and not has_asset("macos", "bootstrap-script"):
        warnings.append(
            "No macOS archive/bootstrap asset attached (core install still possible via repository bootstrap script)."
        )

    for asset in assets:
        try:
            _validate_asset_fields(asset)
        except ValueError as exc:
            blockers.append(str(exc))

    for os_name, preferred_kind in _PREFERRED_KIND_BY_OS.items():
        os_assets = [asset for asset in assets if asset.get("os") == os_name]
        if not os_assets:
            continue
        if not any(str(asset.get("kind", "")).lower() == preferred_kind for asset in os_assets):
            warnings.append(
                f"{os_name} release has no {preferred_kind} asset; using fallback kind {os_assets[0].get('kind', 'asset')}."
            )
            continue
        first_kind = str(os_assets[0].get("kind", "")).lower()
        if first_kind != preferred_kind:
            blockers.append(
                f"Preferred asset ordering violated for {os_name}: first asset kind is {first_kind}, expected {preferred_kind}."
            )

    return blockers, warnings


def _manifest(
    *,
    repo: str,
    release: dict,
    channel: str,
    min_supported_version: str | None,
    token: str | None,
) -> dict:
    tag_name = str(release.get("tag_name", "")).strip()
    version = tag_name.lstrip("vV")
    if not version:
        raise ValueError("release tag_name is empty")
    min_supported = min_supported_version or version
    return {
        "schema_version": 1,
        "app_id": "albion-command-desk",
        "channel": channel,
        "published_at": str(release.get("published_at", "")),
        "latest": {
            "version": version,
            "release_url": str(release.get("html_url", "")),
            "changelog_url": f"https://github.com/{repo}/blob/main/CHANGELOG.md",
            "min_supported_version": min_supported,
        },
        "assets": _parse_assets(release, token=token),
    }


def build_manifest(
    *,
    repo: str,
    tag: str,
    channel: str,
    output: Path,
    min_supported_version: str | None,
    token: str | None,
) -> Path:
    release_url = f"{API_BASE}/repos/{repo}/releases/tags/{tag}"
    release = _json_get(release_url, token=token)
    manifest = _manifest(
        repo=repo,
        release=release,
        channel=channel,
        min_supported_version=min_supported_version,
        token=token,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build release manifest from GitHub release metadata")
    parser.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    parser.add_argument("--tag", required=True, help="Release tag, for example v0.2.0")
    parser.add_argument("--channel", default="stable", choices=["stable", "beta", "nightly"])
    parser.add_argument("--output", required=True, help="Output manifest file path")
    parser.add_argument("--min-supported-version", default="")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    args = parser.parse_args(argv)

    output_path = Path(args.output)
    build_manifest(
        repo=args.repo,
        tag=args.tag,
        channel=args.channel,
        output=output_path,
        min_supported_version=args.min_supported_version or None,
        token=args.token or None,
    )
    print(f"Manifest written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
