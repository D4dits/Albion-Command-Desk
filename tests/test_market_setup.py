from __future__ import annotations

from albion_dps.market.models import CraftSetup, MarketRegion
from albion_dps.market.setup import sanitized_setup, validate_setup


def test_validate_setup_reports_invalid_ranges() -> None:
    setup = CraftSetup(
        region=MarketRegion.EUROPE,
        station_fee_percent=120.0,
        market_tax_percent=-1.0,
        daily_bonus_percent=150.0,
        return_rate_percent=99.0,
        hideout_power_percent=101.0,
        quality=9,
    )
    errors = validate_setup(setup)
    assert len(errors) >= 5
    assert any("quality" in e for e in errors)
    assert any("station_fee_percent" in e for e in errors)


def test_sanitized_setup_clamps_values() -> None:
    setup = CraftSetup(
        region=MarketRegion.WEST,
        craft_city="  Bridgewatch ",
        default_buy_city="  Thetford ",
        default_sell_city="  Martlock ",
        station_fee_percent=150.0,
        market_tax_percent=-5.0,
        daily_bonus_percent=130.0,
        return_rate_percent=99.0,
        hideout_power_percent=120.0,
        quality=0,
    )
    out = sanitized_setup(setup)
    assert out.region == MarketRegion.WEST
    assert out.craft_city == "Bridgewatch"
    assert out.default_buy_city == "Thetford"
    assert out.default_sell_city == "Martlock"
    assert out.station_fee_percent == 100.0
    assert out.market_tax_percent == 0.0
    assert out.daily_bonus_percent == 100.0
    assert out.return_rate_percent == 95.0
    assert out.hideout_power_percent == 100.0
    assert out.quality == 1

