from __future__ import annotations

from dataclasses import dataclass

from albion_dps.market.models import PriceType


@dataclass(frozen=True)
class _JournalRule:
    kind: str
    tier: int
    empty_item_id: str
    full_item_id: str
    max_fame: float
    fame_per_item: float


@dataclass(frozen=True)
class _JournalTotals:
    input_cost: float = 0.0
    output_value: float = 0.0
    market_tax: float = 0.0
    full_quantity: float = 0.0
    lines: tuple["_JournalLine", ...] = ()

    @property
    def net_profit(self) -> float:
        return float(self.output_value - self.input_cost - self.market_tax)


@dataclass(frozen=True)
class _JournalLine:
    kind: str
    tier: int
    empty_item_id: str
    full_item_id: str
    empty_quantity: float
    full_quantity: float
    input_cost: float
    output_value: float
    market_tax: float
    input_price_mode: str = PriceType.SELL_ORDER.value
    output_price_mode: str = PriceType.SELL_ORDER.value
    empty_price_item_id: str = ""
    full_price_item_id: str = ""

    @property
    def net_profit(self) -> float:
        return float(self.output_value - self.input_cost - self.market_tax)


__all__ = ["_JournalLine", "_JournalRule", "_JournalTotals"]
