from __future__ import annotations

from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.models import Recipe
from albion_dps.qt.market.list_models import CraftPlanRow, RecipeOptionRow


def build_recipe_options(
    catalog: RecipeCatalog,
    *,
    is_recipe_plan_candidate,
    recipe_identity,
    recipe_display_label,
) -> list[RecipeOptionRow]:
    rows: list[RecipeOptionRow] = []
    for recipe_id in catalog.items():
        recipe = catalog.get(recipe_id)
        if recipe is None:
            continue
        if not is_recipe_plan_candidate(recipe):
            continue
        rows.append(
            RecipeOptionRow(
                recipe_id=recipe_identity(recipe),
                display_name=recipe_display_label(recipe),
                tier=int(recipe.item.tier or 0),
                enchant=int(recipe.item.enchantment or 0),
                variant_label=str(recipe.variant_label or ""),
                uses_crystallized=bool(recipe.uses_crystallized),
            )
        )
    rows.sort(key=lambda row: row.display_name.lower())
    return rows


def family_recipe_ids(
    catalog: RecipeCatalog,
    recipe_id: str,
    *,
    recipe_tier_filters: set[int],
    recipe_enchant_filters: set[int],
    is_recipe_plan_candidate,
    item_family_key,
    recipe_display_label,
    recipe_identity,
) -> list[str]:
    base_recipe = catalog.get(recipe_id)
    if base_recipe is None:
        return []
    if not is_recipe_plan_candidate(base_recipe):
        return []
    family_key = item_family_key(base_recipe.item.unique_name)
    if not family_key:
        return [recipe_identity(base_recipe)]

    rows: list[tuple[int, int, str, str]] = []
    for candidate_id in catalog.items():
        recipe = catalog.get(candidate_id)
        if recipe is None:
            continue
        if not is_recipe_plan_candidate(recipe):
            continue
        if item_family_key(recipe.item.unique_name) != family_key:
            continue
        tier = int(recipe.item.tier or 0)
        enchant = int(recipe.item.enchantment or 0)
        if recipe_tier_filters and tier not in recipe_tier_filters:
            continue
        if recipe_enchant_filters and enchant not in recipe_enchant_filters:
            continue
        rows.append(
            (
                tier,
                enchant,
                recipe_display_label(recipe).lower(),
                recipe_identity(recipe),
            )
        )
    rows.sort()
    return [row[3] for row in rows]


def family_recipe_ids_for_filtered(
    catalog: RecipeCatalog,
    recipe_ids: list[str],
    *,
    family_recipe_ids_for_recipe,
    item_family_key,
    recipe_identity,
) -> list[str]:
    if not recipe_ids:
        return []
    collected: list[str] = []
    seen_family_keys: set[str] = set()
    seen_recipe_ids: set[str] = set()
    for recipe_id in recipe_ids:
        recipe = catalog.get(recipe_id)
        if recipe is None:
            continue
        family_key = item_family_key(recipe.item.unique_name)
        dedupe_key = family_key or recipe.item.unique_name
        if dedupe_key in seen_family_keys:
            continue
        seen_family_keys.add(dedupe_key)
        for family_recipe_id in family_recipe_ids_for_recipe(recipe_identity(recipe)):
            if family_recipe_id in seen_recipe_ids:
                continue
            seen_recipe_ids.add(family_recipe_id)
            collected.append(family_recipe_id)
    return collected


def station_recipe_ids(
    catalog: RecipeCatalog,
    recipe_id: str,
    *,
    recipe_tier_filters: set[int],
    recipe_enchant_filters: set[int],
    is_recipe_plan_candidate,
    recipe_display_label,
    recipe_identity,
) -> list[str]:
    base_recipe = catalog.get(recipe_id)
    if base_recipe is None:
        return []
    if not is_recipe_plan_candidate(base_recipe):
        return []
    station_key = str(base_recipe.station or "").strip().lower()
    if not station_key:
        return []

    rows: list[tuple[int, int, str, str]] = []
    for candidate_id in catalog.items():
        recipe = catalog.get(candidate_id)
        if recipe is None:
            continue
        if not is_recipe_plan_candidate(recipe):
            continue
        if str(recipe.station or "").strip().lower() != station_key:
            continue
        tier = int(recipe.item.tier or 0)
        enchant = int(recipe.item.enchantment or 0)
        if recipe_tier_filters and tier not in recipe_tier_filters:
            continue
        if recipe_enchant_filters and enchant not in recipe_enchant_filters:
            continue
        rows.append(
            (
                tier,
                enchant,
                recipe_display_label(recipe).lower(),
                recipe_identity(recipe),
            )
        )
    rows.sort()
    return [row[3] for row in rows]


def station_recipe_ids_for_filtered(
    catalog: RecipeCatalog,
    recipe_ids: list[str],
    *,
    station_recipe_ids_for_recipe,
    recipe_identity,
) -> list[str]:
    if not recipe_ids:
        return []
    collected: list[str] = []
    seen_station_keys: set[str] = set()
    seen_recipe_ids: set[str] = set()
    for recipe_id in recipe_ids:
        recipe = catalog.get(recipe_id)
        if recipe is None:
            continue
        station_key = str(recipe.station or "").strip().lower()
        if not station_key or station_key in seen_station_keys:
            continue
        seen_station_keys.add(station_key)
        for station_recipe_id in station_recipe_ids_for_recipe(recipe_identity(recipe)):
            if station_recipe_id in seen_recipe_ids:
                continue
            seen_recipe_ids.add(station_recipe_id)
            collected.append(station_recipe_id)
    return collected


def sorted_craft_plan_rows(
    rows: list[CraftPlanRow],
    *,
    sort_key: str,
    reverse: bool,
) -> list[CraftPlanRow]:
    source = list(rows)

    def pl_value(row: CraftPlanRow) -> float:
        if row.profit_percent is None:
            return float("-inf")
        return float(row.profit_percent)

    if sort_key == "added":
        source.sort(key=lambda row: int(row.row_id), reverse=reverse)
    elif sort_key == "tier":
        source.sort(
            key=lambda row: (int(row.tier), int(row.enchant), row.display_name.lower(), int(row.row_id)),
            reverse=reverse,
        )
    elif sort_key == "city":
        source.sort(key=lambda row: (row.craft_city.lower(), row.display_name.lower(), int(row.row_id)), reverse=reverse)
    elif sort_key == "pl":
        source.sort(key=lambda row: (pl_value(row), row.display_name.lower(), int(row.row_id)), reverse=reverse)
    else:
        source.sort(
            key=lambda row: (row.display_name.lower(), int(row.tier), int(row.enchant), int(row.row_id)),
            reverse=reverse,
        )
    return source
