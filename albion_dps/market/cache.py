from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CacheEntry:
    key: str
    payload: object
    expires_at: float
    updated_at: float

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at


class SQLiteCache:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_cache (
                cache_key TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                expires_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def set(self, key: str, payload: object, ttl_seconds: float) -> None:
        now = time.time()
        expires_at = now + max(0.0, ttl_seconds)
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        self._conn.execute(
            """
            INSERT INTO market_cache(cache_key, payload_json, expires_at, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
              payload_json=excluded.payload_json,
              expires_at=excluded.expires_at,
              updated_at=excluded.updated_at
            """,
            (key, payload_json, expires_at, now),
        )
        self._conn.commit()

    def get_entry(self, key: str, *, allow_expired: bool = False) -> CacheEntry | None:
        row = self._conn.execute(
            """
            SELECT cache_key, payload_json, expires_at, updated_at
            FROM market_cache
            WHERE cache_key=?
            """,
            (key,),
        ).fetchone()
        if row is None:
            return None
        payload = json.loads(row[1])
        entry = CacheEntry(
            key=row[0],
            payload=payload,
            expires_at=float(row[2]),
            updated_at=float(row[3]),
        )
        if entry.expired and not allow_expired:
            return None
        return entry

    def delete(self, key: str) -> int:
        cur = self._conn.execute("DELETE FROM market_cache WHERE cache_key=?", (key,))
        self._conn.commit()
        return int(cur.rowcount)

    def clear_expired(self, *, now: float | None = None) -> int:
        timestamp = time.time() if now is None else now
        cur = self._conn.execute(
            "DELETE FROM market_cache WHERE expires_at <= ?",
            (timestamp,),
        )
        self._conn.commit()
        return int(cur.rowcount)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SQLiteCache":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

