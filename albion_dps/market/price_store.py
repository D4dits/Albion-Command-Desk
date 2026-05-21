from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import MarketRegion


DEFAULT_QUOTE_MAX_AGE_SECONDS = 120 * 60
DEFAULT_QUOTE_RETENTION_SECONDS = 180 * 60

_SIDE_SELL = "sell"
_SIDE_BUY = "buy"


@dataclass(frozen=True)
class StoredQuote:
    region: str
    location: str
    item_id: str
    quality: int
    side: str
    price: int
    amount: int
    observed_at: float
    source: str


class LocalMarketPriceStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_quotes (
                    region TEXT NOT NULL,
                    location TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    quality INTEGER NOT NULL,
                    side TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    amount INTEGER NOT NULL DEFAULT 0,
                    observed_at REAL NOT NULL,
                    source TEXT NOT NULL,
                    PRIMARY KEY(region, location, item_id, quality, side)
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_quotes_fresh ON market_quotes(region, observed_at)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_market_quotes_lookup ON market_quotes(region, location, item_id, quality)"
            )
            self._conn.commit()
        self._normalize_existing_scanner_quotes()

    def upsert_aodata_prices(
        self,
        *,
        region: MarketRegion,
        rows: Iterable[MarketPriceRecord],
        source: str = "aodata",
    ) -> int:
        count = 0
        for row in rows:
            count += self.upsert_price_record(region=region, row=row, source=source)
        return count

    def upsert_price_record(
        self,
        *,
        region: MarketRegion,
        row: MarketPriceRecord,
        source: str,
    ) -> int:
        updates = 0
        sell_price = int(row.sell_price_min or 0)
        buy_price = int(row.buy_price_max or 0)
        if sell_price > 0:
            updates += self.upsert_quote(
                region=region.value,
                location=row.city,
                item_id=row.item_id,
                quality=row.quality,
                side=_SIDE_SELL,
                price=sell_price,
                amount=0,
                observed_at=_parse_observed_at(row.sell_price_min_date),
                source=source,
            )
        if buy_price > 0:
            updates += self.upsert_quote(
                region=region.value,
                location=row.city,
                item_id=row.item_id,
                quality=row.quality,
                side=_SIDE_BUY,
                price=buy_price,
                amount=0,
                observed_at=_parse_observed_at(row.buy_price_max_date),
                source=source,
            )
        return updates

    def upsert_scanner_payload(
        self,
        *,
        region: MarketRegion,
        payload: object,
        source: str = "scanner_ws",
    ) -> int:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return 0
        if not isinstance(payload, dict):
            return 0
        orders = payload.get("Orders")
        if not isinstance(orders, list):
            return 0
        count = 0
        observed_at = time.time()
        for order in orders:
            if not isinstance(order, dict):
                continue
            item_id = str(order.get("ItemTypeId") or "").strip()
            location = normalize_market_location(str(order.get("LocationId") or "").strip())
            side = _auction_side(order.get("AuctionType"))
            price = _normalize_scanner_price(_as_int(order.get("UnitPriceSilver")))
            quality = _as_int(order.get("QualityLevel"), default=1)
            amount = _as_int(order.get("Amount"))
            if not item_id or not location or side not in {_SIDE_SELL, _SIDE_BUY} or price <= 0:
                continue
            count += self.upsert_quote(
                region=region.value,
                location=location,
                item_id=item_id,
                quality=quality,
                side=side,
                price=price,
                amount=amount,
                observed_at=observed_at,
                source=source,
            )
        return count

    def upsert_quote(
        self,
        *,
        region: str,
        location: str,
        item_id: str,
        quality: int,
        side: str,
        price: int,
        amount: int,
        observed_at: float | None = None,
        source: str,
    ) -> int:
        region_text = str(region or "").strip().lower()
        location_text = normalize_market_location(location)
        item_text = str(item_id or "").strip()
        side_text = str(side or "").strip().lower()
        if not region_text or not location_text or not item_text:
            return 0
        if side_text not in {_SIDE_SELL, _SIDE_BUY}:
            return 0
        price_int = int(price or 0)
        if price_int <= 0:
            return 0
        observed = time.time() if observed_at is None else float(observed_at)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO market_quotes(region, location, item_id, quality, side, price, amount, observed_at, source)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(region, location, item_id, quality, side) DO UPDATE SET
                    price=excluded.price,
                    amount=excluded.amount,
                    observed_at=excluded.observed_at,
                    source=excluded.source
                """,
                (
                    region_text,
                    location_text,
                    item_text,
                    max(1, int(quality or 1)),
                    side_text,
                    price_int,
                    max(0, int(amount or 0)),
                    observed,
                    str(source or "unknown"),
                ),
            )
            self._conn.commit()
        return 1

    def get_price_index(
        self,
        *,
        region: MarketRegion,
        item_ids: Iterable[str],
        locations: Iterable[str],
        qualities: Iterable[int],
        max_age_seconds: float = DEFAULT_QUOTE_MAX_AGE_SECONDS,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        item_list = sorted({str(item_id).strip() for item_id in item_ids if str(item_id).strip()})
        location_list = sorted({normalize_market_location(location) for location in locations if normalize_market_location(location)})
        quality_list = sorted({max(1, int(quality or 1)) for quality in qualities})
        if not item_list or not location_list or not quality_list:
            return {}
        cutoff = time.time() - max(0.0, float(max_age_seconds))
        rows = []
        with self._lock:
            for item_chunk in _chunks(item_list, 300):
                sql = f"""
                    SELECT item_id, location, quality, side, price, observed_at
                    FROM market_quotes
                    WHERE region=?
                      AND observed_at>=?
                      AND item_id IN ({",".join("?" for _ in item_chunk)})
                      AND location IN ({",".join("?" for _ in location_list)})
                      AND quality IN ({",".join("?" for _ in quality_list)})
                """
                params: list[object] = [region.value, cutoff, *item_chunk, *location_list, *quality_list]
                rows.extend(self._conn.execute(sql, params).fetchall())
        combined: dict[tuple[str, str, int], dict[str, object]] = {}
        for item_id, location, quality, side, price, observed_at in rows:
            key = (str(item_id), str(location), int(quality))
            bucket = combined.setdefault(
                key,
                {
                    "sell": 0,
                    "buy": 0,
                    "sell_at": "",
                    "buy_at": "",
                },
            )
            if side == _SIDE_SELL:
                bucket["sell"] = int(price)
                bucket["sell_at"] = _format_observed_at(float(observed_at))
            elif side == _SIDE_BUY:
                bucket["buy"] = int(price)
                bucket["buy_at"] = _format_observed_at(float(observed_at))
        return {
            key: MarketPriceRecord(
                item_id=key[0],
                city=key[1],
                quality=key[2],
                sell_price_min=int(values["sell"] or 0),
                buy_price_max=int(values["buy"] or 0),
                sell_price_min_date=str(values["sell_at"] or ""),
                buy_price_max_date=str(values["buy_at"] or ""),
            )
            for key, values in combined.items()
        }

    def clear_old_quotes(self, *, retention_seconds: float = DEFAULT_QUOTE_RETENTION_SECONDS) -> int:
        cutoff = time.time() - max(0.0, float(retention_seconds))
        with self._lock:
            cur = self._conn.execute("DELETE FROM market_quotes WHERE observed_at < ?", (cutoff,))
            self._conn.commit()
        return int(cur.rowcount)

    def count_quotes(self, *, region: MarketRegion | None = None, max_age_seconds: float | None = None) -> int:
        where: list[str] = []
        params: list[object] = []
        if region is not None:
            where.append("region=?")
            params.append(region.value)
        if max_age_seconds is not None:
            where.append("observed_at>=?")
            params.append(time.time() - max(0.0, float(max_age_seconds)))
        sql = "SELECT COUNT(*) FROM market_quotes"
        if where:
            sql += " WHERE " + " AND ".join(where)
        with self._lock:
            row = self._conn.execute(sql, params).fetchone()
        return int(row[0] if row else 0)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _normalize_existing_scanner_quotes(self) -> None:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT region, location, item_id, quality, side, price, amount, observed_at, source
                FROM market_quotes
                WHERE source='scanner_ws'
                """
            ).fetchall()
            if not rows:
                return
            self._conn.execute("DELETE FROM market_quotes WHERE source='scanner_ws'")
            for region, location, item_id, quality, side, price, amount, observed_at, source in rows:
                raw_location = str(location or "").strip()
                normalized_price = _normalize_existing_scanner_price(
                    int(price or 0),
                    raw_location=raw_location,
                )
                normalized_location = normalize_market_location(location)
                if normalized_price <= 0 or not normalized_location:
                    continue
                self._conn.execute(
                    """
                    INSERT INTO market_quotes(region, location, item_id, quality, side, price, amount, observed_at, source)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(region, location, item_id, quality, side) DO UPDATE SET
                        price=excluded.price,
                        amount=excluded.amount,
                        observed_at=excluded.observed_at,
                        source=excluded.source
                    """,
                    (
                        str(region),
                        normalized_location,
                        str(item_id),
                        int(quality or 1),
                        str(side),
                        normalized_price,
                        int(amount or 0),
                        float(observed_at or time.time()),
                        str(source or "scanner_ws"),
                    ),
                )
            self._conn.commit()


_LOCATION_ALIASES = {
    "0007": "Thetford",
    "1002": "Lymhurst",
    "2004": "Bridgewatch",
    "3003": "Black Market",
    "3005": "Caerleon",
    "3008": "Martlock",
    "4002": "Fort Sterling",
    "black market": "Black Market",
    "blackmarket": "Black Market",
    "caerleon": "Caerleon",
    "bridgewatch": "Bridgewatch",
    "martlock": "Martlock",
    "lymhurst": "Lymhurst",
    "fort sterling": "Fort Sterling",
    "fortsterling": "Fort Sterling",
    "thetford": "Thetford",
    "brecilien": "Brecilien",
}


def normalize_market_location(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lower = text.lower().replace("_", " ").replace("-", " ")
    if text.upper().startswith("BLACKBANK-") or "black market" in lower or "blackmarket" in lower:
        return "Black Market"
    for alias, canonical in _LOCATION_ALIASES.items():
        if lower == alias or alias in lower:
            return canonical
    return text


def _auction_side(value: object) -> str:
    text = str(value or "").strip().lower()
    if "offer" in text or "sell" in text:
        return _SIDE_SELL
    if "request" in text or "buy" in text:
        return _SIDE_BUY
    return ""


def _as_int(value: object, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_scanner_price(value: int) -> int:
    price = int(value or 0)
    if price <= 0:
        return 0
    if price >= 10_000 and price % 10_000 == 0:
        return max(1, price // 10_000)
    if price > 10_000:
        return max(1, round(price / 10_000))
    return price


def _normalize_existing_scanner_price(value: int, *, raw_location: str) -> int:
    price = int(value or 0)
    if price <= 0:
        return 0
    location_was_raw = str(raw_location or "").strip() in _LOCATION_ALIASES
    if location_was_raw and price >= 10_000 and price % 10_000 == 0:
        return max(1, price // 10_000)
    if location_was_raw and price > 10_000:
        return max(1, round(price / 10_000))
    if price >= 10_000_000 and price % 10_000 == 0:
        return max(1, price // 10_000)
    if price > 10_000_000:
        return max(1, round(price / 10_000))
    return price


def _parse_observed_at(raw: str) -> float:
    text = str(raw or "").strip()
    if not text:
        return time.time()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return time.time()
    if parsed.year <= 2001:
        return time.time()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).timestamp()


def _format_observed_at(value: float) -> str:
    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()


def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
    step = max(1, int(size))
    for index in range(0, len(values), step):
        yield values[index : index + step]
