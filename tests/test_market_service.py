from __future__ import annotations

import shutil
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
