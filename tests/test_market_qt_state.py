from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from albion_dps.qt.market import MarketSetupState


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

