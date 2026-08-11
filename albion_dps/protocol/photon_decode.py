from __future__ import annotations

import logging
import struct
from dataclasses import dataclass, field
from pathlib import Path

from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.protocol.registry import PhotonRegistry
from albion_dps.protocol.unknown_dump import dump_unknown

_PHOTON_HEADER_LEN = 12
_COMMAND_HEADER_LEN = 12

MESSAGE_TYPE_OPERATION_REQUEST = 2
MESSAGE_TYPE_OPERATION_RESPONSE = 3
MESSAGE_TYPE_EVENT = 4

COMMAND_TYPE_DISCONNECT = 4
COMMAND_TYPE_SEND_RELIABLE = 6
COMMAND_TYPE_SEND_UNRELIABLE = 7
COMMAND_TYPE_SEND_FRAGMENT = 8
_FRAGMENT_HEADER_LEN = 20
_FRAGMENT_TIMEOUT_SECONDS = 30.0
_MAX_FRAGMENTED_MESSAGE_BYTES = 8 * 1024 * 1024
_MAX_FRAGMENT_COUNT = 1024
_MAX_FRAGMENT_GROUPS = 256


@dataclass
class _FragmentGroup:
    total_length: int
    fragment_count: int
    last_seen: float
    buffer: bytearray = field(init=False)
    received: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.buffer = bytearray(self.total_length)


class PhotonDecoder:
    def __init__(
        self,
        registry: PhotonRegistry | None = None,
        debug: bool = False,
        dump_unknowns: bool = False,
        unknown_output_dir: str | Path = "artifacts/unknown",
    ) -> None:
        self._registry = registry
        self._debug = debug
        self._dump_unknowns = dump_unknowns
        self._unknown_output_dir = Path(unknown_output_dir)
        self._logger = logging.getLogger(__name__)
        self._fragments: dict[tuple[str, int, str, int, int, int, int], _FragmentGroup] = {}

    def decode(self, packet: RawPacket) -> PhotonMessage | None:
        messages = self.decode_all(packet)
        return messages[0] if messages else None

    def decode_all(self, packet: RawPacket) -> list[PhotonMessage]:
        return list(
            _decode_messages(
                packet,
                registry=self._registry,
                debug=self._debug,
                dump_unknowns=self._dump_unknowns,
                unknown_output_dir=self._unknown_output_dir,
                logger=self._logger,
                fragments=self._fragments,
            )
        )


def _decode_messages(
    packet: RawPacket,
    *,
    registry: PhotonRegistry | None,
    debug: bool,
    dump_unknowns: bool,
    unknown_output_dir: Path,
    logger: logging.Logger,
    fragments: dict[tuple[str, int, str, int, int, int, int], _FragmentGroup],
) -> list[PhotonMessage]:
    messages: list[PhotonMessage] = []
    payload = packet.payload
    if len(payload) < _PHOTON_HEADER_LEN:
        _dump_unknown(packet, "photon_header_short", dump_unknowns, unknown_output_dir, logger)
        return messages

    offset = 0
    peer_id, offset = _read_u16(payload, offset)
    flags, offset = _read_u8(payload, offset)
    command_count, offset = _read_u8(payload, offset)
    _timestamp, offset = _read_u32(payload, offset)
    _challenge, offset = _read_u32(payload, offset)

    if flags == 1:
        _dump_unknown(packet, "photon_encrypted", dump_unknowns, unknown_output_dir, logger)
        return messages
    if flags == 0xCC:
        if offset + 4 > len(payload):
            _dump_unknown(packet, "photon_crc_short", dump_unknowns, unknown_output_dir, logger)
            return messages
        expected_crc = struct.unpack_from(">I", payload, offset)[0]
        crc_payload = bytearray(payload)
        crc_payload[offset : offset + 4] = b"\x00\x00\x00\x00"
        if expected_crc != _photon_crc(crc_payload):
            _dump_unknown(packet, "photon_crc_invalid", dump_unknowns, unknown_output_dir, logger)
            return messages
        offset += 4

    _expire_fragments(fragments, packet.timestamp)

    for _ in range(command_count):
        if offset + _COMMAND_HEADER_LEN > len(payload):
            _dump_unknown(packet, "photon_command_header_short", dump_unknowns, unknown_output_dir, logger)
            return messages

        command_type, offset = _read_u8(payload, offset)
        channel_id, offset = _read_u8(payload, offset)
        _command_flags, offset = _read_u8(payload, offset)
        offset += 1
        command_length, offset = _read_u32(payload, offset)
        _sequence_number, offset = _read_u32(payload, offset)

        body_length = command_length - _COMMAND_HEADER_LEN
        if body_length < 0 or offset + body_length > len(payload):
            _dump_unknown(packet, "photon_command_length_invalid", dump_unknowns, unknown_output_dir, logger)
            return messages

        if command_type == COMMAND_TYPE_SEND_UNRELIABLE:
            if body_length < 4:
                offset += body_length
                continue
            offset += 4
            body_length -= 4
            command_type = COMMAND_TYPE_SEND_RELIABLE

        if command_type == COMMAND_TYPE_SEND_RELIABLE:
            message = _decode_message(
                packet,
                payload,
                offset,
                body_length,
                registry,
                debug,
                dump_unknowns,
                unknown_output_dir,
                logger,
                peer_id,
            )
            offset += body_length
            if message is not None:
                messages.append(message)
            continue

        if command_type == COMMAND_TYPE_SEND_FRAGMENT:
            message = _decode_fragment(
                packet,
                payload[offset : offset + body_length],
                peer_id=peer_id,
                channel_id=channel_id,
                registry=registry,
                debug=debug,
                dump_unknowns=dump_unknowns,
                unknown_output_dir=unknown_output_dir,
                logger=logger,
                fragments=fragments,
            )
            offset += body_length
            if message is not None:
                messages.append(message)
            continue

        if command_type == COMMAND_TYPE_DISCONNECT:
            offset += body_length
            continue

        offset += body_length

    return messages


def _decode_fragment(
    packet: RawPacket,
    body: bytes,
    *,
    peer_id: int,
    channel_id: int,
    registry: PhotonRegistry | None,
    debug: bool,
    dump_unknowns: bool,
    unknown_output_dir: Path,
    logger: logging.Logger,
    fragments: dict[tuple[str, int, str, int, int, int, int], _FragmentGroup],
) -> PhotonMessage | None:
    if len(body) < _FRAGMENT_HEADER_LEN:
        _dump_unknown(packet, "photon_fragment_short", dump_unknowns, unknown_output_dir, logger)
        return None
    (
        start_sequence,
        fragment_count,
        fragment_number,
        total_length,
        fragment_offset,
    ) = struct.unpack_from(">IIIII", body, 0)
    fragment = body[_FRAGMENT_HEADER_LEN:]
    if (
        fragment_count <= 0
        or fragment_count > _MAX_FRAGMENT_COUNT
        or fragment_number >= fragment_count
        or total_length <= 0
        or total_length > _MAX_FRAGMENTED_MESSAGE_BYTES
        or fragment_offset > total_length
        or len(fragment) > total_length - fragment_offset
    ):
        _dump_unknown(packet, "photon_fragment_invalid", dump_unknowns, unknown_output_dir, logger)
        return None

    key = (
        packet.src_ip,
        packet.src_port,
        packet.dst_ip,
        packet.dst_port,
        peer_id,
        channel_id,
        start_sequence,
    )
    group = fragments.get(key)
    if group is None or (
        group.total_length != total_length or group.fragment_count != fragment_count
    ):
        if len(fragments) >= _MAX_FRAGMENT_GROUPS:
            oldest_key = min(fragments, key=lambda item: fragments[item].last_seen)
            fragments.pop(oldest_key, None)
        group = _FragmentGroup(total_length, fragment_count, packet.timestamp)
        fragments[key] = group
    group.last_seen = packet.timestamp
    if fragment_number not in group.received:
        group.buffer[fragment_offset : fragment_offset + len(fragment)] = fragment
        group.received.add(fragment_number)
    if len(group.received) != group.fragment_count:
        return None

    assembled = bytes(group.buffer)
    fragments.pop(key, None)
    return _decode_message(
        packet,
        assembled,
        0,
        len(assembled),
        registry,
        debug,
        dump_unknowns,
        unknown_output_dir,
        logger,
        peer_id,
    )


def _expire_fragments(
    fragments: dict[tuple[str, int, str, int, int, int, int], _FragmentGroup],
    now: float,
) -> None:
    cutoff = now - _FRAGMENT_TIMEOUT_SECONDS
    for key, group in list(fragments.items()):
        if group.last_seen < cutoff:
            fragments.pop(key, None)


def _decode_message(
    packet: RawPacket,
    payload: bytes,
    offset: int,
    length: int,
    registry: PhotonRegistry | None,
    debug: bool,
    dump_unknowns: bool,
    unknown_output_dir: Path,
    logger: logging.Logger,
    peer_id: int,
) -> PhotonMessage | None:
    if length < 2:
        _dump_unknown(packet, "photon_message_short", dump_unknowns, unknown_output_dir, logger)
        return None

    offset += 1
    length -= 1

    message_type = payload[offset]
    offset += 1
    length -= 1

    message_payload = payload[offset : offset + length]

    if message_type == MESSAGE_TYPE_EVENT:
        if not message_payload:
            _dump_unknown(packet, "photon_event_short", dump_unknowns, unknown_output_dir, logger)
            return None
        event_code = message_payload[0]
        if registry and registry.has_event_codes() and not registry.is_known_event(event_code):
            _dump_unknown(packet, "photon_unknown_event", dump_unknowns, unknown_output_dir, logger)
        if debug:
            logger.debug(
                "Photon event peer=%s code=%s len=%s",
                peer_id,
                event_code,
                len(message_payload),
            )
        return PhotonMessage(
            opcode=event_code,
            event_code=event_code,
            payload=message_payload,
            message_type="event",
        )

    if message_type in (MESSAGE_TYPE_OPERATION_REQUEST, MESSAGE_TYPE_OPERATION_RESPONSE):
        if not message_payload:
            _dump_unknown(packet, "photon_operation_short", dump_unknowns, unknown_output_dir, logger)
            return None
        operation_code = message_payload[0]
        if registry and registry.has_operation_codes() and not registry.is_known_operation(operation_code):
            _dump_unknown(packet, "photon_unknown_opcode", dump_unknowns, unknown_output_dir, logger)
        if debug:
            logger.debug(
                "Photon operation peer=%s type=%s code=%s len=%s",
                peer_id,
                message_type,
                operation_code,
                len(message_payload),
            )
        message_kind = (
            "operation_request"
            if message_type == MESSAGE_TYPE_OPERATION_REQUEST
            else "operation_response"
        )
        return PhotonMessage(
            opcode=operation_code,
            event_code=None,
            payload=message_payload,
            message_type=message_kind,
        )

    _dump_unknown(packet, "photon_message_type_unknown", dump_unknowns, unknown_output_dir, logger)
    return None


def _read_u8(payload: bytes, offset: int) -> tuple[int, int]:
    return payload[offset], offset + 1


def _read_u16(payload: bytes, offset: int) -> tuple[int, int]:
    value = struct.unpack_from(">H", payload, offset)[0]
    return value, offset + 2


def _read_u32(payload: bytes, offset: int) -> tuple[int, int]:
    value = struct.unpack_from(">I", payload, offset)[0]
    return value, offset + 4


def _photon_crc(payload: bytes | bytearray) -> int:
    result = 0xFFFFFFFF
    polynomial = 0xEDB88320
    for value in payload:
        result ^= value
        for _ in range(8):
            if result & 1:
                result = (result >> 1) ^ polynomial
            else:
                result >>= 1
    return result & 0xFFFFFFFF


def _dump_unknown(
    packet: RawPacket,
    reason: str,
    dump_unknowns: bool,
    output_dir: Path,
    logger: logging.Logger,
) -> None:
    if not dump_unknowns:
        return
    try:
        dump_unknown(packet, reason=reason, output_dir=output_dir)
    except Exception:
        logger.exception("Failed to dump unknown payload")
