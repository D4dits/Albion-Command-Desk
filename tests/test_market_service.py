from __future__ import annotations

import shutil
import time
import uuid
from pathlib import Path

from albion_dps.market.aod_client import AODataClient
from albion_dps.market.cache import SQLiteCache
from albion_dps.market.models import MarketRegion
from albion_dps.market.service import MarketDataService


def _make_local_tmp_dir() -> Path:
    path = Path(f"tmp_market_service_{uuid.uuid4().hex}")
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_service_caches_price_payload() -> None:
    call_count = {"value": 0}

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        call_count["value"] += 1
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "city": "Bridgewatch",
                "quality": 1,
                "sell_price_min": 1200,
                "buy_price_max": 1000,
                "sell_price_min_date": "",
                "buy_price_max_date": "",
            }
        ]

    tmp_dir = _make_local_tmp_dir()
    try:
        client = AODataClient(fetch_json=fake_fetch_json)
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            service = MarketDataService(client=client, cache=cache)
            first = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
            )
            second = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert len(first) == 1
    assert len(second) == 1
    assert call_count["value"] == 1
    # First call is live fetch, second should be cache hit.
    assert service.last_prices_meta.source == "cache"
    assert service.last_prices_meta.record_count == 1


def test_service_uses_stale_cache_when_enabled() -> None:
    call_count = {"value": 0}

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        call_count["value"] += 1
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "city": "Bridgewatch",
                "quality": 1,
                "sell_price_min": 1300,
                "buy_price_max": 1100,
                "sell_price_min_date": "",
                "buy_price_max_date": "",
            }
        ]

    tmp_dir = _make_local_tmp_dir()
    try:
        client = AODataClient(fetch_json=fake_fetch_json)
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            service = MarketDataService(client=client, cache=cache)
            _ = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
                ttl_seconds=0.01,
            )
            # Let cache expire.
            import time

            time.sleep(0.02)
            _ = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
                allow_stale=True,
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert call_count["value"] == 1
    assert service.last_prices_meta.source == "stale_cache"


def test_service_allow_cache_false_forces_live_refresh() -> None:
    call_count = {"value": 0}

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        call_count["value"] += 1
        price = 1000 + (call_count["value"] * 111)
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "city": "Bridgewatch",
                "quality": 1,
                "sell_price_min": price,
                "buy_price_max": price - 100,
                "sell_price_min_date": "",
                "buy_price_max_date": "",
            }
        ]

    tmp_dir = _make_local_tmp_dir()
    try:
        client = AODataClient(fetch_json=fake_fetch_json)
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            service = MarketDataService(client=client, cache=cache)
            first = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
            )
            second = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
                allow_cache=False,
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert len(first) == 1
    assert len(second) == 1
    assert first[0].sell_price_min != second[0].sell_price_min
    assert call_count["value"] == 2
    assert service.last_prices_meta.source == "live"


def test_service_charts_cache_and_stale_behavior() -> None:
    call_count = {"value": 0}

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        call_count["value"] += 1
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "location": "Bridgewatch",
                "quality": 1,
                "data": [
                    {"timestamp": "2026-02-10T10:00:00", "item_count": 11, "avg_price": 2500},
                    {"timestamp": "2026-02-10T11:00:00", "item_count": 9, "avg_price": 2550},
                ],
            }
        ]

    tmp_dir = _make_local_tmp_dir()
    try:
        client = AODataClient(fetch_json=fake_fetch_json)
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            service = MarketDataService(client=client, cache=cache)
            first = service.get_charts(
                region=MarketRegion.EUROPE,
                item_id="T4_MAIN_SWORD",
                location="Bridgewatch",
                ttl_seconds=0.02,
            )
            second = service.get_charts(
                region=MarketRegion.EUROPE,
                item_id="T4_MAIN_SWORD",
                location="Bridgewatch",
            )
            assert len(first) == 2
            assert len(second) == 2
            assert service.last_charts_meta.source == "cache"
            time.sleep(0.03)
            third = service.get_charts(
                region=MarketRegion.EUROPE,
                item_id="T4_MAIN_SWORD",
                location="Bridgewatch",
                allow_stale=True,
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert len(third) == 2
    assert call_count["value"] == 1
    assert service.last_charts_meta.source == "stale_cache"


def test_service_cache_only_mode_returns_empty_without_live_call() -> None:
    call_count = {"value": 0}

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        call_count["value"] += 1
        return []

    tmp_dir = _make_local_tmp_dir()
    try:
        client = AODataClient(fetch_json=fake_fetch_json)
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            service = MarketDataService(client=client, cache=cache)
            rows = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
                allow_cache=False,
                allow_live=False,
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert rows == []
    assert call_count["value"] == 0
    assert service.last_prices_meta.source == "cache_miss"
