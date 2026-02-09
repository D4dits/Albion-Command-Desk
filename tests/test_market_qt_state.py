from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import MarketRegion
from albion_dps.market.service import MarketFetchMeta
from albion_dps.qt.market import MarketSetupState


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
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
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
    state.setStationFeePercent(150.0)
    state.setMarketTaxPercent(-5.0)
    state.setQuality(99)

    setup = state.to_setup()
    assert setup.region.value == "west"
    assert setup.station_fee_percent == 100.0
    assert setup.market_tax_percent == 0.0
    assert setup.quality == 6


def test_market_setup_state_builds_outputs_and_results() -> None:
    state = MarketSetupState()
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


def test_market_setup_state_uses_service_and_manual_overrides() -> None:
    service = _FakeMarketService()
    state = MarketSetupState(service=service, auto_refresh_prices=False)

    assert state.pricesSource == "live"
    assert service.calls >= 1

    default_output = state.outputsTotalValue
    state.setOutputPriceType("T4_MAIN_SWORD", "manual")
    state.setOutputManualPrice("T4_MAIN_SWORD", "22000")
    assert state.outputsTotalValue > default_output

    default_input = state.inputsTotalCost
    state.setInputPriceType("T4_METALBAR", "manual")
    state.setInputManualPrice("T4_METALBAR", "1")
    assert state.inputsTotalCost < default_input

    previous_calls = service.calls
    state.refreshPrices()
    assert service.calls > previous_calls


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
    if state.outputsModel.rowCount() <= 0:
        return

    idx = state.outputsModel.index(0, 0)
    item_id = str(state.outputsModel.data(idx, state.outputsModel.ItemIdRole))
    state.setOutputCity(item_id, "Caerleon")
    city_after = str(state.outputsModel.data(idx, state.outputsModel.CityRole))
    assert city_after == "Caerleon"

    state.setResultsSortKey("margin")
    assert state.resultsSortKey == "margin"


def test_market_setup_state_can_export_csv_lists() -> None:
    state = MarketSetupState()
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
