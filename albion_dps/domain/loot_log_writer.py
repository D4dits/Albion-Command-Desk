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
        keep_files: int = 5,
    ) -> None:
        started_at = session_started_at or datetime.now()
        timestamp = started_at.strftime("%Y-%m-%d-%H-%M-%S")
        self._output_dir = Path(output_dir).expanduser().resolve()
        self._path = self._output_dir / f"loot-events-{timestamp}.txt"
        self._last_payload: str | None = None
        self._keep_files = max(1, int(keep_files))

    @property
    def path(self) -> Path:
        return self._path

    @property
    def keep_files(self) -> int:
        return self._keep_files

    def set_keep_files(self, value: int) -> None:
        self._keep_files = max(1, int(value))
        self._prune_old_files()

    def sync_events(self, events: list[LootEvent]) -> Path:
        payload = loot_events_to_txt([event for event in events if not event.is_silver])
        if payload == self._last_payload and self._path.exists():
            self._prune_old_files()
            return self._path
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._path.write_text(payload, encoding="utf-8")
        self._last_payload = payload
        self._prune_old_files()
        return self._path

    def _prune_old_files(self) -> None:
        if self._keep_files <= 0 or not self._output_dir.exists():
            return
        files = sorted(
            self._output_dir.glob("loot-events-*.txt"),
            key=lambda path: (path.name, path.stat().st_mtime if path.exists() else 0.0),
            reverse=True,
        )
        for stale in files[self._keep_files :]:
            try:
                stale.unlink()
            except OSError:
                continue
