from __future__ import annotations

import queue
import threading

import pytest

pytest.importorskip("PySide6")

from albion_dps.domain.fame_tracker import FameTracker
from albion_dps.domain.loot_types import LootEvent, LootItemRef, LootPlayer
from albion_dps.domain.map_resolver import MapResolver
from albion_dps.domain.name_registry import NameRegistry
from albion_dps.domain.party_registry import PartyRegistry
from albion_dps.domain.session_activity import MapTrailTracker
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.models import MeterSnapshot
from albion_dps.qt.loot_state import LootState
from albion_dps.qt.models import UiState
from albion_dps.qt.runner import _drain_snapshots


class _FakeLootTracker:
    def __init__(self, events: list[LootEvent]) -> None:
        self._events = list(events)

    def events(self, limit: int | None = None) -> list[LootEvent]:
        if limit is None:
            return list(self._events)
        return list(self._events[:limit])


def _sample_events() -> list[LootEvent]:
    return [
        LootEvent(
            timestamp=3661.0,
            looted_by=LootPlayer(player_name="Alice", guild_name="Guild A", alliance_name="AAA"),
            looted_from=LootPlayer(player_name="Enemy", guild_name="Guild E", alliance_name="EEE"),
            source_name="Enemy",
            source_kind="player",
            item=LootItemRef(item_num_id=3130, unique_name="T3_BAG", display_name="Journeyman's Bag"),
            quantity=2,
            is_silver=False,
            raw_event_code=1,
            raw_subtype=275,
        ),
        LootEvent(
            timestamp=3660.0,
            looted_by=LootPlayer(player_name="Bob"),
            looted_from=None,
            source_name="@MOB_KEEPER_DRUID_CHAMPION",
            source_kind="mob",
            item=LootItemRef(item_num_id=562, unique_name="T4_POTION", display_name="Adept's Potion"),
            quantity=1,
            is_silver=False,
            raw_event_code=1,
            raw_subtype=275,
        ),
    ]


def test_loot_state_builds_model_and_export_text() -> None:
    state = LootState(history_limit=10)
    tracker = _FakeLootTracker(_sample_events())

    state.update_from_tracker(tracker)

    assert state.eventCount == 2
    assert state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"
    model = state.eventsModel
    assert model.rowCount() == 2
    first = model.index(0, 0)
    assert model.data(first, model.TimestampRole) == "01:01:01"
    assert model.data(first, model.LootedByNameRole) == "Alice"
    assert model.data(first, model.ItemNameRole) == "Journeyman's Bag"
    assert model.data(first, model.SourceKindRole) == "player"
    assert "timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name" in state.exportText
    assert "1970-01-01T01:01:00.000Z;;;Bob;T4_POTION;Adept's Potion;1;;;@MOB_KEEPER_DRUID_CHAMPION" in state.exportText


def test_runner_drain_snapshots_updates_loot_state() -> None:
    snapshot_queue: queue.Queue[MeterSnapshot | None] = queue.Queue()
    snapshot_queue.put(MeterSnapshot(timestamp=10.0, totals={}, names={}))
    ui_state = UiState(sort_key="dps", top_n=5, history_limit=5)
    loot_state = LootState(history_limit=5)
    tracker = _FakeLootTracker(_sample_events()[:1])
    meter = SessionMeter(history_limit=5)
    meter.map_lookup = MapResolver().name_for_index
    stop_event = threading.Event()

    _drain_snapshots(
        snapshot_queue,
        ui_state,
        meter=meter,
        party=PartyRegistry(),
        name_registry=NameRegistry(),
        fame=FameTracker(),
        map_trail=MapTrailTracker(),
        loot_tracker=tracker,
        loot_state=loot_state,
        stop_event=stop_event,
    )

    assert loot_state.eventCount == 1
    assert loot_state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"
