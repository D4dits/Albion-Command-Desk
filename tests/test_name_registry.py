from __future__ import annotations

from types import SimpleNamespace

import albion_dps.domain.name_registry as name_registry_module

from albion_dps.domain.name_registry import NameRegistry
from albion_dps.models import PhotonMessage, RawPacket


_PORTAL_PAYLOAD_HEX = (
    "01002800690001d56b017300096b726f7869676f727a026212057800000005050006030306780000000500040900060778000000108848c929e0b8a54286bfe811e08fda800a7300000b69000000000c69000000000d73000010780000000810c76e0afdecaff911780000000810c76e0afdecaff91269004ac42a136643327bfa14664147c28f1666452eb0001766452eb0001966428bc0b31a69004ac42a1b6643cd80001c6643cd80001e6640ae1f391f69004ac42a2066447b80002166447b800023664120f5c32469004ac42a2566465b71b1266c08de49f4e80ccf8f2762002879000a6b18ed000011230fc2123c0b3c09cc0bde000000002b79000e6b0aff0b090b1f0ea40ee10f1affffffffffffffffffffffff104e100d33730000356203366200377900076bffffffffffffffffffffffff013938620339620c3f6900000000fc6b001d"
)
_GUID_NAME_PAYLOAD_HEX = (
    "01000a007800000010012377a155877d46a2af60b2eecd44410173000653796c616573026f01036c08de4f820d3292eb04620105621906620a076205096200fc6b0068"
)
_ID_GUID_PAYLOAD_HEX = (
    "010004006b02af017800000010695ff68cd8bb1849b8fe05efa59fada50279000266c1f40000c3bf4000fc6b00d6"
)
_GUID_LINK_PAYLOAD_HEX = (
    "01000c00690003afec01690003a8b9026c08de4f8905466936037800000010398e20f6875dd142853b1783791e9e69056214066b01b60762040879000266c304c4a9c3b7b5da0966419a38340a62020b6200fc6b0028"
)
_ID_NAME_PAYLOAD_HEX = "01000500690001498f02730006443464697473036f010569004a6154fc6b0113"


def test_name_registry_extracts_name() -> None:
    registry = NameRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_PORTAL_PAYLOAD_HEX))

    registry.observe(message)
    names = registry.snapshot()

    assert names[120171] == "kroxigorz"


def test_name_registry_guid_name_mapping() -> None:
    registry = NameRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_GUID_NAME_PAYLOAD_HEX))

    registry.observe(message)
    guid_names = registry.snapshot_guid_names()

    assert bytes.fromhex("012377a155877d46a2af60b2eecd4441") in guid_names
    assert guid_names[bytes.fromhex("012377a155877d46a2af60b2eecd4441")] == "Sylaes"


def test_name_registry_id_guid_mapping() -> None:
    registry = NameRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_ID_GUID_PAYLOAD_HEX))

    registry.observe(message)
    id_guids = registry.snapshot_id_guids()

    assert id_guids[687] == bytes.fromhex("695ff68cd8bb1849b8fe05efa59fada5")


def test_name_registry_guid_link_mapping() -> None:
    registry = NameRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_GUID_LINK_PAYLOAD_HEX))

    registry.observe(message)
    id_guids = registry.snapshot_id_guids()

    assert id_guids[239801] == bytes.fromhex("398e20f6875dd142853b1783791e9e69")


def test_name_registry_id_name_mapping() -> None:
    registry = NameRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_ID_NAME_PAYLOAD_HEX))

    registry.observe(message)
    names = registry.snapshot()

    assert names[84367] == "D4dits"


def test_name_registry_tracks_recent_local_entity_ids() -> None:
    registry = NameRegistry()
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(_PORTAL_PAYLOAD_HEX))
    packet = RawPacket(
        timestamp=42.0,
        src_ip="193.169.238.17",
        src_port=5056,
        dst_ip="10.0.0.1",
        dst_port=51000,
        payload=message.payload,
    )

    registry.observe(message, packet)

    assert 120171 in registry.snapshot_recent_ids(42.0, 5.0)
    assert 120171 not in registry.snapshot_recent_ids(60.0, 5.0)


def test_name_registry_accepts_list_int_guid_from_unit_info(monkeypatch) -> None:
    registry = NameRegistry()
    guid = bytes.fromhex("4bb4253238e88941ac4bedfb0647e578")
    message = PhotonMessage(opcode=1, event_code=1, payload=b"\x00")

    monkeypatch.setattr(
        name_registry_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(
            parameters={252: 29, 0: 996330, 1: "CascadeJP", 7: list(guid)}
        ),
    )

    registry.observe(message)

    assert registry.snapshot_id_guids()[996330] == guid
    assert registry.snapshot_guid_names()[guid] == "CascadeJP"
    assert registry.lookup(996330) == "CascadeJP"


def test_name_registry_maps_current_party_player_joined_guid_name(monkeypatch) -> None:
    registry = NameRegistry()
    guid = bytes.fromhex("023247a635fd5d41a3b2985125b3b592")
    message = PhotonMessage(opcode=1, event_code=1, payload=b"\x00")

    monkeypatch.setattr(
        name_registry_module,
        "decode_event_data",
        lambda _payload: SimpleNamespace(
            parameters={252: 233, 1: list(guid), 2: "MERTLER"}
        ),
    )

    registry.observe(message)

    assert registry.snapshot_guid_names()[guid] == "MERTLER"


def test_name_registry_ignores_generic_raw_id_guid_pairs(monkeypatch) -> None:
    registry = NameRegistry()
    good_guid = bytes.fromhex("4bb4253238e88941ac4bedfb0647e578")
    unrelated_guid = bytes.fromhex("c34bfaa5efa52f46bd931adbbeef42a8")
    message = PhotonMessage(opcode=1, event_code=1, payload=b"\x00")
    events = iter(
        [
            SimpleNamespace(
                parameters={252: 29, 0: 996330, 1: "CascadeJP", 7: list(good_guid)}
            ),
            SimpleNamespace(parameters={252: 666, 0: 996330, 1: list(unrelated_guid)}),
        ]
    )

    monkeypatch.setattr(
        name_registry_module,
        "decode_event_data",
        lambda _payload: next(events),
    )

    registry.observe(message)
    registry.observe(message)

    assert registry.snapshot_id_guids()[996330] == good_guid


def test_player_identity_survives_generic_mob_label_for_same_object_id(monkeypatch) -> None:
    registry = NameRegistry()
    guid = bytes.fromhex("4bb4253238e88941ac4bedfb0647e578")
    message = PhotonMessage(opcode=1, event_code=1, payload=b"\x00")
    events = iter(
        [
            SimpleNamespace(
                parameters={252: 29, 0: 996330, 1: "CascadeJP", 7: list(guid)}
            ),
            SimpleNamespace(parameters={252: 666, 0: 996330, 1: "@MOB_WOLF"}),
        ]
    )
    monkeypatch.setattr(
        name_registry_module,
        "decode_event_data",
        lambda _payload: next(events),
    )

    registry.observe(message)
    registry.observe(message)

    assert registry.lookup(996330) == "@MOB_WOLF"
    assert registry.lookup_player(996330) == "CascadeJP"


def test_guid_rebind_keeps_recent_player_object_ids_for_reordered_combat(monkeypatch) -> None:
    registry = NameRegistry()
    guid = bytes.fromhex("4bb4253238e88941ac4bedfb0647e578")
    message = PhotonMessage(opcode=1, event_code=1, payload=b"\x00")
    events = iter(
        [
            SimpleNamespace(parameters={252: 29, 0: 100, 1: "CascadeJP", 7: guid}),
            SimpleNamespace(parameters={252: 29, 0: 200, 1: "CascadeJP", 7: guid}),
        ]
    )
    monkeypatch.setattr(
        name_registry_module,
        "decode_event_data",
        lambda _payload: next(events),
    )

    registry.observe(message)
    registry.observe(message)

    assert registry.snapshot_id_guids()[100] == guid
    assert registry.lookup_player(100) == "CascadeJP"
    assert registry.lookup_player(200) == "CascadeJP"
