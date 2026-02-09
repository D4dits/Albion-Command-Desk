from __future__ import annotations

import json
from pathlib import Path

from albion_dps.market.models import ItemRef, Recipe, RecipeComponent, RecipeOutput


def _to_item_ref(payload: dict[str, object], fallback_name: str = "") -> ItemRef:
    unique_name = str(payload.get("unique_name") or fallback_name).strip()
    return ItemRef(
        unique_name=unique_name,
        display_name=str(payload.get("display_name") or ""),
        tier=_to_int_or_none(payload.get("tier")),
        enchantment=_to_int_or_none(payload.get("enchantment")),
    )


def _to_int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class RecipeCatalog:
    def __init__(self, recipes: dict[str, Recipe] | None = None) -> None:
        self._recipes: dict[str, Recipe] = recipes or {}

    @classmethod
    def from_json(cls, path: Path) -> "RecipeCatalog":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError(f"Recipe file must contain a JSON array: {path}")
        recipes: dict[str, Recipe] = {}
        for row in raw:
            if not isinstance(row, dict):
                continue
            item_payload = row.get("item")
            if not isinstance(item_payload, dict):
                continue
            item = _to_item_ref(item_payload)
            if not item.unique_name:
                continue
            station = str(row.get("station") or "")
            city_bonus = str(row.get("city_bonus") or "")
            focus_per_craft = _to_int_or_none(row.get("focus_per_craft")) or 0
            components = _parse_components(row.get("components"))
            outputs = _parse_outputs(row.get("outputs"), item)
            recipes[item.unique_name] = Recipe(
                item=item,
                station=station,
                city_bonus=city_bonus,
                components=components,
                outputs=outputs,
                focus_per_craft=focus_per_craft,
            )
        return cls(recipes=recipes)

    def get(self, unique_name: str) -> Recipe | None:
        return self._recipes.get(unique_name)

    def has(self, unique_name: str) -> bool:
        return unique_name in self._recipes

    def items(self) -> list[str]:
        return sorted(self._recipes.keys())

    def __len__(self) -> int:
        return len(self._recipes)


def _parse_components(payload: object) -> tuple[RecipeComponent, ...]:
    if not isinstance(payload, list):
        return ()
    out: list[RecipeComponent] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        item_data = row.get("item")
        if not isinstance(item_data, dict):
            continue
        item = _to_item_ref(item_data)
        if not item.unique_name:
            continue
        quantity = float(row.get("quantity") or 0.0)
        if quantity <= 0:
            continue
        out.append(RecipeComponent(item=item, quantity=quantity))
    return tuple(out)


def _parse_outputs(payload: object, fallback_item: ItemRef) -> tuple[RecipeOutput, ...]:
    if not isinstance(payload, list):
        return (RecipeOutput(item=fallback_item, quantity=1.0),)
    out: list[RecipeOutput] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        item_data = row.get("item")
        if not isinstance(item_data, dict):
            continue
        item = _to_item_ref(item_data, fallback_name=fallback_item.unique_name)
        if not item.unique_name:
            continue
        quantity = float(row.get("quantity") or 0.0)
        if quantity <= 0:
            continue
        out.append(RecipeOutput(item=item, quantity=quantity))
    if not out:
        return (RecipeOutput(item=fallback_item, quantity=1.0),)
    return tuple(out)

