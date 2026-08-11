from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import MarketRegion
from albion_dps.market.price_store import normalize_market_location


CITY_NAMES = ("Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien")
BLACK_MARKET_CITY = "Black Market"
LOCATION_ALIASES = {
    "0007": "Thetford",
    "1002": "Lymhurst",
    "2004": "Bridgewatch",
    "3003": BLACK_MARKET_CITY,
    "3005": "Caerleon",
    "3008": "Martlock",
    "4002": "Fort Sterling",
}


@dataclass(frozen=True)
class LocalMarketStats:
    orders_seen: int = 0
    orders_stored: int = 0
    orders_ignored: int = 0


class LocalMarketStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS local_market_orders (
                    region TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    raw_item_id TEXT NOT NULL,
                    location_id TEXT NOT NULL,
                    city TEXT NOT NULL,
                    quality INTEGER NOT NULL,
                    enchantment INTEGER NOT NULL,
                    side TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    auction_type TEXT NOT NULL,
                    expires TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY(region, order_id, side)
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_local_market_lookup "
                "ON local_market_orders(region, item_id, city, quality, side, observed_at)"
            )
            self._migrate_scanner_values()
            self._conn.commit()

    def _migrate_scanner_values(self) -> None:
        version = int(self._conn.execute("PRAGMA user_version").fetchone()[0])
        if version >= 1:
            return
        rows = self._conn.execute(
            "SELECT rowid, location_id, city, price FROM local_market_orders"
        ).fetchall()
        updates: list[tuple[str, int, int]] = []
        for row in rows:
            city = normalize_location_id(row["location_id"]) or str(row["city"])
            price = _normalize_existing_scanner_price(
                int(row["price"] or 0),
                raw_location=str(row["location_id"] or ""),
            )
            updates.append((city, price, int(row["rowid"])))
        if updates:
            self._conn.executemany(
                "UPDATE local_market_orders SET city=?, price=? WHERE rowid=?",
                updates,
            )
        self._conn.execute("PRAGMA user_version=1")

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def upsert_market_upload(
        self,
        payload: dict[str, Any],
        *,
        region: MarketRegion = MarketRegion.EUROPE,
        observed_at: datetime | None = None,
    ) -> LocalMarketStats:
        raw_orders = payload.get("Orders")
        if not isinstance(raw_orders, list):
            return LocalMarketStats()
        observed = _to_aod_timestamp(observed_at or datetime.now(timezone.utc))
        rows: list[tuple[object, ...]] = []
        ignored = 0
        for raw in raw_orders:
            if not isinstance(raw, dict):
                ignored += 1
                continue
            row = _normalize_order(raw, region=region, observed_at=observed)
            if row is None:
                ignored += 1
                continue
            rows.append(row)
        if rows:
            with self._lock:
                self._conn.executemany(
                    """
                    INSERT OR REPLACE INTO local_market_orders(
                        region, order_id, item_id, raw_item_id, location_id, city, quality,
                        enchantment, side, price, amount, auction_type, expires,
                        observed_at, payload_json
                    )
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows,
                )
                self._conn.commit()
        return LocalMarketStats(orders_seen=len(raw_orders), orders_stored=len(rows), orders_ignored=ignored)

    def get_prices(
        self,
        *,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int] | None = None,
    ) -> list[MarketPriceRecord]:
        requested_items = {str(item_id) for item_id in item_ids if str(item_id or "").strip()}
        requested_locations = _location_query_values(locations)
        requested_qualities = {int(quality) for quality in (qualities or [1])}
        if not requested_items or not requested_locations or not requested_qualities:
            return []
        placeholders_items = ",".join("?" for _ in requested_items)
        placeholders_locations = ",".join("?" for _ in requested_locations)
        placeholders_qualities = ",".join("?" for _ in requested_qualities)
        params: list[object] = [
            region.value,
            *sorted(requested_items),
            *sorted(requested_locations),
            *sorted(requested_qualities),
        ]
        query = (
            "SELECT item_id, city, quality, side, price, observed_at "
            "FROM local_market_orders "
            "WHERE region=? "
            f"AND item_id IN ({placeholders_items}) "
            f"AND city IN ({placeholders_locations}) "
            f"AND quality IN ({placeholders_qualities}) "
            "AND price > 0"
        )
        with self._lock:
            rows = list(self._conn.execute(query, params))
        grouped: dict[tuple[str, str, int], dict[str, object]] = {}
        for row in rows:
            city = normalize_location_id(row["city"])
            key = (str(row["item_id"]), city, int(row["quality"]))
            current = grouped.setdefault(
                key,
                {
                    "sell_price_min": 0,
                    "sell_price_min_date": "",
                    "buy_price_max": 0,
                    "buy_price_max_date": "",
                },
            )
            side = str(row["side"])
            price = _normalize_existing_scanner_price(
                int(row["price"]),
                raw_location=str(row["city"]),
            )
            observed = str(row["observed_at"])
            if side == "sell":
                previous = int(current["sell_price_min"] or 0)
                if previous <= 0 or price < previous or (price == previous and observed > str(current["sell_price_min_date"])):
                    current["sell_price_min"] = price
                    current["sell_price_min_date"] = observed
            elif side == "buy":
                previous = int(current["buy_price_max"] or 0)
                if price > previous or (price == previous and observed > str(current["buy_price_max_date"])):
                    current["buy_price_max"] = price
                    current["buy_price_max_date"] = observed
        out: list[MarketPriceRecord] = []
        for (item_id, city, quality), values in grouped.items():
            out.append(
                MarketPriceRecord(
                    item_id=item_id,
                    city=city,
                    quality=quality,
                    sell_price_min=int(values["sell_price_min"] or 0),
                    buy_price_max=int(values["buy_price_max"] or 0),
                    sell_price_min_date=str(values["sell_price_min_date"] or ""),
                    buy_price_max_date=str(values["buy_price_max_date"] or ""),
                )
            )
        return out


def parse_market_upload_message(message: str | bytes) -> dict[str, Any] | None:
    if isinstance(message, bytes):
        message = message.decode("utf-8", errors="replace")
    raw = json.loads(message)
    if not isinstance(raw, dict):
        return None
    topic = str(raw.get("topic") or "")
    if topic != "marketorders.ingest":
        return None
    data = raw.get("data")
    if not isinstance(data, dict):
        return None
    return data


def normalize_location_id(location_id: object) -> str:
    value = str(location_id or "").strip()
    if not value:
        return ""
    upper = value.upper()
    if upper.startswith("BLACKBANK-") or upper == "BLACK MARKET":
        return BLACK_MARKET_CITY
    lower = value.lower().replace("_", " ").replace("-", " ")
    alias = LOCATION_ALIASES.get(lower)
    if alias:
        return alias
    compact = _compact_city(value)
    for city in CITY_NAMES:
        city_compact = _compact_city(city)
        if compact == city_compact or city_compact in compact:
            return city
    return normalize_market_location(value)


def _location_query_values(locations: list[str]) -> set[str]:
    out: set[str] = set()
    reverse_aliases: dict[str, set[str]] = {}
    for alias, city in LOCATION_ALIASES.items():
        reverse_aliases.setdefault(city, set()).add(alias)
    for location in locations:
        raw = str(location or "").strip()
        if not raw:
            continue
        normalized = normalize_location_id(raw)
        out.add(raw)
        out.add(normalized)
        out.update(reverse_aliases.get(normalized, set()))
    return out


def _normalize_order(
    raw: dict[str, Any],
    *,
    region: MarketRegion,
    observed_at: str,
) -> tuple[object, ...] | None:
    raw_item_id = str(raw.get("ItemTypeId") or "").strip()
    if not raw_item_id:
        return None
    location_id = str(raw.get("LocationId") or "").strip()
    city = normalize_location_id(location_id)
    if not city:
        return None
    side = _auction_side(raw.get("AuctionType"))
    if side is None:
        return None
    try:
        price = _normalize_scanner_price(int(raw.get("UnitPriceSilver") or 0))
        amount = int(raw.get("Amount") or 0)
        quality = int(raw.get("QualityLevel") or 1)
        enchantment = int(raw.get("EnchantmentLevel") or 0)
    except (TypeError, ValueError):
        return None
    if price <= 0:
        return None
    item_id = _item_id_with_enchantment(raw_item_id, enchantment)
    order_id = str(raw.get("Id") or "")
    if not order_id:
        order_id = f"{side}:{item_id}:{location_id}:{quality}:{price}:{amount}:{raw.get('Expires') or ''}"
    auction_type = str(raw.get("AuctionType") or "")
    expires = str(raw.get("Expires") or "")
    return (
        region.value,
        order_id,
        item_id,
        raw_item_id,
        location_id,
        city,
        quality,
        enchantment,
        side,
        price,
        amount,
        auction_type,
        expires,
        observed_at,
        json.dumps(raw, sort_keys=True, separators=(",", ":")),
    )


def _item_id_with_enchantment(item_id: str, enchantment: int) -> str:
    if enchantment <= 0:
        return item_id
    if "@" in item_id:
        return item_id
    return f"{item_id}@{enchantment}"


def _auction_side(value: object) -> str | None:
    text = str(value or "").strip().lower()
    if "offer" in text or "sell" in text:
        return "sell"
    if "request" in text or "buy" in text:
        return "buy"
    return None


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
    location_was_raw = str(raw_location or "").strip().lower() in LOCATION_ALIASES
    if location_was_raw and price >= 10_000 and price % 10_000 == 0:
        return max(1, price // 10_000)
    if location_was_raw and price > 10_000:
        return max(1, round(price / 10_000))
    if price >= 10_000_000 and price % 10_000 == 0:
        return max(1, price // 10_000)
    if price > 10_000_000:
        return max(1, round(price / 10_000))
    return price


def _to_aod_timestamp(value: datetime) -> str:
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.isoformat(timespec="seconds")


def _compact_city(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())
