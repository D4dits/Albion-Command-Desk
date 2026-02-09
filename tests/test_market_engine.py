from __future__ import annotations

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.engine import build_craft_run, compute_run_profit
from albion_dps.market.models import (
    CraftSetup,
    ItemRef,
    MarketRegion,
    PriceType,
    Recipe,
    RecipeComponent,
    RecipeOutput,
)


def _build_recipe() -> Recipe:
    sword = ItemRef(unique_name="T4_MAIN_SWORD", display_name="Broadsword", tier=4, enchantment=0)
    bars = ItemRef(unique_name="T4_METALBAR", display_name="Metal Bar", tier=4, enchantment=0)
    planks = ItemRef(unique_name="T4_PLANKS", display_name="Planks", tier=4, enchantment=0)
    return Recipe(
        item=sword,
        station="Warrior Forge",
        city_bonus="Bridgewatch",
        components=(
            RecipeComponent(item=bars, quantity=16.0),
            RecipeComponent(item=planks, quantity=8.0),
        ),
        outputs=(RecipeOutput(item=sword, quantity=1.0),),
        focus_per_craft=200,
    )


def _build_price_index() -> dict[tuple[str, str, int], MarketPriceRecord]:
    return {
        ("T4_METALBAR", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_METALBAR",
            city="Bridgewatch",
            quality=1,
            sell_price_min=1000,
            buy_price_max=900,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T4_PLANKS", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_PLANKS",
            city="Bridgewatch",
            quality=1,
            sell_price_min=600,
            buy_price_max=500,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T4_MAIN_SWORD", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_MAIN_SWORD",
            city="Bridgewatch",
            quality=1,
            sell_price_min=15500,
            buy_price_max=15000,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
    }


def test_build_craft_run_with_return_and_manual_override() -> None:
    recipe = _build_recipe()
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        station_fee_percent=6.0,
        market_tax_percent=4.0,
        return_rate_percent=20.0,
        quality=1,
    )
    run = build_craft_run(
        recipe=recipe,
        quantity=10,
        setup=setup,
        price_index=_build_price_index(),
        input_price_types={"T4_METALBAR": PriceType.MANUAL},
        manual_input_prices={"T4_METALBAR": 700},
    )

    # 16 * 10 with 20% return -> 128
    bars_line = [x for x in run.inputs if x.item.unique_name == "T4_METALBAR"][0]
    assert round(bars_line.quantity, 2) == 128.0
    assert bars_line.unit_price == 700.0

    # 8 * 10 with 20% return -> 64
    planks_line = [x for x in run.inputs if x.item.unique_name == "T4_PLANKS"][0]
    assert round(planks_line.quantity, 2) == 64.0
    assert planks_line.unit_price == 600.0


def test_compute_run_profit_uses_costs_and_fees() -> None:
    recipe = _build_recipe()
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        station_fee_percent=6.0,
        market_tax_percent=4.0,
        return_rate_percent=0.0,
        quality=1,
    )
    run = build_craft_run(
        recipe=recipe,
        quantity=1,
        setup=setup,
        price_index=_build_price_index(),
    )
    breakdown = compute_run_profit(run)
    assert breakdown.input_cost > 0
    assert breakdown.output_value > 0
    assert breakdown.station_fee > 0
    assert breakdown.market_tax > 0
    assert breakdown.focus_used == 200.0

