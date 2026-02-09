from __future__ import annotations

from albion_dps.market.models import CraftSetup


def validate_setup(setup: CraftSetup) -> list[str]:
    errors: list[str] = []
    if setup.quality < 1 or setup.quality > 6:
        errors.append("quality must be in range 1..6")
    if setup.station_fee_percent < 0 or setup.station_fee_percent > 100:
        errors.append("station_fee_percent must be in range 0..100")
    if setup.market_tax_percent < 0 or setup.market_tax_percent > 100:
        errors.append("market_tax_percent must be in range 0..100")
    if setup.daily_bonus_percent < 0 or setup.daily_bonus_percent > 100:
        errors.append("daily_bonus_percent must be in range 0..100")
    if setup.return_rate_percent < 0 or setup.return_rate_percent > 95:
        errors.append("return_rate_percent must be in range 0..95")
    if setup.hideout_power_percent < 0 or setup.hideout_power_percent > 100:
        errors.append("hideout_power_percent must be in range 0..100")
    return errors


def sanitized_setup(setup: CraftSetup) -> CraftSetup:
    def clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    return CraftSetup(
        region=setup.region,
        craft_city=setup.craft_city.strip(),
        default_buy_city=setup.default_buy_city.strip(),
        default_sell_city=setup.default_sell_city.strip(),
        premium=bool(setup.premium),
        station_fee_percent=clamp(setup.station_fee_percent, 0.0, 100.0),
        market_tax_percent=clamp(setup.market_tax_percent, 0.0, 100.0),
        daily_bonus_percent=clamp(setup.daily_bonus_percent, 0.0, 100.0),
        return_rate_percent=clamp(setup.return_rate_percent, 0.0, 95.0),
        hideout_power_percent=clamp(setup.hideout_power_percent, 0.0, 100.0),
        quality=max(1, min(6, int(setup.quality))),
    )

