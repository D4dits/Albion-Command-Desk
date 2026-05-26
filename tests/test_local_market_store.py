from __future__ import annotations

from datetime import datetime, timezone

from albion_dps.market.local_store import LocalMarketStore, normalize_location_id, parse_market_upload_message
from albion_dps.market.models import MarketRegion


def test_local_store_ingests_market_upload_and_aggregates_prices(tmp_path) -> None:
    store = LocalMarketStore(tmp_path / "local_market.sqlite3")
    try:
        stats = store.upsert_market_upload(
            {
                "Orders": [
                    {
                        "Id": 1,
                        "ItemTypeId": "T4_MAIN_SWORD",
                        "LocationId": "Caerleon",
                        "QualityLevel": 1,
                        "EnchantmentLevel": 0,
                        "UnitPriceSilver": 1200,
                        "Amount": 1,
                        "AuctionType": "offer",
                        "Expires": "2026-05-22T12:00:00",
                    },
                    {
                        "Id": 2,
                        "ItemTypeId": "T4_MAIN_SWORD",
                        "LocationId": "Caerleon",
                        "QualityLevel": 1,
                        "EnchantmentLevel": 0,
                        "UnitPriceSilver": 900,
                        "Amount": 1,
                        "AuctionType": "offer",
                        "Expires": "2026-05-22T12:00:00",
                    },
                    {
                        "Id": 3,
                        "ItemTypeId": "T4_MAIN_SWORD",
                        "LocationId": "Caerleon",
                        "QualityLevel": 1,
                        "EnchantmentLevel": 0,
                        "UnitPriceSilver": 700,
                        "Amount": 1,
                        "AuctionType": "request",
                        "Expires": "2026-05-22T12:00:00",
                    },
                ]
            },
            region=MarketRegion.EUROPE,
            observed_at=datetime(2026, 5, 22, 10, 0, tzinfo=timezone.utc),
        )
        rows = store.get_prices(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_SWORD"],
            locations=["Caerleon"],
            qualities=[1],
        )
    finally:
        store.close()

    assert stats.orders_seen == 3
    assert stats.orders_stored == 3
    assert len(rows) == 1
    assert rows[0].sell_price_min == 900
    assert rows[0].buy_price_max == 700
    assert rows[0].sell_price_min_date == "2026-05-22T10:00:00"


def test_local_store_normalizes_enchantment_and_black_market(tmp_path) -> None:
    store = LocalMarketStore(tmp_path / "local_market.sqlite3")
    try:
        store.upsert_market_upload(
            {
                "Orders": [
                    {
                        "Id": 10,
                        "ItemTypeId": "T5_2H_BOW",
                        "LocationId": "BLACKBANK-3003",
                        "QualityLevel": 2,
                        "EnchantmentLevel": 3,
                        "UnitPriceSilver": 5555,
                        "Amount": 1,
                        "AuctionType": "buy",
                    }
                ]
            },
            observed_at=datetime(2026, 5, 22, 11, 0),
        )
        rows = store.get_prices(
            region=MarketRegion.EUROPE,
            item_ids=["T5_2H_BOW@3"],
            locations=["Black Market"],
            qualities=[2],
        )
    finally:
        store.close()

    assert len(rows) == 1
    assert rows[0].item_id == "T5_2H_BOW@3"
    assert rows[0].city == "Black Market"
    assert rows[0].buy_price_max == 5555


def test_parse_market_upload_message_filters_topic() -> None:
    message = '{"topic": "marketorders.ingest", "data": {"Orders": []}}'
    assert parse_market_upload_message(message) == {"Orders": []}
    assert parse_market_upload_message('{"topic": "other", "data": {"Orders": []}}') is None


def test_normalize_location_id_handles_city_variants() -> None:
    assert normalize_location_id("BLACKBANK-3003") == "Black Market"
    assert normalize_location_id("Caerleon-Auction2") == "Caerleon"
    assert normalize_location_id("FortSterling-Auction2") == "Fort Sterling"
