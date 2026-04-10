from __future__ import annotations

from datetime import datetime
from pathlib import Path

from albion_dps.domain.loot_export import loot_events_to_txt
from albion_dps.domain.loot_types import LootEvent


class LootLogWriter:
    def __init__(
        self,
        *,
        output_dir: str | Path = "artifacts/loot",
        session_started_at: datetime | None = None,
    ) -> None:
        started_at = session_started_at or datetime.now()
        timestamp = started_at.strftime("%Y-%m-%d-%H-%M-%S")
        self._output_dir = Path(output_dir).expanduser().resolve()
        self._path = self._output_dir / f"loot-events-{timestamp}.txt"
        self._last_payload: str | None = None

    @property
    def path(self) -> Path:
        return self._path

    def sync_events(self, events: list[LootEvent]) -> Path:
        payload = loot_events_to_txt(events)
        if payload == self._last_payload and self._path.exists():
            return self._path
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._path.write_text(payload, encoding="utf-8")
        self._last_payload = payload
        return self._path
