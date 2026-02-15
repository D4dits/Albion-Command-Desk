from __future__ import annotations

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.engine import (
    BatchCraftRequest,
    build_craft_run,
    build_craft_runs_batch,
    compute_output_valuations,
    compute_batch_profit,
    compute_run_profit,
    effective_return_fraction,
)
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
    sword = ItemRef(
        unique_name="T4_MAIN_SWORD",
        display_name="Broadsword",
        tier=4,
        enchantment=0,
        item_value=1200,
    )
    bars = ItemRef(
        unique_name="T4_METALBAR",
        display_name="Metal Bar",
        tier=4,
        enchantment=0,
        item_value=300,
    )
    planks = ItemRef(
        unique_name="T4_PLANKS",
        display_name="Planks",
        tier=4,
        enchantment=0,
        item_value=200,
    )
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
        input_price_types={"T4_METALBAR": PriceType.SELL_ORDER},
        manual_input_prices={"T4_METALBAR": 700},
    )

    # 16 * 10 with 20% return -> 128
    bars_line = [x for x in run.inputs if x.item.unique_name == "T4_METALBAR"][0]
    assert round(bars_line.quantity, 2) == 128.0
    assert bars_line.unit_price == 700.0

    # 8 * 10 with 20% return -> 64
    planks_line = [x for x in run.inputs if x.item.unique_name == "T4_PLANKS"][0]
    assert round(planks_line.quantity, 2) == 64.0
    assert planks_line.unit_price == 500.0


def test_build_craft_run_manual_price_overrides_selected_mode() -> None:
    recipe = _build_recipe()
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        quality=1,
    )
    run = build_craft_run(
        recipe=recipe,
        quantity=1,
        setup=setup,
        price_index=_build_price_index(),
        output_price_types={"T4_MAIN_SWORD": PriceType.BUY_ORDER},
        manual_output_prices={"T4_MAIN_SWORD": 22222},
    )
    output = run.outputs[0]
    assert output.price_type == PriceType.BUY_ORDER
    assert output.unit_price == 22222.0


def test_build_craft_run_level_item_uses_base_market_quote() -> None:
    spear = ItemRef(
        unique_name="T7_MAIN_SPEAR_KEEPER",
        display_name="Heron Spear",
        tier=7,
        enchantment=0,
        item_value=30000,
    )
    bars = ItemRef(
        unique_name="T7_METALBAR_LEVEL1",
        display_name="Metal Bar",
        tier=7,
        enchantment=0,
        item_value=7000,
    )
    recipe = Recipe(
        item=spear,
        station="Warrior Forge",
        city_bonus="Bridgewatch",
        components=(RecipeComponent(item=bars, quantity=16.0),),
        outputs=(RecipeOutput(item=spear, quantity=1.0),),
    )
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        quality=1,
    )
    price_index = {
        ("T7_METALBAR_LEVEL1", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T7_METALBAR_LEVEL1",
            city="Bridgewatch",
            quality=1,
            sell_price_min=0,
            buy_price_max=0,
            sell_price_min_date="0001-01-01T00:00:00",
            buy_price_max_date="0001-01-01T00:00:00",
        ),
        ("T7_METALBAR", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T7_METALBAR",
            city="Bridgewatch",
            quality=1,
            sell_price_min=7400,
            buy_price_max=7000,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T7_METALBAR@1", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T7_METALBAR@1",
            city="Bridgewatch",
            quality=1,
            sell_price_min=120000,
            buy_price_max=110000,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T7_MAIN_SPEAR_KEEPER", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T7_MAIN_SPEAR_KEEPER",
            city="Bridgewatch",
            quality=1,
            sell_price_min=150000,
            buy_price_max=140000,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
    }
    run = build_craft_run(
        recipe=recipe,
        quantity=1,
        setup=setup,
        price_index=price_index,
    )
    bars_line = run.inputs[0]
    assert bars_line.item.unique_name == "T7_METALBAR_LEVEL1"
    assert bars_line.unit_price == 7000.0


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


def test_build_output_lines_respects_amount_crafted_and_quantity() -> None:
    sword = ItemRef(
        unique_name="T4_MAIN_SWORD",
        display_name="Broadsword",
        tier=4,
        enchantment=0,
        item_value=1200,
    )
    bars = ItemRef(
        unique_name="T4_METALBAR",
        display_name="Metal Bar",
        tier=4,
        enchantment=0,
        item_value=300,
    )
    recipe = Recipe(
        item=sword,
        station="Warrior Forge",
        city_bonus="Bridgewatch",
        components=(RecipeComponent(item=bars, quantity=10.0),),
        outputs=(RecipeOutput(item=sword, quantity=3.0),),
        focus_per_craft=100,
    )
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        quality=1,
    )
    run = build_craft_run(
        recipe=recipe,
        quantity=5,
        setup=setup,
        price_index=_build_price_index(),
    )
    output = run.outputs[0]
    assert output.quantity == 15.0


def test_compute_output_valuations_uses_usage_fee_formula() -> None:
    recipe = _build_recipe()
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        station_fee_percent=300.0,
        market_tax_percent=4.0,
        quality=1,
    )
    run = build_craft_run(
        recipe=recipe,
        quantity=2,
        setup=setup,
        price_index=_build_price_index(),
    )
    rows = compute_output_valuations(
        output_lines=run.outputs,
        station_fee_percent=setup.station_fee_percent,
        market_tax_percent=setup.market_tax_percent,
    )
    assert len(rows) == 1
    row = rows[0]
    assert row.gross_value > 0
    assert row.fee_value > 0
    assert row.tax_value > 0
    assert row.net_value < row.gross_value
    # Usage fee formula: ((ItemValue * 0.1125) * TaxFee) / 100 per crafted item.
    assert row.fee_value == 810.0


def test_compute_output_valuations_skips_usage_fee_for_t2_or_lower() -> None:
    output_item = ItemRef(
        unique_name="T2_METALBAR",
        display_name="Copper Bar",
        tier=2,
        enchantment=0,
        item_value=1000,
    )
    recipe = Recipe(
        item=output_item,
        station="Smelter",
        components=(),
        outputs=(RecipeOutput(item=output_item, quantity=1.0),),
    )
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        station_fee_percent=999.0,
        market_tax_percent=4.0,
        quality=1,
    )
    run = build_craft_run(
        recipe=recipe,
        quantity=3,
        setup=setup,
        price_index={
            ("T2_METALBAR", "Bridgewatch", 1): MarketPriceRecord(
                item_id="T2_METALBAR",
                city="Bridgewatch",
                quality=1,
                sell_price_min=250,
                buy_price_max=200,
                sell_price_min_date="",
                buy_price_max_date="",
            )
        },
    )
    rows = compute_output_valuations(
        output_lines=run.outputs,
        station_fee_percent=setup.station_fee_percent,
        market_tax_percent=setup.market_tax_percent,
    )
    assert len(rows) == 1
    assert rows[0].fee_value == 0.0


def test_compute_output_valuations_falls_back_when_item_value_missing() -> None:
    output_item = ItemRef(
        unique_name="T4_MAIN_ARCANESTAFF",
        display_name="Arcane Staff",
        tier=4,
        enchantment=0,
        item_value=None,
    )
    recipe = Recipe(
        item=output_item,
        station="Mage Tower",
        components=(),
        outputs=(RecipeOutput(item=output_item, quantity=1.0),),
    )
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        station_fee_percent=300.0,
        market_tax_percent=6.5,
        quality=1,
    )
    run = build_craft_run(
        recipe=recipe,
        quantity=1,
        setup=setup,
        price_index={
            ("T4_MAIN_ARCANESTAFF", "Bridgewatch", 1): MarketPriceRecord(
                item_id="T4_MAIN_ARCANESTAFF",
                city="Bridgewatch",
                quality=1,
                sell_price_min=10000,
                buy_price_max=9500,
                sell_price_min_date="",
                buy_price_max_date="",
            )
        },
    )
    rows = compute_output_valuations(
        output_lines=run.outputs,
        station_fee_percent=setup.station_fee_percent,
        market_tax_percent=setup.market_tax_percent,
    )
    assert len(rows) == 1
    assert rows[0].fee_value > 0.0


def test_build_input_lines_do_not_return_non_returnable_components() -> None:
    sword = ItemRef(
        unique_name="T4_MAIN_SWORD",
        display_name="Broadsword",
        tier=4,
        enchantment=0,
        item_value=1200,
    )
    bars = ItemRef(
        unique_name="T4_METALBAR",
        display_name="Metal Bar",
        tier=4,
        enchantment=0,
        item_value=300,
    )
    relic = ItemRef(
        unique_name="T4_ARTEFACT_2H_KEEPER_SWORD",
        display_name="Keeper Sword Relic",
        tier=4,
        enchantment=0,
        item_value=15000,
    )
    recipe = Recipe(
        item=sword,
        station="Warrior Forge",
        city_bonus="Bridgewatch",
        components=(
            RecipeComponent(item=bars, quantity=16.0, returnable=True),
            RecipeComponent(item=relic, quantity=1.0, returnable=False),
        ),
        outputs=(RecipeOutput(item=sword, quantity=1.0),),
        focus_per_craft=200,
    )
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        return_rate_percent=20.0,
        quality=1,
    )
    price_index = {
        ("T4_METALBAR", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_METALBAR",
            city="Bridgewatch",
            quality=1,
            sell_price_min=1000,
            buy_price_max=900,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T4_ARTEFACT_2H_KEEPER_SWORD", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_ARTEFACT_2H_KEEPER_SWORD",
            city="Bridgewatch",
            quality=1,
            sell_price_min=150000,
            buy_price_max=140000,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T4_MAIN_SWORD", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_MAIN_SWORD",
            city="Bridgewatch",
            quality=1,
            sell_price_min=16000,
            buy_price_max=15000,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
    }
    run = build_craft_run(
        recipe=recipe,
        quantity=10,
        setup=setup,
        price_index=price_index,
    )
    bars_line = [x for x in run.inputs if x.item.unique_name == "T4_METALBAR"][0]
    relic_line = [x for x in run.inputs if x.item.unique_name == "T4_ARTEFACT_2H_KEEPER_SWORD"][0]
    assert round(bars_line.quantity, 2) == 128.0
    assert round(relic_line.quantity, 2) == 10.0


def test_effective_return_fraction_uses_table_for_premium_and_city_bonus() -> None:
    recipe = _build_recipe()
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        premium=True,
        focus_enabled=True,
        return_rate_percent=0.0,
        daily_bonus_percent=0.0,
        hideout_power_percent=0.0,
    )
    fraction = effective_return_fraction(setup=setup, recipe=recipe)
    # Crafting, focus enabled, matching city bonus, no daily bonus.
    assert round(fraction, 3) == 0.479


def test_effective_return_fraction_applies_city_specialization_by_item_family() -> None:
    axe = ItemRef(unique_name="T4_MAIN_AXE", display_name="Battleaxe", tier=4, enchantment=0, item_value=1200)
    bars = ItemRef(unique_name="T4_METALBAR", display_name="Metal Bar", tier=4, enchantment=0, item_value=300)
    recipe = Recipe(
        item=axe,
        station="Axe",
        city_bonus="",
        components=(RecipeComponent(item=bars, quantity=16.0),),
        outputs=(RecipeOutput(item=axe, quantity=1.0),),
        focus_per_craft=200,
    )
    setup_martlock = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Martlock",
        default_buy_city="Martlock",
        default_sell_city="Martlock",
        premium=False,
        return_rate_percent=0.0,
        daily_bonus_percent=0.0,
    )
    setup_bridgewatch = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        premium=False,
        return_rate_percent=0.0,
        daily_bonus_percent=0.0,
    )
    martlock_fraction = effective_return_fraction(setup=setup_martlock, recipe=recipe)
    bridgewatch_fraction = effective_return_fraction(setup=setup_bridgewatch, recipe=recipe)
    assert round(martlock_fraction, 3) == 0.248
    assert round(bridgewatch_fraction, 3) == 0.153


def test_effective_return_fraction_applies_offhand_bonus_in_martlock() -> None:
    shield = ItemRef(
        unique_name="T4_OFF_SPIKEDSHIELD_MORGANA",
        display_name="Facebreaker",
        tier=4,
        enchantment=0,
        item_value=1200,
    )
    bars = ItemRef(unique_name="T4_METALBAR", display_name="Metal Bar", tier=4, enchantment=0, item_value=300)
    recipe = Recipe(
        item=shield,
        station="Offhand",
        city_bonus="",
        components=(RecipeComponent(item=bars, quantity=4.0),),
        outputs=(RecipeOutput(item=shield, quantity=1.0),),
        focus_per_craft=200,
    )
    setup_martlock = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Martlock",
        default_buy_city="Martlock",
        default_sell_city="Martlock",
        premium=False,
        return_rate_percent=0.0,
        daily_bonus_percent=0.0,
    )
    setup_caerleon = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Caerleon",
        default_buy_city="Caerleon",
        default_sell_city="Caerleon",
        premium=False,
        return_rate_percent=0.0,
        daily_bonus_percent=0.0,
    )
    martlock_fraction = effective_return_fraction(setup=setup_martlock, recipe=recipe)
    caerleon_fraction = effective_return_fraction(setup=setup_caerleon, recipe=recipe)
    assert round(martlock_fraction, 3) == 0.248
    assert round(caerleon_fraction, 3) == 0.153


def test_effective_return_fraction_crafting_snapshot_matrix() -> None:
    sword = ItemRef(unique_name="T4_MAIN_SWORD", display_name="Broadsword", tier=4, enchantment=0, item_value=1200)
    recipe = Recipe(
        item=sword,
        station="Warrior Forge",
        city_bonus="Lymhurst",
        components=(),
        outputs=(RecipeOutput(item=sword, quantity=1.0),),
    )
    scenarios = [
        ("royal_no_bonus", CraftSetup(craft_city="Bridgewatch", default_buy_city="Bridgewatch", default_sell_city="Bridgewatch"), 0.153),
        ("royal_with_bonus", CraftSetup(craft_city="Lymhurst", default_buy_city="Lymhurst", default_sell_city="Lymhurst"), 0.248),
        (
            "royal_no_bonus_focus",
            CraftSetup(craft_city="Bridgewatch", default_buy_city="Bridgewatch", default_sell_city="Bridgewatch", focus_enabled=True),
            0.435,
        ),
        (
            "royal_with_bonus_focus",
            CraftSetup(craft_city="Lymhurst", default_buy_city="Lymhurst", default_sell_city="Lymhurst", focus_enabled=True),
            0.479,
        ),
        (
            "royal_with_bonus_daily20_focus",
            CraftSetup(
                craft_city="Lymhurst",
                default_buy_city="Lymhurst",
                default_sell_city="Lymhurst",
                focus_enabled=True,
                daily_bonus_percent=20.0,
            ),
            0.528,
        ),
        (
            "island_with_bonus",
            CraftSetup(craft_city="Royal Island", default_buy_city="Bridgewatch", default_sell_city="Bridgewatch"),
            0.000,
        ),
        (
            "outlands_rest_base",
            CraftSetup(craft_city="Arthur's Rest", default_buy_city="Bridgewatch", default_sell_city="Bridgewatch"),
            0.130,
        ),
    ]
    for _name, setup, expected in scenarios:
        fraction = effective_return_fraction(setup=setup, recipe=recipe)
        assert round(fraction, 3) == expected


def test_effective_return_fraction_refining_snapshot_matrix() -> None:
    metalbar = ItemRef(unique_name="T4_METALBAR", display_name="Metal Bar", tier=4, enchantment=0, item_value=300)
    refining_recipe = Recipe(
        item=metalbar,
        station="Smelter",
        city_bonus="Thetford",
        components=(),
        outputs=(RecipeOutput(item=metalbar, quantity=1.0),),
    )
    scenarios = [
        (
            "refine_royal_no_bonus",
            CraftSetup(craft_city="Bridgewatch", default_buy_city="Bridgewatch", default_sell_city="Bridgewatch"),
            0.153,
        ),
        (
            "refine_royal_with_bonus",
            CraftSetup(craft_city="Thetford", default_buy_city="Thetford", default_sell_city="Thetford"),
            0.367,
        ),
        (
            "refine_roads_hideout_power20",
            CraftSetup(
                craft_city="Roads Hideout",
                default_buy_city="Bridgewatch",
                default_sell_city="Bridgewatch",
                hideout_power_percent=20.0,
            ),
            0.231,
        ),
    ]
    for _name, setup, expected in scenarios:
        fraction = effective_return_fraction(setup=setup, recipe=refining_recipe)
        assert round(fraction, 3) == expected


def test_build_craft_runs_batch_and_aggregate_profit() -> None:
    recipe = _build_recipe()
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        station_fee_percent=6.0,
        market_tax_percent=4.0,
        quality=1,
    )
    requests = [
        BatchCraftRequest(recipe=recipe, quantity=2),
        BatchCraftRequest(recipe=recipe, quantity=3),
    ]
    runs = build_craft_runs_batch(
        setup=setup,
        requests=requests,
        price_index=_build_price_index(),
    )
    assert len(runs) == 2
    assert runs[0].quantity == 2
    assert runs[1].quantity == 3

    total = compute_batch_profit(runs)
    assert total.input_cost > 0
    assert total.output_value > 0
    assert total.focus_used == float((2 + 3) * recipe.focus_per_craft)
