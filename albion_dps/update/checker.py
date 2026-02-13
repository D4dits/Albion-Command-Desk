from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.request import Request, urlopen


DEFAULT_MANIFEST_URL = (
    "https://raw.githubusercontent.com/D4dits/Albion-Command-Desk/main/"
    "tools/release/manifest/manifest.json"
)


@dataclass(frozen=True)
class UpdateInfo:
    available: bool
    current_version: str
    latest_version: str
    release_url: str
    manifest_url: str
    error: str = ""


def default_manifest_url() -> str:
    return os.environ.get("ALBION_COMMAND_DESK_MANIFEST_URL", DEFAULT_MANIFEST_URL).strip()


def check_for_updates(
    *,
    current_version: str,
    manifest_url: str | None = None,
    timeout_seconds: float = 4.0,
) -> UpdateInfo:
    url = (manifest_url or default_manifest_url()).strip()
    if not url:
        return UpdateInfo(
            available=False,
            current_version=current_version,
            latest_version=current_version,
            release_url="",
            manifest_url="",
            error="manifest url is empty",
        )
    try:
        payload = _fetch_manifest(url, timeout_seconds=timeout_seconds)
        latest = str(payload.get("latest", {}).get("version", "")).strip()
        release_url = str(payload.get("latest", {}).get("release_url", "")).strip()
        if not latest:
            return UpdateInfo(
                available=False,
                current_version=current_version,
                latest_version=current_version,
                release_url="",
                manifest_url=url,
                error="latest.version missing",
            )
        update_available = _is_version_newer(latest, current_version)
        return UpdateInfo(
            available=bool(update_available and release_url),
            current_version=current_version,
            latest_version=latest,
            release_url=release_url,
            manifest_url=url,
            error="" if update_available else "",
        )
    except Exception as exc:
        return UpdateInfo(
            available=False,
            current_version=current_version,
            latest_version=current_version,
            release_url="",
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
