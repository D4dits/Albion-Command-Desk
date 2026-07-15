from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import sqlite3
import threading
import time
from uuid import uuid4

from albion_dps.domain.loot_types import LootEvent


SETTLEMENT_ACTIONS = {
    "returned",
    "sold",
    "lost",
    "allowed",
    "unreturned",
    "excluded",
}


@dataclass(frozen=True)
class LootSessionRecord:
    session_id: str
    title: str
    status: str
    started_at: float
    capture_from: float
    ended_at: float | None


class LootSessionStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, timeout=15.0)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._create_schema()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _create_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS loot_sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at REAL NOT NULL,
                capture_from REAL NOT NULL,
                ended_at REAL,
                created_at REAL NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_loot_one_active_session
                ON loot_sessions(status) WHERE status = 'active';

            CREATE TABLE IF NOT EXISTS loot_observations (
                event_id TEXT PRIMARY KEY,
                session_id TEXT REFERENCES loot_sessions(session_id) ON DELETE CASCADE,
                timestamp REAL NOT NULL,
                looter_name TEXT NOT NULL,
                looter_guild TEXT NOT NULL DEFAULT '',
                looter_alliance TEXT NOT NULL DEFAULT '',
                item_num_id INTEGER,
                item_id TEXT NOT NULL DEFAULT '',
                item_name TEXT NOT NULL DEFAULT '',
                quality INTEGER,
                quantity INTEGER NOT NULL,
                source_name TEXT NOT NULL DEFAULT '',
                source_kind TEXT NOT NULL DEFAULT 'unknown',
                is_silver INTEGER NOT NULL DEFAULT 0,
                raw_event_code INTEGER NOT NULL DEFAULT 0,
                raw_subtype INTEGER NOT NULL DEFAULT 0,
                eligibility_reason TEXT NOT NULL DEFAULT 'unknown',
                eligible INTEGER NOT NULL DEFAULT 0,
                captured_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_loot_observations_session
                ON loot_observations(session_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_loot_observations_buffer
                ON loot_observations(session_id, eligible, timestamp);

            CREATE TABLE IF NOT EXISTS loot_player_affiliations (
                player_name TEXT PRIMARY KEY,
                guild_name TEXT NOT NULL DEFAULT '',
                alliance_name TEXT NOT NULL DEFAULT '',
                last_seen REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS loot_valuations (
                event_id TEXT PRIMARY KEY REFERENCES loot_observations(event_id) ON DELETE CASCADE,
                region TEXT NOT NULL,
                city TEXT NOT NULL,
                pricing_quality INTEGER NOT NULL,
                market_unit INTEGER NOT NULL DEFAULT 0,
                liquidation_unit INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT '',
                priced_at REAL NOT NULL,
                estimated INTEGER NOT NULL DEFAULT 0,
                manual INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS loot_settlements (
                settlement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL REFERENCES loot_observations(event_id) ON DELETE CASCADE,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                actual_value INTEGER NOT NULL DEFAULT 0,
                note TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_loot_settlements_event
                ON loot_settlements(event_id, settlement_id);
            """
        )
        self._conn.commit()

    def sync_observations(self, events: list[LootEvent]) -> int:
        if not events:
            return 0
        now = time.time()
        with self._lock:
            active = self.active_session()
            count = 0
            for event in events:
                event_id = str(event.event_id or "").strip()
                if not event_id:
                    continue
                item = event.item
                eligible = event.eligibility_reason not in {"", "unknown"}
                self._conn.execute(
                    """
                    INSERT INTO loot_observations(
                        event_id, timestamp, looter_name, looter_guild, looter_alliance,
                        item_num_id, item_id, item_name, quality, quantity, source_name,
                        source_kind, is_silver, raw_event_code, raw_subtype,
                        eligibility_reason, eligible, captured_at
                    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(event_id) DO UPDATE SET
                        looter_name=excluded.looter_name,
                        looter_guild=excluded.looter_guild,
                        looter_alliance=excluded.looter_alliance,
                        quality=COALESCE(excluded.quality, loot_observations.quality),
                        eligibility_reason=excluded.eligibility_reason,
                        eligible=excluded.eligible
                    """,
                    (
                        event_id,
                        float(event.timestamp),
                        event.looted_by.player_name,
                        event.looted_by.guild_name or "",
                        event.looted_by.alliance_name or "",
                        item.item_num_id if item is not None else None,
                        item.unique_name or "" if item is not None else "",
                        item.display_name if item is not None else "",
                        item.quality if item is not None else None,
                        int(event.quantity),
                        event.looted_from.player_name
                        if event.looted_from is not None
                        else event.source_name or "",
                        event.source_kind,
                        1 if event.is_silver else 0,
                        int(event.raw_event_code),
                        int(event.raw_subtype),
                        event.eligibility_reason or "unknown",
                        1 if eligible else 0,
                        now,
                    ),
                )
                self._conn.execute(
                    """
                    INSERT INTO loot_player_affiliations(player_name, guild_name, alliance_name, last_seen)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(player_name) DO UPDATE SET
                        guild_name=CASE WHEN excluded.guild_name <> '' THEN excluded.guild_name ELSE guild_name END,
                        alliance_name=CASE WHEN excluded.alliance_name <> '' THEN excluded.alliance_name ELSE alliance_name END,
                        last_seen=MAX(last_seen, excluded.last_seen)
                    """,
                    (
                        event.looted_by.player_name,
                        event.looted_by.guild_name or "",
                        event.looted_by.alliance_name or "",
                        float(event.timestamp),
                    ),
                )
                count += 1
            if active is not None:
                self._assign_active_session(active)
            self._conn.commit()
            return count

    def start_session(
        self,
        *,
        title: str = "",
        started_at: float | None = None,
        lookback_seconds: float = 120.0,
    ) -> LootSessionRecord:
        with self._lock:
            current = self.active_session()
            if current is not None:
                return current
            started = float(started_at if started_at is not None else time.time())
            session_id = uuid4().hex
            label = str(title or "").strip() or time.strftime(
                "Loot %Y-%m-%d %H:%M", time.localtime(started)
            )
            capture_from = started - max(0.0, float(lookback_seconds))
            self._conn.execute(
                """
                INSERT INTO loot_sessions(session_id, title, status, started_at, capture_from, created_at)
                VALUES(?, ?, 'active', ?, ?, ?)
                """,
                (session_id, label, started, capture_from, time.time()),
            )
            record = LootSessionRecord(
                session_id=session_id,
                title=label,
                status="active",
                started_at=started,
                capture_from=capture_from,
                ended_at=None,
            )
            self._assign_active_session(record)
            self._conn.commit()
            return record

    def stop_session(self, *, ended_at: float | None = None) -> LootSessionRecord | None:
        with self._lock:
            current = self.active_session()
            if current is None:
                return None
            ended = float(ended_at if ended_at is not None else time.time())
            self._conn.execute(
                "UPDATE loot_sessions SET status='closed', ended_at=? WHERE session_id=?",
                (ended, current.session_id),
            )
            self._conn.commit()
            return LootSessionRecord(
                session_id=current.session_id,
                title=current.title,
                status="closed",
                started_at=current.started_at,
                capture_from=current.capture_from,
                ended_at=ended,
            )

    def active_session(self) -> LootSessionRecord | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM loot_sessions WHERE status='active' ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            return _session_from_row(row)

    def list_sessions(self, limit: int = 200) -> list[LootSessionRecord]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM loot_sessions ORDER BY started_at DESC LIMIT ?",
                (max(1, int(limit)),),
            ).fetchall()
            return [_session_from_row(row) for row in rows if row is not None]

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            cursor = self._conn.execute(
                "DELETE FROM loot_sessions WHERE session_id=? AND status <> 'active'",
                (str(session_id),),
            )
            self._conn.commit()
            return cursor.rowcount > 0

    def import_session(self, title: str, events: list[LootEvent]) -> LootSessionRecord:
        timestamps = [float(event.timestamp) for event in events if event.timestamp > 0]
        started = min(timestamps) if timestamps else time.time()
        ended = max(timestamps) if timestamps else started
        session_id = uuid4().hex
        record = LootSessionRecord(
            session_id=session_id,
            title=str(title or "Imported loot").strip() or "Imported loot",
            status="closed",
            started_at=started,
            capture_from=started,
            ended_at=ended,
        )
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO loot_sessions(
                    session_id, title, status, started_at, capture_from, ended_at, created_at
                ) VALUES(?, ?, 'closed', ?, ?, ?, ?)
                """,
                (session_id, record.title, started, started, ended, time.time()),
            )
            imported = [
                replace(
                    event,
                    event_id=event.event_id or f"import:{session_id}:{index}",
                    eligibility_reason=event.eligibility_reason or "imported",
                )
                for index, event in enumerate(events, start=1)
            ]
            self.sync_observations(imported)
            event_ids = [event.event_id for event in imported]
            if event_ids:
                placeholders = ",".join("?" for _ in event_ids)
                self._conn.execute(
                    f"UPDATE loot_observations SET session_id=? WHERE event_id IN ({placeholders})",
                    [session_id, *event_ids],
                )
            self._conn.commit()
            return record

    def loot_rows(
        self,
        *,
        session_id: str | None = None,
        buffer_limit: int = 2000,
    ) -> list[dict[str, object]]:
        with self._lock:
            if session_id:
                rows = self._conn.execute(
                    """
                    SELECT o.*, v.region, v.city, v.pricing_quality, v.market_unit,
                           v.liquidation_unit, v.source AS price_source,
                           v.priced_at, v.estimated, v.manual
                    FROM loot_observations o
                    LEFT JOIN loot_valuations v ON v.event_id=o.event_id
                    WHERE o.session_id=? AND o.eligible=1
                    ORDER BY o.timestamp DESC, o.event_id DESC
                    """,
                    (session_id,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """
                    SELECT o.*, v.region, v.city, v.pricing_quality, v.market_unit,
                           v.liquidation_unit, v.source AS price_source,
                           v.priced_at, v.estimated, v.manual
                    FROM loot_observations o
                    LEFT JOIN loot_valuations v ON v.event_id=o.event_id
                    WHERE o.eligible=1
                    ORDER BY o.timestamp DESC, o.event_id DESC LIMIT ?
                    """,
                    (max(1, int(buffer_limit)),),
                ).fetchall()
            event_ids = [str(row["event_id"]) for row in rows]
            ledger = self._settlement_totals(event_ids)
            actual_values = self._settlement_actual_values(event_ids)
            result: list[dict[str, object]] = []
            for raw in rows:
                row = dict(raw)
                totals = ledger.get(str(raw["event_id"]), {})
                settled = sum(int(value) for value in totals.values())
                quantity = int(raw["quantity"])
                row["settlements"] = totals
                row["settled_quantity"] = min(quantity, settled)
                row["outstanding_quantity"] = max(0, quantity - settled)
                row["settlement_status"] = _settlement_status(quantity, totals)
                row["actual_sold_value"] = actual_values.get(str(raw["event_id"]), 0)
                result.append(row)
            return result

    def pending_scope_count(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS count FROM loot_observations WHERE eligible=0"
            ).fetchone()
            return int(row["count"] if row is not None else 0)

    def add_settlement(
        self,
        event_id: str,
        *,
        action: str,
        quantity: int | None = None,
        actual_value: int = 0,
        note: str = "",
    ) -> bool:
        normalized = str(action or "").strip().lower()
        if normalized not in SETTLEMENT_ACTIONS:
            return False
        with self._lock:
            row = self._conn.execute(
                "SELECT quantity FROM loot_observations WHERE event_id=?",
                (str(event_id),),
            ).fetchone()
            if row is None:
                return False
            totals = self._settlement_totals([str(event_id)]).get(str(event_id), {})
            remaining = max(0, int(row["quantity"]) - sum(totals.values()))
            requested = remaining if quantity is None or int(quantity) <= 0 else int(quantity)
            applied = min(remaining, requested)
            if applied <= 0:
                return False
            self._conn.execute(
                """
                INSERT INTO loot_settlements(event_id, action, quantity, actual_value, note, created_at)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event_id),
                    normalized,
                    applied,
                    max(0, int(actual_value)),
                    str(note or "").strip(),
                    time.time(),
                ),
            )
            self._conn.commit()
            return True

    def reset_settlements(self, event_id: str, *, note: str = "") -> bool:
        with self._lock:
            exists = self._conn.execute(
                "SELECT 1 FROM loot_observations WHERE event_id=?", (str(event_id),)
            ).fetchone()
            if exists is None:
                return False
            self._conn.execute(
                """
                INSERT INTO loot_settlements(event_id, action, quantity, actual_value, note, created_at)
                VALUES(?, 'reset', 0, 0, ?, ?)
                """,
                (str(event_id), str(note or "").strip(), time.time()),
            )
            self._conn.commit()
            return True

    def settle_player(
        self,
        session_id: str,
        player_name: str,
        *,
        action: str,
        note: str = "",
    ) -> int:
        normalized = str(action or "").strip().lower()
        if normalized != "pending" and normalized not in SETTLEMENT_ACTIONS:
            return 0
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT event_id FROM loot_observations
                WHERE session_id=? AND looter_name=? AND eligible=1
                """,
                (str(session_id), str(player_name)),
            ).fetchall()
            changed = 0
            for row in rows:
                event_id = str(row["event_id"])
                if normalized == "pending":
                    changed += int(self.reset_settlements(event_id, note=note))
                else:
                    changed += int(
                        self.add_settlement(
                            event_id,
                            action=normalized,
                            quantity=None,
                            note=note,
                        )
                    )
            return changed

    def upsert_valuation(
        self,
        event_id: str,
        *,
        region: str,
        city: str,
        pricing_quality: int,
        market_unit: int,
        liquidation_unit: int,
        source: str,
        estimated: bool,
        manual: bool = False,
    ) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO loot_valuations(
                    event_id, region, city, pricing_quality, market_unit,
                    liquidation_unit, source, priced_at, estimated, manual
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    region=excluded.region, city=excluded.city,
                    pricing_quality=excluded.pricing_quality,
                    market_unit=excluded.market_unit,
                    liquidation_unit=excluded.liquidation_unit,
                    source=excluded.source, priced_at=excluded.priced_at,
                    estimated=excluded.estimated, manual=excluded.manual
                """,
                (
                    str(event_id),
                    str(region),
                    str(city),
                    min(5, max(1, int(pricing_quality))),
                    max(0, int(market_unit)),
                    max(0, int(liquidation_unit)),
                    str(source),
                    time.time(),
                    1 if estimated else 0,
                    1 if manual else 0,
                ),
            )
            self._conn.commit()

    def set_quality(self, event_id: str, quality: int | None) -> bool:
        normalized = int(quality) if quality is not None else None
        if normalized is not None and normalized not in range(1, 6):
            return False
        with self._lock:
            cursor = self._conn.execute(
                "UPDATE loot_observations SET quality=? WHERE event_id=?",
                (normalized, str(event_id)),
            )
            self._conn.execute("DELETE FROM loot_valuations WHERE event_id=?", (str(event_id),))
            self._conn.commit()
            return cursor.rowcount > 0

    def prune_buffer(self, *, retention_seconds: float = 86400.0) -> int:
        cutoff = time.time() - max(60.0, float(retention_seconds))
        with self._lock:
            cursor = self._conn.execute(
                "DELETE FROM loot_observations WHERE session_id IS NULL AND captured_at < ?",
                (cutoff,),
            )
            self._conn.commit()
            return max(0, int(cursor.rowcount))

    def _assign_active_session(self, active: LootSessionRecord) -> None:
        self._conn.execute(
            """
            UPDATE loot_observations SET session_id=?
            WHERE session_id IS NULL AND eligible=1 AND timestamp >= ?
            """,
            (active.session_id, active.capture_from),
        )

    def _settlement_totals(self, event_ids: list[str]) -> dict[str, dict[str, int]]:
        if not event_ids:
            return {}
        placeholders = ",".join("?" for _ in event_ids)
        rows = self._conn.execute(
            f"""
            SELECT event_id, action, quantity FROM loot_settlements
            WHERE event_id IN ({placeholders}) ORDER BY settlement_id
            """,
            event_ids,
        ).fetchall()
        result: dict[str, dict[str, int]] = {}
        for row in rows:
            event_id = str(row["event_id"])
            action = str(row["action"])
            if action == "reset":
                result[event_id] = {}
                continue
            bucket = result.setdefault(event_id, {})
            bucket[action] = bucket.get(action, 0) + max(0, int(row["quantity"]))
        return result

    def _settlement_actual_values(self, event_ids: list[str]) -> dict[str, int]:
        if not event_ids:
            return {}
        placeholders = ",".join("?" for _ in event_ids)
        rows = self._conn.execute(
            f"""
            SELECT event_id, action, actual_value FROM loot_settlements
            WHERE event_id IN ({placeholders}) ORDER BY settlement_id
            """,
            event_ids,
        ).fetchall()
        result: dict[str, int] = {}
        for row in rows:
            event_id = str(row["event_id"])
            action = str(row["action"])
            if action == "reset":
                result[event_id] = 0
            elif action == "sold":
                result[event_id] = result.get(event_id, 0) + max(
                    0, int(row["actual_value"])
                )
        return result


def _session_from_row(row: sqlite3.Row | None) -> LootSessionRecord | None:
    if row is None:
        return None
    return LootSessionRecord(
        session_id=str(row["session_id"]),
        title=str(row["title"]),
        status=str(row["status"]),
        started_at=float(row["started_at"]),
        capture_from=float(row["capture_from"]),
        ended_at=float(row["ended_at"]) if row["ended_at"] is not None else None,
    )


def _settlement_status(quantity: int, totals: dict[str, int]) -> str:
    settled = sum(max(0, int(value)) for value in totals.values())
    if settled <= 0:
        return "pending"
    if settled < max(0, int(quantity)):
        return "partial"
    active = [action for action, value in totals.items() if value > 0]
    if len(active) == 1:
        return active[0]
    return "resolved"
