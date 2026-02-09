from __future__ import annotations

import json
from pathlib import Path


def convert_legacy_recipe_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows:
        item_unique = str(
            row.get("item_unique_name")
            or row.get("unique_name")
            or row.get("item_id")
            or ""
        ).strip()
        if not item_unique:
            continue
        display_name = str(row.get("display_name") or row.get("item_name") or item_unique)
        tier = _int_or_none(row.get("tier"))
        enchantment = _int_or_none(row.get("enchantment")) or _int_or_none(row.get("enchant"))
        station = str(row.get("station") or row.get("craft_station") or "")
        city_bonus = str(row.get("city_bonus") or row.get("bonus_city") or "")
        focus_per_craft = int(_int_or_none(row.get("focus_per_craft")) or 0)
        components = _convert_lines(row.get("components") or row.get("inputs"))
        outputs = _convert_lines(
            row.get("outputs"),
            fallback_item={
                "unique_name": item_unique,
                "display_name": display_name,
                "tier": tier,
                "enchantment": enchantment,
            },
            fallback_quantity=1.0,
        )
        out.append(
            {
                "item": {
                    "unique_name": item_unique,
                    "display_name": display_name,
                    "tier": tier,
                    "enchantment": enchantment,
                },
                "station": station,
                "city_bonus": city_bonus,
                "focus_per_craft": focus_per_craft,
                "components": components,
                "outputs": outputs,
            }
        )
    return out


def migrate_recipe_file(source_path: Path, target_path: Path) -> int:
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("legacy recipes file must be a JSON array")
    rows = [x for x in payload if isinstance(x, dict)]
    converted = convert_legacy_recipe_rows(rows)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(converted, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(converted)


def _convert_lines(
    payload: object,
    *,
    fallback_item: dict[str, object] | None = None,
    fallback_quantity: float | None = None,
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    if isinstance(payload, list):
        rows = payload
    else:
        rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item_unique = str(
            row.get("item_unique_name")
            or row.get("unique_name")
            or row.get("item_id")
            or ""
        ).strip()
        if not item_unique:
            continue
        quantity = _float_or_none(row.get("quantity"))
        if quantity is None or quantity <= 0:
            continue
        item = {
            "unique_name": item_unique,
            "display_name": str(row.get("display_name") or row.get("item_name") or item_unique),
            "tier": _int_or_none(row.get("tier")),
            "enchantment": _int_or_none(row.get("enchantment")) or _int_or_none(row.get("enchant")),
        }
        out.append({"item": item, "quantity": quantity})
    if not out and fallback_item is not None and fallback_quantity is not None:
        out.append({"item": dict(fallback_item), "quantity": float(fallback_quantity)})
    return out


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

