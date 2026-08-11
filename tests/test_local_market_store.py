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


def test_local_store_normalizes_numeric_location_ids(tmp_path) -> None:
    store = LocalMarketStore(tmp_path / "local_market.sqlite3")
    try:
        store.upsert_market_upload(
            {
                "Orders": [
                    {
                        "Id": 20,
                        "ItemTypeId": "T4_MAIN_SWORD",
                        "LocationId": "3005",
                        "QualityLevel": 1,
                        "EnchantmentLevel": 0,
                        "UnitPriceSilver": 1200,
                        "Amount": 1,
                        "AuctionType": "offer",
                    },
                    {
                        "Id": 21,
                        "ItemTypeId": "T4_MAIN_SWORD",
                        "LocationId": "3003",
                        "QualityLevel": 1,
                        "EnchantmentLevel": 0,
                        "UnitPriceSilver": 2500,
                        "Amount": 1,
                        "AuctionType": "request",
                    },
                ]
            },
            observed_at=datetime(2026, 5, 22, 11, 0, tzinfo=timezone.utc),
        )
        caerleon_rows = store.get_prices(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_SWORD"],
            locations=["Caerleon"],
            qualities=[1],
        )
        black_market_rows = store.get_prices(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_SWORD"],
            locations=["Black Market"],
            qualities=[1],
        )
    finally:
        store.close()

    assert len(caerleon_rows) == 1
    assert caerleon_rows[0].city == "Caerleon"
    assert caerleon_rows[0].sell_price_min == 1200
    assert len(black_market_rows) == 1
    assert black_market_rows[0].city == "Black Market"
    assert black_market_rows[0].buy_price_max == 2500


def test_local_store_reads_existing_raw_location_scanner_prices(tmp_path) -> None:
    store = LocalMarketStore(tmp_path / "local_market.sqlite3")
    try:
        store._conn.execute(
            """
            INSERT INTO local_market_orders(
                region, order_id, item_id, raw_item_id, location_id, city, quality,
                enchantment, side, price, amount, auction_type, expires,
                observed_at, payload_json
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                MarketRegion.EUROPE.value,
                "old-1",
                "T4_METALBAR",
                "T4_METALBAR",
                "3005",
                "3005",
                1,
                0,
                "sell",
                12_000_000,
                1,
                "offer",
                "",
                "2026-05-22T11:00:00",
                "{}",
            ),
        )
        store._conn.commit()
        rows = store.get_prices(
            region=MarketRegion.EUROPE,
            item_ids=["T4_METALBAR"],
            locations=["Caerleon"],
            qualities=[1],
        )
    finally:
        store.close()

    assert len(rows) == 1
    assert rows[0].city == "Caerleon"
    assert rows[0].sell_price_min == 1200


def test_parse_market_upload_message_filters_topic() -> None:
    message = '{"topic": "marketorders.ingest", "data": {"Orders": []}}'
    assert parse_market_upload_message(message) == {"Orders": []}
    assert parse_market_upload_message('{"topic": "other", "data": {"Orders": []}}') is None


def test_normalize_location_id_handles_city_variants() -> None:
    assert normalize_location_id("BLACKBANK-3003") == "Black Market"
    assert normalize_location_id("3003") == "Black Market"
    assert normalize_location_id("3005") == "Caerleon"
    assert normalize_location_id("3008") == "Martlock"
    assert normalize_location_id("Caerleon-Auction2") == "Caerleon"
    assert normalize_location_id("FortSterling-Auction2") == "Fort Sterling"


def test_local_store_normalizes_scanner_fixed_point_price_and_numeric_city(tmp_path) -> None:
    store = LocalMarketStore(tmp_path / "local_market.sqlite3")
    try:
        store.upsert_market_upload(
            {
                "Orders": [
                    {
                        "Id": 20,
                        "ItemTypeId": "T6_2H_DUALSCIMITAR_UNDEAD@3",
                        "LocationId": "3008",
                        "QualityLevel": 3,
                        "EnchantmentLevel": 3,
                        "UnitPriceSilver": 21_999_990_000,
                        "Amount": 1,
                        "AuctionType": "offer",
                    }
                ]
            },
            observed_at=datetime(2026, 8, 1, 20, 43, 40, tzinfo=timezone.utc),
        )
        rows = store.get_prices(
            region=MarketRegion.EUROPE,
            item_ids=["T6_2H_DUALSCIMITAR_UNDEAD@3"],
            locations=["Martlock"],
            qualities=[3],
        )
    finally:
        store.close()

    assert len(rows) == 1
    assert rows[0].sell_price_min == 2_199_999
