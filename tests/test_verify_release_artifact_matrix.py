from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

from tools.qa import verify_release_artifact_matrix as matrix


def _write_manifest(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "app_id": "albion-command-desk",
        "channel": "stable",
        "latest": {
            "version": "9.9.9",
            "release_url": "https://example.invalid/release",
            "changelog_url": "https://example.invalid/changelog",
        },
        "assets": [
            {
                "os": "windows",
                "arch": "x86_64",
                "kind": "installer",
                "name": "AlbionCommandDesk-Setup-v9.9.9-x86_64.exe",
                "url": "https://example.invalid/windows.exe",
                "sha256": "0" * 64,
                "size": 1,
            },
            {
                "os": "linux",
                "arch": "x86_64",
                "kind": "archive",
                "name": "AlbionCommandDesk-v9.9.9-x86_64.AppImage",
                "url": "https://example.invalid/linux.appimage",
                "sha256": "1" * 64,
                "size": 1,
            },
            {
                "os": "macos",
                "arch": "universal",
                "kind": "archive",
                "name": "AlbionCommandDesk-v9.9.9-universal.dmg",
                "url": "https://example.invalid/macos.dmg",
                "sha256": "2" * 64,
                "size": 1,
            },
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_main_passes_with_skip_url_probe(monkeypatch) -> None:
    base = Path("artifacts") / "tmp" / "verify_release_artifact_matrix_pass"
    shutil.rmtree(base, ignore_errors=True)
    try:
        manifest_path = _write_manifest(base)
        monkeypatch.setattr(
            matrix,
            "_parse_args",
            lambda: SimpleNamespace(
                manifest_url=manifest_path.resolve().as_uri(),
                target_os="windows",
                timeout_seconds=1.0,
                advisory=False,
                skip_url_probe=True,
            ),
        )

        assert matrix.main() == 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_main_fails_when_wrong_kind_present(monkeypatch) -> None:
    base = Path("artifacts") / "tmp" / "verify_release_artifact_matrix_fail"
    shutil.rmtree(base, ignore_errors=True)
    try:
        manifest_path = _write_manifest(base)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["assets"][0]["kind"] = "archive"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        monkeypatch.setattr(
            matrix,
            "_parse_args",
            lambda: SimpleNamespace(
                manifest_url=manifest_path.resolve().as_uri(),
                target_os="windows",
                timeout_seconds=1.0,
                advisory=False,
                skip_url_probe=True,
            ),
        )

        assert matrix.main() == 1
    finally:
        shutil.rmtree(base, ignore_errors=True)
