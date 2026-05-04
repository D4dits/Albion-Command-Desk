from __future__ import annotations

from types import SimpleNamespace

import albion_dps.domain.loot_tracker as loot_tracker_module

from albion_dps.domain.item_resolver import ItemResolver
from albion_dps.domain.party_registry import PartyRegistry
from albion_dps.domain.loot_tracker import (
    EV_OTHER_GRABBED_LOOT,
    EV_PARTY_MEMBER_GRABBED_LOOT,
    LootTracker,
)
from albion_dps.meter.aggregate import RollingMeter
from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.pipeline import stream_snapshots


class _DummyDecoder:
    def __init__(self, messages: list[list[PhotonMessage]]) -> None:
        self._messages = messages
        self._index = 0

    def decode_all(self, _packet: RawPacket) -> list[PhotonMessage]:
        messages = self._messages[self._index]
        self._index += 1
        return messages


def test_stream_snapshots_forwards_messages_to_loot_tracker(monkeypatch) -> None:
    party = PartyRegistry()
    party.seed_names(["DjonLii"])
    loot_tracker = LootTracker(
        party_registry=party,
        item_resolver=ItemResolver(
            index_to_unique={3130: "T3_BAG"},
            index_to_name={3130: "Journeyman's Bag"},
        )
    )
    monkeypatch.setattr(
        loot_tracker_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(
            code=1,
            parameters={
                252: EV_OTHER_GRABBED_LOOT,
                1: "@MOB_KEEPER_DRUID_CHAMPION",
                2: "DjonLii",
                4: 3130,
                5: 2,
            },
        ),
    )
    decoder = _DummyDecoder([[PhotonMessage(opcode=1, event_code=1, payload=b"\x00")]])
    packets = [
        RawPacket(10.0, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
    ]

    list(
        stream_snapshots(
            packets,
            decoder,
            RollingMeter(window_seconds=10.0),
            loot_tracker=loot_tracker,
            event_mapper=lambda _message, _packet: None,
            snapshot_interval=0.0,
        )
    )

    events = loot_tracker.events()
    assert len(events) == 1
    assert events[0].looted_by.player_name == "DjonLii"
    assert events[0].looted_from is None
    assert events[0].source_kind == "mob"
    assert events[0].source_name == "@MOB_KEEPER_DRUID_CHAMPION"


def test_stream_snapshots_drops_non_party_loot_events(monkeypatch) -> None:
    party = PartyRegistry()
    party.seed_names(["PartyOne"])
    loot_tracker = LootTracker(
        party_registry=party,
        item_resolver=ItemResolver(
            index_to_unique={3130: "T3_BAG"},
            index_to_name={3130: "Journeyman's Bag"},
        ),
    )
    monkeypatch.setattr(
        loot_tracker_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(
            code=1,
            parameters={
                252: EV_OTHER_GRABBED_LOOT,
                1: "@MOB_KEEPER_DRUID_CHAMPION",
                2: "RandomGuy",
                4: 3130,
                5: 2,
            },
        ),
    )
    decoder = _DummyDecoder([[PhotonMessage(opcode=1, event_code=1, payload=b"\x00")]])
    packets = [
        RawPacket(10.0, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
    ]

    list(
        stream_snapshots(
            packets,
            decoder,
            RollingMeter(window_seconds=10.0),
            loot_tracker=loot_tracker,
            event_mapper=lambda _message, _packet: None,
            snapshot_interval=0.0,
        )
    )

    assert loot_tracker.events() == []


def test_stream_snapshots_keeps_party_member_loot_event(monkeypatch) -> None:
    party = PartyRegistry()
    party.seed_names(["PartyOne"])
    loot_tracker = LootTracker(
        party_registry=party,
        item_resolver=ItemResolver(
            index_to_unique={3130: "T3_BAG"},
            index_to_name={3130: "Journeyman's Bag"},
        ),
    )
    monkeypatch.setattr(
        loot_tracker_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(
            code=1,
            parameters={
                252: EV_PARTY_MEMBER_GRABBED_LOOT,
                1: "@MOB_KEEPER_DRUID_CHAMPION",
                2: "PartyOne",
                4: 3130,
                5: 2,
            },
        ),
    )
    decoder = _DummyDecoder([[PhotonMessage(opcode=1, event_code=1, payload=b"\x00")]])
    packets = [
        RawPacket(10.0, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
    ]

    list(
        stream_snapshots(
            packets,
            decoder,
            RollingMeter(window_seconds=10.0),
            loot_tracker=loot_tracker,
            event_mapper=lambda _message, _packet: None,
            snapshot_interval=0.0,
        )
    )

    events = loot_tracker.events()
    assert len(events) == 1
    assert events[0].looted_by.player_name == "PartyOne"


def test_stream_snapshots_drops_non_party_member_loot_event_after_roster_resolves(monkeypatch) -> None:
    party = PartyRegistry()
    party.seed_names(["PartyOne"])
    loot_tracker = LootTracker(
        party_registry=party,
        item_resolver=ItemResolver(
            index_to_unique={3130: "T3_BAG"},
            index_to_name={3130: "Journeyman's Bag"},
        ),
    )
    monkeypatch.setattr(
        loot_tracker_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(
            code=1,
            parameters={
                252: EV_PARTY_MEMBER_GRABBED_LOOT,
                1: "@MOB_KEEPER_DRUID_CHAMPION",
                2: "RandomNearby",
                4: 3130,
                5: 2,
            },
        ),
    )
    decoder = _DummyDecoder([[PhotonMessage(opcode=1, event_code=1, payload=b"\x00")]])
    packets = [
        RawPacket(10.0, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
    ]

    list(
        stream_snapshots(
            packets,
            decoder,
            RollingMeter(window_seconds=10.0),
            loot_tracker=loot_tracker,
            event_mapper=lambda _message, _packet: None,
            snapshot_interval=0.0,
        )
    )

    assert loot_tracker.events() == []


def test_stream_snapshots_drops_other_looter_before_roster_when_self_known(monkeypatch) -> None:
    party = PartyRegistry()
    party.set_self_name("SelfGuy", confirmed=True)
    loot_tracker = LootTracker(
        party_registry=party,
        item_resolver=ItemResolver(
            index_to_unique={3130: "T3_BAG"},
            index_to_name={3130: "Journeyman's Bag"},
        ),
    )
    monkeypatch.setattr(
        loot_tracker_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(
            code=1,
            parameters={
                252: EV_PARTY_MEMBER_GRABBED_LOOT,
                1: "@MOB_KEEPER_DRUID_CHAMPION",
                2: "NearbyGuy",
                4: 3130,
                5: 2,
            },
        ),
    )
    decoder = _DummyDecoder([[PhotonMessage(opcode=1, event_code=1, payload=b"\x00")]])
    packets = [
        RawPacket(10.0, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
    ]

    list(
        stream_snapshots(
            packets,
            decoder,
            RollingMeter(window_seconds=10.0),
            loot_tracker=loot_tracker,
            event_mapper=lambda _message, _packet: None,
            snapshot_interval=0.0,
        )
    )

    assert loot_tracker.events() == []
