from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.models import CraftSetup, MarketRegion, Recipe
from albion_dps.qt.market.list_models import CraftPlanRow


def default_preset_path() -> Path:
    return Path.home() / ".albion_dps" / "market_presets.json"


def sanitize_preset_name(raw_value: str) -> str:
    value = str(raw_value or "").strip()
    value = re.sub(r"\s+", " ", value)
    return value[:64]


def load_presets(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    out: dict[str, dict[str, object]] = {}
    for key, value in payload.items():
        name = sanitize_preset_name(str(key))
        if not name or not isinstance(value, dict):
            continue
        out[name] = value
    return out


def save_presets(path: Path, presets: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(presets, ensure_ascii=True, indent=2, sort_keys=True)
    path.write_text(serialized, encoding="utf-8")


def setup_to_dict(setup: CraftSetup) -> dict[str, object]:
    return {
        "region": setup.region.value,
        "craft_city": setup.craft_city,
        "default_buy_city": setup.default_buy_city,
        "default_sell_city": setup.default_sell_city,
        "premium": bool(setup.premium),
        "focus_enabled": bool(setup.focus_enabled),
        "station_fee_percent": float(setup.station_fee_percent),
        "market_tax_percent": float(setup.market_tax_percent),
        "daily_bonus_percent": float(setup.daily_bonus_percent),
        "return_rate_percent": float(setup.return_rate_percent),
        "hideout_power_percent": float(setup.hideout_power_percent),
        "quality": int(setup.quality),
    }


def setup_from_dict(payload: dict[str, object], *, fallback: CraftSetup) -> CraftSetup:
    region_raw = str(payload.get("region") or fallback.region.value).strip().lower()
    region_map = {
        "europe": MarketRegion.EUROPE,
        "west": MarketRegion.WEST,
        "east": MarketRegion.EAST,
    }
    region = region_map.get(region_raw, fallback.region)
    return CraftSetup(
        region=region,
        craft_city=str(payload.get("craft_city") or fallback.craft_city),
        default_buy_city=str(payload.get("default_buy_city") or fallback.default_buy_city),
        default_sell_city=str(payload.get("default_sell_city") or fallback.default_sell_city),
        premium=bool(payload.get("premium", fallback.premium)),
        focus_enabled=bool(payload.get("focus_enabled", fallback.focus_enabled)),
        station_fee_percent=float(payload.get("station_fee_percent") or fallback.station_fee_percent),
        market_tax_percent=float(payload.get("market_tax_percent") or fallback.market_tax_percent),
        daily_bonus_percent=float(payload.get("daily_bonus_percent") or fallback.daily_bonus_percent),
        return_rate_percent=float(payload.get("return_rate_percent") or fallback.return_rate_percent),
        hideout_power_percent=float(payload.get("hideout_power_percent") or fallback.hideout_power_percent),
        quality=int(payload.get("quality") or fallback.quality),
    )


def craft_plan_row_to_dict(row: CraftPlanRow) -> dict[str, object]:
    return {
        "row_id": int(row.row_id),
        "recipe_id": row.recipe_id,
        "display_name": row.display_name,
        "tier": int(row.tier),
        "enchant": int(row.enchant),
        "craft_city": row.craft_city,
        "daily_bonus_percent": float(row.daily_bonus_percent),
        "runs": int(row.runs),
        "enabled": bool(row.enabled),
    }


def craft_plan_rows_from_payload(
    payload: object,
    *,
    catalog: RecipeCatalog,
    fallback_city: str,
    fallback_daily_bonus_percent: float,
    normalize_daily_bonus_percent: Callable[[float], float],
    parse_price: Callable[[str], int],
    parse_float: Callable[[str], float],
    parse_bool: Callable[[object, bool], bool],
    recipe_display_label: Callable[[Recipe], str],
    recipe_identity: Callable[[Recipe], str],
) -> list[CraftPlanRow] | None:
    if payload is None:
        return None
    if not isinstance(payload, list):
        return []

    rows: list[CraftPlanRow] = []
    used_recipe_ids: set[str] = set()
    next_row_id = 1
    fallback_city_value = fallback_city.strip() or "Bridgewatch"
    fallback_daily_bonus = float(normalize_daily_bonus_percent(fallback_daily_bonus_percent))
    for raw_row in payload:
        if not isinstance(raw_row, dict):
            continue
        recipe_id = str(raw_row.get("recipe_id") or "").strip()
        if not recipe_id or recipe_id in used_recipe_ids:
            continue
        recipe = catalog.get(recipe_id)
        if recipe is None:
            continue
        used_recipe_ids.add(recipe_id)

        requested_row_id = parse_price(str(raw_row.get("row_id") or next_row_id))
        row_id = max(next_row_id, requested_row_id if requested_row_id > 0 else next_row_id)
        next_row_id = row_id + 1
        display_name = str(raw_row.get("display_name") or "").strip()
        if not display_name:
            display_name = recipe_display_label(recipe)
        tier = parse_price(str(raw_row.get("tier") or int(recipe.item.tier or 0)))
        enchant = parse_price(str(raw_row.get("enchant") or int(recipe.item.enchantment or 0)))
        craft_city = str(raw_row.get("craft_city") or fallback_city_value).strip() or fallback_city_value
        daily_bonus = float(
            normalize_daily_bonus_percent(
                parse_float(str(raw_row.get("daily_bonus_percent") or fallback_daily_bonus))
            )
        )
        runs = max(1, parse_price(str(raw_row.get("runs") or 1)))
        enabled = parse_bool(raw_row.get("enabled"), True)
        rows.append(
            CraftPlanRow(
                row_id=row_id,
                recipe_id=recipe_identity(recipe),
                display_name=display_name,
                tier=tier,
                enchant=enchant,
                variant_label=str(recipe.variant_label or ""),
                uses_crystallized=bool(recipe.uses_crystallized),
                craft_city=craft_city,
                daily_bonus_percent=daily_bonus,
                return_rate_percent=None,
                runs=runs,
                enabled=enabled,
                profit_percent=None,
                has_fresh_component_prices=True,
            )
        )
    return rows


__all__ = [
    "craft_plan_row_to_dict",
    "craft_plan_rows_from_payload",
    "default_preset_path",
    "load_presets",
    "sanitize_preset_name",
    "save_presets",
    "setup_from_dict",
    "setup_to_dict",
]
