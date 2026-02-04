from __future__ import annotations

import struct

from albion_dps.domain import NameRegistry, PartyRegistry
from albion_dps.models import PhotonMessage

TYPE_INTEGER = 105
TYPE_STRING = 115
TYPE_STRING_ARRAY = 97
TYPE_BYTE_ARRAY = 120
TYPE_ARRAY = 121


def _enc_u8(value: int) -> bytes:
    return struct.pack(">B", value)


def _enc_u16(value: int) -> bytes:
    return struct.pack(">H", value)


def _enc_i32(value: int) -> bytes:
    return struct.pack(">i", value)


def _enc_string(value: str) -> bytes:
    data = value.encode("utf-8")
    return _enc_u16(len(data)) + data


def _enc_string_array(values: list[str]) -> bytes:
    return _enc_u16(len(values)) + b"".join(_enc_string(value) for value in values)


def _enc_byte_array(value: bytes) -> bytes:
    return _enc_i32(len(value)) + value


def _enc_array(type_code: int, values: list[bytes]) -> bytes:
    if type_code != TYPE_BYTE_ARRAY:
        raise ValueError("Unsupported array element type")
    return _enc_u16(len(values)) + _enc_u8(type_code) + b"".join(
        _enc_byte_array(value) for value in values
    )


def _enc_param(key: int, type_code: int, value: bytes) -> bytes:
    return _enc_u8(key) + _enc_u8(type_code) + value


def _build_event_payload(event_code: int, params: list[bytes]) -> bytes:
    return _enc_u8(event_code) + _enc_u16(len(params)) + b"".join(params)


def test_party_joined_subtype_maps_guid_names() -> None:
    guid_a = b"\x01" * 16
    guid_b = b"\x02" * 16
    params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(212)),
        _enc_param(3, TYPE_ARRAY, _enc_array(TYPE_BYTE_ARRAY, [guid_a, guid_b])),
        _enc_param(5, TYPE_STRING_ARRAY, _enc_string_array(["Alice", "Bob"])),
    ]
    payload = _build_event_payload(1, params)
    message = PhotonMessage(opcode=1, event_code=1, payload=payload)

    names = NameRegistry()
    party = PartyRegistry()
    names.observe(message)
    party.observe(message)

    guid_names = names.snapshot_guid_names()
    assert guid_names[guid_a] == "Alice"
    assert guid_names[guid_b] == "Bob"
    assert "Alice" in party.snapshot_names()
    assert "Bob" in party.snapshot_names()


def test_party_player_joined_subtype_maps_guid_name() -> None:
    guid = b"\x10" * 16
    params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(214)),
        _enc_param(1, TYPE_BYTE_ARRAY, _enc_byte_array(guid)),
        _enc_param(2, TYPE_STRING, _enc_string("Carol")),
    ]
    payload = _build_event_payload(1, params)
    message = PhotonMessage(opcode=1, event_code=1, payload=payload)

    names = NameRegistry()
    party = PartyRegistry()
    names.observe(message)
    party.observe(message)

    guid_names = names.snapshot_guid_names()
    assert guid_names[guid] == "Carol"
    assert "Carol" in party.snapshot_names()


def test_party_player_left_removes_member() -> None:
    guid_a = b"\x01" * 16
    guid_b = b"\x02" * 16
    joined_params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(212)),
        _enc_param(4, TYPE_ARRAY, _enc_array(TYPE_BYTE_ARRAY, [guid_a, guid_b])),
        _enc_param(5, TYPE_STRING_ARRAY, _enc_string_array(["Alice", "Bob"])),
    ]
    left_params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(216)),
        _enc_param(1, TYPE_BYTE_ARRAY, _enc_byte_array(guid_b)),
    ]
    joined_message = PhotonMessage(
        opcode=1, event_code=1, payload=_build_event_payload(1, joined_params)
    )
    left_message = PhotonMessage(
        opcode=1, event_code=1, payload=_build_event_payload(1, left_params)
    )

    party = PartyRegistry()
    party.observe(joined_message)
    party.observe(left_message)

    assert guid_b not in party.snapshot_guids()
    assert "Bob" not in party.snapshot_names()


def test_guid_link_from_unit_info_subtype() -> None:
    guid = b"\x22" * 16
    params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(29)),
        _enc_param(0, TYPE_INTEGER, _enc_i32(1234)),
        _enc_param(7, TYPE_BYTE_ARRAY, _enc_byte_array(guid)),
    ]
    payload = _build_event_payload(1, params)
    message = PhotonMessage(opcode=1, event_code=1, payload=payload)

    names = NameRegistry()
    names.observe(message)

    id_guids = names.snapshot_id_guids()
    assert id_guids[1234] == guid


def test_guid_link_from_subtype_308() -> None:
    guid = b"\x33" * 16
    params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(308)),
        _enc_param(0, TYPE_INTEGER, _enc_i32(5678)),
        _enc_param(5, TYPE_BYTE_ARRAY, _enc_byte_array(guid)),
    ]
    payload = _build_event_payload(1, params)
    message = PhotonMessage(opcode=1, event_code=1, payload=payload)

    names = NameRegistry()
    names.observe(message)

    id_guids = names.snapshot_id_guids()
    assert id_guids[5678] == guid


def test_party_disband_requires_expected_shape() -> None:
    guid = b"\x44" * 16
    joined_params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(227)),
        _enc_param(12, TYPE_ARRAY, _enc_array(TYPE_BYTE_ARRAY, [guid])),
        _enc_param(13, TYPE_STRING_ARRAY, _enc_string_array(["Alice"])),
    ]
    disband_params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(213)),
        _enc_param(1, TYPE_INTEGER, _enc_i32(14184)),
    ]
    joined_message = PhotonMessage(
        opcode=1, event_code=1, payload=_build_event_payload(1, joined_params)
    )
    disband_message = PhotonMessage(
        opcode=1, event_code=1, payload=_build_event_payload(1, disband_params)
    )

    party = PartyRegistry()
    party.observe(joined_message)
    assert party.snapshot_names() == {"Alice"}

    party.observe(disband_message)
    assert not party.snapshot_names()


def test_party_disband_ignored_for_unexpected_shape() -> None:
    guid = b"\x55" * 16
    joined_params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(227)),
        _enc_param(12, TYPE_ARRAY, _enc_array(TYPE_BYTE_ARRAY, [guid])),
        _enc_param(13, TYPE_STRING_ARRAY, _enc_string_array(["Bob"])),
    ]
    disband_params = [
        _enc_param(252, TYPE_INTEGER, _enc_i32(213)),
        _enc_param(0, TYPE_INTEGER, _enc_i32(584)),
        _enc_param(3, TYPE_BYTE_ARRAY, _enc_byte_array(guid)),
    ]
    joined_message = PhotonMessage(
        opcode=1, event_code=1, payload=_build_event_payload(1, joined_params)
    )
    disband_message = PhotonMessage(
        opcode=1, event_code=1, payload=_build_event_payload(1, disband_params)
    )

    party = PartyRegistry()
    party.observe(joined_message)
    party.observe(disband_message)

    assert party.snapshot_names() == {"Bob"}
