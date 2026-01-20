from __future__ import annotations

from albion_dps.models import RawPacket
from albion_dps.protocol.photon_decode import PhotonDecoder


def _packet(payload_hex: str) -> RawPacket:
    payload = bytes.fromhex(payload_hex)
    return RawPacket(0.0, "1.1.1.1", 1111, "2.2.2.2", 2222, payload)


def test_decode_event_payload_hex() -> None:
    payload_hex = "000100010000002A00000000060000000000001100000001000410AABB"
    decoder = PhotonDecoder()
    message = decoder.decode(_packet(payload_hex))

    assert message is not None
    assert message.event_code == 0x10
    assert message.opcode == 0x10
    assert message.payload == bytes.fromhex("10AABB")


def test_decode_operation_payload_hex() -> None:
    payload_hex = "000100010000002B00000000060000000000001100000001000203CAFE"
    decoder = PhotonDecoder()
    message = decoder.decode(_packet(payload_hex))

    assert message is not None
    assert message.event_code is None
    assert message.opcode == 0x03
    assert message.payload == bytes.fromhex("03CAFE")
