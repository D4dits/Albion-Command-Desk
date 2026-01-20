from __future__ import annotations

from albion_dps.domain.party_registry import PartyRegistry
from albion_dps.meter.aggregate import RollingMeter
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.models import CombatEvent, PhotonMessage, RawPacket
from albion_dps.pipeline import stream_snapshots

_TARGET_OP_REQUEST_PAYLOAD_HEX = (
    "010007006c08de534edbcc5e5d0179000266c316dbf3c3a4be9f026641e8b62403"
    "79000266c316bcf2c3a45135046640b00000056900142e0cfd6b0015"
)
_TARGET_LINK_PAYLOAD_HEX = "010006006900142e0c0169001445df026b0d34036201046200fc6b0015"

def _combat_state_payload(entity_id: int, active: bool, passive: bool, subtype: int = 274) -> bytes:
    import struct

    parts = [
        b"\x01",  # event code
        struct.pack(">H", 4),  # parameter count
        b"\x00\x69" + struct.pack(">i", int(entity_id)),
        b"\x01\x6f" + (b"\x01" if active else b"\x00"),
        b"\x02\x6f" + (b"\x01" if passive else b"\x00"),
        b"\xfc\x6b" + struct.pack(">h", int(subtype)),
    ]
    return b"".join(parts)


class _DummyDecoder:
    def __init__(self, messages: list[list[PhotonMessage]]) -> None:
        self._messages = messages
        self._index = 0

    def decode_all(self, _packet: RawPacket) -> list[PhotonMessage]:
        messages = self._messages[self._index]
        self._index += 1
        return messages


def test_combat_state_does_not_seed_party_ids_for_filtering() -> None:
    combat_state_payload = bytes.fromhex("01000400690001498f016f01026f01fc6b0112")
    combat_state_msg = PhotonMessage(opcode=1, event_code=1, payload=combat_state_payload)
    event_msg = PhotonMessage(opcode=2, event_code=None, payload=b"")
    decoder = _DummyDecoder([[combat_state_msg], [event_msg]])

    packets = [
        RawPacket(0.0, "1.1.1.1", 1111, "2.2.2.2", 2222, b""),
        RawPacket(1.0, "1.1.1.1", 1111, "2.2.2.2", 2222, b""),
    ]

    meter = RollingMeter(window_seconds=10.0)
    party_registry = PartyRegistry()

    def mapper(_message: PhotonMessage, packet: RawPacket) -> CombatEvent | None:
        if packet.timestamp < 1.0:
            return None
        return CombatEvent(packet.timestamp, 84367, 1, 50, "damage")

    snapshots = list(
        stream_snapshots(
            packets,
            decoder,
            meter,
            party_registry=party_registry,
            event_mapper=mapper,
            snapshot_interval=0.0,
        )
    )

    last = snapshots[-1]
    assert last.totals == {}


def test_pending_events_flush_when_party_ids_arrive() -> None:
    request = PhotonMessage(
        opcode=1,
        event_code=None,
        payload=bytes.fromhex(_TARGET_OP_REQUEST_PAYLOAD_HEX),
    )
    link = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_TARGET_LINK_PAYLOAD_HEX),
    )
    dummy = PhotonMessage(opcode=0, event_code=None, payload=b"")
    decoder = _DummyDecoder([[dummy], [request], [link, link], [dummy]])

    packets = [
        RawPacket(0.0, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
        RawPacket(1.0, "10.0.0.1", 50000, "193.169.238.17", 5056, b""),
        RawPacket(1.05, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
        RawPacket(1.10, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
    ]

    meter = RollingMeter(window_seconds=10.0)
    party_registry = PartyRegistry()

    def mapper(_message: PhotonMessage, packet: RawPacket) -> CombatEvent | None:
        if packet.timestamp == 0.0:
            return CombatEvent(packet.timestamp, 1328607, 1, 73, "damage")
        if packet.timestamp == 1.10:
            return CombatEvent(packet.timestamp, 1328607, 1322508, 0, "damage")
        return None

    snapshots = list(
        stream_snapshots(
            packets,
            decoder,
            meter,
            party_registry=party_registry,
            event_mapper=mapper,
            snapshot_interval=0.0,
        )
    )

    last = snapshots[-1]
    assert last.totals[1328607]["damage"] == 73.0


def test_pending_combat_state_flush_enables_auto_end() -> None:
    dummy = PhotonMessage(opcode=0, event_code=None, payload=b"")
    start = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=_combat_state_payload(1328607, True, False),
    )
    end = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=_combat_state_payload(1328607, False, False),
    )
    request = PhotonMessage(
        opcode=1,
        event_code=None,
        payload=bytes.fromhex(_TARGET_OP_REQUEST_PAYLOAD_HEX),
    )
    link = PhotonMessage(
        opcode=1,
        event_code=1,
        payload=bytes.fromhex(_TARGET_LINK_PAYLOAD_HEX),
    )
    decoder = _DummyDecoder([[dummy, start], [request], [link, link], [dummy], [dummy, end]])

    packets = [
        RawPacket(0.0, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
        RawPacket(0.05, "10.0.0.1", 50000, "193.169.238.17", 5056, b""),
        RawPacket(0.06, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
        RawPacket(0.07, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
        RawPacket(0.1, "193.169.238.17", 5056, "10.0.0.1", 50000, b""),
    ]

    party_registry = PartyRegistry()
    meter = SessionMeter(history_limit=5, mode="battle")

    def mapper(_message: PhotonMessage, packet: RawPacket) -> CombatEvent | None:
        if packet.timestamp == 0.0:
            return CombatEvent(packet.timestamp, 1328607, 1, 73, "damage")
        if packet.timestamp == 0.07:
            return CombatEvent(packet.timestamp, 1328607, 1322508, 0, "damage")
        return None

    list(
        stream_snapshots(
            packets,
            decoder,
            meter,
            party_registry=party_registry,
            event_mapper=mapper,
            snapshot_interval=0.0,
        )
    )

    history = meter.history()
    assert len(history) == 1
    assert history[0].reason == "combat_state"
    assert history[0].end_ts == 0.1
