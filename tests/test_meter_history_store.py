from __future__ import annotations

from albion_dps.meter.history_store import MeterHistoryStore
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.models import CombatEvent, RawPacket
from tests.support_temp import mk_test_dir


def _packet(timestamp: float) -> RawPacket:
    return RawPacket(timestamp, "1.1.1.1", 5056, "10.0.0.1", 50000, b"")


def test_completed_encounter_survives_meter_restart() -> None:
    path = mk_test_dir("meter_history_store") / "history.sqlite3"
    store = MeterHistoryStore(path)
    meter = SessionMeter(
        battle_timeout_seconds=1.0,
        history_limit=20,
        history_store=store,
        source="live",
        name_lookup=lambda entity_id: "D4dits" if entity_id == 1 else None,
    )
    meter.push(CombatEvent(10.0, 1, 2, 100, "damage"))
    meter.observe_packet(_packet(12.0))
    encounter_id = meter.history()[0].encounter_id
    store.close()

    reopened = MeterHistoryStore(path)
    restored = SessionMeter(history_limit=20, history_store=reopened)

    assert restored.history()[0].encounter_id == encounter_id
    assert restored.history()[0].entries[0].label == "D4dits"
    reopened.close()


def test_replay_encounters_are_deduplicated_by_capture_fingerprint() -> None:
    path = mk_test_dir("meter_history_replay_dedup") / "history.sqlite3"
    store = MeterHistoryStore(path)
    for _ in range(2):
        meter = SessionMeter(
            battle_timeout_seconds=1.0,
            history_limit=20,
            history_store=store,
            source="replay",
            source_reference="fight.pcapng",
        )
        meter.push(CombatEvent(10.0, 1, 2, 100, "damage"))
        meter.observe_packet(_packet(12.0))

    assert len(store.load("battle", 20)) == 1
    store.close()
