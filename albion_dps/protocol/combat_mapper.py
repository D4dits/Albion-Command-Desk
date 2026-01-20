from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from albion_dps.models import CombatEvent, PhotonMessage, RawPacket
from albion_dps.protocol.protocol16 import Protocol16Error, decode_event_data
from albion_dps.protocol.unknown_dump import dump_unknown

HEALTH_UPDATE_EVENTS = {6, 7}
EVENT_CODE_PARAM = 252
PARAM_AFFECTED_ID = 0
PARAM_HEALTH_CHANGE = 2
PARAM_CURRENT_HEALTH = 3
PARAM_CAUSER_ID = 6
HP_STATE_TTL_SECONDS = 30.0


@dataclass(frozen=True)
class CombatEventMapper:
    dump_unknowns: bool = False
    unknown_output_dir: str | Path = "artifacts/unknown"
    clamp_overkill: bool = False
    _target_hp: dict[int, float] = field(default_factory=dict, init=False, repr=False)
    _target_hp_last_ts: dict[int, float] = field(
        default_factory=dict, init=False, repr=False
    )

    def map(self, message: PhotonMessage, packet: RawPacket) -> CombatEvent | None:
        if message.event_code is None:
            return None

        try:
            event = decode_event_data(message.payload)
        except Protocol16Error:
            if self.dump_unknowns:
                dump_unknown(packet, reason="protocol16_decode_failed", output_dir=self.unknown_output_dir)
            return None

        event_type = event.parameters.get(EVENT_CODE_PARAM)
        if event_type is None:
            event_type = event.code
        if event_type not in HEALTH_UPDATE_EVENTS:
            return None

        changes = _coerce_float_list(event.parameters.get(PARAM_HEALTH_CHANGE))
        if not changes:
            return None

        targets = _coerce_int_list(event.parameters.get(PARAM_AFFECTED_ID), len(changes))
        sources = _coerce_int_list(event.parameters.get(PARAM_CAUSER_ID), len(changes))
        current_hp = _coerce_float_list(event.parameters.get(PARAM_CURRENT_HEALTH))

        if self.clamp_overkill:
            self._expire_hp(packet.timestamp)

        events: list[CombatEvent] = []
        for index, change in enumerate(changes):
            if change is None or change == 0:
                continue
            target_id = targets[index] if index < len(targets) else None
            source_id = sources[index] if index < len(sources) else None
            if source_id is None:
                source_id = target_id
            if source_id is None or target_id is None:
                continue

            kind = "heal" if change > 0 else "damage"
            raw_amount = float(abs(change))
            amount = raw_amount
            if self.clamp_overkill:
                amount = self._clamp_amount(
                    kind,
                    target_id,
                    raw_amount,
                    current_hp[index] if index < len(current_hp) else None,
                    packet.timestamp,
                )
            amount_int = int(round(amount))
            if amount_int <= 0:
                continue

            events.append(
                CombatEvent(
                    timestamp=packet.timestamp,
                    source_id=source_id,
                    target_id=target_id,
                    amount=amount_int,
                    kind=kind,
                )
            )

        if not events:
            return None
        if len(events) == 1:
            return events[0]
        return events

    def _clamp_amount(
        self,
        kind: str,
        target_id: int,
        raw_amount: float,
        hp_after: float | None,
        timestamp: float,
    ) -> float:
        prev_hp = self._target_hp.get(target_id)

        if hp_after is not None:
            hp_after = max(float(hp_after), 0.0)
            if kind == "damage" and prev_hp is not None:
                applied = max(prev_hp - hp_after, 0.0)
                applied = min(applied, raw_amount)
            else:
                applied = raw_amount
            self._target_hp[target_id] = hp_after
            self._target_hp_last_ts[target_id] = timestamp
            return applied

        if prev_hp is None:
            return raw_amount

        if kind == "damage":
            applied = min(raw_amount, max(prev_hp, 0.0))
            self._target_hp[target_id] = max(prev_hp - applied, 0.0)
            self._target_hp_last_ts[target_id] = timestamp
            return applied

        if kind == "heal":
            self._target_hp[target_id] = prev_hp + raw_amount
            self._target_hp_last_ts[target_id] = timestamp
            return raw_amount

        return raw_amount

    def _expire_hp(self, now: float) -> None:
        cutoff = now - HP_STATE_TTL_SECONDS
        for target_id, ts in list(self._target_hp_last_ts.items()):
            if ts < cutoff:
                self._target_hp_last_ts.pop(target_id, None)
                self._target_hp.pop(target_id, None)


def _coerce_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return int(value)
    return None


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _coerce_float_list(value: Any) -> list[float | None]:
    if isinstance(value, list):
        return [_coerce_float(item) for item in value]
    single = _coerce_float(value)
    if single is None:
        return []
    return [single]


def _coerce_int_list(value: Any, count: int) -> list[int | None]:
    if count <= 0:
        return []
    if isinstance(value, list):
        values = [_coerce_int(item) for item in value]
        if len(values) == count:
            return values
        if len(values) == 1:
            return values * count
        output: list[int | None] = []
        for idx in range(count):
            output.append(values[idx] if idx < len(values) else None)
        return output
    single = _coerce_int(value)
    if single is None:
        return [None] * count
    return [single] * count
