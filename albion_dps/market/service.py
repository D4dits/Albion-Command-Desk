from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from albion_dps.market.aod_client import AODataClient, MarketChartPoint, MarketPriceRecord
from albion_dps.market.cache import SQLiteCache
from albion_dps.market.local_store import LocalMarketStore
from albion_dps.market.models import MarketRegion
from albion_dps.market.price_store import LocalMarketPriceStore


@dataclass(frozen=True)
class MarketFetchMeta:
    source: str
    record_count: int
    elapsed_ms: float
    cache_key: str
    local_record_count: int = 0
    remote_record_count: int = 0


class MarketDataService:
    def __init__(
        self,
        *,
        client: AODataClient | None = None,
        cache: SQLiteCache | None = None,
        price_store: LocalMarketPriceStore | None = None,
        local_store: LocalMarketStore | None = None,
        local_fresh_seconds: float = 3600.0,
    ) -> None:
        self.client = client or AODataClient()
        self.cache = cache
        self.price_store = price_store
        self.local_store = local_store
        self.local_fresh_seconds = max(0.0, float(local_fresh_seconds))
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
        price_store: LocalMarketPriceStore | None = None,
        local_store: LocalMarketStore | None = None,
    ) -> "MarketDataService":
        return cls(
            client=client,
            cache=SQLiteCache(cache_path),
            price_store=price_store,
            local_store=local_store,
        )

    def close(self) -> None:
        if self.cache is not None:
            self.cache.close()
        if self.price_store is not None:
            self.price_store.close()
        if self.local_store is not None:
            self.local_store.close()

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
        allow_live: bool = True,
    ) -> list[MarketPriceRecord]:
        started = time.perf_counter()
        qualities = qualities or [1]
        cache_key = _cache_key(
            prefix="prices",
            payload={
                "region": region.value,
                "item_ids": sorted(item_ids),
                "locations": sorted(locations),
                "qualities": sorted(qualities),
            },
        )
        local_store_rows = self._get_local_store_prices(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
        )
        price_store_rows = self._get_price_store_prices(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
        )
        local_rows = _merge_price_rows(local_store_rows, price_store_rows)
        local_source = _local_source(
            local_store_count=len(local_store_rows),
            price_store_count=len(price_store_rows),
        )
        requested_keys = {
            (str(item_id), str(location), int(quality))
            for item_id in item_ids
            for location in locations
            for quality in qualities
        }
        local_index = {(row.item_id, row.city, row.quality): row for row in local_rows}
        remote_needed = True
        if local_rows:
            remote_needed = bool(requested_keys - set(local_index)) or any(
                _price_record_stale(row, max_age_seconds=self.local_fresh_seconds) for row in local_rows
            )

        remote_rows: list[MarketPriceRecord] = []
        remote_source = "none"
        if remote_needed:
            remote_rows, remote_source = self._get_remote_prices(
                cache_key=cache_key,
                region=region,
                item_ids=item_ids,
                locations=locations,
                qualities=qualities,
                ttl_seconds=ttl_seconds,
                allow_stale=allow_stale,
                allow_cache=allow_cache,
                allow_live=allow_live,
            )
        if self.price_store is not None and remote_rows:
            self.price_store.upsert_aodata_prices(region=region, rows=remote_rows)

        rows = _merge_price_rows(local_rows, remote_rows)
        source = _combined_source(
            local_source=local_source,
            local_count=len(local_rows),
            remote_count=len(remote_rows),
            remote_source=remote_source,
            remote_needed=remote_needed,
            allow_live=allow_live,
        )
        self._last_prices_meta = MarketFetchMeta(
            source=source,
            record_count=len(rows),
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            cache_key=cache_key,
            local_record_count=len(local_rows),
            remote_record_count=len(remote_rows),
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
        allow_live: bool = True,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        rows = self.get_prices(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
            ttl_seconds=ttl_seconds,
            allow_stale=allow_stale,
            allow_cache=allow_cache,
            allow_live=allow_live,
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

    def _get_cached_price_subset(
        self,
        *,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int],
        allow_stale: bool,
    ) -> tuple[list[MarketPriceRecord], str] | None:
        if self.cache is None:
            return None
        requested_items = {str(item_id) for item_id in item_ids}
        requested_locations = {str(location) for location in locations}
        requested_qualities = {int(quality) for quality in qualities}
        if not requested_items or not requested_locations or not requested_qualities:
            return None

        entries = self.cache.get_entries_by_prefix(
            "market:prices:",
            allow_expired=allow_stale,
        )
        if not entries:
            return None

        matched: dict[tuple[str, str, int], MarketPriceRecord] = {}
        saw_expired = False
        for entry in entries:
            if entry.expired:
                saw_expired = True
            if not isinstance(entry.payload, list):
                continue
            for row in entry.payload:
                if not isinstance(row, dict):
                    continue
                price = _to_price(row)
                key = (price.item_id, price.city, price.quality)
                if key in matched:
                    continue
                if price.item_id not in requested_items:
                    continue
                if price.city not in requested_locations:
                    continue
                if price.quality not in requested_qualities:
                    continue
                matched[key] = price
        if not matched:
            return None
        source = "partial_stale_cache" if saw_expired else "partial_cache"
        return list(matched.values()), source

    def _get_local_store_prices(
        self,
        *,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int],
    ) -> list[MarketPriceRecord]:
        if self.local_store is None:
            return []
        return self.local_store.get_prices(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
        )

    def _get_price_store_prices(
        self,
        *,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int],
    ) -> list[MarketPriceRecord]:
        if self.price_store is None:
            return []
        index = self.price_store.get_price_index(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
        )
        return list(index.values())

    def _get_remote_prices(
        self,
        *,
        cache_key: str,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int],
        ttl_seconds: float,
        allow_stale: bool,
        allow_cache: bool,
        allow_live: bool,
    ) -> tuple[list[MarketPriceRecord], str]:
        if allow_cache:
            cached = self._get_cached(cache_key, allow_stale=allow_stale)
            if cached is not None:
                payload_raw, source = cached
                return [_to_price(x) for x in payload_raw if isinstance(x, dict)], source
            partial_cached = self._get_cached_price_subset(
                item_ids=item_ids,
                locations=locations,
                qualities=qualities,
                allow_stale=allow_stale,
            )
            if partial_cached is not None:
                rows, source = partial_cached
                return rows, source

        if not allow_live:
            return [], "cache_miss"

        rows = self.client.fetch_prices(
            region=region,
            item_ids=item_ids,
            locations=locations,
            qualities=qualities,
        )
        rows = _mark_live_price_rows_observed(rows)
        self._put_cached(
            cache_key,
            [x.__dict__ for x in rows],
            ttl_seconds=ttl_seconds,
        )
        return rows, "live"

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


def _merge_price_rows(
    local_rows: list[MarketPriceRecord],
    remote_rows: list[MarketPriceRecord],
) -> list[MarketPriceRecord]:
    merged: dict[tuple[str, str, int], MarketPriceRecord] = {}
    for row in remote_rows:
        merged[(row.item_id, row.city, row.quality)] = row
    for row in local_rows:
        key = (row.item_id, row.city, row.quality)
        existing = merged.get(key)
        merged[key] = row if existing is None else _merge_price_record(local=row, remote=existing)
    return list(merged.values())


def _merge_price_record(*, local: MarketPriceRecord, remote: MarketPriceRecord) -> MarketPriceRecord:
    sell_price, sell_date = (
        (local.sell_price_min, local.sell_price_min_date)
        if _date_newer_or_equal(local.sell_price_min_date, remote.sell_price_min_date)
        else (remote.sell_price_min, remote.sell_price_min_date)
    )
    if local.sell_price_min <= 0:
        sell_price, sell_date = remote.sell_price_min, remote.sell_price_min_date
    elif remote.sell_price_min <= 0:
        sell_price, sell_date = local.sell_price_min, local.sell_price_min_date

    buy_price, buy_date = (
        (local.buy_price_max, local.buy_price_max_date)
        if _date_newer_or_equal(local.buy_price_max_date, remote.buy_price_max_date)
        else (remote.buy_price_max, remote.buy_price_max_date)
    )
    if local.buy_price_max <= 0:
        buy_price, buy_date = remote.buy_price_max, remote.buy_price_max_date
    elif remote.buy_price_max <= 0:
        buy_price, buy_date = local.buy_price_max, local.buy_price_max_date

    return MarketPriceRecord(
        item_id=local.item_id,
        city=local.city,
        quality=local.quality,
        sell_price_min=sell_price,
        buy_price_max=buy_price,
        sell_price_min_date=sell_date,
        buy_price_max_date=buy_date,
    )


def _mark_live_price_rows_observed(rows: list[MarketPriceRecord]) -> list[MarketPriceRecord]:
    if not rows:
        return []
    observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out: list[MarketPriceRecord] = []
    for row in rows:
        out.append(
            MarketPriceRecord(
                item_id=row.item_id,
                city=row.city,
                quality=row.quality,
                sell_price_min=row.sell_price_min,
                buy_price_max=row.buy_price_max,
                sell_price_min_date=observed_at if int(row.sell_price_min or 0) > 0 else "",
                buy_price_max_date=observed_at if int(row.buy_price_max or 0) > 0 else "",
            )
        )
    return out


def _combined_source(
    *,
    local_source: str,
    local_count: int,
    remote_count: int,
    remote_source: str,
    remote_needed: bool,
    allow_live: bool,
) -> str:
    if local_count and remote_count:
        return f"{local_source}+{remote_source}"
    if local_count:
        return local_source
    if remote_count:
        return remote_source
    if remote_needed and not allow_live:
        return "cache_miss"
    return remote_source if remote_source != "none" else "none"


def _local_source(*, local_store_count: int, price_store_count: int) -> str:
    if local_store_count and price_store_count:
        return "local+local_db"
    if local_store_count:
        return "local"
    if price_store_count:
        return "local_db"
    return "none"


def _price_record_stale(row: MarketPriceRecord, *, max_age_seconds: float) -> bool:
    if max_age_seconds <= 0:
        return False
    dates = [
        parsed
        for parsed in (
            _parse_timestamp(row.sell_price_min_date),
            _parse_timestamp(row.buy_price_max_date),
        )
        if parsed is not None
    ]
    latest = max(dates) if dates else None
    if latest is None:
        return True
    return (datetime.now(timezone.utc) - latest).total_seconds() > max_age_seconds


def _date_newer_or_equal(left: str, right: str) -> bool:
    left_dt = _parse_timestamp(left)
    right_dt = _parse_timestamp(right)
    if left_dt is None:
        return right_dt is None
    if right_dt is None:
        return True
    return left_dt >= right_dt


def _parse_timestamp(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text or text.startswith("0001-01-01"):
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _to_chart(row: dict[str, object]) -> MarketChartPoint:
    return MarketChartPoint(
        timestamp=str(row.get("timestamp") or ""),
        item_count=int(row.get("item_count") or 0),
        avg_price=int(row.get("avg_price") or 0),
    )
