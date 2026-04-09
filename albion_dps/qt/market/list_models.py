from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Sequence

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from albion_dps.market.models import PriceType

_RECIPE_SEARCH_TOKEN_ALIASES: dict[str, str] = {
    "siedge": "siege",
}
_RECIPE_TIER_ENCHANT_RE = re.compile(r"\b(?:t)?(?P<tier>[1-8])(?:[.\-\/](?P<ench>[0-4]))?\b", re.IGNORECASE)


@dataclass(frozen=True)
class InputPreviewRow:
    item_id: str
    row_key: str
    item: str
    quantity: float
    stock_quantity: float
    buy_quantity: float
    city: str
    price_type: str
    price_age_text: str
    manual_price: int
    unit_price: float
    total_cost: float
    completed: bool = False


class MarketInputsModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    PriceAgeRole = Qt.UserRole + 6
    ManualPriceRole = Qt.UserRole + 7
    UnitPriceRole = Qt.UserRole + 8
    TotalCostRole = Qt.UserRole + 9
    StockQuantityRole = Qt.UserRole + 10
    BuyQuantityRole = Qt.UserRole + 11
    RowKeyRole = Qt.UserRole + 12
    CompletedRole = Qt.UserRole + 13

    def __init__(self) -> None:
        super().__init__()
        self._items: list[InputPreviewRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.RowKeyRole:
            return item.row_key
        if role == self.ItemRole:
            return item.item
        if role == self.QuantityRole:
            return item.quantity
        if role == self.StockQuantityRole:
            return item.stock_quantity
        if role == self.BuyQuantityRole:
            return item.buy_quantity
        if role == self.CityRole:
            return item.city
        if role == self.PriceTypeRole:
            return item.price_type
        if role == self.PriceAgeRole:
            return item.price_age_text
        if role == self.ManualPriceRole:
            return item.manual_price
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.TotalCostRole:
            return item.total_cost
        if role == self.CompletedRole:
            return item.completed
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.RowKeyRole: b"rowKey",
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.PriceAgeRole: b"priceAgeText",
            self.ManualPriceRole: b"manualPrice",
            self.UnitPriceRole: b"unitPrice",
            self.TotalCostRole: b"totalCost",
            self.StockQuantityRole: b"stockQuantity",
            self.BuyQuantityRole: b"buyQuantity",
            self.CompletedRole: b"completed",
        }

    def set_items(self, rows: list[InputPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()

    def set_completed_by_item_id(self, item_id: str, completed: bool) -> None:
        if not item_id:
            return
        changed_rows: list[int] = []
        new_items = list(self._items)
        for idx, row in enumerate(new_items):
            if row.item_id != item_id or bool(row.completed) == bool(completed):
                continue
            new_items[idx] = InputPreviewRow(
                item_id=row.item_id,
                row_key=row.row_key,
                item=row.item,
                quantity=row.quantity,
                stock_quantity=row.stock_quantity,
                buy_quantity=row.buy_quantity,
                city=row.city,
                price_type=row.price_type,
                price_age_text=row.price_age_text,
                manual_price=row.manual_price,
                unit_price=row.unit_price,
                total_cost=row.total_cost,
                completed=bool(completed),
            )
            changed_rows.append(idx)
        if not changed_rows:
            return
        self._items = new_items
        for row_idx in changed_rows:
            model_index = self.index(row_idx, 0)
            self.dataChanged.emit(model_index, model_index, [self.CompletedRole])


@dataclass(frozen=True)
class OutputPreviewRow:
    item_id: str
    item: str
    quantity: float
    city: str
    price_type: str
    price_age_text: str
    manual_price: int
    unit_price: float
    total_value: float
    fee_value: float
    tax_value: float
    net_value: float
    completed: bool = False


class MarketOutputsModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    PriceAgeRole = Qt.UserRole + 6
    ManualPriceRole = Qt.UserRole + 7
    UnitPriceRole = Qt.UserRole + 8
    TotalValueRole = Qt.UserRole + 9
    FeeValueRole = Qt.UserRole + 10
    TaxValueRole = Qt.UserRole + 11
    NetValueRole = Qt.UserRole + 12
    CompletedRole = Qt.UserRole + 13

    def __init__(self) -> None:
        super().__init__()
        self._items: list[OutputPreviewRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.QuantityRole:
            return item.quantity
        if role == self.CityRole:
            return item.city
        if role == self.PriceTypeRole:
            return item.price_type
        if role == self.PriceAgeRole:
            return item.price_age_text
        if role == self.ManualPriceRole:
            return item.manual_price
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.TotalValueRole:
            return item.total_value
        if role == self.FeeValueRole:
            return item.fee_value
        if role == self.TaxValueRole:
            return item.tax_value
        if role == self.NetValueRole:
            return item.net_value
        if role == self.CompletedRole:
            return item.completed
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.PriceAgeRole: b"priceAgeText",
            self.ManualPriceRole: b"manualPrice",
            self.UnitPriceRole: b"unitPrice",
            self.TotalValueRole: b"totalValue",
            self.FeeValueRole: b"feeValue",
            self.TaxValueRole: b"taxValue",
            self.NetValueRole: b"netValue",
            self.CompletedRole: b"completed",
        }

    def set_items(self, rows: list[OutputPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()

    def set_completed_by_item_id(self, item_id: str, completed: bool) -> None:
        if not item_id:
            return
        changed_rows: list[int] = []
        new_items = list(self._items)
        for idx, row in enumerate(new_items):
            if row.item_id != item_id or bool(row.completed) == bool(completed):
                continue
            new_items[idx] = OutputPreviewRow(
                item_id=row.item_id,
                item=row.item,
                quantity=row.quantity,
                city=row.city,
                price_type=row.price_type,
                price_age_text=row.price_age_text,
                manual_price=row.manual_price,
                unit_price=row.unit_price,
                total_value=row.total_value,
                fee_value=row.fee_value,
                tax_value=row.tax_value,
                net_value=row.net_value,
                completed=bool(completed),
            )
            changed_rows.append(idx)
        if not changed_rows:
            return
        self._items = new_items
        for row_idx in changed_rows:
            model_index = self.index(row_idx, 0)
            self.dataChanged.emit(model_index, model_index, [self.CompletedRole])


@dataclass(frozen=True)
class ShoppingPreviewRow:
    item_id: str
    item: str
    quantity: float
    city: str
    price_type: str
    unit_price: float
    total_cost: float


class MarketShoppingModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    UnitPriceRole = Qt.UserRole + 6
    TotalCostRole = Qt.UserRole + 7

    def __init__(self) -> None:
        super().__init__()
        self._items: list[ShoppingPreviewRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.QuantityRole:
            return item.quantity
        if role == self.CityRole:
            return item.city
        if role == self.PriceTypeRole:
            return item.price_type
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.TotalCostRole:
            return item.total_cost
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.UnitPriceRole: b"unitPrice",
            self.TotalCostRole: b"totalCost",
        }

    def set_items(self, rows: list[ShoppingPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class SellingPreviewRow:
    item_id: str
    item: str
    quantity: float
    city: str
    price_type: str
    unit_price: float
    total_value: float


class MarketSellingModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    QuantityRole = Qt.UserRole + 3
    CityRole = Qt.UserRole + 4
    PriceTypeRole = Qt.UserRole + 5
    UnitPriceRole = Qt.UserRole + 6
    TotalValueRole = Qt.UserRole + 7

    def __init__(self) -> None:
        super().__init__()
        self._items: list[SellingPreviewRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.QuantityRole:
            return item.quantity
        if role == self.CityRole:
            return item.city
        if role == self.PriceTypeRole:
            return item.price_type
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.TotalValueRole:
            return item.total_value
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.QuantityRole: b"quantity",
            self.CityRole: b"city",
            self.PriceTypeRole: b"priceType",
            self.UnitPriceRole: b"unitPrice",
            self.TotalValueRole: b"totalValue",
        }

    def set_items(self, rows: list[SellingPreviewRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class ResultItemRow:
    item_id: str
    item: str
    city: str
    quantity: float
    unit_price: float
    revenue: float
    allocated_cost: float
    fee_value: float
    tax_value: float
    profit: float
    margin_percent: float
    demand_proxy: float


class MarketResultsItemsModel(QAbstractListModel):
    ItemIdRole = Qt.UserRole + 1
    ItemRole = Qt.UserRole + 2
    CityRole = Qt.UserRole + 3
    QuantityRole = Qt.UserRole + 4
    UnitPriceRole = Qt.UserRole + 5
    RevenueRole = Qt.UserRole + 6
    CostRole = Qt.UserRole + 7
    FeeRole = Qt.UserRole + 8
    TaxRole = Qt.UserRole + 9
    ProfitRole = Qt.UserRole + 10
    MarginRole = Qt.UserRole + 11
    DemandRole = Qt.UserRole + 12

    def __init__(self) -> None:
        super().__init__()
        self._items: list[ResultItemRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.ItemIdRole:
            return item.item_id
        if role == self.ItemRole:
            return item.item
        if role == self.CityRole:
            return item.city
        if role == self.QuantityRole:
            return item.quantity
        if role == self.UnitPriceRole:
            return item.unit_price
        if role == self.RevenueRole:
            return item.revenue
        if role == self.CostRole:
            return item.allocated_cost
        if role == self.FeeRole:
            return item.fee_value
        if role == self.TaxRole:
            return item.tax_value
        if role == self.ProfitRole:
            return item.profit
        if role == self.MarginRole:
            return item.margin_percent
        if role == self.DemandRole:
            return item.demand_proxy
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.ItemIdRole: b"itemId",
            self.ItemRole: b"item",
            self.CityRole: b"city",
            self.QuantityRole: b"quantity",
            self.UnitPriceRole: b"unitPrice",
            self.RevenueRole: b"revenue",
            self.CostRole: b"cost",
            self.FeeRole: b"feeValue",
            self.TaxRole: b"taxValue",
            self.ProfitRole: b"profit",
            self.MarginRole: b"marginPercent",
            self.DemandRole: b"demandProxy",
        }

    def set_items(self, rows: list[ResultItemRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class BreakdownRow:
    label: str
    value: float


class MarketBreakdownModel(QAbstractListModel):
    LabelRole = Qt.UserRole + 1
    ValueRole = Qt.UserRole + 2

    def __init__(self) -> None:
        super().__init__()
        self._items: list[BreakdownRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.LabelRole:
            return item.label
        if role == self.ValueRole:
            return item.value
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.LabelRole: b"label",
            self.ValueRole: b"value",
        }

    def set_items(self, rows: list[BreakdownRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()


@dataclass(frozen=True)
class RecipeOptionRow:
    recipe_id: str
    display_name: str
    tier: int
    enchant: int
    variant_label: str = ""
    uses_crystallized: bool = False


@dataclass(frozen=True)
class RecipeFilter:
    terms: tuple[str, ...]
    tier: int | None
    enchant: int | None


class RecipeOptionsModel(QAbstractListModel):
    RecipeIdRole = Qt.UserRole + 1
    DisplayNameRole = Qt.UserRole + 2
    TierRole = Qt.UserRole + 3
    EnchantRole = Qt.UserRole + 4
    VariantLabelRole = Qt.UserRole + 5
    UsesCrystallizedRole = Qt.UserRole + 6

    def __init__(self) -> None:
        super().__init__()
        self._all_items: list[RecipeOptionRow] = []
        self._items: list[RecipeOptionRow] = []
        self._filter = RecipeFilter(terms=(), tier=None, enchant=None)
        self._tier_filters: tuple[int, ...] = ()
        self._enchant_filters: tuple[int, ...] = ()

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.RecipeIdRole:
            return item.recipe_id
        if role == self.DisplayNameRole:
            return item.display_name
        if role == self.TierRole:
            return item.tier
        if role == self.EnchantRole:
            return item.enchant
        if role == self.VariantLabelRole:
            return item.variant_label
        if role == self.UsesCrystallizedRole:
            return bool(item.uses_crystallized)
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.RecipeIdRole: b"recipeId",
            self.DisplayNameRole: b"displayName",
            self.TierRole: b"tier",
            self.EnchantRole: b"enchant",
            self.VariantLabelRole: b"variantLabel",
            self.UsesCrystallizedRole: b"usesCrystallized",
        }

    def set_items(self, rows: list[RecipeOptionRow]) -> None:
        self._all_items = list(rows)
        self._apply_filter()

    def set_query(self, query: str) -> None:
        self._filter = _parse_recipe_filter(query)
        self._apply_filter()

    def set_tier_filters(self, tiers: Sequence[int] | None) -> None:
        normalized = tuple(_normalize_int_values(tiers, minimum=1, maximum=8))
        if normalized == self._tier_filters:
            return
        self._tier_filters = normalized
        self._apply_filter()

    def set_enchant_filters(self, enchants: Sequence[int] | None) -> None:
        normalized = tuple(_normalize_int_values(enchants, minimum=0, maximum=4))
        if normalized == self._enchant_filters:
            return
        self._enchant_filters = normalized
        self._apply_filter()

    def set_enchant_filter(self, enchant: int | None) -> None:
        if enchant is None:
            self.set_enchant_filters(())
            return
        parsed = int(enchant)
        if parsed < 0:
            self.set_enchant_filters(())
            return
        self.set_enchant_filters((parsed,))

    def _apply_filter(self) -> None:
        rows = self._all_items
        if self._filter.terms or self._filter.tier is not None or self._filter.enchant is not None:
            rows = [row for row in rows if _matches_recipe_filter(row, self._filter)]
        if self._tier_filters:
            tiers = set(self._tier_filters)
            rows = [row for row in rows if int(row.tier) in tiers]
        if self._enchant_filters:
            enchants = set(self._enchant_filters)
            rows = [row for row in rows if int(row.enchant) in enchants]
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()

    def recipe_id_at(self, index: int) -> str | None:
        if index < 0 or index >= len(self._items):
            return None
        return self._items[index].recipe_id

    def index_of_recipe(self, recipe_id: str) -> int:
        for idx, item in enumerate(self._items):
            if item.recipe_id == recipe_id:
                return idx
        return -1

    def recipe_ids(self) -> list[str]:
        return [item.recipe_id for item in self._items]


@dataclass(frozen=True)
class CraftPlanRow:
    row_id: int
    recipe_id: str
    display_name: str
    tier: int
    enchant: int
    variant_label: str
    uses_crystallized: bool
    craft_city: str
    daily_bonus_percent: float
    return_rate_percent: float | None
    runs: int
    enabled: bool
    profit_percent: float | None = None
    has_fresh_component_prices: bool = True


class CraftPlanModel(QAbstractListModel):
    RowIdRole = Qt.UserRole + 1
    RecipeIdRole = Qt.UserRole + 2
    DisplayNameRole = Qt.UserRole + 3
    TierRole = Qt.UserRole + 4
    EnchantRole = Qt.UserRole + 5
    CraftCityRole = Qt.UserRole + 6
    DailyBonusRole = Qt.UserRole + 7
    ReturnRateRole = Qt.UserRole + 8
    RunsRole = Qt.UserRole + 9
    EnabledRole = Qt.UserRole + 10
    ProfitPercentRole = Qt.UserRole + 11
    HasFreshComponentPricesRole = Qt.UserRole + 12
    VariantLabelRole = Qt.UserRole + 13
    UsesCrystallizedRole = Qt.UserRole + 14

    def __init__(self) -> None:
        super().__init__()
        self._items: list[CraftPlanRow] = []

    def rowCount(self, _parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._items):
            return None
        item = self._items[row]
        if role == self.RowIdRole:
            return item.row_id
        if role == self.RecipeIdRole:
            return item.recipe_id
        if role == self.DisplayNameRole:
            return item.display_name
        if role == self.TierRole:
            return item.tier
        if role == self.EnchantRole:
            return item.enchant
        if role == self.CraftCityRole:
            return item.craft_city
        if role == self.DailyBonusRole:
            return item.daily_bonus_percent
        if role == self.ReturnRateRole:
            return item.return_rate_percent
        if role == self.RunsRole:
            return item.runs
        if role == self.EnabledRole:
            return item.enabled
        if role == self.ProfitPercentRole:
            return item.profit_percent
        if role == self.HasFreshComponentPricesRole:
            return bool(item.has_fresh_component_prices)
        if role == self.VariantLabelRole:
            return item.variant_label
        if role == self.UsesCrystallizedRole:
            return bool(item.uses_crystallized)
        return None

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        return {
            self.RowIdRole: b"rowId",
            self.RecipeIdRole: b"recipeId",
            self.DisplayNameRole: b"displayName",
            self.TierRole: b"tier",
            self.EnchantRole: b"enchant",
            self.CraftCityRole: b"craftCity",
            self.DailyBonusRole: b"dailyBonusPercent",
            self.ReturnRateRole: b"returnRatePercent",
            self.RunsRole: b"runs",
            self.EnabledRole: b"isEnabled",
            self.ProfitPercentRole: b"profitPercent",
            self.HasFreshComponentPricesRole: b"hasFreshComponentPrices",
            self.VariantLabelRole: b"variantLabel",
            self.UsesCrystallizedRole: b"usesCrystallized",
        }

    def set_items(self, rows: list[CraftPlanRow]) -> None:
        self.beginResetModel()
        self._items = list(rows)
        self.endResetModel()

    def set_items_in_place(self, rows: list[CraftPlanRow]) -> None:
        incoming = list(rows)
        if len(incoming) != len(self._items):
            self.set_items(incoming)
            return
        for idx, current in enumerate(self._items):
            if int(current.row_id) != int(incoming[idx].row_id):
                self.set_items(incoming)
                return
        changed_indexes = [idx for idx, current in enumerate(self._items) if incoming[idx] != current]
        if not changed_indexes:
            return
        self._items = incoming
        first = min(changed_indexes)
        last = max(changed_indexes)
        self.dataChanged.emit(self.index(first, 0), self.index(last, 0), [])


def _normalize_recipe_search_token(token: str) -> str:
    normalized = token.strip().lower()
    if not normalized:
        return ""
    return _RECIPE_SEARCH_TOKEN_ALIASES.get(normalized, normalized)


def _parse_recipe_filter(query: str) -> RecipeFilter:
    text = query.strip().lower()
    if not text:
        return RecipeFilter(terms=(), tier=None, enchant=None)

    tier: int | None = None
    enchant: int | None = None
    remainder = text
    match = _RECIPE_TIER_ENCHANT_RE.search(text)
    if match is not None:
        tier = int(match.group("tier"))
        enchant_raw = match.group("ench")
        enchant = int(enchant_raw) if enchant_raw is not None else None
        start, end = match.span()
        remainder = (text[:start] + " " + text[end:]).strip()

    clean = "".join(ch if ch.isalnum() else " " for ch in remainder)
    terms = tuple(_normalize_recipe_search_token(part) for part in clean.split() if _normalize_recipe_search_token(part))
    return RecipeFilter(terms=terms, tier=tier, enchant=enchant)


def _normalize_int_values(
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


def _matches_recipe_filter(row: RecipeOptionRow, recipe_filter: RecipeFilter) -> bool:
    if recipe_filter.tier is not None and int(row.tier or 0) != int(recipe_filter.tier):
        return False
    if recipe_filter.enchant is not None and int(row.enchant or 0) != int(recipe_filter.enchant):
        return False
    if not recipe_filter.terms:
        return True
    haystack = f"{row.display_name} {row.recipe_id}".lower()
    return all(term in haystack for term in recipe_filter.terms)


__all__ = [
    "BreakdownRow",
    "CraftPlanModel",
    "CraftPlanRow",
    "InputPreviewRow",
    "MarketBreakdownModel",
    "MarketInputsModel",
    "MarketOutputsModel",
    "MarketResultsItemsModel",
    "MarketSellingModel",
    "MarketShoppingModel",
    "OutputPreviewRow",
    "RecipeFilter",
    "RecipeOptionRow",
    "RecipeOptionsModel",
    "ResultItemRow",
    "SellingPreviewRow",
    "ShoppingPreviewRow",
]
