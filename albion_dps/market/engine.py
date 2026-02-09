from __future__ import annotations

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import (
    CraftRun,
    CraftSetup,
    InputLine,
    OutputLine,
    PriceType,
    ProfitBreakdown,
    Recipe,
)
from albion_dps.market.pricing import choose_unit_price


def build_craft_run(
    *,
    recipe: Recipe,
    quantity: int,
    setup: CraftSetup,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    input_cities: dict[str, str] | None = None,
    output_cities: dict[str, str] | None = None,
    input_price_types: dict[str, PriceType] | None = None,
    output_price_types: dict[str, PriceType] | None = None,
    manual_input_prices: dict[str, int] | None = None,
    manual_output_prices: dict[str, int] | None = None,
) -> CraftRun:
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    inputs = build_input_lines(
        recipe=recipe,
        quantity=quantity,
        setup=setup,
        price_index=price_index,
        input_cities=input_cities or {},
        input_price_types=input_price_types or {},
        manual_input_prices=manual_input_prices or {},
    )
    outputs = build_output_lines(
        recipe=recipe,
        quantity=quantity,
        setup=setup,
        price_index=price_index,
        output_cities=output_cities or {},
        output_price_types=output_price_types or {},
        manual_output_prices=manual_output_prices or {},
    )
    return CraftRun(
        recipe=recipe,
        quantity=quantity,
        setup=setup,
        inputs=tuple(inputs),
        outputs=tuple(outputs),
    )


def build_input_lines(
    *,
    recipe: Recipe,
    quantity: int,
    setup: CraftSetup,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    input_cities: dict[str, str],
    input_price_types: dict[str, PriceType],
    manual_input_prices: dict[str, int],
) -> list[InputLine]:
    lines: list[InputLine] = []
    return_fraction = _effective_return_fraction(setup)
    for component in recipe.components:
        city = (
            input_cities.get(component.item.unique_name)
            or setup.default_buy_city
            or setup.craft_city
        )
        price_type = input_price_types.get(component.item.unique_name, PriceType.SELL_ORDER)
        quote = _pick_quote(
            price_index,
            item_id=component.item.unique_name,
            city=city,
            quality=setup.quality,
        )
        quantity_raw = component.quantity * float(quantity)
        quantity_effective = quantity_raw * (1.0 - return_fraction)
        unit_price = _select_price(
            quote=quote,
            price_type=price_type,
            manual_price=manual_input_prices.get(component.item.unique_name),
        )
        lines.append(
            InputLine(
                item=component.item,
                quantity=quantity_effective,
                city=city,
                price_type=price_type,
                unit_price=float(unit_price),
            )
        )
    return lines


def build_output_lines(
    *,
    recipe: Recipe,
    quantity: int,
    setup: CraftSetup,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    output_cities: dict[str, str],
    output_price_types: dict[str, PriceType],
    manual_output_prices: dict[str, int],
) -> list[OutputLine]:
    lines: list[OutputLine] = []
    for output in recipe.outputs:
        city = (
            output_cities.get(output.item.unique_name)
            or setup.default_sell_city
            or setup.craft_city
        )
        price_type = output_price_types.get(output.item.unique_name, PriceType.BUY_ORDER)
        quote = _pick_quote(
            price_index,
            item_id=output.item.unique_name,
            city=city,
            quality=setup.quality,
        )
        unit_price = _select_price(
            quote=quote,
            price_type=price_type,
            manual_price=manual_output_prices.get(output.item.unique_name),
        )
        lines.append(
            OutputLine(
                item=output.item,
                quantity=output.quantity * float(quantity),
                city=city,
                price_type=price_type,
                unit_price=float(unit_price),
            )
        )
    return lines


def compute_profit_breakdown(
    *,
    input_cost: float,
    output_value: float,
    station_fee_percent: float,
    market_tax_percent: float,
    focus_used: float = 0.0,
) -> ProfitBreakdown:
    fee_value = max(0.0, output_value * (station_fee_percent / 100.0))
    tax_value = max(0.0, output_value * (market_tax_percent / 100.0))
    return ProfitBreakdown(
        input_cost=max(0.0, input_cost),
        output_value=max(0.0, output_value),
        station_fee=fee_value,
        market_tax=tax_value,
        focus_used=max(0.0, focus_used),
    )


def compute_run_profit(run: CraftRun) -> ProfitBreakdown:
    input_cost = sum(line.total_cost for line in run.inputs)
    output_value = sum(line.total_value for line in run.outputs)
    focus_used = float(run.recipe.focus_per_craft * run.quantity)
    return compute_profit_breakdown(
        input_cost=input_cost,
        output_value=output_value,
        station_fee_percent=run.setup.station_fee_percent,
        market_tax_percent=run.setup.market_tax_percent,
        focus_used=focus_used,
    )


def _effective_return_fraction(setup: CraftSetup) -> float:
    base = max(0.0, setup.return_rate_percent / 100.0)
    bonus = max(0.0, setup.daily_bonus_percent / 100.0)
    hideout = max(0.0, setup.hideout_power_percent / 100.0)
    return min(0.95, base + bonus + hideout)


def _pick_quote(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
) -> MarketPriceRecord | None:
    key = (item_id, city, quality)
    quote = price_index.get(key)
    if quote is not None:
        return quote
    key_q1 = (item_id, city, 1)
    quote = price_index.get(key_q1)
    if quote is not None:
        return quote
    for candidate_key, candidate in price_index.items():
        if candidate_key[0] == item_id and candidate_key[1] == city:
            return candidate
    return None


def _select_price(
    *,
    quote: MarketPriceRecord | None,
    price_type: PriceType,
    manual_price: int | None,
) -> int:
    if quote is None:
        if price_type == PriceType.MANUAL:
            return int(manual_price or 0)
        return 0
    avg_price = None
    if quote.buy_price_max > 0 and quote.sell_price_min > 0:
        avg_price = int((quote.buy_price_max + quote.sell_price_min) / 2)
    return choose_unit_price(
        price_type=price_type,
        buy_price_max=quote.buy_price_max,
        sell_price_min=quote.sell_price_min,
        average_price=avg_price,
        manual_price=manual_price,
    )

