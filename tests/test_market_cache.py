from __future__ import annotations

import shutil
import time
import uuid
from pathlib import Path

from albion_dps.market.cache import SQLiteCache


def _make_local_tmp_dir() -> Path:
    path = Path(f"tmp_market_cache_{uuid.uuid4().hex}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_sqlite_cache_roundtrip() -> None:
    tmp_dir = _make_local_tmp_dir()
    try:
        cache_path = tmp_dir / "market_cache.sqlite3"
        with SQLiteCache(cache_path) as cache:
            cache.set("key-1", {"hello": "world"}, ttl_seconds=60)
            entry = cache.get_entry("key-1")
            assert entry is not None
            assert isinstance(entry.payload, dict)
            assert entry.payload["hello"] == "world"
            assert not entry.expired
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_sqlite_cache_expiration() -> None:
    tmp_dir = _make_local_tmp_dir()
    try:
        cache_path = tmp_dir / "market_cache.sqlite3"
        with SQLiteCache(cache_path) as cache:
            cache.set("key-2", [1, 2, 3], ttl_seconds=0.01)
            time.sleep(0.02)
            assert cache.get_entry("key-2") is None
            stale = cache.get_entry("key-2", allow_expired=True)
            assert stale is not None
            assert stale.expired
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_sqlite_cache_clear_expired() -> None:
    tmp_dir = _make_local_tmp_dir()
    try:
        cache_path = tmp_dir / "market_cache.sqlite3"
        with SQLiteCache(cache_path) as cache:
            cache.set("expired", {"a": 1}, ttl_seconds=0.01)
            cache.set("fresh", {"b": 2}, ttl_seconds=60)
            time.sleep(0.02)
            removed = cache.clear_expired()
            assert removed >= 1
            assert cache.get_entry("expired", allow_expired=True) is None
            assert cache.get_entry("fresh") is not None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
