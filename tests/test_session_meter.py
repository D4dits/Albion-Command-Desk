from __future__ import annotations

from albion_dps.meter.session_meter import SessionMeter
from albion_dps.models import CombatEvent, RawPacket


def _packet(ts: float, ip: str = "1.1.1.1", port: int = 5056) -> RawPacket:
    return RawPacket(
        timestamp=ts,
        src_ip=ip,
        src_port=port,
        dst_ip="10.0.0.1",
        dst_port=50000,
        payload=b"",
    )


def test_battle_mode_archives_on_idle() -> None:
    meter = SessionMeter(battle_timeout_seconds=5.0, history_limit=5, mode="battle")

    meter.observe_packet(_packet(0.0))
    meter.push(CombatEvent(0.0, 1, 2, 100, "damage"))
    meter.observe_packet(_packet(6.0))

    history = meter.history()
    assert len(history) == 1
    assert history[0].total_damage == 100.0
    assert history[0].reason == "idle"


def test_manual_mode_toggle_creates_history() -> None:
    meter = SessionMeter(history_limit=5, mode="manual")
    meter.observe_packet(_packet(0.0))

    meter.push(CombatEvent(1.0, 1, 2, 50, "damage"))
    assert meter.snapshot().totals == {}

    meter.toggle_manual()
    meter.push(CombatEvent(2.0, 1, 2, 25, "damage"))
    meter.toggle_manual()

    history = meter.history()
    assert len(history) == 1
    assert history[0].total_damage == 25.0


def test_zone_mode_archives_on_zone_change() -> None:
    meter = SessionMeter(history_limit=5, mode="zone")
    meter.observe_packet(_packet(0.0, ip="1.1.1.1", port=5056))
    meter.push(CombatEvent(1.0, 1, 2, 10, "damage"))
    meter.observe_packet(_packet(5.0, ip="2.2.2.2", port=5056))

    history = meter.history()
    assert len(history) == 1
    assert history[0].label == "1.1.1.1:5056"


def test_battle_mode_ignores_zone_change() -> None:
    meter = SessionMeter(history_limit=5, mode="battle")
    meter.observe_packet(_packet(0.0, ip="1.1.1.1", port=5056))
    meter.push(CombatEvent(1.0, 1, 2, 10, "damage"))
    meter.observe_packet(_packet(5.0, ip="2.2.2.2", port=5056))

    history = meter.history()
    assert len(history) == 0


def test_battle_mode_archives_on_combat_state_end() -> None:
    meter = SessionMeter(history_limit=5, mode="battle")
    meter.observe_combat_state(1, True, False, 0.0)
    meter.push(CombatEvent(1.0, 1, 2, 10, "damage"))
    meter.observe_combat_state(1, False, False, 2.0)
    meter.observe_packet(_packet(3.5))

    history = meter.history()
    assert len(history) == 1
    assert history[0].reason == "combat_state"


def test_battle_mode_archives_on_combat_state_end_same_tick() -> None:
    meter = SessionMeter(history_limit=5, mode="battle")
    meter.observe_combat_state(1, True, False, 0.0)
    meter.push(CombatEvent(1.0, 1, 2, 10, "damage"))
    meter.observe_combat_state(1, False, False, 2.0)
    meter.observe_packet(_packet(2.3))

    history = meter.history()
    assert len(history) == 1
    assert history[0].reason == "combat_state"


def test_battle_mode_combat_state_end_uses_combat_timestamp() -> None:
    meter = SessionMeter(history_limit=5, mode="battle")
    meter.push(CombatEvent(1.0, 1, 2, 10, "damage"))
    meter.observe_combat_state(1, True, False, 1.5)
    meter.observe_combat_state(1, False, False, 2.0)
    meter.observe_packet(_packet(10.0))

    history = meter.history()
    assert len(history) == 1
    assert history[0].end_ts == 2.0


def test_combat_state_ignored_until_source_seen() -> None:
    meter = SessionMeter(history_limit=5, mode="battle")
    meter.observe_combat_state(99, True, False, 0.0)
    meter.observe_packet(_packet(1.0))

    assert meter.history() == []

    meter.push(CombatEvent(2.0, 1, 2, 10, "damage"))
    meter.observe_combat_state(99, False, False, 3.0)
    meter.observe_packet(_packet(3.0))

    assert meter.history() == []

def test_battle_mode_merges_short_gaps() -> None:
    meter = SessionMeter(battle_timeout_seconds=1.0, history_limit=5, mode="battle")

    meter.observe_packet(_packet(0.0))
    meter.push(CombatEvent(0.0, 1, 2, 10, "damage"))
    meter.observe_packet(_packet(2.0))

    meter.push(CombatEvent(2.5, 1, 2, 5, "damage"))
    meter.observe_packet(_packet(4.0))

    history = meter.history()
    assert len(history) == 1
    assert history[0].total_damage == 15.0


def test_history_preserves_source_ids_for_replay_view() -> None:
    meter = SessionMeter(history_limit=5, mode="battle")
    meter.push(CombatEvent(0.0, 111, 2, 100, "damage"))
    meter.push(CombatEvent(0.5, 222, 2, 40, "damage"))
    meter.observe_packet(_packet(30.0))

    history = meter.history()
    assert len(history) == 1
    summary = history[0]
    assert 111 in summary.totals_by_id
    assert 222 in summary.totals_by_id
    assert any(entry.source_id == 111 for entry in summary.entries)
    assert any(entry.source_id == 222 for entry in summary.entries)
