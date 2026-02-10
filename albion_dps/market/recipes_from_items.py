from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_TIER_RE = re.compile(r"^T(?P<tier>\d+)")
_LEVEL_RE = re.compile(r"_LEVEL(?P<level>\d+)$")
_LEVEL_SUFFIX_RE = re.compile(r"_LEVEL\d+$")


@dataclass(frozen=True)
class RecipesFromItemsReport:
    source_nodes: int
    craftable_nodes: int
    multi_requirement_nodes: int
    skipped_no_unique: int
    skipped_no_resources: int
    skipped_duplicate_unique: int
    recipes_out: int


def extract_recipes_from_items_json(
    *,
    items_json_path: Path,
    indexed_items_path: Path | None = None,
    include_locked: bool = True,
) -> tuple[list[dict[str, Any]], RecipesFromItemsReport]:
    payload = json.loads(items_json_path.read_text(encoding="utf-8"))
    display_names = load_display_names(indexed_items_path) if indexed_items_path is not None else {}
    return extract_recipes_from_items_payload(
        payload=payload,
        display_names=display_names,
        include_locked=include_locked,
    )


def load_display_names(indexed_items_path: Path) -> dict[str, str]:
    raw = json.loads(indexed_items_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        return {}
    out: dict[str, str] = {}
    for row in raw:
        if not isinstance(row, dict):
            continue
        unique_name = str(row.get("UniqueName") or row.get("unique_name") or "").strip()
        if not unique_name:
            continue
        display_name = ""
        localized = row.get("LocalizedNames")
        if isinstance(localized, dict):
            display_name = (
                str(localized.get("EN-US") or localized.get("EN") or "").strip()
            )
            if not display_name:
                for value in localized.values():
                    if isinstance(value, str) and value.strip():
                        display_name = value.strip()
                        break
        if not display_name:
            display_name = str(row.get("DisplayName") or row.get("display_name") or "").strip()
        if display_name:
            out[unique_name] = display_name
    return out


def extract_recipes_from_items_payload(
    *,
    payload: dict[str, Any],
    display_names: dict[str, str] | None = None,
    include_locked: bool = True,
) -> tuple[list[dict[str, Any]], RecipesFromItemsReport]:
    names = display_names or {}
    root = payload.get("items")
    if not isinstance(root, dict):
        raise ValueError("invalid items.json payload: missing 'items' object")
    item_values = _collect_item_values(root)

    source_nodes = 0
    craftable_nodes = 0
    multi_requirement_nodes = 0
    skipped_no_unique = 0
    skipped_no_resources = 0
    skipped_duplicate_unique = 0

    recipes_by_unique: dict[str, dict[str, Any]] = {}

    for node in _iter_craftable_nodes(root):
        source_nodes += 1
        unique_name = str(node.get("@uniquename") or "").strip()
        if not unique_name:
            skipped_no_unique += 1
            continue
        if not include_locked:
            unlocked = str(node.get("@unlockedtocraft") or "").strip().lower()
            if unlocked == "false":
                continue

        requirements = _iter_requirements(node.get("craftingrequirements"))
        if len(requirements) > 1:
            multi_requirement_nodes += 1
        chosen = _choose_requirement(requirements)
        if chosen is None:
            skipped_no_resources += 1
        else:
            requirement, resources = chosen
            recipe = _build_recipe_row(
                item_node=node,
                requirement=requirement,
                resources=resources,
                display_names=names,
                recipe_unique_name=unique_name,
                enchantment=_resolve_enchantment(
                    unique_name=unique_name,
                    raw_level=node.get("@enchantmentlevel"),
                ),
                item_values=item_values,
            )
            if unique_name in recipes_by_unique:
                skipped_duplicate_unique += 1
            else:
                craftable_nodes += 1
            recipes_by_unique[unique_name] = recipe

        for enchant_level, requirement, resources in _iter_enchantment_variants(node):
            enchant_unique = f"{unique_name}@{enchant_level}"
            recipe = _build_recipe_row(
                item_node=node,
                requirement=requirement,
                resources=resources,
                display_names=names,
                recipe_unique_name=enchant_unique,
                enchantment=int(enchant_level),
                item_values=item_values,
            )
            if enchant_unique in recipes_by_unique:
                skipped_duplicate_unique += 1
            else:
                craftable_nodes += 1
            recipes_by_unique[enchant_unique] = recipe

    rows = list(recipes_by_unique.values())
    rows.sort(key=lambda row: str(((row.get("item") or {}).get("unique_name") or "")).lower())

    report = RecipesFromItemsReport(
        source_nodes=source_nodes,
        craftable_nodes=craftable_nodes,
        multi_requirement_nodes=multi_requirement_nodes,
        skipped_no_unique=skipped_no_unique,
        skipped_no_resources=skipped_no_resources,
        skipped_duplicate_unique=skipped_duplicate_unique,
        recipes_out=len(rows),
    )
    return rows, report


def _iter_craftable_nodes(node: Any):
    if isinstance(node, dict):
        if "@uniquename" in node and "craftingrequirements" in node:
            yield node
        for key, value in node.items():
            if key.startswith("@"):
                continue
            if key == "shopcategories":
                continue
            if isinstance(value, (dict, list)):
                yield from _iter_craftable_nodes(value)
    elif isinstance(node, list):
        for value in node:
            if isinstance(value, (dict, list)):
                yield from _iter_craftable_nodes(value)


def _iter_requirements(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def _choose_requirement(
    requirements: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    best: tuple[tuple[float, float, int], dict[str, Any], list[dict[str, Any]]] | None = None
    for requirement in requirements:
        resources = _parse_resources(requirement.get("craftresource"))
        if not resources:
            continue
        amount = _to_float(requirement.get("@amountcrafted")) or 1.0
        level_components = sum(1 for row in resources if "_LEVEL" in row["unique_name"])
        score = (float(level_components), abs(float(amount) - 1.0), len(resources))
        if best is None or score < best[0]:
            best = (score, requirement, resources)
    if best is None:
        return None
    return best[1], best[2]


def _parse_resources(payload: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        source = [payload]
    elif isinstance(payload, list):
        source = [x for x in payload if isinstance(x, dict)]
    else:
        source = []

    for row in source:
        unique_name = str(row.get("@uniquename") or "").strip()
        quantity = _to_float(row.get("@count"))
        if not unique_name or quantity is None or quantity <= 0:
            continue
        rows.append({"unique_name": unique_name, "quantity": float(quantity)})
    return rows


def _build_recipe_row(
    *,
    item_node: dict[str, Any],
    requirement: dict[str, Any],
    resources: list[dict[str, Any]],
    display_names: dict[str, str],
    recipe_unique_name: str,
    enchantment: int | None,
    item_values: dict[str, int],
) -> dict[str, Any]:
    item_unique = str(item_node.get("@uniquename") or "").strip()
    tier = _parse_tier(item_unique)
    if tier is None:
        tier = _to_int(item_node.get("@tier"))
    item = _build_item_ref(
        unique_name=recipe_unique_name,
        display_names=display_names,
        tier=tier,
        enchantment=enchantment,
        item_value=_resolve_item_value(
            unique_name=recipe_unique_name,
            explicit_value=_to_int(item_node.get("@itemvalue")),
            item_values=item_values,
        ),
    )
    components = [
        {
            "item": _build_item_ref(
                unique_name=row["unique_name"],
                display_names=display_names,
                tier=_parse_tier(row["unique_name"]),
                enchantment=_resolve_enchantment(unique_name=row["unique_name"], raw_level=None),
                item_value=_resolve_item_value(
                    unique_name=row["unique_name"],
                    explicit_value=None,
                    item_values=item_values,
                ),
            ),
            "quantity": float(row["quantity"]),
            "returnable": _is_returnable_component(row["unique_name"]),
        }
        for row in resources
    ]
    amount_crafted = _to_float(requirement.get("@amountcrafted")) or 1.0
    outputs = [{"item": dict(item), "quantity": float(amount_crafted)}]

    station = str(
        item_node.get("@craftingcategory")
        or item_node.get("@shopsubcategory1")
        or item_node.get("@shopcategory")
        or "crafting"
    ).strip()
    if not station:
        station = "crafting"
    station = station.replace("_", " ").title()

    focus_per_craft = _to_int(requirement.get("@craftingfocus")) or 0
    return {
        "item": item,
        "station": station,
        "city_bonus": "",
        "focus_per_craft": focus_per_craft,
        "components": components,
        "outputs": outputs,
    }


def _iter_enchantment_variants(item_node: dict[str, Any]):
    enchantments = item_node.get("enchantments")
    if not isinstance(enchantments, dict):
        return
    payload = enchantments.get("enchantment")
    if isinstance(payload, dict):
        candidates = [payload]
    elif isinstance(payload, list):
        candidates = [x for x in payload if isinstance(x, dict)]
    else:
        candidates = []
    for candidate in candidates:
        level = _to_int(candidate.get("@enchantmentlevel"))
        if level is None or level <= 0:
            continue
        requirements = _iter_requirements(candidate.get("craftingrequirements"))
        chosen = _choose_requirement(requirements)
        if chosen is None:
            continue
        requirement, resources = chosen
        yield int(level), requirement, resources


def _build_item_ref(
    *,
    unique_name: str,
    display_names: dict[str, str],
    tier: int | None,
    enchantment: int | None,
    item_value: int | None,
) -> dict[str, Any]:
    display_name = display_names.get(unique_name, unique_name)
    return {
        "unique_name": unique_name,
        "display_name": display_name,
        "tier": tier,
        "enchantment": enchantment,
        "item_value": item_value,
    }


def _collect_item_values(node: Any) -> dict[str, int]:
    out: dict[str, int] = {}
    stack: list[Any] = [node]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            unique_name = str(current.get("@uniquename") or "").strip()
            item_value = _to_int(current.get("@itemvalue"))
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


def _is_returnable_component(unique_name: str) -> bool:
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
    )
    return not any(marker in name for marker in non_returnable_markers)


def _parse_tier(unique_name: str) -> int | None:
    match = _TIER_RE.match(unique_name)
    if not match:
        return None
    try:
        return int(match.group("tier"))
    except (TypeError, ValueError):
        return None


def _resolve_enchantment(*, unique_name: str, raw_level: Any) -> int | None:
    level = _to_int(raw_level)
    if level is not None:
        return max(0, level)
    match = _LEVEL_RE.search(unique_name)
    if not match:
        return 0
    try:
        return max(0, int(match.group("level")))
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(str(value).strip().replace(",", ".")))
        except (TypeError, ValueError):
            return None
