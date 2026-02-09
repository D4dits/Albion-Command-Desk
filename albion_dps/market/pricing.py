from __future__ import annotations

from albion_dps.market.models import PriceType


def choose_unit_price(
    *,
    price_type: PriceType,
    buy_price_max: int,
    sell_price_min: int,
    average_price: int | None = None,
    manual_price: int | None = None,
) -> int:
    if price_type == PriceType.MANUAL:
        return max(0, int(manual_price or 0))
    if price_type == PriceType.BUY_ORDER:
        return max(0, int(buy_price_max))
    if price_type == PriceType.SELL_ORDER:
        return max(0, int(sell_price_min))
    if average_price is not None:
        return max(0, int(average_price))
    # Fallback average if only market spread is available.
    if buy_price_max > 0 and sell_price_min > 0:
        return int((buy_price_max + sell_price_min) / 2)
    return max(0, int(sell_price_min or buy_price_max))

