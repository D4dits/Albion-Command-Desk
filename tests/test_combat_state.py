from __future__ import annotations

from albion_dps.models import PhotonMessage
from albion_dps.pipeline import _decode_combat_state


def test_decode_combat_state_active_flags() -> None:
    payload_hex = "01000400690001498f016f01026f01fc6b0112"
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(payload_hex))

    assert _decode_combat_state(message) == (84367, True, True)


def test_decode_combat_state_inactive_flags() -> None:
    payload_hex = "01000200690001498ffc6b0112"
    message = PhotonMessage(opcode=1, event_code=1, payload=bytes.fromhex(payload_hex))

    assert _decode_combat_state(message) == (84367, False, False)
