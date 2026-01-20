from __future__ import annotations

from collections import deque

from albion_dps.models import CombatEvent, MeterSnapshot


class RollingMeter:
    def __init__(
        self, window_seconds: float = 10.0, session_timeout_seconds: float | None = 20.0
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if session_timeout_seconds is not None and session_timeout_seconds <= 0:
            raise ValueError("session_timeout_seconds must be positive or None")
        self._window_seconds = window_seconds
        self._session_timeout_seconds = session_timeout_seconds
        self._totals: dict[int, dict[str, float]] = {}
        self._rolling_damage: dict[int, float] = {}
        self._rolling_heal: dict[int, float] = {}
        self._damage_events: deque[tuple[float, int, float]] = deque()
        self._heal_events: deque[tuple[float, int, float]] = deque()
        self._last_event_timestamp: float | None = None
        self._last_seen_timestamp: float | None = None

    def push(self, event: CombatEvent) -> None:
        if (
            self._last_event_timestamp is not None
            and self._session_timeout_seconds is not None
        ):
            if event.timestamp - self._last_event_timestamp >= self._session_timeout_seconds:
                self._reset_state(now=event.timestamp)

        if (
            self._last_event_timestamp is None
            or event.timestamp > self._last_event_timestamp
        ):
            self._last_event_timestamp = event.timestamp
        if self._last_seen_timestamp is None or event.timestamp > self._last_seen_timestamp:
            self._last_seen_timestamp = event.timestamp

        totals = self._totals.setdefault(event.source_id, {"damage": 0.0, "heal": 0.0})
        amount = float(event.amount)

        if event.kind == "damage":
            totals["damage"] += amount
            self._damage_events.append((event.timestamp, event.source_id, amount))
            self._rolling_damage[event.source_id] = (
                self._rolling_damage.get(event.source_id, 0.0) + amount
            )
        elif event.kind == "heal":
            totals["heal"] += amount
            self._heal_events.append((event.timestamp, event.source_id, amount))
            self._rolling_heal[event.source_id] = (
                self._rolling_heal.get(event.source_id, 0.0) + amount
            )
        else:
            return

        if self._last_seen_timestamp is not None:
            self._expire_old(self._last_seen_timestamp)

    def touch(self, timestamp: float) -> None:
        if self._last_seen_timestamp is None or timestamp > self._last_seen_timestamp:
            self._last_seen_timestamp = timestamp
        if (
            self._last_event_timestamp is not None
            and self._session_timeout_seconds is not None
            and self._last_seen_timestamp is not None
        ):
            if (
                self._last_seen_timestamp - self._last_event_timestamp
                >= self._session_timeout_seconds
            ):
                self._reset_state(now=self._last_seen_timestamp)
        if self._last_seen_timestamp is not None:
            self._expire_old(self._last_seen_timestamp)

    def snapshot(self, now: float | None = None) -> MeterSnapshot:
        if now is None:
            now = self._last_seen_timestamp
            if now is None:
                now = self._last_event_timestamp or 0.0
        elif self._last_seen_timestamp is None or now > self._last_seen_timestamp:
            self._last_seen_timestamp = now
        self._expire_old(now)
        totals: dict[int, dict[str, float]] = {}
        for source_id, stats in self._totals.items():
            dps = self._rolling_damage.get(source_id, 0.0) / self._window_seconds
            hps = self._rolling_heal.get(source_id, 0.0) / self._window_seconds
            totals[source_id] = {
                "damage": stats["damage"],
                "heal": stats["heal"],
                "dps": dps,
                "hps": hps,
            }
        return MeterSnapshot(timestamp=now, totals=totals)

    def _expire_old(self, now: float) -> None:
        cutoff = now - self._window_seconds
        while self._damage_events and self._damage_events[0][0] < cutoff:
            _ts, source_id, amount = self._damage_events.popleft()
            current = self._rolling_damage.get(source_id, 0.0) - amount
            if current <= 0:
                self._rolling_damage.pop(source_id, None)
            else:
                self._rolling_damage[source_id] = current
        while self._heal_events and self._heal_events[0][0] < cutoff:
            _ts, source_id, amount = self._heal_events.popleft()
            current = self._rolling_heal.get(source_id, 0.0) - amount
            if current <= 0:
                self._rolling_heal.pop(source_id, None)
            else:
                self._rolling_heal[source_id] = current

    def _reset_state(self, now: float | None = None) -> None:
        self._totals.clear()
        self._rolling_damage.clear()
        self._rolling_heal.clear()
        self._damage_events.clear()
        self._heal_events.clear()
        self._last_event_timestamp = None
        self._last_seen_timestamp = now
