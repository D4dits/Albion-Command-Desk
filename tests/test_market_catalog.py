from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from albion_dps.market.catalog import RecipeCatalog, _resolve_item_value


def test_recipe_catalog_default_dataset_loads() -> None:
    catalog = RecipeCatalog.from_default()
    assert len(catalog) >= 1
    assert catalog.get("T4_MAIN_SWORD") is not None
    issues = catalog.validate_integrity()
    assert issues == []


def test_recipe_catalog_integrity_detects_tier_mismatch() -> None:
    tmp_dir = Path(f"tmp_market_catalog_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        path = tmp_dir / "bad_recipes.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "item": {
                            "unique_name": "T4_MAIN_SWORD",
                            "display_name": "Broadsword",
                            "tier": 5,
                            "enchantment": 0,
                        },
                        "station": "Warrior Forge",
                        "components": [
                            {
                                "item": {
                                    "unique_name": "T4_METALBAR",
                                    "display_name": "Metal Bar",
                                    "tier": 4,
                                },
                                "quantity": 16.0,
                            }
                        ],
                        "outputs": [
                            {
                                "item": {
                                    "unique_name": "T4_MAIN_SWORD",
                                    "display_name": "Broadsword",
                                    "tier": 5,
                                },
                                "quantity": 1.0,
                            }
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        catalog = RecipeCatalog.from_json(path)
        issues = catalog.validate_integrity()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert any("tier mismatch" in issue.message for issue in issues)


def test_resolve_item_value_handles_enchant_and_level_suffix() -> None:
    item_values = {
        "T5_MAIN_SPEAR": 1234,
        "T6_MAIN_CROSSBOW": 4321,
    }
    assert (
        _resolve_item_value(
            unique_name="T5_MAIN_SPEAR@2",
            explicit_value=None,
            item_values=item_values,
        )
        == 1234
    )
    assert (
        _resolve_item_value(
            unique_name="T6_MAIN_CROSSBOW_LEVEL3",
            explicit_value=None,
            item_values=item_values,
        )
        == 4321
    )
