from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from albion_dps.market.aod_client import AODataClient, MarketChartPoint, MarketPriceRecord
from albion_dps.market.cache import SQLiteCache
from albion_dps.market.models import MarketRegion


@dataclass(frozen=True)
class MarketFetchMeta:
    source: str
    record_count: int
    elapsed_ms: float
    cache_key: str


class MarketDataService:
    def __init__(
        self,
        *,
        client: AODataClient | None = None,
        cache: SQLiteCache | None = None,
    ) -> None:
        self.client = client or AODataClient()
        self.cache = cache
        self._last_prices_meta = MarketFetchMeta(
            source="none",
            record_count=0,
            elapsed_ms=0.0,
            cache_key="",
        )
        self._last_charts_meta = MarketFetchMeta(
            source="none",
            record_count=0,
            elapsed_ms=0.0,
            cache_key="",
        )

    @property
    def last_prices_meta(self) -> MarketFetchMeta:
        return self._last_prices_meta

    @property
    def last_charts_meta(self) -> MarketFetchMeta:
        return self._last_charts_meta

    @classmethod
    def with_default_cache(
        cls,
        *,
        cache_path: Path,
        client: AODataClient | None = None,
    ) -> "MarketDataService":
        return cls(client=client, cache=SQLiteCache(cache_path))

    def close(self) -> None:
        if self.cache is not None:
            self.cache.close()

    def get_prices(
        self,
        *,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int] | None = None,
        ttl_seconds: float = 120.0,
        allow_stale: bool = True,
        allow_cache: bool = True,
    ) -> list[MarketPriceRecord]:
        started = time.perf_counter()
        cache_key = _cache_key(
            prefix="prices",
            payload={
                "region": region.value,
                "item_ids": sorted(item_ids),
                "locations": sorted(locations),
                "qualities": sorted(qualities or [1]),
            },
        )
        if allow_cache:
            cached = self._get_cached(cache_key, allow_stale=allow_stale)
            if cached is not None:
                payload_raw, source = cached
                rows = [_to_price(x) for x in payload_raw if isinstance(x, dict)]
                self._last_prices_meta = MarketFetchMeta(
                    source=source,
                    record_count=len(rows),
                    elapsed_ms=(time.perf_counter() - started) * 1000.0,
                    cache_key=cache_key,
                )
                return rows

        rows = self.client.fetch_prices(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
        )
        self._put_cached(
            cache_key,
            [x.__dict__ for x in rows],
            ttl_seconds=ttl_seconds,
        )
        self._last_prices_meta = MarketFetchMeta(
            source="live",
            record_count=len(rows),
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            cache_key=cache_key,
        )
        return rows

    def get_price_index(
        self,
        *,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int] | None = None,
        ttl_seconds: float = 120.0,
        allow_stale: bool = True,
        allow_cache: bool = True,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        rows = self.get_prices(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
            ttl_seconds=ttl_seconds,
            allow_stale=allow_stale,
            allow_cache=allow_cache,
        )
        index: dict[tuple[str, str, int], MarketPriceRecord] = {}
        for row in rows:
            key = (row.item_id, row.city, row.quality)
            index[key] = row
        return index

    def get_charts(
        self,
        *,
        region: MarketRegion,
        item_id: str,
        location: str,
        quality: int = 1,
        date_from: date | None = None,
        date_to: date | None = None,
        time_scale: int = 24,
        ttl_seconds: float = 600.0,
        allow_stale: bool = True,
    ) -> list[MarketChartPoint]:
        started = time.perf_counter()
        cache_key = _cache_key(
            prefix="charts",
            payload={
                "region": region.value,
                "item_id": item_id,
                "location": location,
                "quality": quality,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "time_scale": time_scale,
            },
        )
        cached = self._get_cached(cache_key, allow_stale=allow_stale)
        if cached is not None:
            payload_raw, source = cached
            rows = [_to_chart(x) for x in payload_raw if isinstance(x, dict)]
            self._last_charts_meta = MarketFetchMeta(
                source=source,
                record_count=len(rows),
                elapsed_ms=(time.perf_counter() - started) * 1000.0,
                cache_key=cache_key,
            )
            return rows

        rows = self.client.fetch_charts(
            region=region,
            item_id=item_id,
            location=location,
            quality=quality,
            date_from=date_from,
            date_to=date_to,
            time_scale=time_scale,
        )
        self._put_cached(
            cache_key,
            [x.__dict__ for x in rows],
            ttl_seconds=ttl_seconds,
        )
        self._last_charts_meta = MarketFetchMeta(
            source="live",
            record_count=len(rows),
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            cache_key=cache_key,
        )
        return rows

    def _get_cached(
        self,
        key: str,
        *,
        allow_stale: bool,
    ) -> tuple[list[object], str] | None:
        if self.cache is None:
            return None
        entry = self.cache.get_entry(key, allow_expired=allow_stale)
        if entry is None:
            return None
        if isinstance(entry.payload, list):
            source = "stale_cache" if entry.expired else "cache"
            return entry.payload, source
        return None

    def _put_cached(self, key: str, payload: list[object], *, ttl_seconds: float) -> None:
        if self.cache is None:
            return
        self.cache.set(key, payload, ttl_seconds=ttl_seconds)


def _cache_key(*, prefix: str, payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"market:{prefix}:{digest}"


def _to_price(row: dict[str, object]) -> MarketPriceRecord:
    return MarketPriceRecord(
        item_id=str(row.get("item_id") or ""),
        city=str(row.get("city") or ""),
        quality=int(row.get("quality") or 1),
        sell_price_min=int(row.get("sell_price_min") or 0),
        buy_price_max=int(row.get("buy_price_max") or 0),
        sell_price_min_date=str(row.get("sell_price_min_date") or ""),
        buy_price_max_date=str(row.get("buy_price_max_date") or ""),
    )


def _to_chart(row: dict[str, object]) -> MarketChartPoint:
    return MarketChartPoint(
        timestamp=str(row.get("timestamp") or ""),
        item_count=int(row.get("item_count") or 0),
        avg_price=int(row.get("avg_price") or 0),
    )
