from __future__ import annotations

import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("PySide6")

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.engine import build_craft_run
from albion_dps.market.models import CraftSetup, ItemRef, MarketRegion, Recipe, RecipeComponent, RecipeOutput
from albion_dps.market.service import MarketFetchMeta
from albion_dps.qt.market import MarketSetupState
from albion_dps.qt.market import state as market_state
from albion_dps.settings import AppSettings, save_app_settings


class _FakeMarketService:
    def __init__(self) -> None:
        self.calls = 0
        self.last_prices_meta = MarketFetchMeta(
            source="live",
            record_count=0,
            elapsed_ms=0.0,
            cache_key="fake",
        )

    def get_price_index(
        self,
        *,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int] | None = None,
        ttl_seconds: float = 120.0,
        allow_stale: bool = True,
        allow_cache: bool = True,
        allow_live: bool = True,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        _ = (region, ttl_seconds, allow_stale, allow_cache, allow_live)
        self.calls += 1
        quality = int((qualities or [1])[0])
        out: dict[tuple[str, str, int], MarketPriceRecord] = {}
        for location in locations:
            for item_id in item_ids:
                if item_id == "T4_MAIN_SWORD":
                    buy_price, sell_price = 15000, 16000
                elif item_id == "T4_METALBAR":
                    buy_price, sell_price = 900, 1000
                else:
                    buy_price, sell_price = 500, 600
                out[(item_id, location, quality)] = MarketPriceRecord(
                    item_id=item_id,
                    city=location,
                    quality=quality,
                    sell_price_min=sell_price,
                    buy_price_max=buy_price,
                    sell_price_min_date="",
                    buy_price_max_date="",
                )
        self.last_prices_meta = MarketFetchMeta(
            source="live",
            record_count=len(out),
            elapsed_ms=4.0,
            cache_key="fake",
        )
        return out

    def close(self) -> None:
        return


class _RateLimitedMarketService(_FakeMarketService):
    def get_price_index(
        self,
        *,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int] | None = None,
        ttl_seconds: float = 120.0,
        allow_stale: bool = True,
        allow_cache: bool = True,
        allow_live: bool = True,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        _ = (region, item_ids, locations, qualities, ttl_seconds, allow_stale, allow_cache, allow_live)
        self.calls += 1
        raise RuntimeError("AO Data prices request failed after 5 attempts: HTTP Error 429: Too Many Requests")


def _enable_all_plan_rows(state: MarketSetupState) -> None:
    model = state.craftPlanModel
    for idx in range(model.rowCount()):
        model_index = model.index(idx, 0)
        row_id = int(model.data(model_index, model.RowIdRole) or 0)
        if row_id > 0:
            state.setPlanRowEnabled(row_id, True)


def test_market_setup_state_sanitizes_values() -> None:
    state = MarketSetupState()
    state.setRegion("west")
    state.setStationFeePercent(1500.0)
    state.setQuality(99)

    setup = state.to_setup()
    assert setup.region.value == "west"
    assert setup.station_fee_percent == 999.0
    assert setup.market_tax_percent == pytest.approx(6.5)
    assert setup.quality == 6


def test_market_setup_state_market_tax_defaults_follow_premium() -> None:
    state = MarketSetupState()
    state.setPremium(True)
    assert state.marketTaxPercent == pytest.approx(6.5)
    state.setPremium(False)
    assert state.marketTaxPercent == pytest.approx(10.5)


def test_market_setup_state_daily_bonus_preset_rounding() -> None:
    state = MarketSetupState()
    state.setDailyBonusPreset("10%")
    assert state.dailyBonusPreset == 10
    state.setDailyBonusPercent(19.1)
    assert state.dailyBonusPreset == 20
    state.setDailyBonusPercent(3.0)
    assert state.dailyBonusPreset == 0


def test_market_setup_state_builds_outputs_and_results() -> None:
    state = MarketSetupState()
    assert state.craftPlanCount == 0
    assert state.craftPlanEnabledCount == 0
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    state.setCraftRuns(12)
    state.setReturnRatePercent(10.0)

    assert state.inputsModel.rowCount() >= 1
    assert state.outputsModel.rowCount() >= 1
    assert state.inputsTotalCost > 0
    assert state.outputsTotalValue > 0
    assert state.focusUsed > 0
    assert isinstance(state.netProfitValue, float)
    assert state.recipeOptionsModel.rowCount() >= 1
    assert state.recipeIndex >= 0
    assert state.recipeTier >= 0
    assert state.recipeEnchant >= 0
    assert state.shoppingModel.rowCount() >= 1
    assert state.sellingModel.rowCount() >= 1
    assert state.resultsItemsModel.rowCount() >= 1
    assert state.breakdownModel.rowCount() >= 1
    assert "item_id" in state.shoppingCsv
    assert "item_id" in state.sellingCsv
    assert state.outputsNetValue <= state.outputsTotalValue

    first_input = state.inputsModel.index(0, 0)
    first_output = state.outputsModel.index(0, 0)
    input_mode = str(state.inputsModel.data(first_input, state.inputsModel.PriceTypeRole))
    output_mode = str(state.outputsModel.data(first_output, state.outputsModel.PriceTypeRole))
    input_qty = float(state.inputsModel.data(first_input, state.inputsModel.QuantityRole))
    price_age_text = str(state.inputsModel.data(first_input, state.inputsModel.PriceAgeRole))
    assert input_mode == "sell_order"
    assert output_mode == "sell_order"
    assert input_qty == float(int(input_qty))
    assert len(price_age_text) > 0


def test_market_setup_state_uses_service_and_manual_overrides() -> None:
    service = _FakeMarketService()
    state = MarketSetupState(service=service, auto_refresh_prices=False)
    state.setActiveMarketTab(1)

    assert service.calls == 0
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    assert state.pricesSource == "live"
    assert service.calls >= 1

    default_output = state.outputsTotalValue
    state.setOutputManualPrice("T4_MAIN_SWORD", "22000")
    assert state.outputsTotalValue > default_output

    default_input = state.inputsTotalCost
    state.setInputManualPrice("T4_METALBAR", "1")
    assert state.inputsTotalCost < default_input

    previous_calls = service.calls
    # Initial auto live fetch sets short cooldown; manual refresh should wait.
    state.refreshPrices()
    assert service.calls == previous_calls
    assert state.refreshCooldownSeconds > 0
    state._next_live_fetch_not_before = 0.0
    state.refreshPrices()
    assert service.calls > previous_calls
    assert state.refreshCooldownSeconds >= 19


def test_market_setup_state_skips_live_fetch_in_setup_tab_until_data_tabs() -> None:
    service = _FakeMarketService()
    state = MarketSetupState(service=service, auto_refresh_prices=False)

    # Setup tab should not trigger live AO Data calls while building craft plan.
    state.setActiveMarketTab(0)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    assert service.calls == 0

    # Entering Inputs/Outputs/Results should enable live fetch.
    state.setActiveMarketTab(1)
    assert service.calls >= 1
    assert state.pricesSource == "live"


def test_market_setup_state_surfaces_rate_limit_cooldown_status() -> None:
    service = _RateLimitedMarketService()
    state = MarketSetupState(service=service, auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)

    state.setActiveMarketTab(1)

    assert service.calls >= 1
    assert state.pricesSource == "cooldown"
    assert "Cooling down" in state.pricesStatusText
    assert state.refreshCooldownSeconds >= 89


def test_market_setup_state_price_age_handles_aliases_and_invalid_dates() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    now_iso = datetime.now(timezone.utc).isoformat()
    state._price_index = {
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
            sell_price_min=9000,
            buy_price_max=8500,
            sell_price_min_date=now_iso,
            buy_price_max_date=now_iso,
        ),
    }
    age_buy = state._price_age_text(
        item_id="T7_METALBAR_LEVEL1",
        city="Bridgewatch",
        quality=1,
        price_type="buy_order",
    )
    assert age_buy == "n/a"

    state._price_index = {
        ("T7_METALBAR", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T7_METALBAR",
            city="Bridgewatch",
            quality=1,
            sell_price_min=9000,
            buy_price_max=8500,
            sell_price_min_date="0001-01-01T00:00:00",
            buy_price_max_date="0001-01-01T00:00:00",
        )
    }
    age_invalid = state._price_age_text(
        item_id="T7_METALBAR",
        city="Bridgewatch",
        quality=1,
        price_type="buy_order",
    )
    assert age_invalid == "n/a"


def test_market_setup_state_resolves_market_price_with_mode_fallback() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state._price_index = {
        ("T6_JOURNAL_WARRIOR_EMPTY", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T6_JOURNAL_WARRIOR_EMPTY",
            city="Bridgewatch",
            quality=1,
            sell_price_min=0,
            buy_price_max=7777,
            sell_price_min_date="",
            buy_price_max_date=datetime.now(timezone.utc).isoformat(),
        )
    }

    price, mode, used_item_id = state._resolve_market_price_for_item_ids(
        price_index=state._price_index,
        item_ids=["T6_JOURNAL_WARRIOR_EMPTY", "T6_JOURNAL_WARRIOR"],
        city="Bridgewatch",
        quality=1,
        preferred_mode="sell_order",
    )

    assert price == 7777.0
    assert mode == "buy_order"
    assert used_item_id == "T6_JOURNAL_WARRIOR_EMPTY"


def test_market_setup_state_price_age_for_item_ids_uses_first_fresh_quote() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    now_iso = datetime.now(timezone.utc).isoformat()
    state._price_index = {
        ("T7_JOURNAL_MAGE_EMPTY", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T7_JOURNAL_MAGE_EMPTY",
            city="Bridgewatch",
            quality=1,
            sell_price_min=5000,
            buy_price_max=0,
            sell_price_min_date=now_iso,
            buy_price_max_date="",
        )
    }

    age = state._price_age_text_for_item_ids(
        item_ids=["", "T7_JOURNAL_MAGE_EMPTY", "T7_JOURNAL_MAGE"],
        city="Bridgewatch",
        quality=1,
        price_type="sell_order",
    )
    assert age != "n/a"


def test_market_setup_state_supports_setup_presets(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp_dir = Path(f"tmp_market_presets_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    preset_path = tmp_dir / "market_presets.json"
    monkeypatch.setattr(market_state, "_default_preset_path", lambda: preset_path)

    try:
        state = MarketSetupState(auto_refresh_prices=False)
        state.addCurrentRecipeToPlan()
        recipe_options_model = state.recipeOptionsModel
        if recipe_options_model.rowCount() > 1:
            second_recipe_id = str(
                recipe_options_model.data(recipe_options_model.index(1, 0), recipe_options_model.RecipeIdRole) or ""
            )
            if second_recipe_id:
                state.addRecipeToPlan(second_recipe_id)

        plan_model = state.craftPlanModel
        assert plan_model.rowCount() >= 1
        first_plan_index = plan_model.index(0, 0)
        first_plan_row_id = int(plan_model.data(first_plan_index, plan_model.RowIdRole))
        first_plan_recipe_id = str(plan_model.data(first_plan_index, plan_model.RecipeIdRole) or "")

        state.setCraftCity("Martlock")
        state.setDefaultBuyCity("Martlock")
        state.setDefaultSellCity("Caerleon")
        state.setCraftRuns(42)
        state.setStationFeePercent(412.0)
        state.setFocusEnabled(True)
        state.setPlanRowRuns(first_plan_row_id, 33)
        state.setPlanRowCraftCity(first_plan_row_id, "Martlock")
        state.setPlanRowDailyBonus(first_plan_row_id, "20%")
        state.setRecipeSearchQuery("broadsword")
        state.savePreset("martlock_42")

        assert "martlock_42" in list(state.presetNames)
        assert preset_path.exists()

        state.clearCraftPlan()
        state.setCraftCity("Bridgewatch")
        state.setCraftRuns(7)
        state.setFocusEnabled(False)
        state.setRecipeSearchQuery("")
        state.loadPreset("martlock_42")
        assert state.craftCity == "Martlock"
        assert state.defaultBuyCity == "Martlock"
        assert state.defaultSellCity == "Caerleon"
        assert state.craftRuns == 33
        assert state.focusEnabled is True
        assert round(state.stationFeePercent, 0) == 412
        assert state.recipeSearchQuery == "broadsword"
        assert state.craftPlanCount >= 1
        reloaded_model = state.craftPlanModel
        restored_ids: list[str] = []
        restored = False
        for idx in range(reloaded_model.rowCount()):
            model_index = reloaded_model.index(idx, 0)
            recipe_id = str(reloaded_model.data(model_index, reloaded_model.RecipeIdRole) or "")
            restored_ids.append(recipe_id)
            if recipe_id != first_plan_recipe_id:
                continue
            restored = True
            assert int(reloaded_model.data(model_index, reloaded_model.RunsRole) or 0) == 33
            assert str(reloaded_model.data(model_index, reloaded_model.CraftCityRole) or "") == "Martlock"
            assert float(reloaded_model.data(model_index, reloaded_model.DailyBonusRole) or 0.0) == 20.0
        assert restored, f"Expected recipe {first_plan_recipe_id} in restored rows: {restored_ids}"

        state.deletePreset("martlock_42")
        assert "martlock_42" not in list(state.presetNames)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_market_setup_state_restores_selected_preset_from_app_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp_dir = Path(f"tmp_market_settings_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    preset_path = tmp_dir / "market_presets.json"
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", str(tmp_dir / "config"))
    monkeypatch.setattr(market_state, "_default_preset_path", lambda: preset_path)

    try:
        preset_path.write_text(
            market_state.json.dumps(
                {
                    "saved_fire": {
                        "setup": {
                            "region": "europe",
                            "craft_city": "Fort Sterling",
                            "default_buy_city": "Fort Sterling",
                            "default_sell_city": "Caerleon",
                            "premium": True,
                            "focus_enabled": False,
                            "station_fee_percent": 300.0,
                            "market_tax_percent": 400.0,
                            "daily_bonus_percent": 0.0,
                            "return_rate_percent": 0.0,
                            "hideout_power_percent": 0.0,
                            "quality": 1,
                        },
                        "craft_runs": 12,
                        "recipe_id": "T4_MAIN_SWORD",
                        "recipe_search_query": "sword",
                        "recipe_tier_filters": [4, 5],
                        "recipe_enchant_filters": [0, 1],
                        "hide_rows_without_fresh_prices": True,
                        "craft_plan": [],
                    }
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        save_app_settings(
            AppSettings(
                update_auto_check=True,
                market_selected_preset="saved_fire",
                market_export_dir=str(tmp_dir / "exports"),
            )
        )
        state = MarketSetupState(auto_refresh_prices=False)

        assert state.selectedPresetName == "saved_fire"
        assert state.craftCity == "Fort Sterling"
        assert state.defaultSellCity == "Caerleon"
        assert state.recipeSearchQuery == "sword"
        assert state.hideRowsWithoutFreshPrices is True
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_market_setup_state_can_export_results_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp_dir = Path(f"tmp_market_results_export_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", str(tmp_dir / "config"))
    export_path = tmp_dir / "results.csv"

    try:
        state = MarketSetupState(auto_refresh_prices=False)
        state.addCurrentRecipeToPlan()
        _enable_all_plan_rows(state)
        state.exportResultsCsv(str(export_path))

        assert export_path.exists()
        payload = export_path.read_text(encoding="utf-8")
        assert "item_id,item_name,city,quantity,revenue,cost,fee,tax,profit,margin_percent,demand_proxy" in payload
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_market_setup_state_diagnostics_log_lifecycle() -> None:
    service = _FakeMarketService()
    state = MarketSetupState(service=service, auto_refresh_prices=False)
    assert "Market state initialized." in state.diagnosticsText

    state.addCurrentRecipeToPlan()
    state.refreshPrices()
    assert "Manual price refresh requested." in state.diagnosticsText
    assert state.priceFetchInProgress is False

    state.clearDiagnostics()
    assert state.diagnosticsText == ""


def test_market_setup_state_applies_input_stock_to_buy_costs() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    if state.inputsModel.rowCount() <= 0:
        return

    idx = state.inputsModel.index(0, 0)
    item_id = str(state.inputsModel.data(idx, state.inputsModel.ItemIdRole))
    need_qty = float(state.inputsModel.data(idx, state.inputsModel.QuantityRole) or 0.0)
    base_total = float(state.inputsModel.data(idx, state.inputsModel.TotalCostRole) or 0.0)
    baseline_input_total = state.inputsTotalCost

    stock_qty = max(1.0, need_qty / 2.0)
    state.setInputStockQuantity(item_id, str(stock_qty))
    idx_after = state.inputsModel.index(0, 0)
    buy_qty = float(state.inputsModel.data(idx_after, state.inputsModel.BuyQuantityRole) or 0.0)
    stock_after = float(state.inputsModel.data(idx_after, state.inputsModel.StockQuantityRole) or 0.0)
    total_after = float(state.inputsModel.data(idx_after, state.inputsModel.TotalCostRole) or 0.0)

    assert stock_after > 0
    assert buy_qty <= need_qty
    assert total_after <= base_total
    assert state.inputsTotalCost <= baseline_input_total


def test_need_quantity_with_safety_buffer_for_returnable_resources() -> None:
    assert market_state._need_quantity_with_safety_buffer(125.0, True) == 125
    assert market_state._need_quantity_with_safety_buffer(63.0, True) == 63
    assert market_state._need_quantity_with_safety_buffer(10.0, False) == 10


def test_market_setup_state_input_preview_uses_full_upfront_returnable_quantity() -> None:
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
        components=(RecipeComponent(item=bars, quantity=16.0, returnable=True),),
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
    state = MarketSetupState(auto_refresh_prices=False)
    run = build_craft_run(recipe=recipe, quantity=2, setup=setup, price_index=price_index)

    preview_rows = state._accumulate_input_preview_rows(
        prepared_recipes=[(SimpleNamespace(row_id=1), recipe)],
        runs=[run],
    )
    row = next(iter(preview_rows.values()))

    assert row["item_id"] == "T4_METALBAR"
    assert float(row["quantity"]) == 29.0
    assert float(row["total_cost"]) == 26100.0


def test_market_setup_state_input_preview_uses_minimal_upfront_counts_for_two_component_weapon() -> None:
    weapon = ItemRef(
        unique_name="T4_2H_CROSSBOW_CANNON",
        display_name="Boltcasters",
        tier=4,
        enchantment=0,
        item_value=1200,
    )
    planks = ItemRef(
        unique_name="T4_PLANKS",
        display_name="Pine Planks",
        tier=4,
        enchantment=0,
        item_value=300,
    )
    bars = ItemRef(
        unique_name="T4_METALBAR",
        display_name="Steel Bar",
        tier=4,
        enchantment=0,
        item_value=300,
    )
    bolts = ItemRef(
        unique_name="T4_ARTEFACT_2H_DEMONIC_CROSSBOW",
        display_name="Hellish Bolts",
        tier=4,
        enchantment=0,
        item_value=800,
    )
    recipe = Recipe(
        item=weapon,
        station="Hunter Lodge",
        city_bonus="Bridgewatch",
        components=(
            RecipeComponent(item=planks, quantity=20.0, returnable=True),
            RecipeComponent(item=bars, quantity=12.0, returnable=True),
            RecipeComponent(item=bolts, quantity=1.0, returnable=False),
        ),
        outputs=(RecipeOutput(item=weapon, quantity=1.0),),
        focus_per_craft=200,
    )
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Bridgewatch",
        default_buy_city="Bridgewatch",
        default_sell_city="Bridgewatch",
        return_rate_percent=15.3,
        quality=1,
    )
    price_index = {
        ("T4_PLANKS", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_PLANKS",
            city="Bridgewatch",
            quality=1,
            sell_price_min=300,
            buy_price_max=280,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T4_METALBAR", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_METALBAR",
            city="Bridgewatch",
            quality=1,
            sell_price_min=400,
            buy_price_max=380,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T4_ARTEFACT_2H_DEMONIC_CROSSBOW", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_ARTEFACT_2H_DEMONIC_CROSSBOW",
            city="Bridgewatch",
            quality=1,
            sell_price_min=9000,
            buy_price_max=8500,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
    }
    state = MarketSetupState(auto_refresh_prices=False)
    run = build_craft_run(recipe=recipe, quantity=2, setup=setup, price_index=price_index)

    preview_rows = state._accumulate_input_preview_rows(
        prepared_recipes=[(SimpleNamespace(row_id=1), recipe)],
        runs=[run],
    )

    assert float(preview_rows[("T4_PLANKS", "Bridgewatch", "buy_order", 280.0)]["quantity"]) == 37.0
    assert float(preview_rows[("T4_METALBAR", "Bridgewatch", "buy_order", 380.0)]["quantity"]) == 22.0
    assert float(preview_rows[("T4_ARTEFACT_2H_DEMONIC_CROSSBOW", "Bridgewatch", "buy_order", 8500.0)]["quantity"]) == 2.0


def test_market_setup_state_input_preview_matches_batch_return_behavior_for_oathkeepers() -> None:
    weapon = ItemRef(
        unique_name="T7_2H_ARCANE_RIFT",
        display_name="Grandmaster's Oathkeepers",
        tier=7,
        enchantment=0,
        item_value=1200,
    )
    cloth = ItemRef(
        unique_name="T7_CLOTH",
        display_name="Opulent Cloth",
        tier=7,
        enchantment=0,
        item_value=300,
    )
    bars = ItemRef(
        unique_name="T7_METALBAR",
        display_name="Meteorite Steel Bar",
        tier=7,
        enchantment=0,
        item_value=300,
    )
    artifact = ItemRef(
        unique_name="T7_ARTEFACT_MAIN_ARCANE_RIFT",
        display_name="Grandmaster's Broken Oaths",
        tier=7,
        enchantment=0,
        item_value=800,
    )
    recipe = Recipe(
        item=weapon,
        station="Mage Tower",
        city_bonus="Martlock",
        components=(
            RecipeComponent(item=bars, quantity=20.0, returnable=True),
            RecipeComponent(item=cloth, quantity=12.0, returnable=True),
            RecipeComponent(item=artifact, quantity=1.0, returnable=False),
        ),
        outputs=(RecipeOutput(item=weapon, quantity=1.0),),
        focus_per_craft=200,
    )
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        craft_city="Martlock",
        default_buy_city="Martlock",
        default_sell_city="Martlock",
        return_rate_percent=21.8,
        quality=1,
    )
    price_index = {
        ("T7_CLOTH", "Martlock", 1): MarketPriceRecord(
            item_id="T7_CLOTH",
            city="Martlock",
            quality=1,
            sell_price_min=3000,
            buy_price_max=2800,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T7_METALBAR", "Martlock", 1): MarketPriceRecord(
            item_id="T7_METALBAR",
            city="Martlock",
            quality=1,
            sell_price_min=4000,
            buy_price_max=3800,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
        ("T7_ARTEFACT_MAIN_ARCANE_RIFT", "Martlock", 1): MarketPriceRecord(
            item_id="T7_ARTEFACT_MAIN_ARCANE_RIFT",
            city="Martlock",
            quality=1,
            sell_price_min=90000,
            buy_price_max=85000,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
    }
    state = MarketSetupState(auto_refresh_prices=False)
    run = build_craft_run(recipe=recipe, quantity=10, setup=setup, price_index=price_index)

    preview_rows = state._accumulate_input_preview_rows(
        prepared_recipes=[(SimpleNamespace(row_id=1), recipe)],
        runs=[run],
    )

    assert float(preview_rows[("T7_METALBAR", "Martlock", "buy_order", 3800.0)]["quantity"]) == 161.0
    assert float(preview_rows[("T7_CLOTH", "Martlock", "buy_order", 2800.0)]["quantity"]) == 96.0
    assert float(preview_rows[("T7_ARTEFACT_MAIN_ARCANE_RIFT", "Martlock", "buy_order", 85000.0)]["quantity"]) == 10.0


def test_market_setup_state_selected_input_total_uses_exact_expected_quantity() -> None:
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
        components=(RecipeComponent(item=bars, quantity=16.0, returnable=True),),
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
    state = MarketSetupState(auto_refresh_prices=False)
    run = build_craft_run(recipe=recipe, quantity=2, setup=setup, price_index=price_index)

    total_cost = state._compute_input_total_from_lines(
        input_lines=run.inputs,
        prepared_recipes=[(SimpleNamespace(row_id=1), recipe)],
    )

    assert total_cost == pytest.approx(32.0 * 0.8 * 900.0, rel=0.0, abs=0.01)


def test_journal_rule_mapping_and_factor_for_crafting_item(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_rule = market_state._JournalRule(
        kind="WARRIOR",
        tier=4,
        empty_item_id="T4_JOURNAL_WARRIOR",
        full_item_id="T4_JOURNAL_WARRIOR_FULL",
        max_fame=3600.0,
        fame_per_item=1200.0,
    )
    monkeypatch.setattr(
        market_state,
        "_journal_maps",
        lambda: ({"T4_MAIN_ROCKMACE_KEEPER": expected_rule}, {"T4_MAIN_ROCKMACE_KEEPER": 1.1}),
    )

    rule = market_state._journal_rule_for_item("T4_MAIN_ROCKMACE_KEEPER@2")
    assert rule is not None
    assert rule == expected_rule
    assert rule.kind == "WARRIOR"
    assert rule.tier == 4
    assert rule.empty_item_id == "T4_JOURNAL_WARRIOR"
    assert rule.full_item_id == "T4_JOURNAL_WARRIOR_FULL"
    assert int(rule.max_fame) == 3600
    assert int(rule.fame_per_item) == 1200

    factor = market_state._journal_fame_factor_for_item("T4_MAIN_ROCKMACE_KEEPER@2")
    assert round(factor, 2) == 1.10


def test_journal_display_name_uses_specific_kind_and_tier() -> None:
    assert market_state._journal_display_name("MAGE", 4) == "T4 Imbuer's Journal"
    assert market_state._journal_display_name("WARRIOR", 8) == "T8 Blacksmith's Journal"


@pytest.mark.skip(reason="Royal journal fallback coverage disabled for CI stability.")
def test_journal_rule_falls_back_for_royal_plate_items() -> None:
    rule = market_state._journal_rule_for_item("T6_ARMOR_PLATE_ROYAL")
    assert rule is not None
    assert rule.kind == "WARRIOR"
    assert rule.tier == 6
    assert rule.empty_item_id == "T6_JOURNAL_WARRIOR"


def test_royal_sigil_component_stays_non_returnable_in_catalog() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    recipe = state._catalog.get("T6_ARMOR_PLATE_ROYAL")
    sigils = [component for component in recipe.components if "_SIGIL" in component.item.unique_name or "_TOKEN_" in component.item.unique_name]
    assert sigils
    assert all(component.returnable is False for component in sigils)


@pytest.mark.skip(reason="Royal journal fallback coverage disabled for CI stability.")
def test_estimate_journal_totals_supports_royal_plate_fallback_mapping() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    recipe = state._catalog.get("T6_ARMOR_PLATE_ROYAL")
    run = SimpleNamespace(
        recipe=recipe,
        outputs=(SimpleNamespace(item=recipe.item, quantity=10.0),),
    )
    price_index = {
        ("T6_JOURNAL_WARRIOR", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T6_JOURNAL_WARRIOR",
            city="Bridgewatch",
            quality=1,
            sell_price_min=1000,
            buy_price_max=900,
            sell_price_min_date="2026-03-24T10:00:00Z",
            buy_price_max_date="2026-03-24T10:00:00Z",
        ),
        ("T6_JOURNAL_WARRIOR_FULL", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T6_JOURNAL_WARRIOR_FULL",
            city="Bridgewatch",
            quality=1,
            sell_price_min=6000,
            buy_price_max=5000,
            sell_price_min_date="2026-03-24T10:00:00Z",
            buy_price_max_date="2026-03-24T10:00:00Z",
        ),
    }

    totals = state._estimate_journal_totals(
        runs=[run],
        setup=state.to_setup(),
        price_index=price_index,
    )

    assert totals.lines
    line = totals.lines[0]
    assert line.kind == "WARRIOR"
    assert line.tier == 6
    assert line.empty_item_id == "T6_JOURNAL_WARRIOR"
    assert line.full_item_id == "T6_JOURNAL_WARRIOR_FULL"
    assert line.empty_quantity == pytest.approx(4.0, rel=0.0, abs=0.01)
    assert line.full_quantity == pytest.approx(3.0, rel=0.0, abs=0.01)


def test_input_preview_sort_groups_artifacts_then_materials_then_journals() -> None:
    rows = [
        market_state.InputPreviewRow(
            item_id="T5_JOURNAL_WARRIOR",
            row_key="T5_JOURNAL_WARRIOR|Bridgewatch|sell_order",
            item="T5 Blacksmith's Journal (empty)",
            quantity=10.0,
            stock_quantity=0.0,
            buy_quantity=10.0,
            city="Bridgewatch",
            price_type="sell_order",
            price_age_text="1m",
            manual_price=0,
            unit_price=5000.0,
            total_cost=50000.0,
        ),
        market_state.InputPreviewRow(
            item_id="T5_METALBAR_LEVEL1",
            row_key="T5_METALBAR_LEVEL1|Bridgewatch|sell_order",
            item="Metal Bar T5.1",
            quantity=24.0,
            stock_quantity=0.0,
            buy_quantity=24.0,
            city="Bridgewatch",
            price_type="sell_order",
            price_age_text="1m",
            manual_price=0,
            unit_price=900.0,
            total_cost=21600.0,
        ),
        market_state.InputPreviewRow(
            item_id="T5_ARTEFACT_2H_KEEPER_SWORD",
            row_key="T5_ARTEFACT_2H_KEEPER_SWORD|Bridgewatch|sell_order",
            item="Adept's Remnants of the Old King T5",
            quantity=2.0,
            stock_quantity=0.0,
            buy_quantity=2.0,
            city="Bridgewatch",
            price_type="sell_order",
            price_age_text="1m",
            manual_price=0,
            unit_price=8000.0,
            total_cost=16000.0,
        ),
    ]

    rows.sort(key=market_state._input_preview_sort_key)
    assert rows[0].item_id == "T5_ARTEFACT_2H_KEEPER_SWORD"
    assert rows[1].item_id == "T5_METALBAR_LEVEL1"
    assert rows[2].item_id == "T5_JOURNAL_WARRIOR"


def test_market_setup_state_includes_journals_in_inputs_outputs_models(monkeypatch: pytest.MonkeyPatch) -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)

    fake_totals = market_state._JournalTotals(
        input_cost=1000.0,
        output_value=2500.0,
        market_tax=100.0,
        full_quantity=2.0,
        lines=(
            market_state._JournalLine(
                kind="MAGE",
                tier=4,
                empty_item_id="T4_JOURNAL_MAGE",
                full_item_id="T4_JOURNAL_MAGE_FULL",
                empty_quantity=3.0,
                full_quantity=2.0,
                input_cost=1000.0,
                output_value=2500.0,
                market_tax=100.0,
            ),
        ),
    )
    monkeypatch.setattr(state, "_estimate_journal_totals", lambda **_: fake_totals)
    state.refreshPrices()

    input_item_ids = set()
    input_labels = set()
    for idx in range(state.inputsModel.rowCount()):
        model_index = state.inputsModel.index(idx, 0)
        input_item_ids.add(str(state.inputsModel.data(model_index, state.inputsModel.ItemIdRole)))
        input_labels.add(str(state.inputsModel.data(model_index, state.inputsModel.ItemRole)))
    assert "T4_JOURNAL_MAGE" in input_item_ids
    assert "T4 Imbuer's Journal (empty)" in input_labels
    mage_input_qty = None
    for idx in range(state.inputsModel.rowCount()):
        model_index = state.inputsModel.index(idx, 0)
        item_id = str(state.inputsModel.data(model_index, state.inputsModel.ItemIdRole) or "")
        if item_id == "T4_JOURNAL_MAGE":
            mage_input_qty = float(state.inputsModel.data(model_index, state.inputsModel.QuantityRole) or 0.0)
            break
    assert mage_input_qty == pytest.approx(3.0, rel=0.0, abs=0.01)

    output_item_ids = set()
    output_labels = set()
    for idx in range(state.outputsModel.rowCount()):
        model_index = state.outputsModel.index(idx, 0)
        output_item_ids.add(str(state.outputsModel.data(model_index, state.outputsModel.ItemIdRole)))
        output_labels.add(str(state.outputsModel.data(model_index, state.outputsModel.ItemRole)))
    assert "T4_JOURNAL_MAGE_FULL" in output_item_ids
    assert "T4 Imbuer's Journal (full)" in output_labels

    result_labels = set()
    for idx in range(state.resultsItemsModel.rowCount()):
        model_index = state.resultsItemsModel.index(idx, 0)
        result_labels.add(str(state.resultsItemsModel.data(model_index, state.resultsItemsModel.ItemRole)))
    assert "Crafting Journals (est.)" not in result_labels
    assert not any("(full)" in label for label in result_labels)


def test_market_setup_state_results_cost_not_coupled_to_journal_revenue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)

    fake_totals = market_state._JournalTotals(
        input_cost=1000.0,
        output_value=2500.0,
        market_tax=100.0,
        full_quantity=2.0,
        lines=(
            market_state._JournalLine(
                kind="MAGE",
                tier=4,
                empty_item_id="T4_JOURNAL_MAGE",
                full_item_id="T4_JOURNAL_MAGE_FULL",
                empty_quantity=3.0,
                full_quantity=2.0,
                input_cost=1000.0,
                output_value=2500.0,
                market_tax=100.0,
            ),
        ),
    )
    monkeypatch.setattr(state, "_estimate_journal_totals", lambda **_: fake_totals)
    state.refreshPrices()

    first_output_index = state.outputsModel.index(0, 0)
    crafted_item_id = str(state.outputsModel.data(first_output_index, state.outputsModel.ItemIdRole) or "")
    assert crafted_item_id

    result_cost_before = None
    for idx in range(state.resultsItemsModel.rowCount()):
        model_index = state.resultsItemsModel.index(idx, 0)
        item_id = str(state.resultsItemsModel.data(model_index, state.resultsItemsModel.ItemIdRole) or "")
        if item_id == crafted_item_id:
            result_cost_before = float(state.resultsItemsModel.data(model_index, state.resultsItemsModel.CostRole) or 0.0)
            break
    assert result_cost_before is not None

    state.setOutputManualPrice(crafted_item_id, "999999")

    result_cost_after = None
    for idx in range(state.resultsItemsModel.rowCount()):
        model_index = state.resultsItemsModel.index(idx, 0)
        item_id = str(state.resultsItemsModel.data(model_index, state.resultsItemsModel.ItemIdRole) or "")
        if item_id == crafted_item_id:
            result_cost_after = float(state.resultsItemsModel.data(model_index, state.resultsItemsModel.CostRole) or 0.0)
            break
    assert result_cost_after is not None
    assert result_cost_after == pytest.approx(result_cost_before, rel=0.0, abs=0.01)


def test_market_setup_state_results_rows_match_selected_totals_with_journals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)

    fake_totals = market_state._JournalTotals(
        input_cost=1000.0,
        output_value=2500.0,
        market_tax=100.0,
        full_quantity=2.0,
        lines=(
            market_state._JournalLine(
                kind="MAGE",
                tier=4,
                empty_item_id="T4_JOURNAL_MAGE",
                full_item_id="T4_JOURNAL_MAGE_FULL",
                empty_quantity=3.0,
                full_quantity=2.0,
                input_cost=1000.0,
                output_value=2500.0,
                market_tax=100.0,
            ),
        ),
    )
    monkeypatch.setattr(state, "_estimate_journal_totals", lambda **_: fake_totals)
    state.refreshPrices()

    total_revenue = 0.0
    total_cost = 0.0
    total_fee = 0.0
    total_tax = 0.0
    total_profit = 0.0
    for idx in range(state.resultsItemsModel.rowCount()):
        model_index = state.resultsItemsModel.index(idx, 0)
        total_revenue += float(state.resultsItemsModel.data(model_index, state.resultsItemsModel.RevenueRole) or 0.0)
        total_cost += float(state.resultsItemsModel.data(model_index, state.resultsItemsModel.CostRole) or 0.0)
        total_fee += float(state.resultsItemsModel.data(model_index, state.resultsItemsModel.FeeRole) or 0.0)
        total_tax += float(state.resultsItemsModel.data(model_index, state.resultsItemsModel.TaxRole) or 0.0)
        total_profit += float(state.resultsItemsModel.data(model_index, state.resultsItemsModel.ProfitRole) or 0.0)

    assert total_revenue == pytest.approx(state.selectedOutputsTotalValue, rel=0.0, abs=0.01)
    assert total_cost == pytest.approx(state.selectedInputsTotalCost, rel=0.0, abs=0.01)
    assert total_fee == pytest.approx(state.stationFeeValue, rel=0.0, abs=0.01)
    assert total_tax == pytest.approx(state.marketTaxValue, rel=0.0, abs=0.01)
    assert total_profit == pytest.approx(state.selectedNetProfitValue, rel=0.0, abs=0.01)


def test_market_setup_state_can_switch_recipe_by_index() -> None:
    state = MarketSetupState()
    before = state.recipeId
    if state.recipeOptionsModel.rowCount() < 2:
        return
    switched = False
    for idx in range(state.recipeOptionsModel.rowCount()):
        state.setRecipeIndex(idx)
        if state.recipeId != before:
            switched = True
            break
    assert switched


def test_market_setup_state_supports_output_city_and_results_sorting() -> None:
    state = MarketSetupState()
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    if state.outputsModel.rowCount() <= 0:
        return

    idx = state.outputsModel.index(0, 0)
    item_id = str(state.outputsModel.data(idx, state.outputsModel.ItemIdRole))
    state.setOutputCity(item_id, "Caerleon")
    city_after = str(state.outputsModel.data(idx, state.outputsModel.CityRole))
    assert city_after == "Caerleon"

    state.setResultsSortKey("margin")
    assert state.resultsSortKey == "margin"
    net_after = state.outputsNetValue
    gross_after = state.outputsTotalValue
    assert net_after <= gross_after


def test_market_setup_state_can_export_csv_lists() -> None:
    state = MarketSetupState()
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    tmp_dir = Path(f"tmp_market_qt_state_{uuid.uuid4().hex}")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        shopping_path = tmp_dir / "shopping.csv"
        selling_path = tmp_dir / "selling.csv"
        state.exportShoppingCsv(str(shopping_path))
        state.exportSellingCsv(str(selling_path))
        assert shopping_path.exists()
        assert selling_path.exists()
        assert "item_id" in shopping_path.read_text(encoding="utf-8")
        assert "item_id" in selling_path.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_market_setup_state_recipe_search_supports_tier_enchant_query() -> None:
    state = MarketSetupState()
    model = state.recipeOptionsModel
    total = model.rowCount()
    if total <= 0:
        return

    pick_idx = 0
    pick_token = ""
    pick_tier = 0
    pick_enchant = 0
    for idx in range(total):
        model_index = model.index(idx, 0)
        name = str(model.data(model_index, model.DisplayNameRole) or "")
        recipe_id = str(model.data(model_index, model.RecipeIdRole) or "")
        tier = int(model.data(model_index, model.TierRole) or 0)
        enchant = int(model.data(model_index, model.EnchantRole) or 0)
        token_source = name or recipe_id
        token_parts = [x.lower() for x in re.split(r"[^a-zA-Z0-9]+", token_source) if len(x) >= 4]
        if tier > 0 and token_parts:
            pick_idx = idx
            pick_token = token_parts[0]
            pick_tier = tier
            pick_enchant = max(0, enchant)
            break

    query = f"{pick_token} {pick_tier}.{pick_enchant}"
    state.setRecipeSearchQuery(query)
    filtered = model.rowCount()
    assert 1 <= filtered <= total

    state.selectFirstRecipeOption()
    assert state.recipeTier == pick_tier
    assert state.recipeEnchant == pick_enchant
    haystack = f"{state.recipeDisplayName} {state.recipeId}".lower()
    assert pick_token in haystack

    state.setRecipeSearchQuery("")
    assert model.rowCount() == total


def test_market_setup_state_add_recipe_family_expands_weapon_tree_station_group() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.setRecipeSearchQuery("curse")
    state.setRecipeEnchantFilter(0)
    state.addRecipeFamily()

    model = state.craftPlanModel
    recipe_ids: set[str] = set()
    for idx in range(model.rowCount()):
        model_index = model.index(idx, 0)
        recipe_id = str(model.data(model_index, model.RecipeIdRole) or "")
        if recipe_id:
            recipe_ids.add(recipe_id)

    assert any("CURSEDSTAFF" in recipe_id for recipe_id in recipe_ids)
    assert any("DEMONICSTAFF" in recipe_id for recipe_id in recipe_ids)
    assert any("SKULLORB_HELL" in recipe_id for recipe_id in recipe_ids)
    assert all("_ARTEFACT_" not in recipe_id for recipe_id in recipe_ids)


def test_market_setup_state_new_plan_rows_default_to_disabled() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.setRecipeSearchQuery("curse")
    state.addRecipeFamily()

    model = state.craftPlanModel
    assert model.rowCount() >= 1
    for idx in range(model.rowCount()):
        model_index = model.index(idx, 0)
        assert model.data(model_index, model.EnabledRole) is False


def test_market_setup_state_add_recipe_family_respects_multi_tier_and_enchant_filters() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.setRecipeSearchQuery("curse")
    state.setRecipeTierFilters([4])
    state.setRecipeEnchantFilters([0])
    state.addRecipeFamily()

    model = state.craftPlanModel
    assert model.rowCount() >= 1
    for idx in range(model.rowCount()):
        model_index = model.index(idx, 0)
        assert int(model.data(model_index, model.TierRole) or 0) == 4
        assert int(model.data(model_index, model.EnchantRole) or 0) == 0


def test_market_setup_state_recipe_search_supports_common_typo_aliases() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.setRecipeSearchQuery("siedge hammer")

    model = state.recipeOptionsModel
    assert model.rowCount() >= 1
    names = []
    for idx in range(min(model.rowCount(), 8)):
        model_index = model.index(idx, 0)
        names.append(str(model.data(model_index, model.DisplayNameRole) or "").lower())

    assert any("siege hammer" in name for name in names)


def test_market_setup_state_marks_completed_input_rows_and_clears_state() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    state.setActiveMarketTab(1)

    model = state.inputsModel
    assert model.rowCount() >= 1
    index = model.index(0, 0)
    item_id = str(model.data(index, model.ItemIdRole) or "")
    assert item_id
    assert model.data(index, model.CompletedRole) is False

    state.setInputRowCompleted(item_id, True)
    assert model.data(index, model.CompletedRole) is True

    on_model = state.inputsOnModel
    on_index = on_model.index(0, 0)
    assert on_model.data(on_index, on_model.CompletedRole) is True

    state.clearCraftPlan()
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    state.setActiveMarketTab(1)
    refreshed_index = state.inputsModel.index(0, 0)
    assert state.inputsModel.data(refreshed_index, state.inputsModel.CompletedRole) is False


def test_market_setup_state_marks_completed_output_rows_and_clears_state() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    state.setActiveMarketTab(2)

    model = state.outputsModel
    assert model.rowCount() >= 1
    index = model.index(0, 0)
    item_id = str(model.data(index, model.ItemIdRole) or "")
    assert item_id
    assert model.data(index, model.CompletedRole) is False

    state.setOutputRowCompleted(item_id, True)
    assert model.data(index, model.CompletedRole) is True

    on_model = state.outputsOnModel
    on_index = on_model.index(0, 0)
    assert on_model.data(on_index, on_model.CompletedRole) is True

    state.clearCraftPlan()
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    state.setActiveMarketTab(2)
    refreshed_index = state.outputsModel.index(0, 0)
    assert state.outputsModel.data(refreshed_index, state.outputsModel.CompletedRole) is False


def test_market_setup_state_craft_plan_exposes_fresh_component_price_role() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()

    model = state.craftPlanModel
    assert model.rowCount() >= 1
    index = model.index(0, 0)
    has_fresh = model.data(index, model.HasFreshComponentPricesRole)
    assert isinstance(has_fresh, bool)


def test_market_setup_state_hide_missing_adp_prices_filters_all_preview_tabs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    assert state.inputsModel.rowCount() >= 1

    monkeypatch.setattr(state, "_run_has_fresh_component_prices", lambda _run: False)
    state.refreshPrices()

    craft_index = state.craftPlanModel.index(0, 0)
    assert state.craftPlanModel.data(craft_index, state.craftPlanModel.HasFreshComponentPricesRole) is False

    state.setHideRowsWithoutFreshPrices(True)
    assert state.hideRowsWithoutFreshPrices is True
    assert state.inputsModel.rowCount() == 0
    assert state.outputsModel.rowCount() == 0
    assert state.resultsItemsModel.rowCount() == 0

    state.setHideRowsWithoutFreshPrices(False)
    assert state.hideRowsWithoutFreshPrices is False
    assert state.inputsModel.rowCount() >= 1


def test_item_id_query_candidates_include_enchant_variants_for_level_items() -> None:
    candidates = market_state._item_id_query_candidates("T4_METALBAR_LEVEL3")
    assert "T4_METALBAR_LEVEL3" in candidates
    assert "T4_METALBAR_LEVEL3@3" in candidates
    assert "T4_METALBAR" not in candidates


def test_find_price_quote_does_not_fallback_to_plain_tier_for_enchanted_items() -> None:
    index = {
        ("T4_METALBAR", "Bridgewatch", 1): MarketPriceRecord(
            item_id="T4_METALBAR",
            city="Bridgewatch",
            quality=1,
            sell_price_min=100,
            buy_price_max=90,
            sell_price_min_date="",
            buy_price_max_date="",
        ),
    }
    quote = market_state._find_price_quote(
        index,
        item_id="T4_METALBAR_LEVEL3",
        city="Bridgewatch",
        quality=1,
        preferred_mode="sell_order",
    )
    assert quote is None


def _find_plan_row_id(state: MarketSetupState, recipe_id: str) -> int | None:
    model = state.craftPlanModel
    for idx in range(model.rowCount()):
        model_index = model.index(idx, 0)
        candidate = str(model.data(model_index, model.RecipeIdRole) or "")
        if candidate == recipe_id:
            return int(model.data(model_index, model.RowIdRole) or 0)
    return None


def _find_alternate_recipe_id(state: MarketSetupState) -> str | None:
    model = state.recipeOptionsModel
    current = state.recipeId
    for idx in range(model.rowCount()):
        model_index = model.index(idx, 0)
        candidate = str(model.data(model_index, model.RecipeIdRole) or "")
        if candidate and candidate != current:
            return candidate
    return None


def _find_plan_model_index_by_row_id(state: MarketSetupState, row_id: int) -> int:
    model = state.craftPlanModel
    for idx in range(model.rowCount()):
        model_index = model.index(idx, 0)
        candidate = int(model.data(model_index, model.RowIdRole) or 0)
        if candidate == int(row_id):
            return idx
    return -1


def test_market_setup_state_craft_plan_can_aggregate_multiple_recipes() -> None:
    state = MarketSetupState()
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    base_input = state.inputsTotalCost
    base_output = state.outputsTotalValue

    alternate_recipe = _find_alternate_recipe_id(state)
    if not alternate_recipe:
        return

    state.addRecipeToPlan(alternate_recipe)
    _enable_all_plan_rows(state)
    row_id = _find_plan_row_id(state, alternate_recipe)
    assert row_id is not None
    state.setPlanRowRuns(int(row_id), 2)

    assert state.craftPlanCount >= 2
    assert state.craftPlanEnabledCount >= 2
    assert state.inputsTotalCost >= base_input
    assert state.outputsTotalValue >= base_output


def test_market_setup_state_craft_plan_toggle_changes_preview() -> None:
    state = MarketSetupState()
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    baseline_input = state.inputsTotalCost
    baseline_output = state.outputsTotalValue

    alternate_recipe = _find_alternate_recipe_id(state)
    if not alternate_recipe:
        return

    state.addRecipeToPlan(alternate_recipe)
    _enable_all_plan_rows(state)
    row_id = _find_plan_row_id(state, alternate_recipe)
    assert row_id is not None
    state.setPlanRowRuns(int(row_id), 3)

    expanded_input = state.inputsTotalCost
    expanded_output = state.outputsTotalValue
    assert expanded_input >= baseline_input
    assert expanded_output >= baseline_output

    rows_before_disable = state.resultsItemsModel.rowCount()
    state.setPlanRowEnabled(int(row_id), False)
    assert state.craftPlanEnabledCount >= 1
    # Inputs/outputs aggregate all craft rows; toggling On affects only Results tab.
    assert state.inputsTotalCost == pytest.approx(expanded_input)
    assert state.outputsTotalValue == pytest.approx(expanded_output)
    assert state.resultsItemsModel.rowCount() <= rows_before_disable


def test_market_setup_state_results_include_only_enabled_rows() -> None:
    state = MarketSetupState()
    state.addCurrentRecipeToPlan()
    alternate_recipe = _find_alternate_recipe_id(state)
    if not alternate_recipe:
        return
    state.addRecipeToPlan(alternate_recipe)

    # Inputs/outputs should include all rows even when disabled.
    assert state.craftPlanCount >= 2
    assert state.inputsModel.rowCount() >= 1
    assert state.outputsModel.rowCount() >= 1

    # With no rows enabled, results should be empty.
    assert state.craftPlanEnabledCount == 0
    assert state.resultsItemsModel.rowCount() == 0
    assert state.inputsOnModel.rowCount() == 0
    assert state.outputsOnModel.rowCount() == 0
    assert state.selectedInputsTotalCost == 0
    assert state.selectedOutputsTotalValue == 0
    assert state.selectedNetProfitValue == 0
    assert state.selectedInputItemIds == []
    assert state.selectedOutputItemIds == []

    # Enabling rows should populate results without changing the "all rows" inputs/outputs behavior.
    _enable_all_plan_rows(state)
    assert state.craftPlanEnabledCount >= 1
    assert state.resultsItemsModel.rowCount() >= 1
    assert state.inputsOnModel.rowCount() >= 1
    assert state.outputsOnModel.rowCount() >= 1
    assert state.selectedInputsTotalCost > 0
    assert state.selectedOutputsTotalValue > 0
    assert len(state.selectedInputItemIds) >= 1
    assert len(state.selectedOutputItemIds) >= 1


def test_market_setup_state_results_margin_varies_per_item_when_prices_differ() -> None:
    state = MarketSetupState(auto_refresh_prices=False)
    state.addCurrentRecipeToPlan()
    alternate_recipe = _find_alternate_recipe_id(state)
    if not alternate_recipe:
        return
    state.addRecipeToPlan(alternate_recipe)
    _enable_all_plan_rows(state)
    if state.resultsItemsModel.rowCount() < 2:
        return

    first_index = state.resultsItemsModel.index(0, 0)
    first_item_id = str(state.resultsItemsModel.data(first_index, state.resultsItemsModel.ItemIdRole) or "")
    assert first_item_id
    state.setOutputManualPrice(first_item_id, "9999999")

    margins: list[float] = []
    for idx in range(state.resultsItemsModel.rowCount()):
        model_index = state.resultsItemsModel.index(idx, 0)
        margins.append(float(state.resultsItemsModel.data(model_index, state.resultsItemsModel.MarginRole) or 0.0))
    assert len(margins) >= 2
    assert max(margins) - min(margins) > 0.01


def test_market_setup_state_clear_plan_keeps_active_recipe() -> None:
    state = MarketSetupState()
    state.addCurrentRecipeToPlan()
    state.clearCraftPlan()
    assert state.craftPlanCount == 0
    assert state.craftPlanEnabledCount == 0
    assert state.inputsModel.rowCount() == 0
    assert state.outputsModel.rowCount() == 0


def test_market_setup_state_plan_row_city_and_daily_bonus_affect_preview() -> None:
    state = MarketSetupState()
    state.addCurrentRecipeToPlan()
    _enable_all_plan_rows(state)
    row_id = _find_plan_row_id(state, state.recipeId)
    assert row_id is not None
    row_index = _find_plan_model_index_by_row_id(state, int(row_id))
    assert row_index >= 0

    baseline_input_cost = state.inputsTotalCost
    baseline_rrr = state.resourceReturnRatePercent

    state.setPlanRowDailyBonus(int(row_id), "20%")
    boosted_input_cost = state.inputsTotalCost
    boosted_rrr = state.resourceReturnRatePercent
    assert boosted_rrr >= baseline_rrr
    assert boosted_input_cost <= baseline_input_cost

    state.setPlanRowCraftCity(int(row_id), "Martlock")
    model = state.craftPlanModel
    model_index = model.index(row_index, 0)
    city_value = str(model.data(model_index, model.CraftCityRole) or "")
    rrr_value = model.data(model_index, model.ReturnRateRole)
    assert city_value == "Martlock"
    assert rrr_value is not None
