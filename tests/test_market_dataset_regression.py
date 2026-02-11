from __future__ import annotations

from albion_dps.market.catalog import RecipeCatalog


def test_market_recipe_dataset_keeps_expected_baseline_shape() -> None:
    catalog = RecipeCatalog.from_default()
    issues = catalog.validate_integrity()

    # Guardrails for accidental dataset shrink/corruption.
    assert len(catalog) >= 9000
    assert issues == []

    recipe_ids = set(catalog.items())
    assert "T4_MAIN_SWORD" in recipe_ids
    assert "T4_MAIN_SWORD@1" in recipe_ids
    assert "T7_MAIN_SPEAR_KEEPER" in recipe_ids
    assert "T7_MAIN_SPEAR_KEEPER@1" in recipe_ids

    enchant_count = sum(1 for recipe_id in recipe_ids if "@" in recipe_id)
    assert enchant_count >= 5000


def test_market_recipe_dataset_marks_artifact_components_non_returnable() -> None:
    catalog = RecipeCatalog.from_default()
    recipe = catalog.get("T7_MAIN_SPEAR_KEEPER")
    assert recipe is not None

    artifact_components = [x for x in recipe.components if "_ARTEFACT" in x.item.unique_name]
    assert artifact_components
    assert all(x.returnable is False for x in artifact_components)
