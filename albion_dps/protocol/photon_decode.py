from __future__ import annotations

import logging
import struct
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
        _dump_unknown(packet, "photon_crc_unsupported", dump_unknowns, unknown_output_dir, logger)
        return messages

    for _ in range(command_count):
        if offset + _COMMAND_HEADER_LEN > len(payload):
            _dump_unknown(packet, "photon_command_header_short", dump_unknowns, unknown_output_dir, logger)
            return messages

        command_type, offset = _read_u8(payload, offset)
        _channel_id, offset = _read_u8(payload, offset)
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
            offset += body_length
            continue

        if command_type == COMMAND_TYPE_DISCONNECT:
            offset += body_length
            continue

        offset += body_length

    return messages


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
        return PhotonMessage(opcode=event_code, event_code=event_code, payload=message_payload)

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
        return PhotonMessage(opcode=operation_code, event_code=None, payload=message_payload)

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
