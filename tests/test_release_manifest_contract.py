from __future__ import annotations

import json
from pathlib import Path


def test_manifest_example_has_required_contract_fields() -> None:
    path = Path("tools/release/manifest/manifest.example.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))

    assert manifest.get("schema_version") == 1
    assert str(manifest.get("app_id", "")).strip() == "albion-command-desk"
    assert str(manifest.get("channel", "")).strip()

    latest = manifest.get("latest")
    assert isinstance(latest, dict)
    assert str(latest.get("version", "")).strip()
    assert str(latest.get("release_url", "")).strip()
    assert str(latest.get("changelog_url", "")).strip()

    assets = manifest.get("assets")
    assert isinstance(assets, list)
