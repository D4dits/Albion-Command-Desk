from __future__ import annotations

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import CraftSetup, Recipe


def price_key(
    setup: CraftSetup,
    *,
    item_ids: tuple[str, ...],
    locations: tuple[str, ...],
) -> tuple[str, int, tuple[str, ...], tuple[str, ...]]:
    return (setup.region.value, int(setup.quality), item_ids, locations)


def default_market_tax_percent(premium: bool) -> float:
    return 6.5 if premium else 10.5


def is_market_location(location: str) -> bool:
    normalized = location.strip().lower()
    normalized = " ".join(normalized.split())
    market_locations = {
        "bridgewatch",
        "martlock",
        "lymhurst",
        "fort sterling",
        "fortsterling",
        "thetford",
        "caerleon",
        "brecilien",
        "black market",
        "blackmarket",
    }
    return normalized in market_locations


def build_fallback_price_index(
    *,
    setup: CraftSetup,
    locations: set[str],
    prices: dict[str, tuple[int, int]],
) -> dict[tuple[str, str, int], MarketPriceRecord]:
    index: dict[tuple[str, str, int], MarketPriceRecord] = {}
    for location in locations:
        if not location:
            continue
        for item_id, (buy_price, sell_price) in prices.items():
            index[(item_id, location, int(setup.quality))] = MarketPriceRecord(
                item_id=item_id,
                city=location,
                quality=int(setup.quality),
                sell_price_min=int(sell_price),
                buy_price_max=int(buy_price),
                sell_price_min_date="",
                buy_price_max_date="",
            )
            if int(setup.quality) != 1:
                index[(item_id, location, 1)] = MarketPriceRecord(
                    item_id=item_id,
                    city=location,
                    quality=1,
                    sell_price_min=int(sell_price),
                    buy_price_max=int(buy_price),
                    sell_price_min_date="",
                    buy_price_max_date="",
                )
    return index


def estimate_fallback_prices(
    *,
    recipes: list[Recipe],
) -> dict[str, tuple[int, int]]:
    known_prices: dict[str, tuple[int, int]] = {
        "T4_METALBAR": (900, 1000),
        "T4_PLANKS": (500, 600),
        "T4_CLOTH": (540, 620),
        "T4_LEATHER": (560, 640),
    }
    prices: dict[str, tuple[int, int]] = {}
    for recipe in recipes:
        for component in recipe.components:
            item_id = component.item.unique_name
            prices[item_id] = known_prices.get(item_id, price_by_tier(component.item.tier))

        component_sell_total = 0.0
        for component in recipe.components:
            buy_price, sell_price = prices.get(
                component.item.unique_name,
                price_by_tier(component.item.tier),
            )
            _ = buy_price
            component_sell_total += sell_price * component.quantity

        outputs = recipe.outputs or ()
        total_output_qty = sum(max(0.01, x.quantity) for x in outputs)
        if outputs and component_sell_total > 0:
            estimated_sell = int((component_sell_total / total_output_qty) * 1.30)
        else:
            estimated_sell = 1200
        estimated_buy = int(max(1, estimated_sell * 0.95))
        for output in outputs:
            prices[output.item.unique_name] = (estimated_buy, estimated_sell)
    return prices


def price_by_tier(tier: int | None) -> tuple[int, int]:
    value_by_tier = {
        2: 80,
        3: 220,
        4: 600,
        5: 1800,
        6: 5200,
        7: 14500,
        8: 42000,
    }
    tier_value = value_by_tier.get(int(tier or 4), value_by_tier[4])
    buy_price = int(max(1, tier_value * 0.92))
    sell_price = int(max(1, tier_value))
    return buy_price, sell_price


__all__ = [
    "build_fallback_price_index",
    "default_market_tax_percent",
    "estimate_fallback_prices",
    "is_market_location",
    "price_by_tier",
    "price_key",
]
