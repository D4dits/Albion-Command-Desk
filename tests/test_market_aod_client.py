from __future__ import annotations

import pytest

from albion_dps.market.aod_client import AODataClient
from albion_dps.market.models import MarketRegion


def test_fetch_prices_builds_expected_url_and_parses_rows() -> None:
    called: list[str] = []

    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        called.append(url)
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "city": "Bridgewatch",
                "quality": 1,
                "sell_price_min": 1111,
                "buy_price_max": 999,
                "sell_price_min_date": "2026-02-09T10:00:00",
                "buy_price_max_date": "2026-02-09T10:01:00",
            }
        ]

    client = AODataClient(fetch_json=fake_fetch_json)
    rows = client.fetch_prices(
        region=MarketRegion.EUROPE,
        item_ids=["T4_MAIN_SWORD"],
        locations=["Bridgewatch", "Martlock"],
        qualities=[1, 2],
    )

    assert len(rows) == 1
    assert rows[0].item_id == "T4_MAIN_SWORD"
    assert rows[0].sell_price_min == 1111
    assert "europe.albion-online-data.com/api/v2/stats/prices/T4_MAIN_SWORD.json" in called[0]
    assert "locations=Bridgewatch%2CMartlock" in called[0]
    assert "qualities=1%2C2" in called[0]


def test_fetch_charts_parses_data_points() -> None:
    def fake_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "location": "Bridgewatch",
                "quality": 1,
                "data": [
                    {"timestamp": "2026-02-08T00:00:00", "item_count": 12, "avg_price": 2500},
                    {"timestamp": "2026-02-09T00:00:00", "item_count": 9, "avg_price": 2600},
                ],
            }
        ]

    client = AODataClient(fetch_json=fake_fetch_json)
    points = client.fetch_charts(
        region=MarketRegion.EUROPE,
        item_id="T4_MAIN_SWORD",
        location="Bridgewatch",
        quality=1,
        time_scale=24,
    )

    assert len(points) == 2
    assert points[0].item_count == 12
    assert points[1].avg_price == 2600


def test_fetch_prices_retries_on_transient_error() -> None:
    calls = {"value": 0}

    def flaky_fetch_json(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        calls["value"] += 1
        if calls["value"] < 3:
            raise RuntimeError("temporary network error")
        return [
            {
                "item_id": "T4_MAIN_SWORD",
                "city": "Bridgewatch",
                "quality": 1,
                "sell_price_min": 1111,
                "buy_price_max": 999,
                "sell_price_min_date": "",
                "buy_price_max_date": "",
            }
        ]

    sleeps: list[float] = []
    client = AODataClient(
        fetch_json=flaky_fetch_json,
        max_retries=3,
        retry_backoff_initial_seconds=0.01,
        sleeper=sleeps.append,
    )
    rows = client.fetch_prices(
        region=MarketRegion.EUROPE,
        item_ids=["T4_MAIN_SWORD"],
        locations=["Bridgewatch"],
    )
    assert len(rows) == 1
    assert calls["value"] == 3
    assert len(sleeps) == 2
    assert client.last_request_stats.success
    assert client.last_request_stats.attempts == 3


def test_fetch_prices_raises_after_retry_exhaustion() -> None:
    def always_fail(url: str, timeout_seconds: float, user_agent: str):
        _ = (url, timeout_seconds, user_agent)
        raise RuntimeError("down")

    client = AODataClient(
        fetch_json=always_fail,
        max_retries=2,
        retry_backoff_initial_seconds=0.0,
        sleeper=lambda _seconds: None,
    )
    with pytest.raises(RuntimeError):
        _ = client.fetch_prices(
            region=MarketRegion.EUROPE,
            item_ids=["T4_MAIN_SWORD"],
            locations=["Bridgewatch"],
        )
    assert not client.last_request_stats.success
    assert client.last_request_stats.attempts == 3
