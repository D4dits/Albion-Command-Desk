from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from albion_dps.market.models import MarketRegion


REGION_HOSTS: dict[MarketRegion, str] = {
    MarketRegion.EUROPE: "europe.albion-online-data.com",
    MarketRegion.WEST: "west.albion-online-data.com",
    MarketRegion.EAST: "east.albion-online-data.com",
}


@dataclass(frozen=True)
class MarketPriceRecord:
    item_id: str
    city: str
    quality: int
    sell_price_min: int
    buy_price_max: int
    sell_price_min_date: str
    buy_price_max_date: str


@dataclass(frozen=True)
class MarketChartPoint:
    timestamp: str
    item_count: int
    avg_price: int


@dataclass(frozen=True)
class AODataRequestStats:
    endpoint: str
    url: str
    attempts: int
    elapsed_ms: float
    success: bool
    error: str


class AODataClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 12.0,
        user_agent: str = "albion-dps-market/0.1",
        fetch_json: Callable[[str, float, str], object] | None = None,
        max_retries: int = 2,
        retry_backoff_initial_seconds: float = 0.20,
        retry_backoff_factor: float = 2.0,
        retry_backoff_max_seconds: float = 2.0,
        sleeper: Callable[[float], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._user_agent = user_agent
        self._fetch_json = fetch_json or _default_fetch_json
        self._max_retries = max(0, int(max_retries))
        self._retry_backoff_initial_seconds = max(0.0, float(retry_backoff_initial_seconds))
        self._retry_backoff_factor = max(1.0, float(retry_backoff_factor))
        self._retry_backoff_max_seconds = max(0.0, float(retry_backoff_max_seconds))
        self._sleep = sleeper or time.sleep
        self._log = logger or logging.getLogger(__name__)
        self._last_request_stats = AODataRequestStats(
            endpoint="",
            url="",
            attempts=0,
            elapsed_ms=0.0,
            success=False,
            error="",
        )

    @property
    def last_request_stats(self) -> AODataRequestStats:
        return self._last_request_stats

    def fetch_prices(
        self,
        *,
        region: MarketRegion,
        item_ids: list[str],
        locations: list[str],
        qualities: list[int] | None = None,
    ) -> list[MarketPriceRecord]:
        if not item_ids:
            return []
        if not locations:
            return []
        base = self._base_url(region)
        ids = ",".join(item_ids)
        params = {
            "locations": ",".join(locations),
            "qualities": ",".join(str(x) for x in (qualities or [1])),
        }
        url = f"{base}/api/v2/stats/prices/{ids}.json?{urlencode(params)}"
        data = self._fetch_with_retry(url=url, endpoint="prices")
        return _normalize_prices(data)

    def fetch_charts(
        self,
        *,
        region: MarketRegion,
        item_id: str,
        location: str,
        quality: int = 1,
        date_from: date | None = None,
        date_to: date | None = None,
        time_scale: int = 24,
    ) -> list[MarketChartPoint]:
        base = self._base_url(region)
        params: dict[str, str] = {
            "locations": location,
            "qualities": str(quality),
            "time-scale": str(time_scale),
        }
        if date_from is not None:
            params["date"] = date_from.isoformat()
        if date_to is not None:
            params["end_date"] = date_to.isoformat()
        url = f"{base}/api/v2/stats/charts/{item_id}.json?{urlencode(params)}"
        data = self._fetch_with_retry(url=url, endpoint="charts")
        return _normalize_charts(data)

    def _base_url(self, region: MarketRegion) -> str:
        host = REGION_HOSTS[region]
        return f"https://{host}"

    def _fetch_with_retry(self, *, url: str, endpoint: str) -> object:
        max_attempts = self._max_retries + 1
        started = time.perf_counter()
        attempt = 0
        last_error: Exception | None = None
        backoff_seconds = self._retry_backoff_initial_seconds

        while attempt < max_attempts:
            attempt += 1
            try:
                payload = self._fetch_json(url, self._timeout_seconds, self._user_agent)
                self._last_request_stats = AODataRequestStats(
                    endpoint=endpoint,
                    url=url,
                    attempts=attempt,
                    elapsed_ms=(time.perf_counter() - started) * 1000.0,
                    success=True,
                    error="",
                )
                return payload
            except Exception as exc:
                last_error = exc
                if attempt >= max_attempts:
                    break
                if backoff_seconds > 0:
                    self._sleep(backoff_seconds)
                    backoff_seconds = min(
                        self._retry_backoff_max_seconds,
                        backoff_seconds * self._retry_backoff_factor,
                    )
                self._log.debug(
                    "AO Data request retry (%s), attempt %d/%d, url=%s, error=%s",
                    endpoint,
                    attempt + 1,
                    max_attempts,
                    url,
                    exc,
                )

        error_message = str(last_error) if last_error is not None else "unknown fetch error"
        self._last_request_stats = AODataRequestStats(
            endpoint=endpoint,
            url=url,
            attempts=max_attempts,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            success=False,
            error=error_message,
        )
        raise RuntimeError(f"AO Data {endpoint} request failed after {max_attempts} attempts: {error_message}")


def _normalize_prices(payload: object) -> list[MarketPriceRecord]:
    if not isinstance(payload, list):
        return []
    out: list[MarketPriceRecord] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        out.append(
            MarketPriceRecord(
                item_id=str(row.get("item_id") or ""),
                city=str(row.get("city") or row.get("location") or ""),
                quality=_as_int(row.get("quality"), default=1),
                sell_price_min=_as_int(row.get("sell_price_min"), default=0),
                buy_price_max=_as_int(row.get("buy_price_max"), default=0),
                sell_price_min_date=str(row.get("sell_price_min_date") or ""),
                buy_price_max_date=str(row.get("buy_price_max_date") or ""),
            )
        )
    return out


def _normalize_charts(payload: object) -> list[MarketChartPoint]:
    if not isinstance(payload, list):
        return []
    points: list[MarketChartPoint] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        series = row.get("data")
        if not isinstance(series, list):
            continue
        for p in series:
            if not isinstance(p, dict):
                continue
            points.append(
                MarketChartPoint(
                    timestamp=str(p.get("timestamp") or ""),
                    item_count=_as_int(p.get("item_count"), default=0),
                    avg_price=_as_int(p.get("avg_price"), default=0),
                )
            )
    return points


def _as_int(value: object, *, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _default_fetch_json(url: str, timeout_seconds: float, user_agent: str) -> object:
    request = Request(url, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)

