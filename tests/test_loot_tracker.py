from __future__ import annotations

from types import SimpleNamespace

import albion_dps.domain.loot_tracker as loot_tracker_module

from albion_dps.domain.item_resolver import ItemResolver
from albion_dps.domain.party_registry import PartyRegistry
from albion_dps.domain.loot_tracker import (
    EV_ATTACH_ITEM_CONTAINER,
    EV_CHARACTER_STATS,
    EV_DETACH_ITEM_CONTAINER,
    EV_NEW_CHARACTER,
    EV_NEW_LOOT,
    EV_NEW_SIMPLE_ITEM,
    EV_OTHER_GRABBED_LOOT,
    LootTracker,
    OP_INVENTORY_MOVE_ITEM,
)
from albion_dps.models import PhotonMessage, RawPacket


def _message(*, event_code: int | None = 1) -> PhotonMessage:
    return PhotonMessage(opcode=1, event_code=event_code, payload=b"\x00")


def _packet(timestamp: float = 0.0) -> RawPacket:
    return RawPacket(
        timestamp=timestamp,
        src_ip="127.0.0.1",
        src_port=5055,
        dst_ip="127.0.0.1",
        dst_port=50000,
        payload=b"\x00",
    )


def _set_event(monkeypatch, *, subtype: int, parameters: dict[int, object], code: int = 1) -> None:
    monkeypatch.setattr(
        loot_tracker_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(code=code, parameters={252: subtype, **parameters}),
    )


def test_loot_tracker_tracks_player_metadata_from_character_events(monkeypatch) -> None:
    tracker = LootTracker()

    _set_event(
        monkeypatch,
        subtype=EV_NEW_CHARACTER,
        parameters={1: "Alice", 8: "Guild A", 51: "Alliance A"},
    )
    tracker.observe(_message())

    _set_event(
        monkeypatch,
        subtype=EV_CHARACTER_STATS,
        parameters={1: "Alice", 2: "Guild B", 4: "Alliance B"},
    )
    tracker.observe(_message())

    player = tracker.player("Alice")
    assert player is not None
    assert player.guild_name == "Guild B"
    assert player.alliance_name == "Alliance B"


def test_loot_tracker_records_loot_event_with_resolved_item(monkeypatch) -> None:
    tracker = LootTracker(
        item_resolver=ItemResolver(
            index_to_unique={12345: "T4_MAIN_SWORD"},
            index_to_name={12345: "Adept's Broadsword"},
        )
    )

    _set_event(
        monkeypatch,
        subtype=EV_OTHER_GRABBED_LOOT,
        parameters={1: "Enemy", 2: "Alice", 3: False, 4: 12345, 5: 2},
    )
    tracker.observe(_message(), _packet(12.5))

    events = tracker.events()
    assert len(events) == 1
    event = events[0]
    assert event.timestamp == 12.5
    assert event.looted_by.player_name == "Alice"
    assert event.looted_from is not None
    assert event.looted_from.player_name == "Enemy"
    assert event.source_kind == "player"
    assert event.source_name == "Enemy"
    assert event.item is not None
    assert event.item.unique_name == "T4_MAIN_SWORD"
    assert event.item.display_name == "Adept's Broadsword"
    assert event.quantity == 2
    assert event.is_silver is False


def test_loot_tracker_ignores_silver_by_default(monkeypatch) -> None:
    tracker = LootTracker()

    _set_event(
        monkeypatch,
        subtype=EV_OTHER_GRABBED_LOOT,
        parameters={1: "Enemy", 2: "Alice", 3: True, 5: 1500},
    )
    tracker.observe(_message(), _packet(1.0))

    assert tracker.events() == []


def test_loot_tracker_can_include_silver(monkeypatch) -> None:
    tracker = LootTracker(include_silver=True)

    _set_event(
        monkeypatch,
        subtype=EV_OTHER_GRABBED_LOOT,
        parameters={1: "Enemy", 2: "Alice", 3: True, 5: 1500},
    )
    tracker.observe(_message(), _packet(1.0))

    events = tracker.events()
    assert len(events) == 1
    assert events[0].is_silver is True
    assert events[0].item is not None
    assert events[0].item.unique_name == "SILVER"
    assert events[0].looted_from is None
    assert events[0].source_kind == "silver"
    assert events[0].source_name is None


def test_loot_tracker_marks_mob_source_without_creating_fake_player(monkeypatch) -> None:
    tracker = LootTracker(
        item_resolver=ItemResolver(
            index_to_unique={3130: "T3_BAG"},
            index_to_name={3130: "Journeyman's Bag"},
        )
    )

    _set_event(
        monkeypatch,
        subtype=EV_OTHER_GRABBED_LOOT,
        parameters={
            1: "@MOB_KEEPER_DRUID_CHAMPION",
            2: "Alice",
            4: 3130,
            5: 2,
        },
    )
    tracker.observe(_message(), _packet(2.0))

    events = tracker.events()
    assert len(events) == 1
    assert events[0].looted_by.player_name == "Alice"
    assert events[0].looted_from is None
    assert events[0].source_kind == "mob"
    assert events[0].source_name == "@MOB_KEEPER_DRUID_CHAMPION"
    assert tracker.player("@MOB_KEEPER_DRUID_CHAMPION") is None


def test_loot_tracker_rejects_loot_from_non_party_player(monkeypatch) -> None:
    party = PartyRegistry()
    party.seed_names(["Alice", "Bob"])
    tracker = LootTracker(
        party_registry=party,
        item_resolver=ItemResolver(
            index_to_unique={3130: "T3_BAG"},
            index_to_name={3130: "Journeyman's Bag"},
        ),
    )

    _set_event(
        monkeypatch,
        subtype=EV_OTHER_GRABBED_LOOT,
        parameters={
            1: "@MOB_KEEPER_DRUID_CHAMPION",
            2: "EnemyGuy",
            4: 3130,
            5: 2,
        },
    )
    tracker.observe(_message(), _packet(2.0))

    assert tracker.events() == []


def test_loot_tracker_accepts_loot_from_party_player(monkeypatch) -> None:
    party = PartyRegistry()
    party.seed_names(["Alice", "Bob"])
    tracker = LootTracker(
        party_registry=party,
        item_resolver=ItemResolver(
            index_to_unique={3130: "T3_BAG"},
            index_to_name={3130: "Journeyman's Bag"},
        ),
    )

    _set_event(
        monkeypatch,
        subtype=EV_OTHER_GRABBED_LOOT,
        parameters={
            1: "@MOB_KEEPER_DRUID_CHAMPION",
            2: "Alice",
            4: 3130,
            5: 2,
        },
    )
    tracker.observe(_message(), _packet(2.0))

    events = tracker.events()
    assert len(events) == 1
    assert events[0].looted_by.player_name == "Alice"


def test_loot_tracker_attaches_loot_objects_to_container(monkeypatch) -> None:
    tracker = LootTracker(
        item_resolver=ItemResolver(
            index_to_unique={333: "T4_BAG"},
            index_to_name={333: "Adept's Bag"},
        )
    )

    _set_event(
        monkeypatch,
        subtype=EV_NEW_SIMPLE_ITEM,
        parameters={0: 7001, 1: 333, 2: 4},
    )
    tracker.observe(_message())

    _set_event(
        monkeypatch,
        subtype=EV_NEW_LOOT,
        parameters={0: 9001, 3: "Enemy"},
    )
    tracker.observe(_message())

    raw_uuid = bytes.fromhex("00112233445566778899aabbccddeeff")
    _set_event(
        monkeypatch,
        subtype=EV_ATTACH_ITEM_CONTAINER,
        parameters={0: 9001, 1: raw_uuid, 3: [7001]},
    )
    tracker.observe(_message())

    container = tracker.container(9001)
    assert container is not None
    assert container.owner_name == "Enemy"
    assert set(container.items) == {7001}

    loot = tracker.loot_object(7001)
    assert loot is not None
    assert loot.owner_name == "Enemy"
    assert loot.item.unique_name == "T4_BAG"
    assert container.slot_items[0].object_id == 7001


def test_loot_tracker_records_inventory_move_from_loot_container(monkeypatch) -> None:
    party = PartyRegistry()
    party.set_self_name("D4dits", confirmed=True)
    tracker = LootTracker(
        party_registry=party,
        item_resolver=ItemResolver(
            index_to_unique={3131: "UNIQUE_ROTTEN_CHOCOLATE_EGG"},
            index_to_name={3131: "Rotten Chocolate Egg"},
        ),
    )

    raw_uuid = bytes.fromhex("f52922571799bd4ca728e95c7868ec6c")
    inventory_uuid = bytes.fromhex("a8813ad2bf29b442900ced9b69c88034")

    _set_event(
        monkeypatch,
        subtype=EV_NEW_LOOT,
        parameters={0: 184088, 3: "@MOB_T2_MOB_EVENT_EASTER_RESOURCE"},
    )
    tracker.observe(_message())

    _set_event(
        monkeypatch,
        subtype=EV_NEW_SIMPLE_ITEM,
        parameters={0: 184090, 1: 3131, 2: 1},
    )
    tracker.observe(_message())

    _set_event(
        monkeypatch,
        subtype=EV_ATTACH_ITEM_CONTAINER,
        parameters={0: 184088, 1: raw_uuid, 3: [184090], 4: 1},
    )
    tracker.observe(_message())

    monkeypatch.setattr(
        loot_tracker_module,
        "decode_operation_request",
        lambda _payload: SimpleNamespace(
            code=OP_INVENTORY_MOVE_ITEM,
            parameters={
                1: list(raw_uuid),
                2: 2,
                4: list(inventory_uuid),
                5: 2,
                253: OP_INVENTORY_MOVE_ITEM,
            },
        ),
    )
    tracker.observe(_message(event_code=None), _packet(1776085534.558984))

    events = tracker.events()
    assert len(events) == 1
    event = events[0]
    assert event.timestamp == 1776085534.558984
    assert event.looted_by.player_name == "D4dits"
    assert event.looted_from is None
    assert event.source_name == "@MOB_T2_MOB_EVENT_EASTER_RESOURCE"
    assert event.source_kind == "mob"
    assert event.item is not None
    assert event.item.item_num_id == 3131
    assert event.item.display_name == "Rotten Chocolate Egg"
    assert event.quantity == 1
    assert event.is_silver is False
    assert event.raw_event_code == OP_INVENTORY_MOVE_ITEM
    assert tracker.loot_object(184090) is None


def test_loot_tracker_detaches_container_by_uuid(monkeypatch) -> None:
    tracker = LootTracker()

    _set_event(
        monkeypatch,
        subtype=EV_NEW_LOOT,
        parameters={0: 9001, 3: "Enemy"},
    )
    tracker.observe(_message())

    raw_uuid = bytes.fromhex("00112233445566778899aabbccddeeff")
    _set_event(
        monkeypatch,
        subtype=EV_ATTACH_ITEM_CONTAINER,
        parameters={0: 9001, 1: raw_uuid, 3: []},
    )
    tracker.observe(_message())
    assert tracker.container(9001) is not None

    _set_event(
        monkeypatch,
        subtype=EV_DETACH_ITEM_CONTAINER,
        parameters={0: raw_uuid},
    )
    tracker.observe(_message())

    assert tracker.container(9001) is None


def test_loot_tracker_ignores_non_event_messages(monkeypatch) -> None:
    tracker = LootTracker()
    called = {"decode": False}

    def _decode(_payload: bytes):
        called["decode"] = True
        return SimpleNamespace(code=1, parameters={252: EV_NEW_CHARACTER, 1: "Alice"})

    monkeypatch.setattr(loot_tracker_module, "decode_event_data", _decode)

    tracker.observe(_message(event_code=None))

    assert called["decode"] is False
    assert tracker.player("Alice") is None
