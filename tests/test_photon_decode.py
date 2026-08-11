from __future__ import annotations

import struct

from albion_dps.models import RawPacket
from albion_dps.protocol.photon_decode import PhotonDecoder, _photon_crc


def _packet(payload_hex: str) -> RawPacket:
    payload = bytes.fromhex(payload_hex)
    return RawPacket(0.0, "1.1.1.1", 1111, "2.2.2.2", 2222, payload)


def _fragment_packet(
    fragment_number: int,
    fragment_offset: int,
    fragment: bytes,
    *,
    timestamp: float,
) -> RawPacket:
    assembled_length = 6
    fragment_body = struct.pack(
        ">IIIII", 50, 2, fragment_number, assembled_length, fragment_offset
    ) + fragment
    command = (
        struct.pack(">BBBBII", 8, 1, 0, 0, 12 + len(fragment_body), 80 + fragment_number)
        + fragment_body
    )
    photon = struct.pack(">HBBII", 1, 0, 1, 42, 0) + command
    return RawPacket(timestamp, "1.1.1.1", 1111, "2.2.2.2", 2222, photon)


def test_decode_event_payload_hex() -> None:
    payload_hex = "000100010000002A00000000060000000000001100000001000410AABB"
    decoder = PhotonDecoder()
    message = decoder.decode(_packet(payload_hex))

    assert message is not None
    assert message.event_code == 0x10
    assert message.opcode == 0x10
    assert message.payload == bytes.fromhex("10AABB")
    assert message.message_type == "event"


def test_decode_operation_payload_hex() -> None:
    payload_hex = "000100010000002B00000000060000000000001100000001000203CAFE"
    decoder = PhotonDecoder()
    message = decoder.decode(_packet(payload_hex))

    assert message is not None
    assert message.event_code is None
    assert message.opcode == 0x03
    assert message.payload == bytes.fromhex("03CAFE")
    assert message.message_type == "operation_request"


def test_decode_reassembles_out_of_order_fragments() -> None:
    decoder = PhotonDecoder()
    # Reliable message body: reserved byte, event type, event code and payload.
    assembled = bytes.fromhex("000410AABBCC")

    assert decoder.decode(_fragment_packet(1, 3, assembled[3:], timestamp=1.0)) is None
    message = decoder.decode(_fragment_packet(0, 0, assembled[:3], timestamp=2.0))

    assert message is not None
    assert message.event_code == 0x10
    assert message.payload == bytes.fromhex("10AABBCC")


def test_decode_ignores_duplicate_fragment_until_group_is_complete() -> None:
    decoder = PhotonDecoder()
    assembled = bytes.fromhex("000410AABBCC")
    first = _fragment_packet(0, 0, assembled[:3], timestamp=1.0)

    assert decoder.decode(first) is None
    assert decoder.decode(first) is None
    assert decoder.decode(_fragment_packet(1, 3, assembled[3:], timestamp=2.0)) is not None


def test_decode_validates_crc_enabled_packet() -> None:
    body = bytes.fromhex("000410AABB")
    command = struct.pack(">BBBBII", 6, 0, 0, 0, 12 + len(body), 1) + body
    payload = bytearray(struct.pack(">HBBII", 1, 0xCC, 1, 42, 0) + b"\x00" * 4 + command)
    struct.pack_into(">I", payload, 12, _photon_crc(payload))

    message = PhotonDecoder().decode(
        RawPacket(0.0, "1.1.1.1", 1111, "2.2.2.2", 2222, bytes(payload))
    )

    assert message is not None
    assert message.payload == bytes.fromhex("10AABB")


def test_decode_rejects_invalid_crc_packet() -> None:
    body = bytes.fromhex("000410AABB")
    command = struct.pack(">BBBBII", 6, 0, 0, 0, 12 + len(body), 1) + body
    payload = struct.pack(">HBBII", 1, 0xCC, 1, 42, 0) + b"\x00" * 4 + command

    assert PhotonDecoder().decode(
        RawPacket(0.0, "1.1.1.1", 1111, "2.2.2.2", 2222, payload)
    ) is None
