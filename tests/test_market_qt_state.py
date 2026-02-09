from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import MarketRegion
from albion_dps.qt.market import MarketSetupState


class _FakeMarketService:
    def __init__(self) -> None:
        self.calls = 0

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


def test_market_setup_state_uses_service_and_manual_overrides() -> None:
    service = _FakeMarketService()
    state = MarketSetupState(service=service, auto_refresh_prices=False)

    assert state.pricesSource == "ao_data"
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
