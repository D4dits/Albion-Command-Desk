from __future__ import annotations

import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Sequence

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import CraftSetup, PriceType
from albion_dps.qt.market.state_types import _JournalLine, _JournalRule, _JournalTotals

_JOURNAL_NPC_EMPTY_PRICES: dict[int, int] = {
    2: 500,
    3: 1000,
    4: 2000,
    5: 4000,
    6: 8000,
    7: 16000,
    8: 32000,
}
_JOURNAL_NAME_BY_KIND: dict[str, str] = {
    "WARRIOR": "Blacksmith's Journal",
    "HUNTER": "Fletcher's Journal",
    "MAGE": "Imbuer's Journal",
    "TOOLMAKER": "Tinker's Journal",
}
_TIER_PREFIX_RE = re.compile(r"^T(?P<tier>\d+)_(?P<rest>.+)$", re.IGNORECASE)
_LEVEL_SUFFIX_RE = re.compile(r"_LEVEL\d+$", re.IGNORECASE)
_HALF_FAME_MARKERS = ("_HEAD_", "_SHOES_", "_OFF_")


def _base_item_id(item_id: str) -> str:
    value = str(item_id or "").strip().upper()
    if not value:
        return ""
    if "@" in value:
        value = value.rsplit("@", 1)[0]
    value = _LEVEL_SUFFIX_RE.sub("", value)
    return value


def _tier_from_item_id(item_id: str) -> int:
    match = _TIER_PREFIX_RE.match(_base_item_id(item_id))
    if match is None:
        return 0
    try:
        return int(match.group("tier"))
    except (TypeError, ValueError):
        return 0


@lru_cache(maxsize=1)
def journal_maps() -> tuple[dict[str, _JournalRule], dict[str, float]]:
    items_path = Path(__file__).resolve().parents[3] / "data" / "items.json"
    try:
        payload = json.loads(items_path.read_text(encoding="utf-8"))
    except Exception:
        return {}, {}
    raw_items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(raw_items, dict):
        return {}, {}

    entries: dict[str, dict[str, object]] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            unique_name = node.get("@uniquename")
            if isinstance(unique_name, str) and unique_name:
                entries[unique_name] = node
            for value in node.values():
                walk(value)
            return
        if isinstance(node, list):
            for value in node:
                walk(value)

    walk(raw_items)

    journal_by_item: dict[str, _JournalRule] = {}
    fame_factor_by_item: dict[str, float] = {}
    for unique_name, node in entries.items():
        factor_raw = node.get("@destinyandjournalcraftfamefactor")
        if factor_raw is not None:
            try:
                fame_factor_by_item[_base_item_id(unique_name)] = float(factor_raw)
            except (TypeError, ValueError):
                pass

    journal_types = ("WARRIOR", "HUNTER", "MAGE", "TOOLMAKER")
    for tier in range(2, 9):
        for kind in journal_types:
            journal_id = f"T{tier}_JOURNAL_{kind}"
            node = entries.get(journal_id)
            if node is None:
                continue
            max_fame_raw = node.get("@maxfame")
            fame_missions = node.get("famefillingmissions")
            if not isinstance(fame_missions, dict):
                continue
            craft = fame_missions.get("craftitemfame")
            if not isinstance(craft, dict):
                continue
            value_raw = craft.get("@value")
            valid_items = craft.get("validitem")
            if isinstance(valid_items, dict):
                valid_list = [valid_items]
            elif isinstance(valid_items, list):
                valid_list = [x for x in valid_items if isinstance(x, dict)]
            else:
                valid_list = []
            try:
                max_fame = float(max_fame_raw)
                fame_per_item = float(value_raw)
            except (TypeError, ValueError):
                continue
            if max_fame <= 0 or fame_per_item <= 0:
                continue
            rule = _JournalRule(
                kind=kind,
                tier=tier,
                empty_item_id=journal_id,
                full_item_id=f"{journal_id}_FULL",
                max_fame=max_fame,
                fame_per_item=fame_per_item,
            )
            for row in valid_list:
                item_id = row.get("@id")
                if not isinstance(item_id, str) or not item_id:
                    continue
                journal_by_item[_base_item_id(item_id)] = rule
    return journal_by_item, fame_factor_by_item


@lru_cache(maxsize=1)
def journal_rule_templates() -> dict[tuple[int, str], _JournalRule]:
    journal_by_item, _ = journal_maps()
    templates_from_rules: dict[tuple[int, str], _JournalRule] = {}
    for rule in journal_by_item.values():
        templates_from_rules.setdefault((int(rule.tier), str(rule.kind).upper()), rule)
    if templates_from_rules:
        return templates_from_rules

    items_path = Path(__file__).resolve().parents[3] / "data" / "items.json"
    try:
        payload = json.loads(items_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    raw_items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(raw_items, dict):
        return {}

    entries: dict[str, dict[str, object]] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            unique_name = node.get("@uniquename")
            if isinstance(unique_name, str) and unique_name:
                entries[unique_name] = node
            for value in node.values():
                walk(value)
            return
        if isinstance(node, list):
            for value in node:
                walk(value)

    walk(raw_items)

    templates: dict[tuple[int, str], _JournalRule] = {}
    journal_types = ("WARRIOR", "HUNTER", "MAGE", "TOOLMAKER")
    for tier in range(2, 9):
        for kind in journal_types:
            journal_id = f"T{tier}_JOURNAL_{kind}"
            node = entries.get(journal_id)
            if node is None:
                continue
            max_fame_raw = node.get("@maxfame")
            fame_missions = node.get("famefillingmissions")
            if not isinstance(fame_missions, dict):
                continue
            craft = fame_missions.get("craftitemfame")
            if not isinstance(craft, dict):
                continue
            value_raw = craft.get("@value")
            try:
                max_fame = float(max_fame_raw)
                fame_per_item = float(value_raw)
            except (TypeError, ValueError):
                continue
            if max_fame <= 0 or fame_per_item <= 0:
                continue
            templates[(tier, kind)] = _JournalRule(
                kind=kind,
                tier=tier,
                empty_item_id=journal_id,
                full_item_id=f"{journal_id}_FULL",
                max_fame=max_fame,
                fame_per_item=fame_per_item,
            )
    return templates


@lru_cache(maxsize=1)
def item_metadata_map() -> dict[str, dict[str, str]]:
    items_path = Path(__file__).resolve().parents[3] / "data" / "items.json"
    try:
        payload = json.loads(items_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    raw_items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(raw_items, dict):
        return {}

    out: dict[str, dict[str, str]] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            unique_name = node.get("@uniquename")
            if isinstance(unique_name, str) and unique_name:
                out[_base_item_id(unique_name)] = {
                    "shopcategory": str(node.get("@shopcategory") or ""),
                    "shopsubcategory1": str(node.get("@shopsubcategory1") or ""),
                    "shopsubcategory2": str(node.get("@shopsubcategory2") or ""),
                    "slottype": str(node.get("@slottype") or ""),
                }
            for value in node.values():
                walk(value)
            return
        if isinstance(node, list):
            for value in node:
                walk(value)

    walk(raw_items)
    return out


def infer_journal_kind_for_item(item_id: str) -> str | None:
    base_id = _base_item_id(item_id)
    if "_PLATE_" in base_id:
        return "WARRIOR"
    if "_LEATHER_" in base_id:
        return "HUNTER"
    if "_CLOTH_" in base_id:
        return "MAGE"
    metadata = item_metadata_map().get(base_id, {})
    hints = [
        str(metadata.get("shopcategory") or "").upper(),
        str(metadata.get("shopsubcategory1") or "").upper(),
        str(metadata.get("shopsubcategory2") or "").upper(),
        str(metadata.get("slottype") or "").upper(),
        base_id,
    ]
    combined = " ".join(hint for hint in hints if hint)
    if "PLATE" in combined:
        return "WARRIOR"
    if "LEATHER" in combined:
        return "HUNTER"
    if "CLOTH" in combined:
        return "MAGE"
    return None


def journal_display_name(kind: str, tier: int) -> str:
    base_name = _JOURNAL_NAME_BY_KIND.get(str(kind or "").upper(), "Journal")
    normalized_tier = max(0, int(tier))
    if normalized_tier > 0:
        return f"T{normalized_tier} {base_name}"
    return base_name


def _journal_fame_weight_for_recipe(recipe: Any) -> float:
    item = getattr(recipe, "item", None)
    base_id = _base_item_id(str(getattr(item, "unique_name", "") or ""))
    if any(marker in base_id for marker in _HALF_FAME_MARKERS):
        return 0.5
    station = str(getattr(recipe, "station", "") or "").strip().lower()
    if station.endswith((" helmet", " shoes")) or station == "offhand":
        return 0.5
    return 1.0


def estimate_journal_totals(
    *,
    runs: list[Any],
    setup: CraftSetup,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    resolve_market_price_for_item_ids: Callable[[dict[tuple[str, str, int], MarketPriceRecord], list[str], str, int, str], tuple[float, str, str]],
    journal_rule_for_item: Callable[[str], _JournalRule | None],
    journal_fame_factor_for_item: Callable[[str], float],
    tier_from_item_id: Callable[[str], int],
) -> _JournalTotals:
    buy_city = (setup.default_buy_city or setup.craft_city or "").strip()
    sell_city = (setup.default_sell_city or setup.craft_city or "").strip()
    if not buy_city or not sell_city:
        return _JournalTotals()

    aggregates: dict[str, dict[str, float | str]] = {}
    for run in runs:
        recipe = getattr(run, "recipe", None)
        outputs = getattr(run, "outputs", ())
        if recipe is None:
            continue
        rule = journal_rule_for_item(str(recipe.item.unique_name))
        if rule is None:
            continue
        recipe_base = _base_item_id(str(recipe.item.unique_name))
        crafted_units = 0.0
        for line in outputs:
            if _base_item_id(str(line.item.unique_name)) == recipe_base:
                crafted_units += float(line.quantity)
        if crafted_units <= 0:
            continue
        factor = journal_fame_factor_for_item(str(recipe.item.unique_name))
        fame_weight = _journal_fame_weight_for_recipe(recipe)
        gained_fame = crafted_units * float(rule.fame_per_item) * float(factor) * float(fame_weight)
        if gained_fame <= 0:
            continue
        key = f"{rule.empty_item_id}|{rule.full_item_id}|{rule.max_fame}"
        row = aggregates.get(key)
        if row is None:
            aggregates[key] = {
                "kind": rule.kind,
                "tier": float(rule.tier),
                "empty_item_id": rule.empty_item_id,
                "full_item_id": rule.full_item_id,
                "max_fame": float(rule.max_fame),
                "gained_fame": gained_fame,
            }
        else:
            row["gained_fame"] = float(row["gained_fame"]) + gained_fame

    if not aggregates:
        return _JournalTotals()

    total_input_cost = 0.0
    total_output_value = 0.0
    total_full_quantity = 0.0
    journal_lines: list[_JournalLine] = []
    for row in aggregates.values():
        max_fame = max(1.0, float(row["max_fame"]))
        full_equivalent = max(0.0, float(row["gained_fame"]) / max_fame)
        empty_quantity = float(max(0, math.ceil(full_equivalent - 1e-9)))
        full_quantity = float(max(0, math.floor(full_equivalent + 1e-9)))
        if empty_quantity <= 0 and full_quantity <= 0:
            continue
        kind = str(row.get("kind", ""))
        tier = int(float(row.get("tier", 0.0)))
        empty_item_id = str(row["empty_item_id"])
        full_item_id = str(row["full_item_id"])

        empty_market_price, empty_price_mode, empty_price_item_id = resolve_market_price_for_item_ids(
            price_index,
            [f"{empty_item_id}_EMPTY", empty_item_id],
            buy_city,
            setup.quality,
            PriceType.SELL_ORDER.value,
        )
        empty_npc_price = float(_JOURNAL_NPC_EMPTY_PRICES.get(tier_from_item_id(empty_item_id), 0))
        empty_unit_price = empty_market_price if empty_market_price > 0 else empty_npc_price

        full_unit_price, full_price_mode, full_price_item_id = resolve_market_price_for_item_ids(
            price_index,
            [full_item_id],
            sell_city,
            setup.quality,
            PriceType.SELL_ORDER.value,
        )
        if full_unit_price <= 0:
            continue

        line_input_cost = float(empty_quantity * empty_unit_price)
        line_output_value = float(full_quantity * full_unit_price)
        line_market_tax = max(0.0, line_output_value * (float(setup.market_tax_percent) / 100.0))

        total_input_cost += line_input_cost
        total_output_value += line_output_value
        total_full_quantity += full_quantity
        journal_lines.append(
            _JournalLine(
                kind=kind,
                tier=tier,
                empty_item_id=empty_item_id,
                full_item_id=full_item_id,
                empty_quantity=float(empty_quantity),
                input_price_mode=str(empty_price_mode),
                output_price_mode=str(full_price_mode),
                full_quantity=float(full_quantity),
                input_cost=line_input_cost,
                output_value=line_output_value,
                market_tax=float(line_market_tax),
                empty_price_item_id=str(empty_price_item_id),
                full_price_item_id=str(full_price_item_id),
            )
        )

    journal_market_tax = max(0.0, sum(line.market_tax for line in journal_lines))
    return _JournalTotals(
        input_cost=float(total_input_cost),
        output_value=float(total_output_value),
        market_tax=float(journal_market_tax),
        full_quantity=float(total_full_quantity),
        lines=tuple(journal_lines),
    )


__all__ = [
    "estimate_journal_totals",
    "infer_journal_kind_for_item",
    "item_metadata_map",
    "journal_display_name",
    "journal_maps",
    "journal_rule_templates",
]
