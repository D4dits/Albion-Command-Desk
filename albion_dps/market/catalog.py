from __future__ import annotations

import json
import re
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path

from albion_dps.market.models import ItemRef, Recipe, RecipeComponent, RecipeOutput


DEFAULT_RECIPES_PATH = Path(__file__).resolve().parent / "data" / "recipes.json"
DEFAULT_ITEMS_PATH = Path(__file__).resolve().parents[2] / "data" / "items.json"
_TIER_PATTERN = re.compile(r"^T(?P<tier>\d+)")
_LEVEL_SUFFIX_RE = re.compile(r"_LEVEL\d+$")
_CRYSTALLIZED_RECIPE_SUFFIX = "#CRYSTALLIZED"
_CRYSTALLIZED_COMPONENT_MAP: dict[str, tuple[str, str]] = {
    "RUNE": ("ARTEFACT_TOKEN_FAVOR_1", "Crystallized Spirit"),
    "SOUL": ("ARTEFACT_TOKEN_FAVOR_2", "Crystallized Dread"),
    "RELIC": ("ARTEFACT_TOKEN_FAVOR_3", "Crystallized Magic"),
    "SHARD_AVALONIAN": ("ARTEFACT_TOKEN_FAVOR_4", "Crystallized Divinity"),
}


def _to_item_ref(
    payload: dict[str, object],
    fallback_name: str = "",
    item_values: dict[str, int] | None = None,
) -> ItemRef:
    unique_name = str(payload.get("unique_name") or fallback_name).strip()
    explicit_item_value = _to_int_or_none(payload.get("item_value"))
    derived_item_value = _resolve_item_value(
        unique_name=unique_name,
        explicit_value=explicit_item_value,
        item_values=item_values or {},
    )
    return ItemRef(
        unique_name=unique_name,
        display_name=str(payload.get("display_name") or ""),
        tier=_to_int_or_none(payload.get("tier")),
        enchantment=_to_int_or_none(payload.get("enchantment")),
        item_value=derived_item_value,
    )


def _to_int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value).strip().replace(",", ".")))
        except (TypeError, ValueError):
            return None


def _resolve_item_value(
    *,
    unique_name: str,
    explicit_value: int | None,
    item_values: dict[str, int],
) -> int | None:
    if explicit_value is not None:
        return int(explicit_value)
    direct = item_values.get(unique_name)
    if direct is not None:
        return int(direct)
    if "@" in unique_name:
        base = unique_name.split("@", 1)[0]
        direct = item_values.get(base)
        if direct is not None:
            return int(direct)
    no_level = _LEVEL_SUFFIX_RE.sub("", unique_name)
    if no_level != unique_name:
        direct = item_values.get(no_level)
        if direct is not None:
            return int(direct)
    return None


@dataclass(frozen=True)
class CatalogIssue:
    recipe_id: str
    message: str


class RecipeCatalog:
    def __init__(self, recipes: dict[str, Recipe] | None = None) -> None:
        self._recipes: dict[str, Recipe] = recipes or {}

    @classmethod
    def from_json(cls, path: Path) -> "RecipeCatalog":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError(f"Recipe file must contain a JSON array: {path}")
        craftable_item_ids = _collect_craftable_item_ids(raw)
        item_values = _load_item_values(DEFAULT_ITEMS_PATH)
        recipes: dict[str, Recipe] = {}
        for row in raw:
            if not isinstance(row, dict):
                continue
            item_payload = row.get("item")
            if not isinstance(item_payload, dict):
                continue
            item = _to_item_ref(item_payload, item_values=item_values)
            if not item.unique_name:
                continue
            station = str(row.get("station") or "")
            city_bonus = str(row.get("city_bonus") or "")
            focus_per_craft = _to_int_or_none(row.get("focus_per_craft")) or 0
            components = _parse_components(
                row.get("components"),
                item_values=item_values,
                recipe_enchantment=int(item.enchantment or 0),
                craftable_item_ids=craftable_item_ids,
            )
            outputs = _parse_outputs(row.get("outputs"), item, item_values=item_values)
            recipe_id = str(row.get("recipe_id") or item.unique_name).strip() or item.unique_name
            variant_label = str(row.get("variant_label") or "").strip()
            uses_crystallized = bool(row.get("uses_crystallized"))
            recipes[recipe_id] = Recipe(
                item=item,
                station=station,
                city_bonus=city_bonus,
                components=components,
                outputs=outputs,
                focus_per_craft=focus_per_craft,
                recipe_id=recipe_id,
                variant_label=variant_label,
                uses_crystallized=uses_crystallized,
            )
        recipes.update(_build_crystallized_variants(recipes, item_values=item_values))
        return cls(recipes=recipes)

    @classmethod
    def from_default(cls) -> "RecipeCatalog":
        return cls.from_json(DEFAULT_RECIPES_PATH)

    def get(self, unique_name: str) -> Recipe | None:
        return self._recipes.get(unique_name)

    def has(self, unique_name: str) -> bool:
        return unique_name in self._recipes

    def items(self) -> list[str]:
        return sorted(self._recipes.keys())

    def first(self) -> Recipe | None:
        if not self._recipes:
            return None
        first_key = min(self._recipes.keys())
        return self._recipes.get(first_key)

    def validate_integrity(self) -> list[CatalogIssue]:
        issues: list[CatalogIssue] = []
        if not self._recipes:
            issues.append(CatalogIssue(recipe_id="-", message="catalog is empty"))
            return issues

        for recipe_id, recipe in self._recipes.items():
            if not recipe.station.strip():
                issues.append(CatalogIssue(recipe_id, "station is empty"))
            if recipe.focus_per_craft < 0:
                issues.append(CatalogIssue(recipe_id, "focus_per_craft must be >= 0"))
            if not recipe.components:
                issues.append(CatalogIssue(recipe_id, "components are empty"))
            if not recipe.outputs:
                issues.append(CatalogIssue(recipe_id, "outputs are empty"))

            _check_item_meta(recipe.item, recipe_id, issues)

            component_ids: set[str] = set()
            for comp in recipe.components:
                if comp.quantity <= 0:
                    issues.append(
                        CatalogIssue(
                            recipe_id,
                            f"component {comp.item.unique_name} quantity must be > 0",
                        )
                    )
                if comp.item.unique_name in component_ids:
                    issues.append(
                        CatalogIssue(
                            recipe_id,
                            f"duplicate component {comp.item.unique_name}",
                        )
                    )
                component_ids.add(comp.item.unique_name)
                _check_item_meta(comp.item, recipe_id, issues)

            for output in recipe.outputs:
                if output.quantity <= 0:
                    issues.append(
                        CatalogIssue(
                            recipe_id,
                            f"output {output.item.unique_name} quantity must be > 0",
                        )
                    )
                _check_item_meta(output.item, recipe_id, issues)

        return issues

    def __len__(self) -> int:
        return len(self._recipes)


def _check_item_meta(item: ItemRef, recipe_id: str, issues: list[CatalogIssue]) -> None:
    unique_name = item.unique_name.strip()
    if not unique_name:
        issues.append(CatalogIssue(recipe_id, "item unique_name is empty"))
        return

    tier_from_name = _parse_tier_from_unique_name(unique_name)
    if item.tier is not None:
        if item.tier <= 0:
            issues.append(CatalogIssue(recipe_id, f"{unique_name} has invalid tier {item.tier}"))
        if tier_from_name is not None and item.tier != tier_from_name:
            issues.append(
                CatalogIssue(
                    recipe_id,
                    f"{unique_name} tier mismatch (meta={item.tier}, name={tier_from_name})",
                )
            )
    if item.enchantment is not None and (item.enchantment < 0 or item.enchantment > 4):
        issues.append(
            CatalogIssue(
                recipe_id,
                f"{unique_name} has invalid enchantment {item.enchantment}",
            )
        )
    if item.item_value is not None and item.item_value < 0:
        issues.append(
            CatalogIssue(
                recipe_id,
                f"{unique_name} has invalid item_value {item.item_value}",
            )
        )


def _parse_tier_from_unique_name(unique_name: str) -> int | None:
    match = _TIER_PATTERN.match(unique_name)
    if not match:
        return None
    try:
        return int(match.group("tier"))
    except (TypeError, ValueError):
        return None


def _parse_components(
    payload: object,
    *,
    item_values: dict[str, int] | None = None,
    recipe_enchantment: int = 0,
    craftable_item_ids: set[str] | None = None,
) -> tuple[RecipeComponent, ...]:
    if not isinstance(payload, list):
        return ()
    craftable_ids = craftable_item_ids or set()
    out: list[RecipeComponent] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        item_data = row.get("item")
        if not isinstance(item_data, dict):
            continue
        item = _to_item_ref(item_data, item_values=item_values)
        if not item.unique_name:
            continue
        item = _inherit_component_enchantment(
            item=item,
            recipe_enchantment=recipe_enchantment,
            craftable_item_ids=craftable_ids,
        )
        quantity = float(row.get("quantity") or 0.0)
        if quantity <= 0:
            continue
        returnable_raw = row.get("returnable")
        if isinstance(returnable_raw, bool):
            returnable = returnable_raw
        elif returnable_raw is None:
            returnable = _infer_component_returnable(item.unique_name)
        else:
            returnable = str(returnable_raw).strip().lower() not in {"0", "false", "no"}
        out.append(RecipeComponent(item=item, quantity=quantity, returnable=returnable))
    return tuple(out)


def _infer_component_returnable(unique_name: str) -> bool:
    name = unique_name.strip().upper()
    non_returnable_markers = (
        "_ARTEFACT",
        "_RELIC",
        "_SOUL",
        "_RUNE",
        "_AVALON",
        "_MORGANA",
        "_KEEPER",
        "_UNDEAD",
        "_DEMON",
        "_TOKEN",
        "QUESTITEM_",
        "_SIGIL",
    )
    return not any(marker in name for marker in non_returnable_markers)


def _build_crystallized_variants(
    recipes: dict[str, Recipe],
    *,
    item_values: dict[str, int],
) -> dict[str, Recipe]:
    variants: dict[str, Recipe] = {}
    for recipe in list(recipes.values()):
        variant = _build_crystallized_artifact_variant(recipe, item_values=item_values)
        if variant is None:
            continue
        if variant.recipe_id in recipes or variant.recipe_id in variants:
            continue
        variants[variant.recipe_id] = variant
    materialized = dict(recipes)
    materialized.update(variants)
    for recipe in list(materialized.values()):
        variant = _build_crystallized_item_variant(recipe, recipes=materialized)
        if variant is None:
            continue
        if variant.recipe_id in recipes or variant.recipe_id in variants:
            continue
        variants[variant.recipe_id] = variant
    return variants


def _build_crystallized_artifact_variant(
    recipe: Recipe,
    *,
    item_values: dict[str, int],
) -> Recipe | None:
    output_item = recipe.outputs[0].item if recipe.outputs else recipe.item
    output_id = str(output_item.unique_name or "").strip().upper()
    if "_ARTEFACT_" not in output_id:
        return None
    if recipe.uses_crystallized:
        return None
    if len(recipe.components) != 1:
        return None
    component = recipe.components[0]
    base_component_id = str(component.item.unique_name or "").strip().upper()
    tier = int(output_item.tier or component.item.tier or _parse_tier_from_unique_name(output_id) or 0)
    if tier <= 0:
        return None
    component_kind = _base_component_kind(base_component_id, tier=tier)
    crystal_suffix, display_name = _CRYSTALLIZED_COMPONENT_MAP.get(component_kind, ("", ""))
    if not crystal_suffix:
        return None
    crystal_item_id = f"T{tier}_{crystal_suffix}"
    crystal_item = ItemRef(
        unique_name=crystal_item_id,
        display_name=display_name,
        tier=tier,
        enchantment=0,
        item_value=_resolve_item_value(
            unique_name=crystal_item_id,
            explicit_value=None,
            item_values=item_values,
        ),
    )
    return Recipe(
        item=recipe.item,
        station=recipe.station,
        city_bonus=recipe.city_bonus,
        components=(RecipeComponent(item=crystal_item, quantity=1.0, returnable=False),),
        outputs=recipe.outputs,
        focus_per_craft=recipe.focus_per_craft,
        recipe_id=f"{output_item.unique_name}{_CRYSTALLIZED_RECIPE_SUFFIX}",
        variant_label="Crystallized",
        uses_crystallized=True,
    )


def _build_crystallized_item_variant(
    recipe: Recipe,
    *,
    recipes: dict[str, Recipe],
) -> Recipe | None:
    output_item = recipe.outputs[0].item if recipe.outputs else recipe.item
    output_id = str(output_item.unique_name or "").strip().upper()
    if not output_id or "_ARTEFACT_" in output_id:
        return None
    if recipe.uses_crystallized:
        return None

    replaced_components: list[RecipeComponent] = []
    replaced_any = False
    for component in recipe.components:
        crystallized_component = _crystallized_component_for_artifact(component.item.unique_name, recipes=recipes)
        if crystallized_component is None:
            replaced_components.append(component)
            continue
        replaced_any = True
        replaced_components.append(
            RecipeComponent(
                item=crystallized_component.item,
                quantity=float(component.quantity) * float(crystallized_component.quantity),
                returnable=False,
            )
        )
    if not replaced_any:
        return None
    return Recipe(
        item=recipe.item,
        station=recipe.station,
        city_bonus=recipe.city_bonus,
        components=tuple(replaced_components),
        outputs=recipe.outputs,
        focus_per_craft=recipe.focus_per_craft,
        recipe_id=f"{output_item.unique_name}{_CRYSTALLIZED_RECIPE_SUFFIX}",
        variant_label="Crystallized",
        uses_crystallized=True,
    )


def _crystallized_component_for_artifact(
    artifact_item_id: str,
    *,
    recipes: dict[str, Recipe],
) -> RecipeComponent | None:
    base_id = str(artifact_item_id or "").strip()
    if not base_id:
        return None
    variant = recipes.get(f"{base_id}{_CRYSTALLIZED_RECIPE_SUFFIX}")
    if variant is None or not variant.components:
        return None
    if len(variant.components) != 1:
        return None
    return variant.components[0]


def _base_component_kind(component_id: str, *, tier: int) -> str:
    normalized = str(component_id or "").strip().upper()
    if not normalized:
        return ""
    normalized = normalized.split("@", 1)[0]
    normalized = _LEVEL_SUFFIX_RE.sub("", normalized)
    tier_prefix = f"T{int(tier)}_"
    if normalized.startswith(tier_prefix):
        return normalized[len(tier_prefix) :]
    tier_match = _TIER_PATTERN.match(normalized)
    if tier_match is not None and "_" in normalized:
        return normalized.split("_", 1)[1]
    return normalized


def _parse_outputs(
    payload: object,
    fallback_item: ItemRef,
    *,
    item_values: dict[str, int] | None = None,
) -> tuple[RecipeOutput, ...]:
    if not isinstance(payload, list):
        return (RecipeOutput(item=fallback_item, quantity=1.0),)
    out: list[RecipeOutput] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        item_data = row.get("item")
        if not isinstance(item_data, dict):
            continue
        item = _to_item_ref(
            item_data,
            fallback_name=fallback_item.unique_name,
            item_values=item_values,
        )
        if not item.unique_name:
            continue
        quantity = float(row.get("quantity") or 0.0)
        if quantity <= 0:
            continue
        out.append(RecipeOutput(item=item, quantity=quantity))
    if not out:
        return (RecipeOutput(item=fallback_item, quantity=1.0),)
    return tuple(out)


def _collect_craftable_item_ids(raw_rows: list[object]) -> set[str]:
    out: set[str] = set()
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        item_payload = row.get("item")
        if isinstance(item_payload, dict):
            unique_name = str(item_payload.get("unique_name") or "").strip()
            if unique_name:
                out.add(unique_name)
        outputs_payload = row.get("outputs")
        if not isinstance(outputs_payload, list):
            continue
        for output in outputs_payload:
            if not isinstance(output, dict):
                continue
            output_item = output.get("item")
            if not isinstance(output_item, dict):
                continue
            unique_name = str(output_item.get("unique_name") or "").strip()
            if unique_name:
                out.add(unique_name)
    return out


def _inherit_component_enchantment(
    *,
    item: ItemRef,
    recipe_enchantment: int,
    craftable_item_ids: set[str],
) -> ItemRef:
    if recipe_enchantment <= 0:
        return item
    if int(item.enchantment or 0) > 0:
        return item
    unique_name = str(item.unique_name or "").strip()
    if not unique_name:
        return item
    if "@" in unique_name or _LEVEL_SUFFIX_RE.search(unique_name):
        return item
    candidate = f"{unique_name}@{recipe_enchantment}"
    if candidate not in craftable_item_ids:
        return item
    return ItemRef(
        unique_name=candidate,
        display_name=item.display_name,
        tier=item.tier,
        enchantment=recipe_enchantment,
        item_value=item.item_value,
    )


@lru_cache(maxsize=1)
def _load_item_values(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    root = payload.get("items")
    if not isinstance(root, dict):
        return {}

    out: dict[str, int] = {}
    stack: list[object] = [root]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            unique_name = str(current.get("@uniquename") or "").strip()
            item_value = _to_int_or_none(current.get("@itemvalue"))
            if unique_name and item_value is not None:
                out[unique_name] = int(item_value)
            for key, value in current.items():
                if key.startswith("@"):
                    continue
                if isinstance(value, (dict, list)):
                    stack.append(value)
        elif isinstance(current, list):
            for value in current:
                if isinstance(value, (dict, list)):
                    stack.append(value)
    return out
