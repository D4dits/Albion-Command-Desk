from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.models import ItemRef


BLACK_MARKET_CITY = "Black Market"
DEFAULT_SELL_FRESHNESS_MINUTES = 180
DEFAULT_BUY_FRESHNESS_MINUTES = 60
FLIP_QUALITIES = (1, 2, 3, 4, 5)


@dataclass(frozen=True)
class FlipCandidate:
    item: ItemRef
    recipe_id: str


@dataclass(frozen=True)
class FlipOpportunity:
    item_id: str
    item_name: str
    tier: int
    enchant: int
    quality: int
    source_city: str
    target_city: str
    source_sell_price: int
    target_buy_price: int
    source_age_text: str
    target_age_text: str
    tax_value: float
    buffer_value: float
    net_profit: float
    roi_percent: float
    valid: bool
    stale_reason: str


def collect_flip_candidates(catalog: RecipeCatalog) -> list[FlipCandidate]:
    candidates: dict[str, FlipCandidate] = {}
    for recipe_id in catalog.items():
        recipe = catalog.get(recipe_id)
        if recipe is None:
            continue
        for output in recipe.outputs:
            item = output.item
            item_id = str(item.unique_name or "").strip()
            if not item_id or item_id in candidates:
                continue
            if not _looks_like_tradeable_gear(item_id):
                continue
            candidates[item_id] = FlipCandidate(item=item, recipe_id=recipe_id)
    return sorted(
        candidates.values(),
        key=lambda row: (
            int(row.item.tier or 0),
            int(row.item.enchantment or 0),
            str(row.item.display_name or row.item.unique_name).lower(),
            str(row.item.unique_name),
        ),
    )


def build_flip_opportunities(
    *,
    candidates: Iterable[FlipCandidate],
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    source_city: str,
    quality: int,
    sale_tax_percent: float,
    risk_buffer_percent: float,
    min_profit: float,
    min_roi_percent: float,
    sell_freshness_minutes: int = DEFAULT_SELL_FRESHNESS_MINUTES,
    buy_freshness_minutes: int = DEFAULT_BUY_FRESHNESS_MINUTES,
    item_id_candidates: Callable[[str], tuple[str, ...]] | None = None,
    now: datetime | None = None,
) -> list[FlipOpportunity]:
    now_utc = _normalize_now(now)
    source = str(source_city or "").strip()
    item_id_candidates = item_id_candidates or (lambda item_id: (item_id,))
    rows: list[FlipOpportunity] = []
    for candidate in candidates:
        item = candidate.item
        item_id = str(item.unique_name or "").strip()
        item_name = str(item.display_name or item_id)
        rows.append(
            _build_best_quality_opportunity(
                item_id=item_id,
                item_name=item_name,
                tier=int(item.tier or _tier_from_item_id(item_id)),
                enchant=int(item.enchantment or _enchant_from_item_id(item_id)),
                price_index=price_index,
                source_city=source,
                preferred_quality=int(quality),
                sale_tax_percent=sale_tax_percent,
                risk_buffer_percent=risk_buffer_percent,
                min_profit=min_profit,
                min_roi_percent=min_roi_percent,
                sell_freshness_minutes=sell_freshness_minutes,
                buy_freshness_minutes=buy_freshness_minutes,
                item_id_candidates=item_id_candidates,
                now_utc=now_utc,
            )
        )
    rows.sort(key=lambda row: (row.valid, row.net_profit, row.roi_percent), reverse=True)
    return rows


@dataclass(frozen=True)
class _Age:
    minutes: int | None
    text: str


def _build_best_quality_opportunity(
    *,
    item_id: str,
    item_name: str,
    tier: int,
    enchant: int,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    source_city: str,
    preferred_quality: int,
    sale_tax_percent: float,
    risk_buffer_percent: float,
    min_profit: float,
    min_roi_percent: float,
    sell_freshness_minutes: int,
    buy_freshness_minutes: int,
    item_id_candidates: Callable[[str], tuple[str, ...]],
    now_utc: datetime,
) -> FlipOpportunity:
    options = [
        _build_quality_opportunity(
            item_id=item_id,
            item_name=item_name,
            tier=tier,
            enchant=enchant,
            price_index=price_index,
            source_city=source_city,
            quality=quality,
            sale_tax_percent=sale_tax_percent,
            risk_buffer_percent=risk_buffer_percent,
            min_profit=min_profit,
            min_roi_percent=min_roi_percent,
            sell_freshness_minutes=sell_freshness_minutes,
            buy_freshness_minutes=buy_freshness_minutes,
            item_id_candidates=item_id_candidates,
            now_utc=now_utc,
        )
        for quality in _quality_order(preferred_quality)
    ]
    return max(
        options,
        key=lambda row: (
            row.valid,
            row.source_sell_price > 0 and row.target_buy_price > 0,
            row.source_sell_price > 0,
            row.target_buy_price > 0,
            row.net_profit,
        ),
    )


def _build_quality_opportunity(
    *,
    item_id: str,
    item_name: str,
    tier: int,
    enchant: int,
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    source_city: str,
    quality: int,
    sale_tax_percent: float,
    risk_buffer_percent: float,
    min_profit: float,
    min_roi_percent: float,
    sell_freshness_minutes: int,
    buy_freshness_minutes: int,
    item_id_candidates: Callable[[str], tuple[str, ...]],
    now_utc: datetime,
) -> FlipOpportunity:
    source_quote = _find_quote_with_price(
        price_index,
        item_id=item_id,
        city=source_city,
        quality=quality,
        price_type="sell",
        item_id_candidates=item_id_candidates,
    )
    target_quote = _find_best_black_market_buy_for_source_quality(
        price_index,
        item_id=item_id,
        source_quality=quality,
        item_id_candidates=item_id_candidates,
    )
    source_price = int(source_quote.sell_price_min if source_quote else 0)
    target_price = int(target_quote.buy_price_max if target_quote else 0)
    source_age = _price_age(source_quote.sell_price_min_date if source_quote else "", now_utc)
    target_age = _price_age(target_quote.buy_price_max_date if target_quote else "", now_utc)
    stale_reason = _stale_reason(
        source_price=source_price,
        target_price=target_price,
        source_age_minutes=source_age.minutes,
        target_age_minutes=target_age.minutes,
        sell_freshness_minutes=sell_freshness_minutes,
        buy_freshness_minutes=buy_freshness_minutes,
    )
    if source_price > 0 and target_price > 0:
        tax_value = target_price * max(0.0, float(sale_tax_percent)) / 100.0
        buffer_value = source_price * max(0.0, float(risk_buffer_percent)) / 100.0
        net_profit = float(target_price - source_price - tax_value - buffer_value)
        roi = (net_profit / source_price * 100.0) if source_price > 0 else 0.0
    else:
        tax_value = 0.0
        buffer_value = 0.0
        net_profit = 0.0
        roi = 0.0
    if not stale_reason:
        if net_profit < float(min_profit):
            stale_reason = "below min profit"
        elif roi < float(min_roi_percent):
            stale_reason = "below min ROI"
    return FlipOpportunity(
        item_id=item_id,
        item_name=item_name,
        tier=tier,
        enchant=enchant,
        quality=quality,
        source_city=source_city,
        target_city=BLACK_MARKET_CITY,
        source_sell_price=source_price,
        target_buy_price=target_price,
        source_age_text=source_age.text,
        target_age_text=target_age.text,
        tax_value=tax_value,
        buffer_value=buffer_value,
        net_profit=net_profit,
        roi_percent=roi,
        valid=not stale_reason,
        stale_reason=stale_reason,
    )


def _find_quote_with_price(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
    price_type: str,
    item_id_candidates: Callable[[str], tuple[str, ...]],
) -> MarketPriceRecord | None:
    for candidate_id in item_id_candidates(item_id):
        quote = price_index.get((candidate_id, city, int(quality)))
        if quote is None:
            continue
        if price_type == "sell" and int(quote.sell_price_min or 0) > 0:
            return quote
        if price_type == "buy" and int(quote.buy_price_max or 0) > 0:
            return quote
    return None


def _find_best_black_market_buy_for_source_quality(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    source_quality: int,
    item_id_candidates: Callable[[str], tuple[str, ...]],
) -> MarketPriceRecord | None:
    best: MarketPriceRecord | None = None
    for candidate_id in item_id_candidates(item_id):
        for candidate_quality in range(1, int(source_quality) + 1):
            quote = price_index.get((candidate_id, BLACK_MARKET_CITY, candidate_quality))
            if quote is None or int(quote.buy_price_max or 0) <= 0:
                continue
            if best is None or int(quote.buy_price_max or 0) > int(best.buy_price_max or 0):
                best = quote
    return best


def _quality_order(preferred_quality: int) -> tuple[int, ...]:
    preferred = max(1, min(5, int(preferred_quality or 1)))
    return (preferred,) + tuple(quality for quality in FLIP_QUALITIES if quality != preferred)


def _price_age(raw: str, now: datetime) -> _Age:
    parsed = _parse_datetime(raw)
    if parsed is None:
        return _Age(minutes=None, text="n/a")
    seconds = max(0, int((now - parsed).total_seconds()))
    minutes = seconds // 60
    if seconds < 60:
        return _Age(minutes=0, text="<1m")
    if minutes < 60:
        return _Age(minutes=minutes, text=f"{minutes}m")
    hours = minutes // 60
    if hours < 24:
        rem = minutes % 60
        return _Age(minutes=minutes, text=f"{hours}h {rem}m" if rem else f"{hours}h")
    days = hours // 24
    rem_h = hours % 24
    return _Age(minutes=minutes, text=f"{days}d {rem_h}h" if rem_h else f"{days}d")


def _parse_datetime(raw: str) -> datetime | None:
    text = str(raw or "").strip()
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
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_now(now: datetime | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def _stale_reason(
    *,
    source_price: int,
    target_price: int,
    source_age_minutes: int | None,
    target_age_minutes: int | None,
    sell_freshness_minutes: int,
    buy_freshness_minutes: int,
) -> str:
    if source_price <= 0:
        return "missing source sell"
    if target_price <= 0:
        return "missing Black Market buy"
    if source_age_minutes is None:
        return "missing source age"
    if target_age_minutes is None:
        return "missing Black Market age"
    if source_age_minutes > int(sell_freshness_minutes):
        return "stale source sell"
    if target_age_minutes > int(buy_freshness_minutes):
        return "stale Black Market buy"
    return ""


def _looks_like_tradeable_gear(item_id: str) -> bool:
    upper = item_id.upper()
    if not upper.startswith("T"):
        return False
    blocked = ("_JOURNAL_", "_TOKEN_", "_ARTEFACT_", "_RUNE", "_SOUL", "_RELIC")
    if any(part in upper for part in blocked):
        return False
    return any(
        part in upper
        for part in (
            "_MAIN_",
            "_2H_",
            "_OFF_",
            "_ARMOR_",
            "_HEAD_",
            "_SHOES_",
            "_BAG",
            "_CAPE",
            "_MOUNT_",
        )
    )


def _tier_from_item_id(item_id: str) -> int:
    text = str(item_id or "").upper()
    if len(text) < 2 or text[0] != "T":
        return 0
    digits = []
    for char in text[1:]:
        if not char.isdigit():
            break
        digits.append(char)
    return int("".join(digits) or 0)


def _enchant_from_item_id(item_id: str) -> int:
    text = str(item_id or "").upper()
    if "@" in text:
        try:
            return int(text.rsplit("@", 1)[1])
        except ValueError:
            return 0
    if "_LEVEL" in text:
        try:
            return int(text.rsplit("_LEVEL", 1)[1])
        except ValueError:
            return 0
    return 0
