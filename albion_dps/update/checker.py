from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass
from urllib.request import Request, urlopen


DEFAULT_MANIFEST_URL = (
    "https://github.com/D4dits/Albion-Command-Desk/releases/latest/download/manifest.json"
)


@dataclass(frozen=True)
class UpdateInfo:
    available: bool
    current_version: str
    latest_version: str
    release_url: str
    download_url: str
    notes_url: str
    manifest_url: str
    error: str = ""


def default_manifest_url() -> str:
    return os.environ.get("ALBION_COMMAND_DESK_MANIFEST_URL", DEFAULT_MANIFEST_URL).strip()


def check_for_updates(
    *,
    current_version: str,
    manifest_url: str | None = None,
    timeout_seconds: float = 4.0,
    target_os: str | None = None,
    target_arch: str | None = None,
) -> UpdateInfo:
    url = (manifest_url or default_manifest_url()).strip()
    if not url:
        return UpdateInfo(
            available=False,
            current_version=current_version,
            latest_version=current_version,
            release_url="",
            download_url="",
            notes_url="",
            manifest_url="",
            error="manifest url is empty",
        )
    try:
        payload = _fetch_manifest(url, timeout_seconds=timeout_seconds)
        latest = str(payload.get("latest", {}).get("version", "")).strip()
        release_url = str(payload.get("latest", {}).get("release_url", "")).strip()
        changelog_url = str(payload.get("latest", {}).get("changelog_url", "")).strip()
        selected_os, selected_arch = _resolve_platform(
            os_override=target_os,
            arch_override=target_arch,
        )
        download_url = _select_asset_url(payload, os_name=selected_os, arch=selected_arch)
        if not download_url:
            download_url = release_url
        notes_url = changelog_url or release_url
        if not latest:
            return UpdateInfo(
                available=False,
                current_version=current_version,
                latest_version=current_version,
                release_url="",
                download_url="",
                notes_url="",
                manifest_url=url,
                error="latest.version missing",
            )
        update_available = _is_version_newer(latest, current_version)
        return UpdateInfo(
            available=bool(update_available and (download_url or release_url)),
            current_version=current_version,
            latest_version=latest,
            release_url=release_url,
            download_url=download_url,
            notes_url=notes_url,
            manifest_url=url,
            error="" if update_available else "",
        )
    except Exception as exc:
        return UpdateInfo(
            available=False,
            current_version=current_version,
            latest_version=current_version,
            release_url="",
            download_url="",
            notes_url="",
            manifest_url=url,
            error=str(exc),
        )


def _fetch_manifest(url: str, *, timeout_seconds: float) -> dict:
    req = Request(url, headers={"User-Agent": "AlbionCommandDesk/0.1"})
    with urlopen(req, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object")
    return data


def _is_version_newer(candidate: str, current: str) -> bool:
    return _parse_version_tuple(candidate) > _parse_version_tuple(current)


def _parse_version_tuple(value: str) -> tuple[int, int, int]:
    cleaned = value.strip().lstrip("vV")
    parts = cleaned.split(".")
    numbers: list[int] = []
    for token in parts[:3]:
        digits = "".join(ch for ch in token if ch.isdigit())
        numbers.append(int(digits) if digits else 0)
    while len(numbers) < 3:
        numbers.append(0)
    return (numbers[0], numbers[1], numbers[2])


def _resolve_platform(*, os_override: str | None, arch_override: str | None) -> tuple[str, str]:
    os_raw = (os_override or "").strip().lower()
    if not os_raw:
        detected_os = platform.system().lower()
        if detected_os.startswith("win"):
            os_raw = "windows"
        elif detected_os.startswith("linux"):
            os_raw = "linux"
        elif detected_os.startswith("darwin"):
            os_raw = "macos"
        else:
            os_raw = "unknown"
    arch_raw = (arch_override or "").strip().lower()
    if not arch_raw:
        detected_arch = platform.machine().lower()
        if detected_arch in ("x86_64", "amd64", "x64"):
            arch_raw = "x86_64"
        elif detected_arch in ("arm64", "aarch64"):
            arch_raw = "arm64"
        else:
            arch_raw = "x86_64"
    return os_raw, arch_raw


def _select_asset_url(payload: dict, *, os_name: str, arch: str) -> str:
    assets = payload.get("assets")
    if not isinstance(assets, list):
        return ""
    arch_preferences = [arch]
    if arch != "universal":
        arch_preferences.append("universal")
    if arch != "x86_64":
        arch_preferences.append("x86_64")
    arch_preferences.append("")
    for preferred_arch in arch_preferences:
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            if str(asset.get("os", "")).strip().lower() != os_name:
                continue
            asset_arch = str(asset.get("arch", "")).strip().lower()
            if preferred_arch and asset_arch != preferred_arch:
                continue
            if not preferred_arch and asset_arch:
                continue
            candidate = str(asset.get("url", "")).strip()
            if candidate:
                return candidate
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        if str(asset.get("os", "")).strip().lower() != os_name:
            continue
        candidate = str(asset.get("url", "")).strip()
        if candidate:
            return candidate
    return ""
