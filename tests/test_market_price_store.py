from __future__ import annotations

import time
from pathlib import Path

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import MarketRegion
from albion_dps.market.price_store import LocalMarketPriceStore, normalize_market_location


def test_price_store_roundtrip_aodata_prices(tmp_path: Path) -> None:
    store = LocalMarketPriceStore(tmp_path / "prices.sqlite3")
    try:
        store.upsert_aodata_prices(
            region=MarketRegion.EUROPE,
            rows=[
                MarketPriceRecord(
                    item_id="T4_MAIN_SWORD",
                    city="Caerleon",
                    quality=1,
                    sell_price_min=1000,
                    buy_price_max=900,
                    sell_price_min_date="2026-05-20T10:00:00+00:00",
                    buy_price_max_date="2026-05-20T10:01:00+00:00",
                )
            ],
        )
        index = store.get_price_index(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_SWORD"],
            locations=["Caerleon"],
            qualities=[1],
            max_age_seconds=10 * 365 * 24 * 3600,
        )
    finally:
        store.close()

    row = index[("T4_MAIN_SWORD", "Caerleon", 1)]
    assert row.sell_price_min == 1000
    assert row.buy_price_max == 900


def test_price_store_ingests_scanner_market_orders(tmp_path: Path) -> None:
    store = LocalMarketPriceStore(tmp_path / "prices.sqlite3")
    try:
        stored = store.upsert_scanner_payload(
            region=MarketRegion.EUROPE,
            payload={
                "Orders": [
                    {
                        "ItemTypeId": "T4_MAIN_BOW",
                        "LocationId": "3005",
                        "QualityLevel": 2,
                        "UnitPriceSilver": 50_000_000,
                        "Amount": 3,
                        "AuctionType": "offer",
                    },
                    {
                        "ItemTypeId": "T4_MAIN_BOW",
                        "LocationId": "3003",
                        "QualityLevel": 1,
                        "UnitPriceSilver": 70_000_000,
                        "Amount": 1,
                        "AuctionType": "request",
                    },
                ]
            },
        )
        index = store.get_price_index(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_BOW"],
            locations=["Caerleon", "Black Market"],
            qualities=[1, 2],
        )
    finally:
        store.close()

    assert stored == 2
    assert index[("T4_MAIN_BOW", "Caerleon", 2)].sell_price_min == 5000
    assert index[("T4_MAIN_BOW", "Black Market", 1)].buy_price_max == 7000


def test_price_store_migrates_existing_raw_scanner_quotes(tmp_path: Path) -> None:
    path = tmp_path / "prices.sqlite3"
    store = LocalMarketPriceStore(path)
    try:
        store.upsert_quote(
            region="europe",
            location="3005",
            item_id="T4_MAIN_BOW",
            quality=1,
            side="sell",
            price=12_340_000,
            amount=1,
            source="scanner_ws",
        )
    finally:
        store.close()

    reopened = LocalMarketPriceStore(path)
    try:
        index = reopened.get_price_index(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_BOW"],
            locations=["Caerleon"],
            qualities=[1],
        )
    finally:
        reopened.close()

    assert index[("T4_MAIN_BOW", "Caerleon", 1)].sell_price_min == 1234


def test_price_store_migration_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "prices.sqlite3"
    store = LocalMarketPriceStore(path)
    try:
        store.upsert_quote(
            region="europe",
            location="3005",
            item_id="T4_MAIN_BOW",
            quality=1,
            side="sell",
            price=12_340_000,
            amount=1,
            source="scanner_ws",
        )
    finally:
        store.close()

    first = LocalMarketPriceStore(path)
    first.close()
    second = LocalMarketPriceStore(path)
    try:
        index = second.get_price_index(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_BOW"],
            locations=["Caerleon"],
            qualities=[1],
        )
    finally:
        second.close()

    assert index[("T4_MAIN_BOW", "Caerleon", 1)].sell_price_min == 1234


def test_price_store_cleanup_removes_old_quotes(tmp_path: Path) -> None:
    store = LocalMarketPriceStore(tmp_path / "prices.sqlite3")
    try:
        store.upsert_quote(
            region="europe",
            location="Caerleon",
            item_id="T4_MAIN_SWORD",
            quality=1,
            side="sell",
            price=1000,
            amount=1,
            observed_at=time.time() - 10_000,
            source="test",
        )
        removed = store.clear_old_quotes(retention_seconds=60)
        count = store.count_quotes(region=MarketRegion.EUROPE)
    finally:
        store.close()

    assert removed == 1
    assert count == 0


def test_normalize_market_location_handles_black_market() -> None:
    assert normalize_market_location("3003") == "Black Market"
    assert normalize_market_location("3005") == "Caerleon"
    assert normalize_market_location("Fort-Sterling-Auction2") == "Fort Sterling"
