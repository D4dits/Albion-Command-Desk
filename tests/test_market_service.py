from __future__ import annotations

import shutil
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from albion_dps.market.aod_client import AODataClient
from albion_dps.market.cache import SQLiteCache
from albion_dps.market.local_store import LocalMarketStore
from albion_dps.market.models import MarketRegion
from albion_dps.market.price_store import LocalMarketPriceStore
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


def test_service_live_prices_use_fetch_time_for_display_age() -> None:
    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "city": "Bridgewatch",
                "quality": 1,
                "sell_price_min": 1200,
                "buy_price_max": 1000,
                "sell_price_min_date": "2026-01-01T00:00:00",
                "buy_price_max_date": "2026-01-01T00:00:00",
            }
        ]

    tmp_dir = _make_local_tmp_dir()
    before = datetime.now(timezone.utc)
    try:
        client = AODataClient(fetch_json=fake_fetch_json)
        store = LocalMarketPriceStore(tmp_dir / "prices.sqlite3")
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            service = MarketDataService(client=client, cache=cache, price_store=store)
            rows = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
            )
            cached_rows = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Bridgewatch"],
            )
            service.close()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert len(rows) == 1
    assert len(cached_rows) == 1
    sell_dt = datetime.fromisoformat(rows[0].sell_price_min_date)
    buy_dt = datetime.fromisoformat(rows[0].buy_price_max_date)
    assert sell_dt >= before - timedelta(seconds=1)
    assert buy_dt >= before - timedelta(seconds=1)
    assert cached_rows[0].sell_price_min_date == rows[0].sell_price_min_date
    assert service.last_prices_meta.source == "local_db"


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


def test_service_cache_only_mode_reads_local_price_store() -> None:
    tmp_dir = _make_local_tmp_dir()
    try:
        store = LocalMarketPriceStore(tmp_dir / "prices.sqlite3")
        store.upsert_quote(
            region="europe",
            location="Caerleon",
            item_id="T4_MAIN_SWORD",
            quality=1,
            side="sell",
            price=1200,
            amount=1,
            source="test",
        )
        cache = SQLiteCache(tmp_dir / "cache.sqlite3")
        service = MarketDataService(cache=cache, price_store=store)
        rows = service.get_prices(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_SWORD"],
            locations=["Caerleon"],
            allow_live=False,
        )
        service.close()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert len(rows) == 1
    assert rows[0].sell_price_min == 1200
    assert service.last_prices_meta.source == "local_db"


def test_service_uses_partial_price_cache_on_exact_key_miss() -> None:
    call_count = {"value": 0}

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        call_count["value"] += 1
        return []

    tmp_dir = _make_local_tmp_dir()
    try:
        client = AODataClient(fetch_json=fake_fetch_json)
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            cache.set(
                "market:prices:previous-thetford",
                [
                    {
                        "item_id": "T4_METALBAR",
                        "city": "Thetford",
                        "quality": 1,
                        "sell_price_min": 1200,
                        "buy_price_max": 1000,
                        "sell_price_min_date": "2026-05-05T10:00:00",
                        "buy_price_max_date": "2026-05-05T10:01:00",
                    },
                    {
                        "item_id": "T4_PLANKS",
                        "city": "Martlock",
                        "quality": 1,
                        "sell_price_min": 800,
                        "buy_price_max": 700,
                        "sell_price_min_date": "2026-05-05T10:00:00",
                        "buy_price_max_date": "2026-05-05T10:01:00",
                    },
                ],
                ttl_seconds=120.0,
            )
            service = MarketDataService(client=client, cache=cache)
            rows = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_METALBAR", "T4_PLANKS"],
                locations=["Thetford"],
                allow_live=False,
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert call_count["value"] == 0
    assert len(rows) == 1
    assert rows[0].item_id == "T4_METALBAR"
    assert rows[0].city == "Thetford"
    assert rows[0].buy_price_max == 1000
    assert service.last_prices_meta.source == "partial_cache"


def test_service_uses_fresh_local_prices_without_live_call() -> None:
    call_count = {"value": 0}

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        call_count["value"] += 1
        return []

    tmp_dir = _make_local_tmp_dir()
    try:
        local_store = LocalMarketStore(tmp_dir / "local.sqlite3")
        local_store.upsert_market_upload(
            {
                "Orders": [
                    {
                        "Id": 100,
                        "ItemTypeId": "T4_MAIN_SWORD",
                        "LocationId": "Caerleon",
                        "QualityLevel": 1,
                        "UnitPriceSilver": 1234,
                        "Amount": 1,
                        "AuctionType": "offer",
                    }
                ]
            }
        )
        client = AODataClient(fetch_json=fake_fetch_json)
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            service = MarketDataService(client=client, cache=cache, local_store=local_store)
            rows = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Caerleon"],
                qualities=[1],
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert call_count["value"] == 0
    assert len(rows) == 1
    assert rows[0].sell_price_min == 1234
    assert service.last_prices_meta.source == "local"


def test_service_merges_stale_local_with_live_fresher_record() -> None:
    call_count = {"value": 0}

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        call_count["value"] += 1
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "city": "Caerleon",
                "quality": 1,
                "sell_price_min": 2000,
                "buy_price_max": 1600,
                "sell_price_min_date": "2026-05-22T11:00:00",
                "buy_price_max_date": "2026-05-22T11:00:00",
            }
        ]

    tmp_dir = _make_local_tmp_dir()
    try:
        local_store = LocalMarketStore(tmp_dir / "local.sqlite3")
        local_store.upsert_market_upload(
            {
                "Orders": [
                    {
                        "Id": 101,
                        "ItemTypeId": "T4_MAIN_SWORD",
                        "LocationId": "Caerleon",
                        "QualityLevel": 1,
                        "UnitPriceSilver": 1200,
                        "Amount": 1,
                        "AuctionType": "offer",
                    }
                ]
            },
            observed_at=datetime(2020, 1, 1, 0, 0),
        )
        client = AODataClient(fetch_json=fake_fetch_json)
        with SQLiteCache(tmp_dir / "cache.sqlite3") as cache:
            service = MarketDataService(client=client, cache=cache, local_store=local_store)
            rows = service.get_prices(
                region=MarketRegion.EUROPE,
                item_ids=["T4_MAIN_SWORD"],
                locations=["Caerleon"],
                qualities=[1],
            )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    assert call_count["value"] == 1
    assert len(rows) == 1
    assert rows[0].sell_price_min == 2000
    assert rows[0].buy_price_max == 1600
    assert service.last_prices_meta.source == "local+live"
