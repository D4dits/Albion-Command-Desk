from __future__ import annotations

import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import MarketRegion
from albion_dps.market.service import MarketFetchMeta
from albion_dps.qt.market import MarketSetupState
from albion_dps.qt.market import state as market_state


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
    assert service.calls == 0

    # Entering Inputs/Outputs/Results should enable live fetch.
    state.setActiveMarketTab(1)
    assert service.calls >= 1
    assert state.pricesSource == "live"


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
    assert age_buy != "n/a"

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
    assert market_state._need_quantity_with_safety_buffer(125.0, True) == 128
    assert market_state._need_quantity_with_safety_buffer(63.0, True) == 65
    assert market_state._need_quantity_with_safety_buffer(10.0, False) == 10


def test_journal_rule_mapping_and_factor_for_crafting_item() -> None:
    journal_by_item, fame_factor_by_item = market_state._journal_maps()
    assert journal_by_item

    sample_item_id, sample_rule = next(iter(journal_by_item.items()))
    mapped_rule = market_state._journal_rule_for_item(f"{sample_item_id}@2")
    assert mapped_rule is not None
    assert mapped_rule == sample_rule
    assert mapped_rule.max_fame > 0
    assert mapped_rule.fame_per_item > 0

    if fame_factor_by_item:
        factor_item_id, expected_factor = next(iter(fame_factor_by_item.items()))
        factor = market_state._journal_fame_factor_for_item(f"{factor_item_id}@2")
        assert factor == pytest.approx(float(expected_factor))


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
    base_input = state.inputsTotalCost
    base_output = state.outputsTotalValue

    alternate_recipe = _find_alternate_recipe_id(state)
    if not alternate_recipe:
        return

    state.addRecipeToPlan(alternate_recipe)
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
    baseline_input = state.inputsTotalCost
    baseline_output = state.outputsTotalValue

    alternate_recipe = _find_alternate_recipe_id(state)
    if not alternate_recipe:
        return

    state.addRecipeToPlan(alternate_recipe)
    row_id = _find_plan_row_id(state, alternate_recipe)
    assert row_id is not None
    state.setPlanRowRuns(int(row_id), 3)

    expanded_input = state.inputsTotalCost
    expanded_output = state.outputsTotalValue
    assert expanded_input >= baseline_input
    assert expanded_output >= baseline_output

    state.setPlanRowEnabled(int(row_id), False)
    assert state.craftPlanEnabledCount >= 1
    assert state.inputsTotalCost == pytest.approx(baseline_input)
    assert state.outputsTotalValue == pytest.approx(baseline_output)


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
