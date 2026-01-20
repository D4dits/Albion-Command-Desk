from __future__ import annotations

from dataclasses import dataclass

from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.protocol.protocol16 import Protocol16Error, decode_event_data

FIXPOINT_FACTOR = 10000.0

FAME_EVENT_CODE = 1
FAME_SUBTYPE_KEY = 252
FAME_SUBTYPE_VALUES = {72, 82}

FAME_TOTAL_PLAYER_KEY = 1
FAME_BASE_FAME_KEY = 2
FAME_ZONE_FAME_KEY = 3
FAME_PREMIUM_KEY = 5
FAME_BONUS_KEY = 6
FAME_BONUS_ALT_KEY = 17
FAME_SATCHEL_FAME_KEY = 10


@dataclass
class FameTracker:
    _total_gained: int = 0
    _last_total_player: int | None = None
    _start_ts: float | None = None
    _last_ts: float | None = None

    def observe(self, message: PhotonMessage, packet: RawPacket) -> None:
        if message.event_code is None or message.event_code != FAME_EVENT_CODE:
            return
        try:
            event = decode_event_data(message.payload)
        except Protocol16Error:
            return
        if event.parameters.get(FAME_SUBTYPE_KEY) not in FAME_SUBTYPE_VALUES:
            return
        total_player = event.parameters.get(FAME_TOTAL_PLAYER_KEY)
        if isinstance(total_player, int):
            if self._last_total_player is not None and total_player <= self._last_total_player:
                return
            self._last_total_player = total_player

        gained = _compute_gained_fame(event.parameters)
        if gained is None or gained <= 0:
            return
        self._total_gained += gained
        if self._start_ts is None:
            self._start_ts = packet.timestamp
        self._last_ts = packet.timestamp

    def reset(self) -> None:
        self._total_gained = 0
        if self._last_ts is None:
            self._start_ts = None
        else:
            self._start_ts = self._last_ts

    def total(self) -> int:
        return self._total_gained

    def per_hour(self) -> float:
        if self._start_ts is None or self._last_ts is None:
            return 0.0
        elapsed = self._last_ts - self._start_ts
        if elapsed <= 0:
            return 0.0
        return self.total() / (elapsed / 3600.0)


def _compute_gained_fame(parameters: dict[int, object]) -> int | None:
    base_fame = _fixpoint_to_float(parameters.get(FAME_BASE_FAME_KEY))
    if base_fame is None:
        return None
    premium = _coerce_bool(parameters.get(FAME_PREMIUM_KEY))
    satchel_fame = _fixpoint_to_float(parameters.get(FAME_SATCHEL_FAME_KEY)) or 0.0

    total = base_fame
    if premium:
        total += base_fame * 0.5
    total += satchel_fame
    if total <= 0:
        return None
    return int(round(total))


def _fixpoint_to_float(value: object) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int):
        return value / FIXPOINT_FACTOR
    if isinstance(value, float):
        return value
    return None


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, float):
        return value != 0.0
    return False

