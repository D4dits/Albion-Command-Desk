from __future__ import annotations

import logging

from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.models import ItemRef, Recipe, RecipeComponent, RecipeOutput


def load_catalog(logger: logging.Logger) -> RecipeCatalog:
    try:
        catalog = RecipeCatalog.from_default()
    except Exception as exc:
        logger.warning("Market recipe catalog load failed: %s", exc)
        return RecipeCatalog(recipes={})
    issues = catalog.validate_integrity()
    if issues:
        logger.warning("Market recipe catalog integrity issues: %d", len(issues))
        for issue in issues[:5]:
            logger.warning("Recipe issue [%s]: %s", issue.recipe_id, issue.message)
    return catalog


def resolve_recipe(catalog: RecipeCatalog, recipe_id: str) -> Recipe | None:
    recipe = catalog.get(recipe_id)
    if recipe is not None:
        return recipe
    return catalog.first()


def build_builtin_recipe() -> Recipe:
    sword = ItemRef(unique_name="T4_MAIN_SWORD", display_name="Broadsword", tier=4, enchantment=0)
    bars = ItemRef(unique_name="T4_METALBAR", display_name="Metal Bar", tier=4, enchantment=0)
    planks = ItemRef(unique_name="T4_PLANKS", display_name="Planks", tier=4, enchantment=0)
    return Recipe(
        item=sword,
        station="Warrior Forge",
        city_bonus="Bridgewatch",
        components=(
            RecipeComponent(item=bars, quantity=16.0),
            RecipeComponent(item=planks, quantity=8.0),
        ),
        outputs=(RecipeOutput(item=sword, quantity=1.0),),
        focus_per_craft=200,
    )
