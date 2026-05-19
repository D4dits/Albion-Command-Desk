from __future__ import annotations

from datetime import datetime, timezone

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.flipper import BLACK_MARKET_CITY, FlipCandidate, build_flip_opportunities
from albion_dps.market.models import ItemRef


NOW = datetime(2026, 5, 19, 12, 0, tzinfo=timezone.utc)


def _record(
    item_id: str,
    city: str,
    *,
    sell: int = 0,
    buy: int = 0,
    sell_date: str = "2026-05-19T10:30:00Z",
    buy_date: str = "2026-05-19T11:30:00Z",
) -> MarketPriceRecord:
    return MarketPriceRecord(
        item_id=item_id,
        city=city,
        quality=1,
        sell_price_min=sell,
        buy_price_max=buy,
        sell_price_min_date=sell_date,
        buy_price_max_date=buy_date,
    )


def test_flip_profit_subtracts_sale_tax_and_buffer() -> None:
    candidate = FlipCandidate(
        item=ItemRef(unique_name="T6_MAIN_FROSTSTAFF", display_name="Great Frost Staff", tier=6, enchantment=0),
        recipe_id="T6_MAIN_FROSTSTAFF",
    )
    price_index = {
        ("T6_MAIN_FROSTSTAFF", "Caerleon", 1): _record("T6_MAIN_FROSTSTAFF", "Caerleon", sell=100_000),
        ("T6_MAIN_FROSTSTAFF", BLACK_MARKET_CITY, 1): _record("T6_MAIN_FROSTSTAFF", BLACK_MARKET_CITY, buy=140_000),
    }

    rows = build_flip_opportunities(
        candidates=[candidate],
        price_index=price_index,
        source_city="Caerleon",
        quality=1,
        sale_tax_percent=4.0,
        risk_buffer_percent=2.0,
        min_profit=0,
        min_roi_percent=0,
        now=NOW,
    )

    assert rows[0].valid is True
    assert rows[0].tax_value == 5_600
    assert rows[0].buffer_value == 2_000
    assert rows[0].net_profit == 32_400
    assert round(rows[0].roi_percent, 2) == 32.4


def test_flip_rejects_stale_black_market_buy_order() -> None:
    candidate = FlipCandidate(
        item=ItemRef(unique_name="T5_2H_CROSSBOW", display_name="Crossbow", tier=5, enchantment=0),
        recipe_id="T5_2H_CROSSBOW",
    )
    price_index = {
        ("T5_2H_CROSSBOW", "Caerleon", 1): _record("T5_2H_CROSSBOW", "Caerleon", sell=10_000),
        ("T5_2H_CROSSBOW", BLACK_MARKET_CITY, 1): _record(
            "T5_2H_CROSSBOW",
            BLACK_MARKET_CITY,
            buy=30_000,
            buy_date="2026-05-19T10:00:00Z",
        ),
    }

    rows = build_flip_opportunities(
        candidates=[candidate],
        price_index=price_index,
        source_city="Caerleon",
        quality=1,
        sale_tax_percent=4.0,
        risk_buffer_percent=0.0,
        min_profit=0,
        min_roi_percent=0,
        buy_freshness_minutes=45,
        now=NOW,
    )

    assert rows[0].valid is False
    assert rows[0].stale_reason == "stale Black Market buy"


def test_flip_missing_source_does_not_show_fake_profit() -> None:
    candidate = FlipCandidate(
        item=ItemRef(unique_name="T4_2H_BOW", display_name="Bow", tier=4, enchantment=0),
        recipe_id="T4_2H_BOW",
    )
    price_index = {
        ("T4_2H_BOW", BLACK_MARKET_CITY, 1): _record("T4_2H_BOW", BLACK_MARKET_CITY, buy=30_000),
    }

    rows = build_flip_opportunities(
        candidates=[candidate],
        price_index=price_index,
        source_city="Caerleon",
        quality=1,
        sale_tax_percent=4.0,
        risk_buffer_percent=0.0,
        min_profit=0,
        min_roi_percent=0,
        now=NOW,
    )

    assert rows[0].valid is False
    assert rows[0].stale_reason == "missing source sell"
    assert rows[0].net_profit == 0
    assert rows[0].roi_percent == 0


def test_flip_uses_enchanted_query_aliases() -> None:
    candidate = FlipCandidate(
        item=ItemRef(unique_name="T6_MAIN_FROSTSTAFF_LEVEL2", display_name="Great Frost Staff", tier=6, enchantment=2),
        recipe_id="T6_MAIN_FROSTSTAFF_LEVEL2",
    )
    price_index = {
        ("T6_MAIN_FROSTSTAFF_LEVEL2@2", "Martlock", 1): _record("T6_MAIN_FROSTSTAFF_LEVEL2@2", "Martlock", sell=70_000),
        ("T6_MAIN_FROSTSTAFF_LEVEL2@2", BLACK_MARKET_CITY, 1): _record(
            "T6_MAIN_FROSTSTAFF_LEVEL2@2",
            BLACK_MARKET_CITY,
            buy=100_000,
        ),
    }

    rows = build_flip_opportunities(
        candidates=[candidate],
        price_index=price_index,
        source_city="Martlock",
        quality=1,
        sale_tax_percent=4.0,
        risk_buffer_percent=0.0,
        min_profit=0,
        min_roi_percent=0,
        item_id_candidates=lambda _item_id: ("T6_MAIN_FROSTSTAFF_LEVEL2", "T6_MAIN_FROSTSTAFF_LEVEL2@2"),
        now=NOW,
    )

    assert rows[0].valid is True
    assert rows[0].source_sell_price == 70_000
    assert rows[0].target_buy_price == 100_000


def test_flip_uses_best_compatible_quality_pair_across_qualities() -> None:
    candidate = FlipCandidate(
        item=ItemRef(unique_name="T4_HEAD_CLOTH_KEEPER@3", display_name="Druid Cowl", tier=4, enchantment=3),
        recipe_id="T4_HEAD_CLOTH_KEEPER@3",
    )
    price_index = {
        ("T4_HEAD_CLOTH_KEEPER@3", "Caerleon", 1): _record("T4_HEAD_CLOTH_KEEPER@3", "Caerleon", sell=0),
        ("T4_HEAD_CLOTH_KEEPER@3", BLACK_MARKET_CITY, 1): _record(
            "T4_HEAD_CLOTH_KEEPER@3",
            BLACK_MARKET_CITY,
            buy=50_000,
        ),
        ("T4_HEAD_CLOTH_KEEPER@3", "Caerleon", 3): _record("T4_HEAD_CLOTH_KEEPER@3", "Caerleon", sell=20_000),
        ("T4_HEAD_CLOTH_KEEPER@3", BLACK_MARKET_CITY, 3): _record(
            "T4_HEAD_CLOTH_KEEPER@3",
            BLACK_MARKET_CITY,
            buy=40_000,
        ),
    }

    rows = build_flip_opportunities(
        candidates=[candidate],
        price_index=price_index,
        source_city="Caerleon",
        quality=1,
        sale_tax_percent=4.0,
        risk_buffer_percent=0.0,
        min_profit=0,
        min_roi_percent=0,
        now=NOW,
    )

    assert rows[0].valid is True
    assert rows[0].quality == 3
    assert rows[0].source_sell_price == 20_000
    assert rows[0].target_buy_price == 50_000


def test_flip_can_sell_higher_quality_to_lower_quality_black_market_order() -> None:
    candidate = FlipCandidate(
        item=ItemRef(unique_name="T4_HEAD_CLOTH_KEEPER@3", display_name="Druid Cowl", tier=4, enchantment=3),
        recipe_id="T4_HEAD_CLOTH_KEEPER@3",
    )
    price_index = {
        ("T4_HEAD_CLOTH_KEEPER@3", "Caerleon", 3): _record("T4_HEAD_CLOTH_KEEPER@3", "Caerleon", sell=20_000),
        ("T4_HEAD_CLOTH_KEEPER@3", BLACK_MARKET_CITY, 1): _record(
            "T4_HEAD_CLOTH_KEEPER@3",
            BLACK_MARKET_CITY,
            buy=60_000,
        ),
        ("T4_HEAD_CLOTH_KEEPER@3", BLACK_MARKET_CITY, 3): _record(
            "T4_HEAD_CLOTH_KEEPER@3",
            BLACK_MARKET_CITY,
            buy=30_000,
        ),
    }

    rows = build_flip_opportunities(
        candidates=[candidate],
        price_index=price_index,
        source_city="Caerleon",
        quality=1,
        sale_tax_percent=4.0,
        risk_buffer_percent=0.0,
        min_profit=0,
        min_roi_percent=0,
        now=NOW,
    )

    assert rows[0].valid is True
    assert rows[0].quality == 3
    assert rows[0].source_sell_price == 20_000
    assert rows[0].target_buy_price == 60_000
