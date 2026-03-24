from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from albion_dps.models import PhotonMessage, RawPacket
from albion_dps.protocol.map_index import extract_map_index


@dataclass(frozen=True)
class SessionActivityEvent:
    kind: str
    title: str
    detail: str
    timestamp: float


@dataclass
class MapTrailTracker:
    map_lookup: Callable[[str], str | None] | None = None
    history_limit: int = 24
    _current_map_index: str | None = None
    _events: deque[SessionActivityEvent] = field(default_factory=lambda: deque(maxlen=24))

    def __post_init__(self) -> None:
        if self._events.maxlen != self.history_limit:
            self._events = deque(self._events, maxlen=self.history_limit)

    def observe_message(self, message: PhotonMessage, packet: RawPacket | None = None) -> None:
        map_index = extract_map_index(message)
        if not map_index:
            return
        timestamp = packet.timestamp if packet is not None else 0.0
        if map_index == self._current_map_index:
            return
        self._current_map_index = map_index
        label = map_index
        if self.map_lookup is not None:
            resolved = self.map_lookup(map_index)
            if resolved:
                label = resolved
        detail = "Map entered" if not self._events else "Map changed"
        self._events.append(
            SessionActivityEvent(
                kind="map",
                title=label,
                detail=detail,
                timestamp=timestamp,
            )
        )

    def events(self, limit: int | None = None) -> list[SessionActivityEvent]:
        items = list(reversed(self._events))
        if limit is None:
            return items
        return items[: max(limit, 0)]
