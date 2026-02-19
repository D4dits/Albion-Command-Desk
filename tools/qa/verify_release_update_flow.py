from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from albion_dps.qt.models import UiState
from albion_dps.update.checker import check_for_updates


def _write_temp_manifest() -> Path:
    template_path = Path("tools/release/manifest/manifest.example.json")
    manifest = json.loads(template_path.read_text(encoding="utf-8"))
    manifest["latest"]["version"] = "9.9.9"
    manifest["latest"]["release_url"] = "https://example.com/acd/release"
    manifest["latest"]["changelog_url"] = "https://example.com/acd/changelog"
    manifest["assets"] = [
        {
            "os": "windows",
            "arch": "x86_64",
            "kind": "installer",
            "name": "AlbionCommandDesk-Setup-v9.9.9-x86_64.exe",
            "url": "https://example.com/acd/download/windows-setup.exe",
            "sha256": "f3fe4ad3c1f596b0df6ec75f7f5d9ce25f11a1f7ebc8de4a7fca0178c8cdb4ac",
            "size": 123,
        }
    ]
    base = Path("artifacts") / "tmp" / "qa_release_update" / str(uuid.uuid4())
    base.mkdir(parents=True, exist_ok=True)
    target = base / "manifest.json"
    target.write_text(json.dumps(manifest), encoding="utf-8")
    return target


def main() -> int:
    manifest_path = _write_temp_manifest()
    try:
        info = check_for_updates(
            current_version="0.1.0",
            manifest_url=manifest_path.resolve().as_uri(),
            target_os="windows",
            target_arch="x86_64",
        )
        if not info.available:
            print("[qa] FAIL: update checker did not report available update")
            return 1

        state = UiState(sort_key="dps", top_n=10, history_limit=50)
        state.setUpdateStatus(
            True,
            info.current_version,
            info.latest_version,
            info.download_url or info.release_url,
            info.notes_url or info.release_url,
        )
        if not state.updateBannerVisible:
            print("[qa] FAIL: update banner is not visible after setUpdateStatus")
            return 1
        if info.latest_version not in state.updateBannerText:
            print("[qa] FAIL: banner text does not include latest version")
            return 1
        if state.updateBannerUrl != "https://example.com/acd/download/windows-setup.exe":
            print("[qa] FAIL: banner URL mismatch (installer URL expected)")
            return 1
        if state.updateBannerNotesUrl != "https://example.com/acd/changelog":
            print("[qa] FAIL: banner notes URL mismatch")
            return 1
        state.dismissUpdateBanner()
        if state.updateBannerVisible:
            print("[qa] FAIL: dismissUpdateBanner did not hide banner")
            return 1
        state.setUpdateStatus(
            True,
            info.current_version,
            info.latest_version,
            info.download_url or info.release_url,
            info.notes_url or info.release_url,
        )
        if state.updateBannerVisible:
            print("[qa] FAIL: dismissed version was shown again")
            return 1

        print("[qa] PASS: release manifest + update banner flow validated")
        return 0
    finally:
        shutil.rmtree(manifest_path.parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
