from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from albion_dps.update.checker import (
    DEFAULT_MANIFEST_URL,
    check_for_updates,
    default_manifest_url,
)


def _write_manifest(data: dict) -> Path:
    base = Path("artifacts") / "tmp" / "update_checker_tests" / str(uuid.uuid4())
    base.mkdir(parents=True, exist_ok=True)
    path = base / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _cleanup_manifest(path: Path) -> None:
    shutil.rmtree(path.parent, ignore_errors=True)


def test_check_for_updates_reports_available_for_newer_version() -> None:
    manifest = {
        "schema_version": 1,
        "app_id": "albion-command-desk",
        "channel": "stable",
        "published_at": "2026-02-13T12:00:00Z",
        "latest": {
            "version": "0.2.0",
            "release_url": "https://example.com/release",
            "changelog_url": "https://example.com/changelog",
            "min_supported_version": "0.1.0",
        },
        "assets": [
            {
                "os": "windows",
                "arch": "x86_64",
                "kind": "installer",
                "name": "AlbionCommandDesk-Setup-v0.2.0-x86_64.exe",
                "url": "https://example.com/download/windows-setup.exe",
                "sha256": "6f3fb6cd2f5fbd4f5b8c4977f9f6f95fe0e7277d7c7e3610f10608b2307389df",
                "size": 123,
            },
            {
                "os": "windows",
                "arch": "x86_64",
                "kind": "bootstrap-script",
                "name": "acd-install-windows-v0.2.0.ps1",
                "url": "https://example.com/download/windows-install.ps1",
                "sha256": "bb8f5f7f0e4fb38d6bf69f7f2dfbc22dc15de6190f4067189a7c0f31dbb7fc01",
                "size": 222,
            },
        ],
    }
    path = _write_manifest(manifest)

    try:
        info = check_for_updates(
            current_version="0.1.0",
            manifest_url=path.resolve().as_uri(),
            target_os="windows",
            target_arch="x86_64",
        )
    finally:
        _cleanup_manifest(path)

    assert info.available is True
    assert info.latest_version == "0.2.0"
    assert info.release_url == "https://example.com/release"
    assert info.download_url == "https://example.com/download/windows-setup.exe"
    assert info.notes_url == "https://example.com/changelog"


def test_check_for_updates_reports_not_available_for_same_version() -> None:
    manifest = {
        "latest": {
            "version": "0.1.0",
            "release_url": "https://example.com/release",
        }
    }
    path = _write_manifest(manifest)

    try:
        info = check_for_updates(current_version="0.1.0", manifest_url=path.resolve().as_uri())
    finally:
        _cleanup_manifest(path)

    assert info.available is False
    assert info.latest_version == "0.1.0"


def test_check_for_updates_falls_back_to_release_url_when_asset_missing() -> None:
    manifest = {
        "latest": {
            "version": "0.2.0",
            "release_url": "https://example.com/release",
            "changelog_url": "https://example.com/changelog",
        },
        "assets": [],
    }
    path = _write_manifest(manifest)
    try:
        info = check_for_updates(
            current_version="0.1.0",
            manifest_url=path.resolve().as_uri(),
            target_os="windows",
            target_arch="x86_64",
        )
    finally:
        _cleanup_manifest(path)

    assert info.available is True
    assert info.download_url == "https://example.com/release"
    assert info.notes_url == "https://example.com/changelog"


def test_check_for_updates_falls_back_to_release_url_for_notes() -> None:
    manifest = {
        "latest": {
            "version": "0.2.0",
            "release_url": "https://example.com/release",
        },
        "assets": [],
    }
    path = _write_manifest(manifest)
    try:
        info = check_for_updates(
            current_version="0.1.0",
            manifest_url=path.resolve().as_uri(),
            target_os="windows",
            target_arch="x86_64",
        )
    finally:
        _cleanup_manifest(path)

    assert info.available is True
    assert info.notes_url == "https://example.com/release"


def test_default_manifest_url_uses_environment_override(monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_MANIFEST_URL", "https://example.com/manifest.json")
    assert default_manifest_url() == "https://example.com/manifest.json"


def test_default_manifest_url_falls_back_to_release_asset(monkeypatch) -> None:
    monkeypatch.delenv("ALBION_COMMAND_DESK_MANIFEST_URL", raising=False)
    assert default_manifest_url() == DEFAULT_MANIFEST_URL
