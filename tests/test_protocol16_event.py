from __future__ import annotations

from albion_dps.protocol.protocol16 import decode_event_data, decode_operation_request


_NEGATIVE_PAYLOAD_HEX = (
    "010009006b58170169002000310266c329000003664495c000046201056202066b5809076b0d34fc6b0006"
)
_LIST_PAYLOAD_HEX = (
    "010009006900013aff0179000269005976c8005977540279000266c2ec000041a8000003790002664500d0004502200004780000000202020578000000020303067900026900013a0300013aff077900026b0bd50eb6fc6b0007"
)
_OP_REQUEST_PAYLOAD_HEX = (
    "010007006c08de4f767cdfd80e0179000266c2d54548c3a86591026641e9383503"
    "79000266c2cb9bbcc3a659be046640f6666605690001867cfd6b0015"
)


def test_decode_event_data_health_update() -> None:
    event = decode_event_data(bytes.fromhex(_NEGATIVE_PAYLOAD_HEX))

    assert event.code == 1
    assert event.parameters[0] == 22551
    assert event.parameters[2] == -169.0
    assert event.parameters[6] == 22537


def test_decode_event_data_array_parameters() -> None:
    event = decode_event_data(bytes.fromhex(_LIST_PAYLOAD_HEX))

    assert event.code == 1
    assert event.parameters[0] == 80639
    assert event.parameters[2] == [-118.0, 21.0]


def test_decode_operation_request() -> None:
    request = decode_operation_request(bytes.fromhex(_OP_REQUEST_PAYLOAD_HEX))

    assert request.code == 1
    assert request.parameters[5] == 99964
