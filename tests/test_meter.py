from __future__ import annotations

from albion_dps.meter.aggregate import RollingMeter
from albion_dps.models import CombatEvent


def test_meter_totals_and_dps() -> None:
    meter = RollingMeter(window_seconds=10.0)
    events = [
        CombatEvent(0.0, 1, 2, 100, "damage"),
        CombatEvent(5.0, 1, 2, 50, "damage"),
        CombatEvent(5.0, 2, 1, 20, "damage"),
        CombatEvent(11.0, 1, 2, 25, "damage"),
        CombatEvent(12.0, 1, 1, 40, "heal"),
    ]

    for event in events:
        meter.push(event)

    snapshot = meter.snapshot()

    assert snapshot.totals[1]["damage"] == 175.0
    assert snapshot.totals[1]["heal"] == 40.0
    assert abs(snapshot.totals[1]["dps"] - 7.5) < 1e-6
    assert abs(snapshot.totals[1]["hps"] - 4.0) < 1e-6

    assert snapshot.totals[2]["damage"] == 20.0
    assert snapshot.totals[2]["heal"] == 0.0
    assert abs(snapshot.totals[2]["dps"] - 2.0) < 1e-6
    assert abs(snapshot.totals[2]["hps"] - 0.0) < 1e-6


def test_meter_session_reset_after_idle() -> None:
    meter = RollingMeter(window_seconds=10.0, session_timeout_seconds=5.0)
    meter.push(CombatEvent(0.0, 1, 2, 100, "damage"))
    meter.push(CombatEvent(2.0, 1, 2, 50, "damage"))

    meter.push(CombatEvent(10.0, 1, 2, 25, "damage"))
    snapshot = meter.snapshot()

    assert snapshot.totals[1]["damage"] == 25.0
    assert abs(snapshot.totals[1]["dps"] - 2.5) < 1e-6
    assert abs(snapshot.totals[1]["hps"] - 0.0) < 1e-6


def test_meter_touch_expires_dps_window() -> None:
    meter = RollingMeter(window_seconds=10.0, session_timeout_seconds=None)
    meter.push(CombatEvent(0.0, 1, 2, 100, "damage"))

    meter.touch(11.0)
    snapshot = meter.snapshot()

    assert snapshot.totals[1]["damage"] == 100.0
    assert abs(snapshot.totals[1]["dps"] - 0.0) < 1e-6
    assert abs(snapshot.totals[1]["hps"] - 0.0) < 1e-6
