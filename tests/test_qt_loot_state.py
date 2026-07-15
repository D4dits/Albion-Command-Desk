from __future__ import annotations

import queue
import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from albion_dps.domain.fame_tracker import FameTracker
from albion_dps.domain.loot_types import LootEvent, LootItemRef, LootPlayer
from albion_dps.domain.loot_session_store import LootSessionStore
from albion_dps.domain.map_resolver import MapResolver
from albion_dps.domain.name_registry import NameRegistry
from albion_dps.domain.party_registry import PartyRegistry
from albion_dps.domain.session_activity import MapTrailTracker
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.models import MeterSnapshot
from albion_dps.qt.loot_state import LootState, _item_category, _loot_icon_url
from albion_dps.qt.models import UiState
from albion_dps.qt.runner import _drain_snapshots
from tests.support_temp import mk_test_dir


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


def _sample_events_with_silver() -> list[LootEvent]:
    return _sample_events() + [
        LootEvent(
            timestamp=3659.0,
            looted_by=LootPlayer(player_name="Alice", guild_name="Guild A", alliance_name="AAA"),
            looted_from=None,
            source_name=None,
            source_kind="silver",
            item=LootItemRef(item_num_id=None, unique_name="SILVER", display_name="Silver"),
            quantity=1500,
            is_silver=True,
            raw_event_code=1,
            raw_subtype=275,
        ),
    ]


def test_loot_state_builds_model_and_export_text() -> None:
    state = LootState(history_limit=10)
    tracker = _FakeLootTracker(_sample_events())

    state.update_from_tracker(tracker)

    assert state.eventCount == 2
    assert state.totalQuantity == 3
    assert state.uniqueLooters == 2
    assert state.uniqueItems == 2
    assert state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"
    model = state.eventsModel
    assert model.rowCount() == 2
    first = model.index(0, 0)
    assert model.data(first, model.TimestampRole) == "01:01:01"
    assert model.data(first, model.LootedByNameRole) == "Alice"
    assert model.data(first, model.ItemNameRole) == "Journeyman's Bag"
    assert model.data(first, model.IconUrlRole).endswith("/T3_BAG?size=64")
    assert model.data(first, model.CategoryRole) == "bag"
    assert model.data(first, model.SourceKindRole) == "player"
    assert "timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name" in state.exportText
    assert "1970-01-01T01:01:00.000Z;;;Bob;T4_POTION;Adept's Potion;1;;;@MOB_KEEPER_DRUID_CHAMPION" in state.exportText
    looters = state.topLootersModel
    assert looters.rowCount() == 2
    top_looter = looters.index(0, 0)
    assert looters.data(top_looter, looters.LabelRole) == "Alice"
    items = state.topItemsModel
    assert items.rowCount() == 2
    first_item = items.index(0, 0)
    assert items.data(first_item, items.LabelRole) == "Journeyman's Bag"
    assert items.data(first_item, items.SublabelRole) == "T3_BAG"
    sources = state.topSourcesModel
    assert sources.rowCount() == 1
    source = sources.index(0, 0)
    assert sources.data(source, sources.LabelRole) == "Enemy"
    assert sources.data(source, sources.SublabelRole) == ""


def test_loot_state_moves_buffered_event_into_session_without_duplicates(tmp_path) -> None:
    store = LootSessionStore(tmp_path / "loot-sessions.sqlite3")
    try:
        event = LootEvent(
            timestamp=time.time() - 5,
            looted_by=LootPlayer(player_name="Alice", guild_name="Guild A"),
            looted_from=None,
            source_name="@MOB_KEEPER",
            source_kind="mob",
            item=LootItemRef(
                item_num_id=3130,
                unique_name="T3_BAG",
                display_name="Journeyman's Bag",
            ),
            quantity=1,
            is_silver=False,
            raw_event_code=1,
            raw_subtype=275,
            event_id="run-1:1",
            eligibility_reason="party",
        )
        tracker = _FakeLootTracker([event])
        state = LootState(history_limit=10, session_store=store)

        state.update_from_tracker(tracker)
        state.update_from_tracker(tracker)

        assert state.eventCount == 1
        assert state.startSession("Dungeon") is True
        assert state.sessionActive is True
        assert state.eventCount == 1
        assert len(store.loot_rows(session_id=state.selectedSessionId)) == 1
    finally:
        store.close()


def test_loot_state_skips_missing_renderer_icons_for_trash_items() -> None:
    assert _loot_icon_url("T5_TRASH") == ""
    assert _loot_icon_url("T6_TRASH") == ""
    assert _loot_icon_url("T3_BAG").endswith("/T3_BAG?size=64")


def test_loot_state_filters_and_rebuilds_aggregates() -> None:
    state = LootState(history_limit=10)
    tracker = _FakeLootTracker(_sample_events())

    state.update_from_tracker(tracker)
    state.setSearchQuery("potion")

    assert state.eventCount == 1
    assert state.totalQuantity == 1
    assert state.uniqueLooters == 1
    assert state.uniqueItems == 1
    assert state.latestLootSummary == "Bob looted 1x Adept's Potion from @MOB_KEEPER_DRUID_CHAMPION"
    assert "Adept's Potion" in state.exportText
    assert "Journeyman's Bag" not in state.exportText

    state.setSearchQuery("")
    state.setSourceFilter("player")
    assert state.eventCount == 1
    assert state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"

    state.setSourceNameFilter("Enemy")
    assert state.sourceNameFilter == "Enemy"
    assert state.sourceFilter == "player"
    assert state.eventCount == 1
    assert state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"

    state.setSourceNameFilter("")
    assert state.sourceNameFilter == ""

    state.setSourceFilter("mob")
    assert state.eventCount == 1
    assert state.latestLootSummary == "Bob looted 1x Adept's Potion from @MOB_KEEPER_DRUID_CHAMPION"

    state.setSourceFilter("all")
    state.setLooterFilter("Alice")
    assert state.eventCount == 1
    assert state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"

    state.setLooterFilter("all")
    state.setCategoryFilter("consumable")
    assert state.eventCount == 1
    assert state.latestLootSummary == "Bob looted 1x Adept's Potion from @MOB_KEEPER_DRUID_CHAMPION"


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
        loot_writer=None,
        loot_state=loot_state,
        stop_event=stop_event,
    )

    assert loot_state.eventCount == 1
    assert loot_state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"


def test_loot_state_copy_and_export_actions(monkeypatch) -> None:
    state = LootState(history_limit=10)
    tracker = _FakeLootTracker(_sample_events())
    state.update_from_tracker(tracker)

    copied: list[str] = []
    monkeypatch.setattr(state, "_copy_to_clipboard", lambda value: copied.append(value) or True)

    assert state.copyLatestSummary() is True
    assert copied[0] == "Alice looted 2x Journeyman's Bag from Enemy"
    assert state.copyCurrentView() is True
    assert "timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name" in copied[1]

    tmp_dir = mk_test_dir("loot_state_export")
    export_path = tmp_dir / "loot-view.txt"
    monkeypatch.setattr(state, "_prompt_export_path", lambda **_kwargs: str(export_path))

    written = state.exportCurrentViewInteractive()
    assert written == str(export_path)
    payload = export_path.read_text(encoding="utf-8")
    assert "Journeyman's Bag" in payload
    assert "Adept's Potion" in payload


def test_loot_state_keeps_loot_view_item_only() -> None:
    state = LootState(history_limit=10)
    tracker = _FakeLootTracker(_sample_events_with_silver())

    state.update_from_tracker(tracker)

    assert state.eventCount == 2
    assert state.itemEventCount == 2
    assert state.itemTotalQuantity == 3
    assert state.silverEventCount == 0
    assert state.silverTotalQuantity == 0
    assert state.kindFilter == "items"
    assert state.kindFilterOptions == ["items"]
    assert state.sourceFilterOptions == ["all", "player", "mob", "system"]
    assert state.looterFilterOptions == ["all", "Alice", "Bob"]
    assert state.topSilverLootersModel.rowCount() == 0
    assert "SILVER;Silver;1500" not in state.exportText

    state.setKindFilter("silver")

    assert state.eventCount == 2
    assert state.totalQuantity == 3
    assert state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"


def test_loot_state_classifies_armor_before_material_tokens() -> None:
    assert _item_category("T6_SHOES_LEATHER_SET3@3") == "armor"
    assert _item_category("T4_ARMOR_LEATHER_SET3@4") == "armor"
    assert _item_category("T5_HEAD_LEATHER_SET3@2") == "armor"
    assert _item_category("T4_LEATHER") == "resource"


def test_loot_state_can_import_log_and_return_to_live(monkeypatch) -> None:
    state = LootState(history_limit=10)
    live_tracker = _FakeLootTracker(_sample_events())
    state.update_from_tracker(live_tracker)

    tmp_dir = mk_test_dir("loot_state_import")
    import_path = tmp_dir / "loot-events-import.txt"
    import_path.write_text(
        "timestamp_utc;looted_by__alliance;looted_by__guild;looted_by__name;item_id;item_name;quantity;looted_from__alliance;looted_from__guild;looted_from__name\n"
        "1970-01-01T01:02:03.000Z;;;Carol;SILVER;Silver;900;;;\n"
        "1970-01-01T01:02:04.000Z;;;Carol;T4_POTION;Adept's Potion;1;;;@MOB_KEEPER_DRUID_CHAMPION\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(state, "_prompt_import_path", lambda **_kwargs: str(import_path))

    imported = state.importLogInteractive()

    assert imported == str(import_path.resolve())
    assert state.importedLogActive is True
    assert state.eventCount == 1
    assert state.silverEventCount == 0
    assert state.latestLootSummary == "Carol looted 1x Adept's Potion from @MOB_KEEPER_DRUID_CHAMPION"
    assert "SILVER;Silver;900" not in state.exportText

    state.useLiveLog()

    assert state.importedLogActive is False
    assert state.eventCount == 2
    assert state.latestLootSummary == "Alice looted 2x Journeyman's Bag from Enemy"
