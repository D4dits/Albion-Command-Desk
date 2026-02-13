from __future__ import annotations

from types import SimpleNamespace

import albion_dps.domain.party_registry as party_registry_module

from albion_dps.domain.name_registry import NameRegistry
from albion_dps.domain.party_registry import PartyRegistry
from albion_dps.models import CombatEvent, PhotonMessage, RawPacket


_PARTY_229_PAYLOAD_HEX = (
    "01000d006b1a69026900000001047800000010ecbec680090a5e4ebcd7ae6ef65a43a6057900027800000010ecbec680090a5e4ebcd7ae6ef65a43a600000010398e20f6875dd142853b1783791e9e690679000273000b536f6369616c467572313000064434646974730778000000020100087800000002000409780000000200000a780000000200010b7900026bffffffff0c7900026bffff00060d7900026f0101fc6b00e5"
)
_PARTY_227_PAYLOAD_HEX = (
    "01000d007800000010398e20f6875dd142853b1783791e9e69017300064434646974730262040462010562000673000756696b696e6773076b1b8a0c7900017800000010398e20f6875dd142853b1783791e9e690d7900017300064434646974730e7800000001040f78000000010110780000000100fc6b00e3"
)
_SELF_238_PAYLOAD_HEX = "01000400730006443464697473016f01036205fc6b00ee"
_SELF_228_PAYLOAD_HEX = (
    "010008007800000010398e20f6875dd142853b1783791e9e6901730006443464697473"
    "0262040462010562000673000756696b696e67730769000183b2fc6b00e4"
)
_TARGET_OP_REQUEST_PAYLOAD_HEX = (
    "010007006c08de534edbcc5e5d0179000266c316dbf3c3a4be9f026641e8b62403"
    "79000266c316bcf2c3a45135046640b00000056900142e0cfd6b0015"
)
_TARGET_LINK_PAYLOAD_HEX = "010006006900142e0c0169001445df026b0d34036201046200fc6b0015"
_ID_NAME_PAYLOAD_HEX = "01000500690001498f02730006443464697473036f010569004a6154fc6b0113"
_GUID_LINK_PAYLOAD_HEX = (
    "01000c00690003afec01690003a8b9026c08de4f8905466936037800000010398e20f6875dd142"
    "853b1783791e9e69056214066b01b60762040879000266c304c4a9c3b7b5da0966419a38340a"
    "62020b6200fc6b0028"
)
_GUID_SELF = bytes.fromhex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
_GUID_PARTY = bytes.fromhex("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")


def test_party_registry_extracts_names_subtype_229() -> None:
    registry = PartyRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_PARTY_229_PAYLOAD_HEX))

    registry.observe(message)

    assert registry.snapshot_names() == {"SocialFur10", "D4dits"}


def test_party_registry_extracts_names_subtype_227() -> None:
    registry = PartyRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_PARTY_227_PAYLOAD_HEX))

    registry.observe(message)

    assert registry.snapshot_names() == {"D4dits"}


def test_party_registry_detects_self_subtype_238() -> None:
    registry = PartyRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_SELF_238_PAYLOAD_HEX))

    registry.observe(message)

    registry.seed_self_ids([101])
    names = NameRegistry()
    registry.sync_id_names(names)
    assert registry._self_name == "D4dits"
    assert not registry._self_name_confirmed
    assert names.lookup(101) is None


def test_party_registry_detects_self_subtype_228() -> None:
    registry = PartyRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_SELF_228_PAYLOAD_HEX))

    registry.observe(message)

    registry.seed_self_ids([101])
    names = NameRegistry()
    registry.sync_id_names(names)
    assert registry._self_name == "D4dits"
    assert not registry._self_name_confirmed
    assert names.lookup(101) is None


def test_party_registry_tracks_target_from_client_request() -> None:
    registry = PartyRegistry()
    message = PhotonMessage(opcode=1, event_code=None, payload=bytes.fromhex(_TARGET_OP_REQUEST_PAYLOAD_HEX))
    packet = RawPacket(
        timestamp=0.0,
        src_ip="10.0.0.1",
        src_port=50000,
        dst_ip="193.169.238.17",
        dst_port=5056,
        payload=message.payload,
    )

    registry.observe(message, packet)

    assert registry.snapshot_ids() == set()


def test_party_registry_resolves_self_from_target_link() -> None:
    registry = PartyRegistry()
    request = PhotonMessage(
        opcode=1,
        event_code=None,
        payload=bytes.fromhex(_TARGET_OP_REQUEST_PAYLOAD_HEX),
    )
    packet = RawPacket(
        timestamp=0.0,
        src_ip="10.0.0.1",
        src_port=50000,
        dst_ip="193.169.238.17",
        dst_port=5056,
        payload=request.payload,
    )
    registry.observe(request, packet)

    link = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_TARGET_LINK_PAYLOAD_HEX),
    )
    registry.observe(
        link,
        RawPacket(
            timestamp=0.05,
            src_ip="193.169.238.17",
            src_port=5056,
            dst_ip="10.0.0.1",
            dst_port=50000,
            payload=link.payload,
        ),
    )
    registry.observe_combat_event(CombatEvent(0.10, 1328607, 1322508, 0, "damage"))
    registry.observe_combat_event(CombatEvent(0.20, 1328607, 1322508, 0, "damage"))
    registry.try_resolve_self_id()

    assert registry.snapshot_ids() == {1328607}


def test_party_registry_does_not_resolve_self_from_links_without_combat_hits() -> None:
    registry = PartyRegistry()
    request = PhotonMessage(
        opcode=1,
        event_code=None,
        payload=bytes.fromhex(_TARGET_OP_REQUEST_PAYLOAD_HEX),
    )
    registry.observe(
        request,
        RawPacket(
            timestamp=0.0,
            src_ip="10.0.0.1",
            src_port=50000,
            dst_ip="193.169.238.17",
            dst_port=5056,
            payload=request.payload,
        ),
    )

    link = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_TARGET_LINK_PAYLOAD_HEX),
    )
    for idx in range(10):
        registry.observe(
            link,
            RawPacket(
                timestamp=0.05 + (idx * 0.01),
                src_ip="193.169.238.17",
                src_port=5056,
                dst_ip="10.0.0.1",
                dst_port=50000,
                payload=link.payload,
            ),
        )
    registry.try_resolve_self_id()

    assert registry.snapshot_self_ids() == set()


def test_party_registry_resolves_self_when_link_arrives_before_request() -> None:
    registry = PartyRegistry()

    link = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_TARGET_LINK_PAYLOAD_HEX),
    )
    registry.observe(
        link,
        RawPacket(
            timestamp=0.00,
            src_ip="193.169.238.17",
            src_port=5056,
            dst_ip="10.0.0.1",
            dst_port=50000,
            payload=link.payload,
        ),
    )

    request = PhotonMessage(
        opcode=1,
        event_code=None,
        payload=bytes.fromhex(_TARGET_OP_REQUEST_PAYLOAD_HEX),
    )
    registry.observe(
        request,
        RawPacket(
            timestamp=0.02,
            src_ip="10.0.0.1",
            src_port=50000,
            dst_ip="193.169.238.17",
            dst_port=5056,
            payload=request.payload,
        ),
    )
    registry.observe_combat_event(CombatEvent(0.03, 1328607, 1322508, 0, "damage"))
    registry.observe_combat_event(CombatEvent(0.04, 1328607, 1322508, 0, "damage"))
    registry.try_resolve_self_id()

    assert registry.snapshot_self_ids() == {1328607}


def test_party_registry_does_not_seed_ids_from_id_name_events() -> None:
    registry = PartyRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_ID_NAME_PAYLOAD_HEX))

    registry.observe(message)

    assert registry.snapshot_ids() == set()


def test_party_registry_replaces_self_id_on_join() -> None:
    registry = PartyRegistry()
    registry.seed_self_ids([123])

    registry._set_self_id(456, replace=True)

    assert registry.snapshot_self_ids() == {456}
    assert registry.snapshot_ids() == {456}


def test_sync_self_name_does_not_override_confirmed() -> None:
    registry = PartyRegistry()
    registry.set_self_name("D4dits", confirmed=True)
    registry.seed_self_ids([42])
    names = NameRegistry()
    names.record(42, "OtherPlayer")

    registry.sync_self_name(names)

    assert registry._self_name == "D4dits"


def test_sync_id_names_overrides_conflicting_name() -> None:
    registry = PartyRegistry()
    registry.set_self_name("D4dits", confirmed=True)
    registry.seed_self_ids([42])
    names = NameRegistry()
    names.record(42, "OtherPlayer")

    registry.sync_id_names(names)

    assert names.lookup(42) == "D4dits"


def test_allows_self_by_name_without_ids() -> None:
    registry = PartyRegistry()
    registry.set_self_name("D4dits", confirmed=True)
    names = NameRegistry()
    names.record(101, "D4dits")

    assert registry.allows(101, names)


def test_sync_guids_populates_party_ids_from_id_guids() -> None:
    names = NameRegistry()
    names.observe(PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_GUID_LINK_PAYLOAD_HEX)))

    registry = PartyRegistry()
    registry.observe(PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_PARTY_229_PAYLOAD_HEX)))
    registry.sync_guids(names)

    assert 239801 in registry.snapshot_ids()
    assert registry.snapshot_self_ids() == set()


def test_party_registry_allows_only_party_members() -> None:
    registry = PartyRegistry(strict=False)
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_PARTY_229_PAYLOAD_HEX))
    registry.observe(message)

    names = NameRegistry()
    names.record(101, "D4dits")
    names.record(202, "Enemy")
    registry.sync_names(names)

    assert registry.allows(101, names)
    assert not registry.allows(202, names)


def test_party_registry_seeding() -> None:
    registry = PartyRegistry(strict=False)
    registry.seed_names(["Self"])
    registry.seed_ids([99])

    names = NameRegistry()
    names.record(101, "Self")

    registry.sync_names(names)

    assert registry.allows(101, names)
    assert registry.allows(99, names)


def test_party_registry_maps_missing_id_name_via_target_link() -> None:
    registry = PartyRegistry()
    request = PhotonMessage(
        opcode=1,
        event_code=None,
        payload=bytes.fromhex(_TARGET_OP_REQUEST_PAYLOAD_HEX),
    )
    packet = RawPacket(
        timestamp=0.0,
        src_ip="10.0.0.1",
        src_port=50000,
        dst_ip="193.169.238.17",
        dst_port=5056,
        payload=request.payload,
    )
    registry.observe(request, packet)
    link = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_TARGET_LINK_PAYLOAD_HEX),
    )
    registry.observe(link)

    names = NameRegistry()
    names.record(1322508, "D4dits")

    registry.sync_id_names(names)

    assert names.lookup(1328607) is None


def test_party_registry_reuses_sticky_self_name_for_new_self_id() -> None:
    registry = PartyRegistry()
    registry.set_self_name("D4dits", confirmed=True)
    registry.seed_self_ids([101])

    names = NameRegistry()
    registry.sync_id_names(names)

    assert names.lookup(101) == "D4dits"


def test_party_registry_infers_self_name_from_repeated_targets() -> None:
    registry = PartyRegistry()
    names = NameRegistry()
    names.record(1322508, "D4dits")

    request = PhotonMessage(
        opcode=1,
        event_code=None,
        payload=bytes.fromhex(_TARGET_OP_REQUEST_PAYLOAD_HEX),
    )
    for idx in range(25):
        ts = idx * 0.1
        packet = RawPacket(
            timestamp=ts,
            src_ip="10.0.0.1",
            src_port=50000,
            dst_ip="193.169.238.17",
            dst_port=5056,
            payload=request.payload,
        )
        registry.observe(request, packet)
        registry.infer_self_name_from_targets(names)

    link = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_TARGET_LINK_PAYLOAD_HEX),
    )
    registry.observe(
        link,
        RawPacket(
            timestamp=2.55,
            src_ip="193.169.238.17",
            src_port=5056,
            dst_ip="10.0.0.1",
            dst_port=50000,
            payload=link.payload,
        ),
    )
    registry.observe_combat_event(CombatEvent(2.60, 1328607, 1322508, 0, "damage"))
    registry.observe_combat_event(CombatEvent(2.65, 1328607, 1322508, 0, "damage"))
    registry.try_resolve_self_id(names)
    registry.sync_id_names(names)

    assert names.lookup(1328607) == "D4dits"


def test_party_registry_ignores_mob_names_for_self_inference() -> None:
    registry = PartyRegistry()
    names = NameRegistry()
    names.record(42, "@MOB_WOLF")
    for idx in range(10):
        registry._recent_target_ids.append((float(idx), 42))

    registry.infer_self_name_from_targets(names)

    assert registry._self_name is None


def test_party_registry_resolves_self_id_from_confirmed_name() -> None:
    registry = PartyRegistry()
    names = NameRegistry()
    registry.set_self_name("SocialFur10", confirmed=True)
    names.record(101, "SocialFur10")

    registry.sync_self_name(names)

    assert registry.snapshot_self_ids() == {101}


def test_party_registry_fallback_parses_unknown_roster_subtype(monkeypatch) -> None:
    registry = PartyRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=b"\x00")
    params = {
        252: 245,
        7: [_GUID_SELF, _GUID_PARTY],
        8: ["D4dits", "SocialFur3"],
    }

    monkeypatch.setattr(
        party_registry_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(parameters=params),
    )

    registry.observe(message)
    registry.seed_self_ids([101])
    names = NameRegistry()
    names.record(101, "D4dits")
    names.record(202, "SocialFur3")
    names.record(303, "EnemyPlayer")
    registry.sync_names(names)

    assert registry.snapshot_names() == {"D4dits", "SocialFur3"}
    assert registry.snapshot_guids() == {_GUID_SELF, _GUID_PARTY}
    assert registry.allows(101, names)
    assert registry.allows(202, names)
    assert not registry.allows(303, names)


def test_party_registry_fallback_parses_unknown_join(monkeypatch) -> None:
    registry = PartyRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=b"\x00")
    events = iter([SimpleNamespace(parameters={252: 246, 1: _GUID_PARTY, 2: "SocialFur3"})])

    monkeypatch.setattr(
        party_registry_module,
        "decode_event_data",
        lambda _payload: next(events),
    )

    registry.observe(message)
    assert "SocialFur3" in registry.snapshot_names()
    assert _GUID_PARTY in registry.snapshot_guids()

def test_party_registry_fallback_ignores_unknown_guid_without_join_name(monkeypatch) -> None:
    registry = PartyRegistry()
    registry._add_party_member(_GUID_PARTY, "SocialFur3")
    message = PhotonMessage(opcode=1, event_code=1, payload=b"\x00")

    monkeypatch.setattr(
        party_registry_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(parameters={252: 247, 1: _GUID_PARTY, 0: "Other"}),
    )

    registry.observe(message)
    assert "SocialFur3" in registry.snapshot_names()
    assert _GUID_PARTY in registry.snapshot_guids()
