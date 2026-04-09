from __future__ import annotations

from typing import Sequence

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import CraftRun, PriceType
from albion_dps.qt.market.list_models import CraftPlanRow


def demand_proxy_percent(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
    find_price_quote,
) -> float:
    quote = find_price_quote(
        price_index,
        item_id=item_id,
        city=city,
        quality=quality,
        preferred_mode=None,
    )
    if quote is None:
        return 0.0
    if quote.sell_price_min <= 0 or quote.buy_price_max <= 0:
        return 0.0
    return (float(quote.buy_price_max) / float(quote.sell_price_min)) * 100.0


def set_plan_profit_map(
    state,
    values: dict[int, float],
    *,
    return_rates: dict[int, float] | None = None,
    fresh_component_prices: dict[int, bool] | None = None,
) -> None:
    rates = return_rates or {}
    freshness = fresh_component_prices or {}
    next_rows: list[CraftPlanRow] = []
    changed = False
    for row in state._craft_plan_rows:
        next_profit = values.get(int(row.row_id))
        next_rrr = rates.get(int(row.row_id), row.return_rate_percent)
        if int(row.row_id) in freshness:
            next_has_fresh = bool(freshness[int(row.row_id)])
        elif row.enabled and fresh_component_prices is not None:
            next_has_fresh = False
        else:
            next_has_fresh = bool(row.has_fresh_component_prices)
        next_row = CraftPlanRow(
            row_id=row.row_id,
            recipe_id=row.recipe_id,
            display_name=row.display_name,
            tier=row.tier,
            enchant=row.enchant,
            variant_label=row.variant_label,
            uses_crystallized=bool(row.uses_crystallized),
            craft_city=row.craft_city,
            daily_bonus_percent=row.daily_bonus_percent,
            return_rate_percent=next_rrr,
            runs=row.runs,
            enabled=row.enabled,
            profit_percent=next_profit,
            has_fresh_component_prices=next_has_fresh,
        )
        if next_row != row:
            changed = True
        next_rows.append(next_row)
    if changed:
        state._craft_plan_rows = next_rows
        if str(state._craft_plan_sort_key or "") == "pl":
            state._sync_craft_plan_model()
        else:
            state._craft_plan_model.set_items_in_place(state._sorted_craft_plan_rows(state._craft_plan_rows))


def price_age_text(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
    price_type: str,
    find_price_quote,
    parse_iso_datetime,
    format_age,
) -> str:
    normalized = str(price_type).strip().lower()
    if normalized == PriceType.MANUAL.value:
        return "manual"
    quote = find_price_quote(
        price_index,
        item_id=item_id,
        city=city,
        quality=quality,
        preferred_mode=normalized,
    )
    if quote is None:
        return "n/a"

    if normalized == PriceType.BUY_ORDER.value:
        if int(quote.buy_price_max or 0) <= 0:
            return "n/a"
        dt = parse_iso_datetime(quote.buy_price_max_date)
    elif normalized == PriceType.SELL_ORDER.value:
        if int(quote.sell_price_min or 0) <= 0:
            return "n/a"
        dt = parse_iso_datetime(quote.sell_price_min_date)
    else:
        dt_buy = parse_iso_datetime(quote.buy_price_max_date) if int(quote.buy_price_max or 0) > 0 else None
        dt_sell = parse_iso_datetime(quote.sell_price_min_date) if int(quote.sell_price_min or 0) > 0 else None
        dt = max([x for x in [dt_buy, dt_sell] if x is not None], default=None)

    if dt is None:
        return "n/a"
    return format_age(dt)


def run_has_fresh_component_prices(state, run: CraftRun) -> bool:
    checked: set[tuple[str, str, str]] = set()
    for line in run.inputs:
        key = (str(line.item.unique_name), str(line.city), str(line.price_type.value))
        if key in checked:
            continue
        checked.add(key)
        if not state._has_fresh_price(
            item_id=str(line.item.unique_name),
            city=str(line.city),
            quality=int(state._setup.quality),
            price_type=str(line.price_type.value),
        ):
            return False
    return True


def has_fresh_price(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
    price_type: str,
    find_price_quote,
    parse_iso_datetime,
) -> bool:
    normalized = str(price_type).strip().lower()
    if normalized == PriceType.MANUAL.value:
        return True
    quote = find_price_quote(
        price_index,
        item_id=item_id,
        city=city,
        quality=quality,
        preferred_mode=normalized,
    )
    if quote is None:
        return False
    if normalized == PriceType.BUY_ORDER.value:
        return int(quote.buy_price_max or 0) > 0 and parse_iso_datetime(quote.buy_price_max_date) is not None
    if normalized == PriceType.SELL_ORDER.value:
        return int(quote.sell_price_min or 0) > 0 and parse_iso_datetime(quote.sell_price_min_date) is not None
    has_buy = int(quote.buy_price_max or 0) > 0 and parse_iso_datetime(quote.buy_price_max_date) is not None
    has_sell = int(quote.sell_price_min or 0) > 0 and parse_iso_datetime(quote.sell_price_min_date) is not None
    return bool(has_buy or has_sell)


def resolve_market_price_for_item_ids(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_ids: list[str],
    city: str,
    quality: int,
    preferred_mode: str,
    find_price_quote,
) -> tuple[float, str, str]:
    normalized_mode = str(preferred_mode).strip().lower()
    fallback_modes: list[str] = []
    if normalized_mode != PriceType.SELL_ORDER.value:
        fallback_modes.append(PriceType.SELL_ORDER.value)
    if normalized_mode != PriceType.BUY_ORDER.value:
        fallback_modes.append(PriceType.BUY_ORDER.value)
    mode_order = [normalized_mode] + fallback_modes
    for mode in mode_order:
        for item_id in item_ids:
            quote = find_price_quote(
                price_index,
                item_id=item_id,
                city=city,
                quality=quality,
                preferred_mode=mode,
            )
            if quote is None:
                continue
            if mode == PriceType.BUY_ORDER.value:
                value = int(quote.buy_price_max or 0)
            else:
                value = int(quote.sell_price_min or 0)
            if value > 0:
                return float(value), mode, str(item_id)
    return 0.0, normalized_mode, (str(item_ids[0]) if item_ids else "")


def price_age_text_for_item_ids(
    state,
    *,
    item_ids: Sequence[str],
    city: str,
    quality: int,
    price_type: str,
) -> str:
    seen: set[str] = set()
    for item_id in item_ids:
        normalized_item_id = str(item_id).strip()
        if not normalized_item_id or normalized_item_id in seen:
            continue
        seen.add(normalized_item_id)
        age_text = state._price_age_text(
            item_id=normalized_item_id,
            city=city,
            quality=quality,
            price_type=price_type,
        )
        if age_text.strip().lower() not in {"", "n/a", "unknown"}:
            return age_text
    return "n/a"
