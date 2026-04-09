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


def test_recipe_catalog_inherits_component_enchant_when_enchanted_variant_exists() -> None:
    tmp_dir = Path(f"tmp_market_catalog_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        path = tmp_dir / "recipes.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "item": {
                            "unique_name": "T4_ARMOR_PLATE_SET1@3",
                            "display_name": "Adept's Soldier Armor 4.3",
                            "tier": 4,
                            "enchantment": 3,
                        },
                        "station": "Warrior Forge",
                        "components": [
                            {
                                "item": {
                                    "unique_name": "T4_METALBAR_LEVEL3",
                                    "display_name": "Metal Bar 4.3",
                                    "tier": 4,
                                    "enchantment": 3,
                                },
                                "quantity": 16.0,
                            }
                        ],
                        "outputs": [
                            {
                                "item": {
                                    "unique_name": "T4_ARMOR_PLATE_SET1@3",
                                    "display_name": "Adept's Soldier Armor 4.3",
                                    "tier": 4,
                                    "enchantment": 3,
                                },
                                "quantity": 1.0,
                            }
                        ],
                    },
                    {
                        "item": {
                            "unique_name": "T4_ARMOR_PLATE_ROYAL@3",
                            "display_name": "Adept's Royal Armor 4.3",
                            "tier": 4,
                            "enchantment": 3,
                        },
                        "station": "Warrior Forge",
                        "components": [
                            {
                                "item": {
                                    "unique_name": "T4_ARMOR_PLATE_SET1",
                                    "display_name": "Adept's Soldier Armor T4",
                                    "tier": 4,
                                    "enchantment": 0,
                                },
                                "quantity": 1.0,
                            }
                        ],
                        "outputs": [
                            {
                                "item": {
                                    "unique_name": "T4_ARMOR_PLATE_ROYAL@3",
                                    "display_name": "Adept's Royal Armor 4.3",
                                    "tier": 4,
                                    "enchantment": 3,
                                },
                                "quantity": 1.0,
                            }
                        ],
                    },
                ]
            ),
            encoding="utf-8",
        )
        catalog = RecipeCatalog.from_json(path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    royal_recipe = catalog.get("T4_ARMOR_PLATE_ROYAL@3")
    assert royal_recipe is not None
    assert royal_recipe.components
    assert royal_recipe.components[0].item.unique_name == "T4_ARMOR_PLATE_SET1@3"
    assert int(royal_recipe.components[0].item.enchantment or 0) == 3


def test_recipe_catalog_marks_quest_tokens_non_returnable() -> None:
    tmp_dir = Path(f"tmp_market_catalog_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        path = tmp_dir / "recipes.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "item": {
                            "unique_name": "T4_ARMOR_PLATE_ROYAL",
                            "display_name": "Adept's Royal Armor",
                            "tier": 4,
                            "enchantment": 0,
                        },
                        "station": "Warrior Forge",
                        "components": [
                            {
                                "item": {
                                    "unique_name": "QUESTITEM_TOKEN_ROYAL_T4",
                                    "display_name": "Royal Sigil",
                                    "tier": 4,
                                    "enchantment": 0,
                                },
                                "quantity": 4.0,
                            }
                        ],
                        "outputs": [
                            {
                                "item": {
                                    "unique_name": "T4_ARMOR_PLATE_ROYAL",
                                    "display_name": "Adept's Royal Armor",
                                    "tier": 4,
                                    "enchantment": 0,
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
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    royal_recipe = catalog.get("T4_ARMOR_PLATE_ROYAL")
    assert royal_recipe is not None
    assert royal_recipe.components
    assert royal_recipe.components[0].returnable is False


def test_recipe_catalog_builds_crystallized_variant_for_artifact_recipe() -> None:
    tmp_dir = Path(f"tmp_market_catalog_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        path = tmp_dir / "recipes.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "item": {
                            "unique_name": "T4_ARTEFACT_2H_BOW_KEEPER",
                            "display_name": "Adept's Keeper Bow Artifact",
                            "tier": 4,
                            "enchantment": 0,
                        },
                        "station": "Artifact Foundry",
                        "components": [
                            {
                                "item": {
                                    "unique_name": "T4_RELIC",
                                    "display_name": "Relic",
                                    "tier": 4,
                                    "enchantment": 0,
                                },
                                "quantity": 50.0,
                            }
                        ],
                        "outputs": [
                            {
                                "item": {
                                    "unique_name": "T4_ARTEFACT_2H_BOW_KEEPER",
                                    "display_name": "Adept's Keeper Bow Artifact",
                                    "tier": 4,
                                    "enchantment": 0,
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
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    variant = catalog.get("T4_ARTEFACT_2H_BOW_KEEPER#CRYSTALLIZED")
    assert variant is not None
    assert variant.variant_label == "Crystallized"
    assert variant.uses_crystallized is True
    assert len(variant.components) == 1
    assert variant.components[0].quantity == 1.0
    assert variant.components[0].returnable is False
    assert variant.components[0].item.unique_name == "T4_ARTEFACT_TOKEN_FAVOR_3"
    assert variant.components[0].item.display_name == "Crystallized Magic"


def test_recipe_catalog_builds_crystallized_variant_for_final_item_recipe() -> None:
    tmp_dir = Path(f"tmp_market_catalog_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        path = tmp_dir / "recipes.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "item": {
                            "unique_name": "T4_ARTEFACT_2H_BOW_KEEPER",
                            "display_name": "Adept's Keeper Bow Artifact",
                            "tier": 4,
                            "enchantment": 0,
                        },
                        "station": "Artifact Foundry",
                        "components": [
                            {
                                "item": {
                                    "unique_name": "T4_RELIC",
                                    "display_name": "Relic",
                                    "tier": 4,
                                    "enchantment": 0,
                                },
                                "quantity": 50.0,
                            }
                        ],
                        "outputs": [
                            {
                                "item": {
                                    "unique_name": "T4_ARTEFACT_2H_BOW_KEEPER",
                                    "display_name": "Adept's Keeper Bow Artifact",
                                    "tier": 4,
                                    "enchantment": 0,
                                },
                                "quantity": 1.0,
                            }
                        ],
                    },
                    {
                        "item": {
                            "unique_name": "T4_2H_BOW_KEEPER",
                            "display_name": "Adept's Wailing Bow",
                            "tier": 4,
                            "enchantment": 0,
                        },
                        "station": "Hunter's Lodge",
                        "components": [
                            {
                                "item": {
                                    "unique_name": "T4_PLANKS",
                                    "display_name": "Planks",
                                    "tier": 4,
                                    "enchantment": 0,
                                },
                                "quantity": 16.0,
                            },
                            {
                                "item": {
                                    "unique_name": "T4_ARTEFACT_2H_BOW_KEEPER",
                                    "display_name": "Adept's Keeper Bow Artifact",
                                    "tier": 4,
                                    "enchantment": 0,
                                },
                                "quantity": 1.0,
                            }
                        ],
                        "outputs": [
                            {
                                "item": {
                                    "unique_name": "T4_2H_BOW_KEEPER",
                                    "display_name": "Adept's Wailing Bow",
                                    "tier": 4,
                                    "enchantment": 0,
                                },
                                "quantity": 1.0,
                            }
                        ],
                    },
                ]
            ),
            encoding="utf-8",
        )
        catalog = RecipeCatalog.from_json(path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    variant = catalog.get("T4_2H_BOW_KEEPER#CRYSTALLIZED")
    assert variant is not None
    assert variant.variant_label == "Crystallized"
    assert variant.uses_crystallized is True
    assert [component.item.unique_name for component in variant.components] == [
        "T4_PLANKS",
        "T4_ARTEFACT_TOKEN_FAVOR_3",
    ]
    assert variant.components[0].returnable is True
    assert variant.components[1].quantity == 1.0
    assert variant.components[1].returnable is False


def test_recipe_catalog_default_dataset_contains_crystallized_variants() -> None:
    catalog = RecipeCatalog.from_default()
    crystallized_ids = [recipe_id for recipe_id in catalog.items() if recipe_id.endswith("#CRYSTALLIZED")]
    assert crystallized_ids
