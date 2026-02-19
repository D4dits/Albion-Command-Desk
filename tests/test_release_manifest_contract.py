from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path
import re


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_manifest_strategy(manifest: dict) -> tuple[list[str], list[str]]:
    builder_path = Path(__file__).resolve().parents[1] / "tools" / "release" / "manifest" / "build_manifest.py"
    spec = importlib.util.spec_from_file_location("acd_manifest_builder", builder_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load build_manifest.py for validation tests")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.validate_manifest_strategy(manifest)


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
    assert assets, "manifest example must include at least one asset"

    for asset in assets:
        assert str(asset.get("url", "")).startswith("https://")
        assert _SHA256_RE.fullmatch(str(asset.get("sha256", "")))
        assert int(asset.get("size", 0)) > 0


def test_manifest_example_passes_strategy_validation() -> None:
    path = Path("tools/release/manifest/manifest.example.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    blockers, warnings = _validate_manifest_strategy(manifest)
    assert blockers == []
    assert warnings == []


def test_manifest_example_orders_preferred_asset_first_per_os() -> None:
    path = Path("tools/release/manifest/manifest.example.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assets = manifest.get("assets", [])

    def first_kind(os_name: str) -> str:
        for asset in assets:
            if asset.get("os") == os_name:
                return str(asset.get("kind", ""))
        return ""

    assert first_kind("windows") == "installer"
    assert first_kind("linux") == "archive"
    assert first_kind("macos") == "archive"
