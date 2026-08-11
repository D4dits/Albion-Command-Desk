from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from albion_dps.meter.session_meter import SessionSummary


class MeterHistoryStore:
    """Small durable store for completed meter encounters."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, timeout=15.0)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meter_encounters (
                    encounter_id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    start_ts REAL NOT NULL,
                    end_ts REAL NOT NULL,
                    source TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_meter_encounters_mode_end "
                "ON meter_encounters(mode, end_ts DESC)"
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def save(self, summary: SessionSummary) -> None:
        payload = _summary_to_json(summary)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO meter_encounters(
                    encounter_id, mode, start_ts, end_ts, source, payload
                ) VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(encounter_id) DO UPDATE SET
                    mode=excluded.mode,
                    start_ts=excluded.start_ts,
                    end_ts=excluded.end_ts,
                    source=excluded.source,
                    payload=excluded.payload,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    summary.encounter_id,
                    summary.mode,
                    float(summary.start_ts),
                    float(summary.end_ts),
                    summary.source,
                    payload,
                ),
            )
            self._conn.commit()

    def load(self, mode: str, limit: int) -> list[SessionSummary]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT payload FROM meter_encounters WHERE mode=? "
                "ORDER BY end_ts DESC LIMIT ?",
                (mode, max(1, int(limit))),
            ).fetchall()
        return [_summary_from_json(str(row["payload"])) for row in rows]

    def delete(self, encounter_id: str) -> bool:
        with self._lock:
            cursor = self._conn.execute(
                "DELETE FROM meter_encounters WHERE encounter_id=?", (encounter_id,)
            )
            self._conn.commit()
            return cursor.rowcount > 0

    def clear(self, mode: str | None = None) -> int:
        with self._lock:
            if mode is None:
                cursor = self._conn.execute("DELETE FROM meter_encounters")
            else:
                cursor = self._conn.execute(
                    "DELETE FROM meter_encounters WHERE mode=?", (mode,)
                )
            self._conn.commit()
            return max(0, cursor.rowcount)

    def prune(self, mode: str, keep: int) -> None:
        with self._lock:
            self._conn.execute(
                """
                DELETE FROM meter_encounters
                WHERE mode=? AND encounter_id NOT IN (
                    SELECT encounter_id FROM meter_encounters
                    WHERE mode=? ORDER BY end_ts DESC LIMIT ?
                )
                """,
                (mode, mode, max(1, int(keep))),
            )
            self._conn.commit()


def _summary_to_json(summary: SessionSummary) -> str:
    return json.dumps(
        {
            "encounter_id": summary.encounter_id,
            "mode": summary.mode,
            "start_ts": summary.start_ts,
            "end_ts": summary.end_ts,
            "duration": summary.duration,
            "label": summary.label,
            "entries": [
                {
                    "label": entry.label,
                    "damage": entry.damage,
                    "heal": entry.heal,
                    "dps": entry.dps,
                    "hps": entry.hps,
                    "source_id": entry.source_id,
                }
                for entry in summary.entries
            ],
            "total_damage": summary.total_damage,
            "total_heal": summary.total_heal,
            "reason": summary.reason,
            "totals_by_id": {
                str(entity_id): stats
                for entity_id, stats in summary.totals_by_id.items()
            },
            "source": summary.source,
            "roster_names": list(summary.roster_names),
            "participant_names": list(summary.participant_names),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _summary_from_json(payload: str) -> SessionSummary:
    from albion_dps.meter.session_meter import SessionEntry, SessionSummary

    raw = json.loads(payload)
    return SessionSummary(
        mode=str(raw.get("mode", "battle")),
        start_ts=float(raw.get("start_ts", 0.0)),
        end_ts=float(raw.get("end_ts", 0.0)),
        duration=float(raw.get("duration", 0.0)),
        label=raw.get("label"),
        entries=[SessionEntry(**entry) for entry in raw.get("entries", [])],
        total_damage=float(raw.get("total_damage", 0.0)),
        total_heal=float(raw.get("total_heal", 0.0)),
        reason=str(raw.get("reason", "unknown")),
        totals_by_id={
            int(entity_id): {
                str(key): float(value) for key, value in stats.items()
            }
            for entity_id, stats in raw.get("totals_by_id", {}).items()
        },
        encounter_id=str(raw.get("encounter_id", "")),
        source=str(raw.get("source", "live")),
        roster_names=tuple(str(item) for item in raw.get("roster_names", [])),
        participant_names=tuple(
            str(item) for item in raw.get("participant_names", [])
        ),
    )
