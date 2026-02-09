from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MarketRegion(str, Enum):
    EUROPE = "europe"
    WEST = "west"
    EAST = "east"


class PriceType(str, Enum):
    BUY_ORDER = "buy_order"
    SELL_ORDER = "sell_order"
    AVERAGE = "average"
    MANUAL = "manual"


@dataclass(frozen=True)
class ItemRef:
    unique_name: str
    display_name: str = ""
    tier: int | None = None
    enchantment: int | None = None


@dataclass(frozen=True)
class RecipeComponent:
    item: ItemRef
    quantity: float


@dataclass(frozen=True)
class RecipeOutput:
    item: ItemRef
    quantity: float


@dataclass(frozen=True)
class Recipe:
    item: ItemRef
    station: str
    city_bonus: str = ""
    components: tuple[RecipeComponent, ...] = ()
    outputs: tuple[RecipeOutput, ...] = ()
    focus_per_craft: int = 0


@dataclass(frozen=True)
class CraftSetup:
    region: MarketRegion = MarketRegion.EUROPE
    craft_city: str = ""
    default_buy_city: str = ""
    default_sell_city: str = ""
    premium: bool = True
    station_fee_percent: float = 0.0
    market_tax_percent: float = 0.0
    daily_bonus_percent: float = 0.0
    return_rate_percent: float = 0.0
    hideout_power_percent: float = 0.0
    quality: int = 1


@dataclass(frozen=True)
class InputLine:
    item: ItemRef
    quantity: float
    city: str
    price_type: PriceType
    unit_price: float

    @property
    def total_cost(self) -> float:
        return self.quantity * self.unit_price


@dataclass(frozen=True)
class OutputLine:
    item: ItemRef
    quantity: float
    city: str
    price_type: PriceType
    unit_price: float

    @property
    def total_value(self) -> float:
        return self.quantity * self.unit_price


@dataclass(frozen=True)
class CraftRun:
    recipe: Recipe
    quantity: int
    setup: CraftSetup
    inputs: tuple[InputLine, ...] = ()
    outputs: tuple[OutputLine, ...] = ()


@dataclass
class ProfitBreakdown:
    input_cost: float = 0.0
    output_value: float = 0.0
    station_fee: float = 0.0
    market_tax: float = 0.0
    focus_used: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def net_profit(self) -> float:
        return self.output_value - self.input_cost - self.station_fee - self.market_tax

    @property
    def margin_percent(self) -> float:
        if self.input_cost <= 0:
            return 0.0
        return (self.net_profit / self.input_cost) * 100.0
