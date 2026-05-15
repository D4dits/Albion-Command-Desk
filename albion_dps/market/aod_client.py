from __future__ import annotations

import json
import logging
import time
import gzip
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from typing import Callable
from urllib.error import HTTPError
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
        user_agent: str = "albion-command-desk-market/0.1",
        fetch_json: Callable[[str, float, str], object] | None = None,
        max_retries: int = 5,
        max_price_retries: int | None = None,
        retry_backoff_initial_seconds: float = 1.0,
        retry_backoff_factor: float = 2.0,
        retry_backoff_max_seconds: float = 30.0,
        max_prices_url_length: int = 4000,
        max_prices_items_per_batch: int = 100,
        max_prices_items_per_rate_limited_batch: int = 40,
        batch_pause_seconds: float = 0.0,
        rate_limited_batch_pause_seconds: float = 1.25,
        max_price_batch_workers: int | None = None,
        sleeper: Callable[[float], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._user_agent = user_agent
        self._fetch_json = fetch_json or _default_fetch_json
        self._max_retries = max(0, int(max_retries))
        self._max_price_retries = self._max_retries if max_price_retries is None else max(0, int(max_price_retries))
        self._retry_backoff_initial_seconds = max(0.0, float(retry_backoff_initial_seconds))
        self._retry_backoff_factor = max(1.0, float(retry_backoff_factor))
        self._retry_backoff_max_seconds = max(0.0, float(retry_backoff_max_seconds))
        self._max_prices_url_length = max(256, int(max_prices_url_length))
        self._max_prices_items_per_batch = max(1, int(max_prices_items_per_batch))
        self._max_prices_items_per_rate_limited_batch = max(1, int(max_prices_items_per_rate_limited_batch))
        self._batch_pause_seconds = max(0.0, float(batch_pause_seconds))
        self._rate_limited_batch_pause_seconds = max(0.0, float(rate_limited_batch_pause_seconds))
        if max_price_batch_workers is None:
            max_price_batch_workers = 1 if fetch_json is not None else 4
        self._max_price_batch_workers = max(1, int(max_price_batch_workers))
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
        params = {
            "locations": ",".join(locations),
            "qualities": ",".join(str(x) for x in (qualities or [1])),
        }
        out: list[MarketPriceRecord] = []
        batches = self._split_price_batches(base=base, item_ids=item_ids, params=params)
        if len(batches) > 1 and self._max_price_batch_workers > 1:
            return self._fetch_price_batches_parallel(base=base, batches=batches, params=params)
        errors: list[RuntimeError] = []
        for batch_index, item_batch in enumerate(batches):
            if batch_index > 0 and self._batch_pause_seconds > 0:
                self._sleep(self._batch_pause_seconds)
            try:
                out.extend(self._fetch_prices_batch(base=base, item_ids=item_batch, params=params))
            except RuntimeError as exc:
                errors.append(exc)
                self._log.warning("AO Data prices batch failed; continuing with partial prices: %s", exc)
        if out or not errors:
            return out
        raise errors[0]

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

    def _fetch_with_retry(
        self,
        *,
        url: str,
        endpoint: str,
        max_retries: int | None = None,
        retry_rate_limits: bool = True,
    ) -> object:
        max_attempts = (self._max_retries if max_retries is None else max(0, int(max_retries))) + 1
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
                if _is_too_many_requests_error(exc) and not retry_rate_limits:
                    break
                if attempt >= max_attempts:
                    break
                sleep_seconds = backoff_seconds
                if _is_too_many_requests_error(exc):
                    retry_after_seconds = _retry_after_seconds(exc)
                    if retry_after_seconds is not None:
                        sleep_seconds = max(sleep_seconds, retry_after_seconds)
                    else:
                        sleep_seconds = max(
                            sleep_seconds,
                            min(self._retry_backoff_max_seconds, 3.0 * attempt),
                        )
                if sleep_seconds > 0:
                    self._sleep(sleep_seconds)
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
            attempts=attempt,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
            success=False,
            error=error_message,
        )
        raise RuntimeError(f"AO Data {endpoint} request failed after {attempt} attempts: {error_message}")

    def _split_price_batches(
        self,
        *,
        base: str,
        item_ids: list[str],
        params: dict[str, str],
    ) -> list[list[str]]:
        batches: list[list[str]] = []
        current: list[str] = []
        for item_id in item_ids:
            candidate = current + [item_id]
            exceeds_item_limit = len(candidate) > self._max_prices_items_per_batch
            exceeds_url_limit = len(current) > 0 and len(self._build_prices_url(base=base, item_ids=candidate, params=params)) > self._max_prices_url_length
            if len(current) > 0 and (exceeds_item_limit or exceeds_url_limit):
                batches.append(current)
                current = [item_id]
            else:
                current = candidate
        if current:
            batches.append(current)
        return batches

    def _fetch_prices_batch(
        self,
        *,
        base: str,
        item_ids: list[str],
        params: dict[str, str],
    ) -> list[MarketPriceRecord]:
        url = self._build_prices_url(base=base, item_ids=item_ids, params=params)
        try:
            data = self._fetch_with_retry(
                url=url,
                endpoint="prices",
                max_retries=self._max_price_retries,
                retry_rate_limits=False,
            )
            return _normalize_prices(data)
        except RuntimeError as exc:
            if len(item_ids) <= 1:
                raise
            if _is_uri_too_large_error(exc):
                self._log.warning(
                    "AO Data prices batch URL too large, splitting batch of %d items.",
                    len(item_ids),
                )
                midpoint = max(1, len(item_ids) // 2)
                left = self._fetch_prices_batch(base=base, item_ids=item_ids[:midpoint], params=params)
                right = self._fetch_prices_batch(base=base, item_ids=item_ids[midpoint:], params=params)
                return left + right
            if _is_too_many_requests_error(exc) and len(item_ids) > self._max_prices_items_per_rate_limited_batch:
                self._log.warning(
                    "AO Data prices batch rate-limited (429), splitting batch of %d items.",
                    len(item_ids),
                )
                out: list[MarketPriceRecord] = []
                for chunk_index, chunk in enumerate(
                    self._split_rate_limited_price_batches(item_ids=item_ids)
                ):
                    if chunk_index > 0 and self._rate_limited_batch_pause_seconds > 0:
                        self._sleep(self._rate_limited_batch_pause_seconds)
                    out.extend(self._fetch_prices_batch(base=base, item_ids=chunk, params=params))
                return out
            raise

    def _fetch_price_batches_parallel(
        self,
        *,
        base: str,
        batches: list[list[str]],
        params: dict[str, str],
    ) -> list[MarketPriceRecord]:
        results: list[list[MarketPriceRecord]] = [[] for _ in batches]
        errors: list[RuntimeError] = []
        worker_count = min(self._max_price_batch_workers, len(batches))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_by_index = {
                executor.submit(self._fetch_prices_batch, base=base, item_ids=batch, params=params): idx
                for idx, batch in enumerate(batches)
            }
            for future, idx in future_by_index.items():
                try:
                    results[idx] = future.result()
                except RuntimeError as exc:
                    errors.append(exc)
                    self._log.warning("AO Data prices batch failed; continuing with partial prices: %s", exc)
        out = [row for batch_rows in results for row in batch_rows]
        if out or not errors:
            return out
        raise errors[0]

    def _split_rate_limited_price_batches(self, *, item_ids: list[str]) -> list[list[str]]:
        chunk_size = self._max_prices_items_per_rate_limited_batch
        return [item_ids[index : index + chunk_size] for index in range(0, len(item_ids), chunk_size)]

    @staticmethod
    def _build_prices_url(*, base: str, item_ids: list[str], params: dict[str, str]) -> str:
        ids = ",".join(item_ids)
        return f"{base}/api/v2/stats/prices/{ids}.json?{urlencode(params)}"


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
    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip",
        },
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        payload_raw = response.read()
        if str(response.headers.get("Content-Encoding") or "").lower() == "gzip":
            payload_raw = gzip.decompress(payload_raw)
        payload = payload_raw.decode("utf-8")
    return json.loads(payload)


def _is_uri_too_large_error(exc: Exception) -> bool:
    message = str(exc).lower()
    code = getattr(exc, "code", None)
    if code == 414:
        return True
    return "414" in message or "request-uri too large" in message or "uri too large" in message


def _is_too_many_requests_error(exc: Exception) -> bool:
    message = str(exc).lower()
    code = getattr(exc, "code", None)
    if code == 429:
        return True
    return "429" in message or "too many requests" in message


def _retry_after_seconds(exc: Exception) -> float | None:
    if not isinstance(exc, HTTPError):
        return None
    retry_after = exc.headers.get("Retry-After")
    if not retry_after:
        return None
    try:
        parsed = float(retry_after)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    # clamp to a sane upper bound to avoid excessive stalls from bad headers
    return min(parsed, 60.0)


