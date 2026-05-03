from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Sequence

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.models import PriceType
from albion_dps.qt.market.list_models import InputPreviewRow

_TIER_PREFIX_RE = re.compile(r"^T(?P<tier>\d+)_(?P<rest>.+)$", re.IGNORECASE)
_LEVEL_SUFFIX_RE = re.compile(r"_LEVEL\d+$", re.IGNORECASE)


def base_item_id(item_id: str) -> str:
    value = str(item_id or "").strip().upper()
    if not value:
        return ""
    if "@" in value:
        value = value.rsplit("@", 1)[0]
    value = _LEVEL_SUFFIX_RE.sub("", value)
    return value


def tier_from_item_id(item_id: str) -> int:
    match = _TIER_PREFIX_RE.match(base_item_id(item_id))
    if match is None:
        return 0
    try:
        return int(match.group("tier"))
    except (TypeError, ValueError):
        return 0


def input_group_rank(item_id: str) -> int:
    base_id = base_item_id(item_id)
    if "_JOURNAL_" in base_id:
        return 2
    if (
        "_ARTEFACT_" in base_id
        or "_TOKEN_" in base_id
        or "_RELIC_" in base_id
        or "_SOUL_" in base_id
        or "_RUNE_" in base_id
    ):
        return 0
    return 1


def input_preview_sort_key(row: InputPreviewRow, *, item_family_key) -> tuple[int, int, str, str, str]:
    item_id = str(row.item_id or "")
    return (
        input_group_rank(item_id),
        tier_from_item_id(item_id),
        item_family_key(item_id),
        str(row.item or "").lower(),
        str(row.city or "").lower(),
    )


def mode_has_price(quote: MarketPriceRecord, preferred_mode: str | None) -> bool:
    mode = str(preferred_mode or "").strip().lower()
    if mode == PriceType.BUY_ORDER.value:
        return int(quote.buy_price_max or 0) > 0
    if mode == PriceType.SELL_ORDER.value:
        return int(quote.sell_price_min or 0) > 0
    if mode == PriceType.MANUAL.value:
        return True
    return int(quote.buy_price_max or 0) > 0 or int(quote.sell_price_min or 0) > 0


def find_price_quote(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
    preferred_mode: str | None,
    item_id_candidates,
) -> MarketPriceRecord | None:
    candidates = item_id_candidates(item_id)
    if not candidates:
        return None
    fallback: MarketPriceRecord | None = None
    quality_candidates = [int(quality)]
    if int(quality) != 1:
        quality_candidates.append(1)
    for candidate_id in candidates:
        for candidate_quality in quality_candidates:
            quote = price_index.get((candidate_id, city, candidate_quality))
            if quote is None:
                continue
            if mode_has_price(quote, preferred_mode):
                return quote
            if fallback is None:
                fallback = quote
    for (candidate_id, candidate_city, _candidate_quality), quote in price_index.items():
        if candidate_city != city or candidate_id not in candidates:
            continue
        if mode_has_price(quote, preferred_mode):
            return quote
        if fallback is None:
            fallback = quote
    return fallback


def parse_iso_datetime(raw_value: str) -> datetime | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.year <= 2001:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def result_row_profit_and_margin(*, allocated_cost: float, net_value: float) -> tuple[float, float]:
    normalized_cost = max(0.0, float(allocated_cost))
    normalized_net = float(net_value)
    profit = normalized_net - normalized_cost
    margin = (profit / normalized_cost * 100.0) if normalized_cost > 0 else 0.0
    return float(profit), float(margin)


def format_age(updated_at: datetime) -> str:
    now = datetime.now(timezone.utc)
    seconds = max(0, int((now - updated_at).total_seconds()))
    if seconds < 60:
        return "<1m"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    if hours < 24:
        rem_minutes = minutes % 60
        if rem_minutes == 0:
            return f"{hours}h"
        return f"{hours}h {rem_minutes}m"
    days = hours // 24
    rem_hours = hours % 24
    if rem_hours == 0:
        return f"{days}d"
    return f"{days}d {rem_hours}h"


def need_quantity_with_safety_buffer(quantity_raw: float, is_returnable: bool) -> int:
    base = max(0.0, float(quantity_raw))
    return int(math.ceil(base))


def minimal_upfront_quantity_for_batches(batches: Sequence[tuple[float, float]]) -> float:
    if not batches:
        return 0.0
    required = 0.0
    gross_so_far = 0.0
    returned_so_far = 0.0
    for gross_quantity, return_fraction in batches:
        gross = max(0.0, float(gross_quantity))
        fraction = max(0.0, min(1.0, float(return_fraction)))
        gross_so_far += gross
        required = max(required, gross_so_far - returned_so_far)
        returned_so_far += float(max(0, int(math.floor(gross * fraction))))
    return float(required)


def upfront_return_safety_units(batches: Sequence[tuple[float, float]]) -> int:
    # The per-craft floor in minimal_upfront_quantity_for_batches already keeps
    # the shopping quantity conservative without adding arbitrary extra units.
    _ = batches
    return 0


def input_preview_row_key(item_id: str, city: str, price_type: str) -> str:
    return f"{item_id}|{city}|{price_type}"


def normalize_int_values(
    values: Sequence[object] | None,
    *,
    minimum: int,
    maximum: int,
) -> list[int]:
    normalized: set[int] = set()
    for raw in values or ():
        candidate: object = raw
        to_variant = getattr(candidate, "toVariant", None)
        if callable(to_variant):
            try:
                candidate = to_variant()
            except Exception:
                continue
        if isinstance(candidate, bool):
            continue
        parsed: int
        if isinstance(candidate, int):
            parsed = candidate
        elif isinstance(candidate, float):
            parsed = int(candidate)
        elif isinstance(candidate, str):
            text = candidate.strip()
            if not text:
                continue
            try:
                parsed = int(text)
            except ValueError:
                continue
        else:
            continue
        if minimum <= parsed <= maximum:
            normalized.add(parsed)
    return sorted(normalized)
