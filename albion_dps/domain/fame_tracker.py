from __future__ import annotations

from dataclasses import dataclass, field

from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.protocol.protocol16 import Protocol16Error, decode_event_data

FIXPOINT_FACTOR = 10000.0

FAME_EVENT_CODE = 1
FAME_SUBTYPE_KEY = 252
FAME_SUBTYPE_VALUES = {72, 82}
SILVER_SUBTYPE_VALUE = 275

FAME_TOTAL_PLAYER_KEY = 1
FAME_BASE_FAME_KEY = 2
FAME_ZONE_FAME_KEY = 3
FAME_PREMIUM_KEY = 5
FAME_BONUS_KEY = 6
FAME_BONUS_ALT_KEY = 17
FAME_SATCHEL_FAME_KEY = 10
FAME_SOURCE_ID_KEY = 0
SILVER_GAIN_KEY = 5
SILVER_SOURCE_ID_KEY = 0


@dataclass
class FameTracker:
    _total_gained: int = 0
    _last_total_player: int | None = None
    _start_ts: float | None = None
    _last_ts: float | None = None
    _silver_total: int = 0
    _silver_start_ts: float | None = None
    _silver_last_ts: float | None = None
    _self_source_ids: set[int] = field(default_factory=set)

    def observe(self, message: PhotonMessage, packet: RawPacket) -> None:
        if message.event_code is None or message.event_code != FAME_EVENT_CODE:
            return
        try:
            event = decode_event_data(message.payload)
        except Protocol16Error:
            return
        subtype = event.parameters.get(FAME_SUBTYPE_KEY)
        if subtype in FAME_SUBTYPE_VALUES:
            self._observe_fame(event.parameters, packet.timestamp)
        if subtype == SILVER_SUBTYPE_VALUE:
            self._observe_silver(event.parameters, packet.timestamp)

    def _observe_fame(self, parameters: dict[int, object], timestamp: float) -> None:
        if parameters.get(FAME_SUBTYPE_KEY) not in FAME_SUBTYPE_VALUES:
            return
        source_id = parameters.get(FAME_SOURCE_ID_KEY)
        if isinstance(source_id, int):
            self._self_source_ids.add(source_id)
        total_player = parameters.get(FAME_TOTAL_PLAYER_KEY)
        if isinstance(total_player, int):
            if self._last_total_player is not None and total_player <= self._last_total_player:
                return
            self._last_total_player = total_player

        gained = _compute_gained_fame(parameters)
        if gained is None or gained <= 0:
            return
        self._total_gained += gained
        if self._start_ts is None:
            self._start_ts = timestamp
        self._last_ts = timestamp

    def _observe_silver(self, parameters: dict[int, object], timestamp: float) -> None:
        if not self._self_source_ids:
            return
        source_id = parameters.get(SILVER_SOURCE_ID_KEY)
        if (
            isinstance(source_id, int)
            and self._self_source_ids
            and source_id not in self._self_source_ids
        ):
            return
        gained = _compute_gained_silver(parameters)
        if gained is None or gained <= 0:
            return
        self._silver_total += gained
        if self._silver_start_ts is None:
            self._silver_start_ts = timestamp
        self._silver_last_ts = timestamp

    def reset(self) -> None:
        self._total_gained = 0
        self._silver_total = 0
        if self._last_ts is None:
            self._start_ts = None
        else:
            self._start_ts = self._last_ts
        if self._silver_last_ts is None:
            self._silver_start_ts = None
        else:
            self._silver_start_ts = self._silver_last_ts

    def total(self) -> int:
        return self._total_gained

    def per_hour(self) -> float:
        if self._start_ts is None or self._last_ts is None:
            return 0.0
        elapsed = self._last_ts - self._start_ts
        if elapsed <= 0:
            return 0.0
        return self.total() / (elapsed / 3600.0)

    def silver_total(self) -> int:
        return self._silver_total

    def silver_per_hour(self) -> float:
        if self._silver_start_ts is None or self._silver_last_ts is None:
            return 0.0
        elapsed = self._silver_last_ts - self._silver_start_ts
        if elapsed <= 0:
            return 0.0
        return self.silver_total() / (elapsed / 3600.0)


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


def _compute_gained_silver(parameters: dict[int, object]) -> int | None:
    silver = _fixpoint_to_float(parameters.get(SILVER_GAIN_KEY))
    if silver is None or silver <= 0:
        return None
    # Silver events are encoded as fixed-point values (e.g. 560.5590); we
    # display whole silver in UI using floor semantics.
    return int(silver)


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

