from __future__ import annotations

import csv
import io
import json
import logging
import math
import time
from math import ceil
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlencode

from PySide6.QtCore import QObject, Property, Qt, QTimer, Signal, Slot

from albion_dps.market.aod_client import MarketPriceRecord, REGION_HOSTS
from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.engine import (
    build_craft_run,
    compute_batch_profit,
    compute_output_valuations,
    compute_run_profit,
    effective_return_fraction,
)
from albion_dps.market.models import (
    CraftRun,
    CraftSetup,
    InputLine,
    ItemRef,
    MarketRegion,
    PriceType,
    ProfitBreakdown,
    Recipe,
)
from albion_dps.market.planner import build_selling_entries, build_shopping_entries
from albion_dps.market.service import MarketDataService
from albion_dps.market.setup import sanitized_setup, validate_setup
from albion_dps.qt.market.list_models import (
    BreakdownRow,
    CraftPlanModel,
    CraftPlanRow,
    InputPreviewRow,
    MarketBreakdownModel,
    MarketInputsModel,
    MarketOutputsModel,
    MarketResultsItemsModel,
    MarketSellingModel,
    MarketShoppingModel,
    OutputPreviewRow,
    RecipeOptionRow,
    RecipeOptionsModel,
    ResultItemRow,
    SellingPreviewRow,
    ShoppingPreviewRow,
)
from albion_dps.qt.market import common_ops
from albion_dps.qt.market import catalog_ops
from albion_dps.qt.market import journal_ops
from albion_dps.qt.market import preset_ops
from albion_dps.qt.market import pricing_ops
from albion_dps.qt.market import price_refresh_ops
from albion_dps.qt.market import recipe_ops
from albion_dps.qt.market import selection_ops
from albion_dps.qt.market.preview_ops import (
    accumulate_input_preview_rows,
    build_breakdown_rows,
    build_results_rows_from_runs,
    compute_input_total_from_lines,
)
from albion_dps.qt.market.state_types import _JournalLine, _JournalRule, _JournalTotals
from albion_dps.settings import load_app_settings, update_app_settings


class MarketSetupState(QObject):
    setupChanged = Signal()
    validationChanged = Signal()
    pricesChanged = Signal()
    inputsChanged = Signal()
    outputsChanged = Signal()
    resultsChanged = Signal()
    listsChanged = Signal()
    resultsDetailsChanged = Signal()
    diagnosticsChanged = Signal()

    def __init__(
        self,
        *,
        service: MarketDataService | None = None,
        logger: logging.Logger | None = None,
        auto_refresh_prices: bool = True,
        recipe_id: str = "T4_MAIN_SWORD",
    ) -> None:
        super().__init__()
        self._service = service
        self._log = logger or logging.getLogger(__name__)
        self._setup = CraftSetup(
            region=MarketRegion.EUROPE,
            craft_city="Bridgewatch",
            default_buy_city="Bridgewatch",
            default_sell_city="Bridgewatch",
            premium=True,
            focus_enabled=False,
            station_fee_percent=300.0,
            market_tax_percent=self._default_market_tax_percent(True),
            daily_bonus_percent=0.0,
            return_rate_percent=0.0,
            hideout_power_percent=0.0,
            quality=1,
        )
        self._craft_runs = 10
        self._inputs_model = MarketInputsModel()
        self._inputs_on_model = MarketInputsModel()
        self._outputs_model = MarketOutputsModel()
        self._outputs_on_model = MarketOutputsModel()
        self._shopping_model = MarketShoppingModel()
        self._selling_model = MarketSellingModel()
        self._results_items_model = MarketResultsItemsModel()
        self._breakdown_model = MarketBreakdownModel()
        self._recipe_options_model = RecipeOptionsModel()
        self._craft_plan_model = CraftPlanModel()
        self._catalog = self._load_catalog()
        self._recipe = self._resolve_recipe(recipe_id)
        self._recipe_options_model.set_items(self._build_recipe_options())
        self._craft_plan_rows: list[CraftPlanRow] = []
        self._next_plan_row_id = 1
        self._breakdown = ProfitBreakdown()
        self._base_input_total_cost = 0.0
        self._journal_totals = _JournalTotals()
        self._results_journal_totals = _JournalTotals()
        self._selected_material_input_total_cost = 0.0
        self._selected_input_total_cost = 0.0
        self._selected_output_total_value = 0.0
        self._selected_output_net_value = 0.0
        self._selected_net_profit_value = 0.0
        self._selected_margin_percent = 0.0
        self._selected_input_item_ids: list[str] = []
        self._selected_output_item_ids: list[str] = []
        self._input_price_types: dict[str, PriceType] = {}
        self._output_price_types: dict[str, PriceType] = {}
        self._manual_input_prices: dict[str, int] = {}
        self._input_stock_quantities: dict[str, float] = {}
        self._completed_input_item_ids: set[str] = set()
        self._manual_output_prices: dict[str, int] = {}
        self._completed_output_item_ids: set[str] = set()
        self._output_cities: dict[str, str] = {}
        self._price_index: dict[tuple[str, str, int], MarketPriceRecord] = {}
        self._price_context_key: tuple[str, int, tuple[str, ...], tuple[str, ...]] | None = None
        self._prices_source = "fallback"
        self._prices_status_text = "Using bundled fallback prices."
        self._price_fetch_in_progress = False
        self._results_sort_key = "profit"
        self._shopping_csv = ""
        self._selling_csv = ""
        self._results_csv = ""
        self._list_action_text = ""
        self._diagnostics_lines: list[str] = []
        self._recipe_search_query = ""
        self._recipe_tier_filters: list[int] = []
        self._recipe_enchant_filters: list[int] = []
        self._hide_rows_without_fresh_prices = False
        self._app_settings = load_app_settings()
        self._default_export_dir = str(self._app_settings.market_export_dir or "").strip()
        self._preset_path = _default_preset_path()
        self._presets: dict[str, dict[str, object]] = self._load_presets()
        self._selected_preset_name = str(self._app_settings.market_selected_preset or "").strip()
        self._craft_plan_sort_key = "added"
        self._craft_plan_sort_desc = False
        self._active_market_tab_index = 0
        self._market_data_tabs_live_bootstrap_done = False
        self._manual_refresh_cooldown_seconds = 30.0
        self._min_live_refresh_interval_seconds = 2.0
        self._rate_limit_cooldown_seconds = 90.0
        self._next_live_fetch_not_before = 0.0
        self._deferred_price_refresh_timer = QTimer(self)
        self._deferred_price_refresh_timer.setSingleShot(True)
        self._deferred_price_refresh_timer.timeout.connect(self._on_deferred_price_refresh_timeout)
        self._refresh_cooldown_tick_timer = QTimer(self)
        self._refresh_cooldown_tick_timer.setInterval(1000)
        self._refresh_cooldown_tick_timer.timeout.connect(self._on_refresh_cooldown_tick)
        self._deferred_force_price_refresh = False
        if self._selected_preset_name and self._selected_preset_name in self._presets:
            self._apply_preset_payload(self._selected_preset_name, self._presets[self._selected_preset_name])
        self._ensure_price_preferences_for_recipe(self._recipe)
        if auto_refresh_prices and self._service is not None:
            self._refresh_price_index(self.to_setup(), force=True)
        self._rebuild_preview(force_price_refresh=False)
        self._append_diag("Market state initialized.", level="INFO")

    @Property(str, notify=setupChanged)
    def region(self) -> str:
        return self._setup.region.value

    @Property(str, notify=setupChanged)
    def craftCity(self) -> str:
        return self._setup.craft_city

    @Property(str, notify=setupChanged)
    def defaultBuyCity(self) -> str:
        return self._setup.default_buy_city

    @Property(str, notify=setupChanged)
    def defaultSellCity(self) -> str:
        return self._setup.default_sell_city

    @Property(bool, notify=setupChanged)
    def premium(self) -> bool:
        return self._setup.premium

    @Property(bool, notify=setupChanged)
    def focusEnabled(self) -> bool:
        return self._setup.focus_enabled

    @Property(float, notify=setupChanged)
    def stationFeePercent(self) -> float:
        return self._setup.station_fee_percent

    @Property(float, notify=setupChanged)
    def marketTaxPercent(self) -> float:
        return self._setup.market_tax_percent

    @Property(float, notify=setupChanged)
    def dailyBonusPercent(self) -> float:
        return self._setup.daily_bonus_percent

    @Property(int, notify=setupChanged)
    def dailyBonusPreset(self) -> int:
        return self._normalize_daily_bonus_percent(self._setup.daily_bonus_percent)

    @Property(float, notify=setupChanged)
    def returnRatePercent(self) -> float:
        return self._setup.return_rate_percent

    @Property(float, notify=setupChanged)
    def hideoutPowerPercent(self) -> float:
        return self._setup.hideout_power_percent

    @Property(int, notify=setupChanged)
    def quality(self) -> int:
        return self._setup.quality

    @Property(int, notify=setupChanged)
    def craftRuns(self) -> int:
        return self._craft_runs

    @Property(str, notify=setupChanged)
    def recipeId(self) -> str:
        return _recipe_identity(self._recipe)

    @Property(str, notify=setupChanged)
    def recipeDisplayName(self) -> str:
        return _recipe_display_label(self._recipe)

    @Property(int, notify=setupChanged)
    def recipeTier(self) -> int:
        return int(self._recipe.item.tier or 0)

    @Property(int, notify=setupChanged)
    def recipeEnchant(self) -> int:
        return int(self._recipe.item.enchantment or 0)

    @Property(int, notify=setupChanged)
    def recipeIndex(self) -> int:
        return self._recipe_options_model.index_of_recipe(self.recipeId)

    @Property(str, notify=setupChanged)
    def recipeSearchQuery(self) -> str:
        return self._recipe_search_query

    @Property(int, notify=setupChanged)
    def recipeEnchantFilter(self) -> int:
        if not self._recipe_enchant_filters:
            return -1
        return int(self._recipe_enchant_filters[0])

    @Property("QVariantList", notify=setupChanged)
    def recipeTierFilters(self) -> list[int]:
        return list(self._recipe_tier_filters)

    @Property("QVariantList", notify=setupChanged)
    def recipeEnchantFilters(self) -> list[int]:
        return list(self._recipe_enchant_filters)

    @Property(bool, notify=setupChanged)
    def hideRowsWithoutFreshPrices(self) -> bool:
        return bool(self._hide_rows_without_fresh_prices)

    @Property("QVariantList", notify=setupChanged)
    def presetNames(self) -> list[str]:
        return sorted(self._presets.keys(), key=lambda x: x.lower())

    @Property(str, notify=setupChanged)
    def selectedPresetName(self) -> str:
        return self._selected_preset_name

    @Property(str, notify=pricesChanged)
    def pricesSource(self) -> str:
        return self._prices_source

    @Property(str, notify=pricesChanged)
    def pricesStatusText(self) -> str:
        return self._prices_status_text

    @Property(bool, notify=pricesChanged)
    def priceFetchInProgress(self) -> bool:
        return self._price_fetch_in_progress

    @Property(bool, notify=pricesChanged)
    def priceFetchPending(self) -> bool:
        return self._price_fetch_in_progress or self._deferred_price_refresh_timer.isActive()

    @Property(int, notify=pricesChanged)
    def refreshCooldownSeconds(self) -> int:
        remaining = self._next_live_fetch_not_before - time.monotonic()
        if remaining <= 0:
            return 0
        return int(ceil(remaining))

    @Property(bool, notify=pricesChanged)
    def canRefreshPrices(self) -> bool:
        return (not self._price_fetch_in_progress) and self.refreshCooldownSeconds <= 0

    @Property(str, notify=pricesChanged)
    def refreshPricesButtonText(self) -> str:
        if self.refreshCooldownSeconds > 0:
            return f"Refresh in {self.refreshCooldownSeconds}s"
        return "Refresh prices"

    @Property(QObject, constant=True)
    def inputsModel(self) -> QObject:
        return self._inputs_model

    @Property(QObject, constant=True)
    def inputsOnModel(self) -> QObject:
        return self._inputs_on_model

    @Property(QObject, constant=True)
    def outputsModel(self) -> QObject:
        return self._outputs_model

    @Property(QObject, constant=True)
    def outputsOnModel(self) -> QObject:
        return self._outputs_on_model

    @Property(QObject, constant=True)
    def recipeOptionsModel(self) -> QObject:
        return self._recipe_options_model

    @Property(QObject, constant=True)
    def craftPlanModel(self) -> QObject:
        return self._craft_plan_model

    @Property(int, notify=setupChanged)
    def craftPlanCount(self) -> int:
        return len(self._craft_plan_rows)

    @Property(int, notify=setupChanged)
    def craftPlanEnabledCount(self) -> int:
        return len([row for row in self._craft_plan_rows if row.enabled])

    @Property(str, notify=setupChanged)
    def craftPlanSortKey(self) -> str:
        return self._craft_plan_sort_key

    @Property(bool, notify=setupChanged)
    def craftPlanSortDescending(self) -> bool:
        return self._craft_plan_sort_desc

    @Property(QObject, constant=True)
    def shoppingModel(self) -> QObject:
        return self._shopping_model

    @Property(QObject, constant=True)
    def sellingModel(self) -> QObject:
        return self._selling_model

    @Property(QObject, constant=True)
    def resultsItemsModel(self) -> QObject:
        return self._results_items_model

    @Property(QObject, constant=True)
    def breakdownModel(self) -> QObject:
        return self._breakdown_model

    @Property(str, notify=listsChanged)
    def shoppingCsv(self) -> str:
        return self._shopping_csv

    @Property(str, notify=listsChanged)
    def sellingCsv(self) -> str:
        return self._selling_csv

    @Property(str, notify=resultsChanged)
    def resultsCsv(self) -> str:
        return self._results_csv

    @Property(str, notify=listsChanged)
    def listActionText(self) -> str:
        return self._list_action_text

    @Property(str, notify=diagnosticsChanged)
    def diagnosticsText(self) -> str:
        return "\n".join(self._diagnostics_lines)

    @Property(str, notify=resultsDetailsChanged)
    def resultsSortKey(self) -> str:
        return self._results_sort_key

    @Property(float, notify=inputsChanged)
    def inputsTotalCost(self) -> float:
        total = 0.0
        for idx in range(self._inputs_model.rowCount()):
            model_index = self._inputs_model.index(idx, 0)
            value = self._inputs_model.data(model_index, MarketInputsModel.TotalCostRole)
            if value is not None:
                total += float(value)
        return float(total)

    @Property(float, notify=outputsChanged)
    def outputsTotalValue(self) -> float:
        total = 0.0
        for idx in range(self._outputs_model.rowCount()):
            model_index = self._outputs_model.index(idx, 0)
            value = self._outputs_model.data(model_index, MarketOutputsModel.TotalValueRole)
            if value is not None:
                total += float(value)
        return float(total)

    @Property(float, notify=outputsChanged)
    def outputsNetValue(self) -> float:
        total = 0.0
        for idx in range(self._outputs_model.rowCount()):
            model_index = self._outputs_model.index(idx, 0)
            value = self._outputs_model.data(model_index, MarketOutputsModel.NetValueRole)
            if value is not None:
                total += float(value)
        return float(total)

    @Property(float, notify=resultsChanged)
    def stationFeeValue(self) -> float:
        return float(self._breakdown.station_fee)

    @Property(float, notify=resultsChanged)
    def marketTaxValue(self) -> float:
        return float(self._breakdown.market_tax)

    @Property(float, notify=resultsChanged)
    def netProfitValue(self) -> float:
        return float(self._breakdown.net_profit)

    @Property(float, notify=resultsChanged)
    def marginPercent(self) -> float:
        return float(self._breakdown.margin_percent)

    @Property(float, notify=resultsChanged)
    def selectedInputsTotalCost(self) -> float:
        return float(self._selected_input_total_cost)

    @Property(float, notify=resultsChanged)
    def selectedOutputsTotalValue(self) -> float:
        return float(self._selected_output_total_value)

    @Property(float, notify=resultsChanged)
    def selectedOutputsNetValue(self) -> float:
        return float(self._selected_output_net_value)

    @Property(float, notify=resultsChanged)
    def selectedNetProfitValue(self) -> float:
        return float(self._selected_net_profit_value)

    @Property(float, notify=resultsChanged)
    def selectedMarginPercent(self) -> float:
        return float(self._selected_margin_percent)

    @Property("QVariantList", notify=inputsChanged)
    def selectedInputItemIds(self) -> list[str]:
        return list(self._selected_input_item_ids)

    @Property("QVariantList", notify=outputsChanged)
    def selectedOutputItemIds(self) -> list[str]:
        return list(self._selected_output_item_ids)

    @Property(float, notify=resultsChanged)
    def focusUsed(self) -> float:
        return float(self._breakdown.focus_used)

    @Property(float, notify=resultsChanged)
    def silverPerFocus(self) -> float:
        if self._breakdown.focus_used <= 0:
            return 0.0
        return float(self._breakdown.net_profit / self._breakdown.focus_used)

    @Property(float, notify=setupChanged)
    def resourceReturnRatePercent(self) -> float:
        setup = self.to_setup()
        row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
        if row is not None:
            setup = self._setup_for_plan_row(setup, row)
        return float(effective_return_fraction(setup=setup, recipe=self._recipe) * 100.0)

    @Property(str, notify=validationChanged)
    def validationText(self) -> str:
        errors = validate_setup(self._setup)
        if self._craft_runs <= 0:
            errors.append("craftRuns must be > 0")
        if not self._craft_plan_rows:
            errors.append("craftPlan must contain at least one recipe")
        if not errors:
            return ""
        return "; ".join(errors)

    @Slot(str)
    def setRegion(self, value: str) -> None:
        value_norm = value.strip().lower()
        mapping = {
            "europe": MarketRegion.EUROPE,
            "west": MarketRegion.WEST,
            "east": MarketRegion.EAST,
        }
        if value_norm not in mapping:
            return
        self._replace(region=mapping[value_norm])

    @Slot(int)
    def setActiveMarketTab(self, index: int) -> None:
        normalized = max(0, int(index))
        if normalized == self._active_market_tab_index:
            return
        self._active_market_tab_index = normalized
        if self._active_market_tab_index >= 1:
            if not self._should_defer_price_refresh():
                self._rebuild_preview(force_price_refresh=False)
            elif not self._market_data_tabs_live_bootstrap_done:
                # First data-tab visit: schedule async refresh so UI can paint loading state.
                self._schedule_deferred_price_refresh(0.05, force=False)
            else:
                # Subsequent tab switches: rebuild synchronously using current data (no loading flash).
                self._rebuild_preview(force_price_refresh=False)

    @Slot(int)
    def setRecipeIndex(self, index: int) -> None:
        recipe_id = self._recipe_options_model.recipe_id_at(int(index))
        if recipe_id is None:
            return
        self.setRecipeId(recipe_id)

    @Slot(str)
    def setRecipeId(self, recipe_id: str) -> None:
        recipe = self._catalog.get(recipe_id)
        if recipe is None:
            return
        if _recipe_identity(recipe) == _recipe_identity(self._recipe):
            return
        self._recipe = recipe
        self._ensure_price_preferences_for_recipe(self._recipe)
        plan_row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
        if plan_row is not None:
            self._craft_runs = max(1, int(plan_row.runs))
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(str)
    def setRecipeSearchQuery(self, query: str) -> None:
        normalized = query.strip()
        if normalized == self._recipe_search_query:
            return
        self._recipe_search_query = normalized
        self._recipe_options_model.set_query(normalized)
        self.setupChanged.emit()

    @Slot(int)
    def setRecipeEnchantFilter(self, value: int) -> None:
        raw = int(value)
        if raw < 0:
            self.setRecipeEnchantFilters([])
            return
        if raw > 4:
            return
        self.setRecipeEnchantFilters([raw])

    @Slot("QVariantList")
    def setRecipeTierFilters(self, values: list[object]) -> None:
        normalized = self._normalize_int_filter_list(values, minimum=1, maximum=8)
        if normalized == self._recipe_tier_filters:
            return
        self._recipe_tier_filters = normalized
        self._recipe_options_model.set_tier_filters(normalized)
        self.setupChanged.emit()

    @Slot("QVariantList")
    def setRecipeEnchantFilters(self, values: list[object]) -> None:
        normalized = self._normalize_int_filter_list(values, minimum=0, maximum=4)
        if normalized == self._recipe_enchant_filters:
            return
        self._recipe_enchant_filters = normalized
        self._recipe_options_model.set_enchant_filters(normalized)
        self.setupChanged.emit()

    @Slot(bool)
    def setHideRowsWithoutFreshPrices(self, enabled: bool) -> None:
        normalized = bool(enabled)
        if normalized == self._hide_rows_without_fresh_prices:
            return
        self._hide_rows_without_fresh_prices = normalized
        self.setupChanged.emit()
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str)
    def setSelectedPresetName(self, value: str) -> None:
        name = value.strip()
        if name == self._selected_preset_name:
            return
        self._selected_preset_name = name
        self._persist_app_settings()
        self.setupChanged.emit()

    @Slot(str)
    def savePreset(self, raw_name: str) -> None:
        name = _sanitize_preset_name(raw_name)
        if not name:
            self._set_list_action_text("Preset name is empty.")
            return
        self._presets[name] = {
            "setup": _setup_to_dict(self._setup),
            "craft_runs": int(self._craft_runs),
            "recipe_id": _recipe_identity(self._recipe),
            "recipe_search_query": self._recipe_search_query,
            "recipe_tier_filters": list(self._recipe_tier_filters),
            "recipe_enchant_filters": list(self._recipe_enchant_filters),
            "hide_rows_without_fresh_prices": bool(self._hide_rows_without_fresh_prices),
            "craft_plan": [_craft_plan_row_to_dict(row) for row in self._craft_plan_rows],
        }
        if self._save_presets():
            self._selected_preset_name = name
            self._persist_app_settings()
            self._set_list_action_text(f"Preset saved: {name}")
            self._append_diag(f"Preset saved: {name}", level="INFO")
            self.setupChanged.emit()

    @Slot(str)
    def loadPreset(self, raw_name: str) -> None:
        name = _sanitize_preset_name(raw_name)
        if not name:
            self._set_list_action_text("Preset name is empty.")
            return
        payload = self._presets.get(name)
        if payload is None:
            self._set_list_action_text(f"Preset not found: {name}")
            return
        if not self._apply_preset_payload(name, payload):
            self._set_list_action_text(f"Preset is invalid: {name}")
            return
        self._persist_app_settings()
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()
        self._set_list_action_text(f"Preset loaded: {name}")
        self._append_diag(f"Preset loaded: {name}", level="INFO")

    @Slot(str)
    def deletePreset(self, raw_name: str) -> None:
        name = _sanitize_preset_name(raw_name)
        if not name:
            self._set_list_action_text("Preset name is empty.")
            return
        if name not in self._presets:
            self._set_list_action_text(f"Preset not found: {name}")
            return
        del self._presets[name]
        if self._selected_preset_name == name:
            self._selected_preset_name = ""
        if self._save_presets():
            self._persist_app_settings()
            self._set_list_action_text(f"Preset deleted: {name}")
            self._append_diag(f"Preset deleted: {name}", level="INFO")
            self.setupChanged.emit()

    def _apply_preset_payload(self, name: str, payload: object) -> bool:
        if not isinstance(payload, dict):
            return False
        setup_data = payload.get("setup")
        if not isinstance(setup_data, dict):
            return False

        self._setup = sanitized_setup(_setup_from_dict(setup_data, fallback=self._setup))
        loaded_rows = _craft_plan_rows_from_payload(
            payload.get("craft_plan"),
            catalog=self._catalog,
            fallback_city=self._setup.craft_city,
            fallback_daily_bonus_percent=float(self._setup.daily_bonus_percent),
        )
        if loaded_rows is not None:
            self._craft_plan_rows = loaded_rows
            self._next_plan_row_id = max((row.row_id for row in loaded_rows), default=0) + 1
            self._sync_craft_plan_model()
            for plan_row in self._craft_plan_rows:
                plan_recipe = self._catalog.get(plan_row.recipe_id)
                if plan_recipe is not None:
                    self._ensure_price_preferences_for_recipe(plan_recipe)

        recipe_id = str(payload.get("recipe_id") or "").strip()
        if recipe_id and self._catalog.get(recipe_id) is not None:
            self._recipe = self._resolve_recipe(recipe_id)
        elif self._craft_plan_rows:
            self._recipe = self._resolve_recipe(self._craft_plan_rows[0].recipe_id)
        self._ensure_price_preferences_for_recipe(self._recipe)

        search_query = str(payload.get("recipe_search_query") or "").strip()
        self._recipe_search_query = search_query
        self._recipe_options_model.set_query(search_query)
        tier_filters = payload.get("recipe_tier_filters")
        enchant_filters = payload.get("recipe_enchant_filters")
        self._recipe_tier_filters = self._normalize_int_filter_list(
            tier_filters if isinstance(tier_filters, list) else [],
            minimum=1,
            maximum=8,
        )
        self._recipe_enchant_filters = self._normalize_int_filter_list(
            enchant_filters if isinstance(enchant_filters, list) else [],
            minimum=0,
            maximum=4,
        )
        self._recipe_options_model.set_tier_filters(self._recipe_tier_filters)
        self._recipe_options_model.set_enchant_filters(self._recipe_enchant_filters)
        self._hide_rows_without_fresh_prices = bool(payload.get("hide_rows_without_fresh_prices", False))

        self._craft_runs = max(1, int(payload.get("craft_runs") or self._craft_runs))
        active_row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
        if active_row is not None:
            self._craft_runs = max(1, int(active_row.runs))
        self._selected_preset_name = name
        return True

    def _persist_app_settings(self) -> None:
        try:
            self._app_settings = update_app_settings(
                market_selected_preset=str(self._selected_preset_name or ""),
                market_export_dir=str(self._default_export_dir or ""),
            )
        except Exception as exc:
            self._log.warning("Market app settings save failed: %s", exc)

    @Slot()
    def selectFirstRecipeOption(self) -> None:
        if self._recipe_options_model.rowCount() <= 0:
            return
        recipe_id = self._recipe_options_model.recipe_id_at(0)
        if recipe_id is None:
            return
        self.setRecipeId(recipe_id)

    @Slot()
    def addFirstRecipeOption(self) -> None:
        if self._recipe_options_model.rowCount() <= 0:
            return
        recipe_id = self._recipe_options_model.recipe_id_at(0)
        if recipe_id is None:
            return
        self.addRecipeToPlan(recipe_id)
        self.setRecipeId(recipe_id)

    @Slot(int)
    def addRecipeAtIndex(self, index: int) -> None:
        recipe_id = self._recipe_options_model.recipe_id_at(int(index))
        if recipe_id is None:
            return
        self.addRecipeToPlan(recipe_id)
        self.setRecipeId(recipe_id)

    @Slot()
    def addFilteredRecipeOptions(self) -> None:
        recipe_ids = self._recipe_options_model.recipe_ids()
        if not recipe_ids:
            self._set_list_action_text("No recipes match current filters.")
            return
        added = 0
        for recipe_id in recipe_ids:
            if self._add_recipe_to_plan_internal(recipe_id, runs=self._craft_runs, enabled=False):
                added += 1
        if added <= 0:
            self._set_list_action_text("No new recipes were added.")
            return
        self._set_list_action_text(f"Added {added} recipes to craft plan (On = off).")
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def addRecipeFamily(self) -> None:
        family_ids: list[str] = []
        if self._recipe_search_query.strip():
            filtered_ids = self._recipe_options_model.recipe_ids()
            family_ids = self._station_recipe_ids_for_filtered(filtered_ids)
            if not family_ids:
                family_ids = self._family_recipe_ids_for_filtered(filtered_ids)
        else:
            family_ids = self._station_recipe_ids(_recipe_identity(self._recipe))
            if not family_ids:
                family_ids = self._family_recipe_ids(_recipe_identity(self._recipe))
        if not family_ids:
            self._set_list_action_text("No recipes found for selected family.")
            return
        added = 0
        for recipe_id in family_ids:
            if self._add_recipe_to_plan_internal(recipe_id, runs=self._craft_runs, enabled=False):
                added += 1
        if added <= 0:
            self._set_list_action_text("No new family recipes were added.")
            return
        self._set_list_action_text(f"Added {added} family recipes (On = off).")
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def addCurrentRecipeToPlan(self) -> None:
        added = self._add_recipe_to_plan_internal(_recipe_identity(self._recipe), runs=self._craft_runs, enabled=False)
        if not added:
            row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
            if row is not None and row.runs != self._craft_runs:
                self._update_plan_row(row.row_id, runs=self._craft_runs)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(str)
    def addRecipeToPlan(self, recipe_id: str) -> None:
        added = self._add_recipe_to_plan_internal(recipe_id, runs=self._craft_runs, enabled=False)
        if not added:
            row = self._find_plan_row_by_recipe(recipe_id)
            if row is not None and row.runs != self._craft_runs:
                self._update_plan_row(row.row_id, runs=self._craft_runs)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int)
    def selectPlanRow(self, row_id: int) -> None:
        row = self._find_plan_row(row_id)
        if row is None:
            return
        self.setRecipeId(row.recipe_id)

    @Slot(int)
    def removePlanRow(self, row_id: int) -> None:
        before = len(self._craft_plan_rows)
        self._craft_plan_rows = [row for row in self._craft_plan_rows if int(row.row_id) != int(row_id)]
        if len(self._craft_plan_rows) == before:
            return
        self._sync_craft_plan_model()
        if not any(row.recipe_id == _recipe_identity(self._recipe) for row in self._craft_plan_rows):
            if self._craft_plan_rows:
                self._recipe = self._resolve_recipe(self._craft_plan_rows[0].recipe_id)
                self._craft_runs = max(1, int(self._craft_plan_rows[0].runs))
                self._ensure_price_preferences_for_recipe(self._recipe)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, bool)
    def setPlanRowEnabled(self, row_id: int, enabled: bool) -> None:
        if not self._update_plan_row(row_id, enabled=bool(enabled)):
            return
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, int)
    def setPlanRowRuns(self, row_id: int, runs: int) -> None:
        normalized = max(1, int(runs))
        if not self._update_plan_row(row_id, runs=normalized):
            return
        row = self._find_plan_row(row_id)
        if row is not None and row.recipe_id == _recipe_identity(self._recipe):
            self._craft_runs = normalized
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, str)
    def setPlanRowCraftCity(self, row_id: int, craft_city: str) -> None:
        city_value = craft_city.strip()
        if not city_value:
            city_value = self._setup.craft_city
        if not self._update_plan_row(row_id, craft_city=city_value):
            return
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(int, str)
    def setPlanRowDailyBonus(self, row_id: int, daily_bonus: str) -> None:
        text = daily_bonus.strip().replace("%", "")
        try:
            parsed = float(text)
        except ValueError:
            return
        normalized = float(self._normalize_daily_bonus_percent(parsed))
        if not self._update_plan_row(row_id, daily_bonus_percent=normalized):
            return
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def clearCraftPlan(self) -> None:
        self._craft_plan_rows = []
        self._next_plan_row_id = 1
        self._completed_input_item_ids.clear()
        self._completed_output_item_ids.clear()
        self._sync_craft_plan_model()
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot(str)
    def setCraftCity(self, value: str) -> None:
        self._replace(craft_city=value)

    @Slot(str)
    def setDefaultBuyCity(self, value: str) -> None:
        self._replace(default_buy_city=value)

    @Slot(str)
    def setDefaultSellCity(self, value: str) -> None:
        self._replace(default_sell_city=value)

    @Slot(bool)
    def setPremium(self, value: bool) -> None:
        self._replace(premium=bool(value))

    @Slot(bool)
    def setFocusEnabled(self, value: bool) -> None:
        self._replace(focus_enabled=bool(value))

    @Slot(float)
    def setStationFeePercent(self, value: float) -> None:
        self._replace(station_fee_percent=float(value))

    @Slot(float)
    def setMarketTaxPercent(self, value: float) -> None:
        self._replace(market_tax_percent=float(value))

    @Slot(float)
    def setDailyBonusPercent(self, value: float) -> None:
        self._replace(daily_bonus_percent=float(self._normalize_daily_bonus_percent(value)))

    @Slot(str)
    def setDailyBonusPreset(self, value: str) -> None:
        text = value.strip().replace("%", "")
        try:
            parsed = float(text)
        except ValueError:
            return
        self.setDailyBonusPercent(parsed)

    @Slot(float)
    def setReturnRatePercent(self, value: float) -> None:
        self._replace(return_rate_percent=float(value))

    @Slot(float)
    def setHideoutPowerPercent(self, value: float) -> None:
        self._replace(hideout_power_percent=float(value))

    @Slot(int)
    def setQuality(self, value: int) -> None:
        self._replace(quality=int(value))

    @Slot(int)
    def setCraftRuns(self, value: int) -> None:
        runs = max(1, int(value))
        if runs == self._craft_runs:
            return
        self._craft_runs = runs
        row = self._find_plan_row_by_recipe(_recipe_identity(self._recipe))
        if row is not None and row.runs != runs:
            self._update_plan_row(row.row_id, runs=runs)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    @Slot()
    def refreshPrices(self) -> None:
        price_refresh_ops.refresh_prices(self)

    @Slot()
    def showAoDataRaw(self) -> None:
        url = self._build_aodata_url()
        if not url:
            return
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtGui import QDesktopServices
        except Exception as exc:  # pragma: no cover - optional
            self._set_list_action_text(f"Failed to open AOData URL: {exc}")
            return
        opened = QDesktopServices.openUrl(QUrl(url))
        if opened:
            self._set_list_action_text("Opened AOData prices in browser.")
            self._append_diag("Opened AOData raw URL in browser.", level="INFO")
        else:
            self._set_list_action_text(f"AOData URL: {url}")
            self._append_diag("Failed to open browser; AOData URL copied to status.", level="WARN")

    @Slot(str, str)
    def setInputPriceType(self, item_id: str, price_type: str) -> None:
        normalized = self._to_price_type(price_type)
        if normalized is None:
            return
        if self._input_price_types.get(item_id) == normalized:
            return
        self._input_price_types[item_id] = normalized
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, str)
    def setOutputPriceType(self, item_id: str, price_type: str) -> None:
        normalized = self._to_price_type(price_type)
        if normalized is None:
            return
        if self._output_price_types.get(item_id) == normalized:
            return
        self._output_price_types[item_id] = normalized
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, str)
    def setOutputCity(self, item_id: str, city: str) -> None:
        city_value = city.strip()
        if not city_value:
            city_value = self._setup.default_sell_city or self._setup.craft_city
        if self._output_cities.get(item_id, "") == city_value:
            return
        self._output_cities[item_id] = city_value
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, str)
    def setInputManualPrice(self, item_id: str, raw_value: str) -> None:
        price = _parse_price(raw_value)
        if price <= 0:
            self._manual_input_prices.pop(item_id, None)
        else:
            self._manual_input_prices[item_id] = price
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, str)
    def setInputStockQuantity(self, item_id: str, raw_value: str) -> None:
        quantity = _parse_float(raw_value)
        if quantity <= 0:
            self._input_stock_quantities.pop(item_id, None)
        else:
            self._input_stock_quantities[item_id] = quantity
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str, bool)
    def setInputRowCompleted(self, item_id: str, completed: bool) -> None:
        normalized_item_id = str(item_id or "").strip()
        if not normalized_item_id:
            return
        if completed:
            if normalized_item_id in self._completed_input_item_ids:
                return
            self._completed_input_item_ids.add(normalized_item_id)
        else:
            if normalized_item_id not in self._completed_input_item_ids:
                return
            self._completed_input_item_ids.discard(normalized_item_id)
        self._inputs_model.set_completed_by_item_id(normalized_item_id, completed)
        self._inputs_on_model.set_completed_by_item_id(normalized_item_id, completed)
        self.inputsChanged.emit()

    @Slot(str, bool)
    def setOutputRowCompleted(self, item_id: str, completed: bool) -> None:
        normalized_item_id = str(item_id or "").strip()
        if not normalized_item_id:
            return
        if completed:
            if normalized_item_id in self._completed_output_item_ids:
                return
            self._completed_output_item_ids.add(normalized_item_id)
        else:
            if normalized_item_id not in self._completed_output_item_ids:
                return
            self._completed_output_item_ids.discard(normalized_item_id)
        self._outputs_model.set_completed_by_item_id(normalized_item_id, completed)
        self._outputs_on_model.set_completed_by_item_id(normalized_item_id, completed)
        self.outputsChanged.emit()

    @Slot(str, str)
    def setOutputManualPrice(self, item_id: str, raw_value: str) -> None:
        price = _parse_price(raw_value)
        if price <= 0:
            self._manual_output_prices.pop(item_id, None)
        else:
            self._manual_output_prices[item_id] = price
        self._rebuild_preview(force_price_refresh=False)

    @Slot(str)
    def setResultsSortKey(self, key: str) -> None:
        normalized = key.strip().lower()
        if normalized not in {"profit", "margin", "revenue"}:
            return
        if normalized == self._results_sort_key:
            return
        self._results_sort_key = normalized
        self._rebuild_preview(force_price_refresh=False)
        self.resultsDetailsChanged.emit()

    @Slot(str)
    def setCraftPlanSortKey(self, key: str) -> None:
        normalized = key.strip().lower()
        if normalized not in {"added", "craft", "tier", "city", "pl"}:
            return
        changed = normalized != self._craft_plan_sort_key
        self._craft_plan_sort_key = normalized
        if normalized == "pl" and not self._craft_plan_sort_desc:
            self._craft_plan_sort_desc = True
            changed = True
        if not changed:
            return
        self._sync_craft_plan_model()
        self.setupChanged.emit()

    @Slot(bool)
    def setCraftPlanSortDescending(self, value: bool) -> None:
        normalized = bool(value)
        if normalized == self._craft_plan_sort_desc:
            return
        self._craft_plan_sort_desc = normalized
        self._sync_craft_plan_model()
        self.setupChanged.emit()

    @Slot()
    def toggleCraftPlanSortDescending(self) -> None:
        self.setCraftPlanSortDescending(not self._craft_plan_sort_desc)

    @Slot()
    def copyShoppingCsv(self) -> None:
        if not self._shopping_csv:
            self._set_list_action_text("Shopping CSV is empty.")
            return
        self._copy_to_clipboard(self._shopping_csv, success_message="Shopping CSV copied to clipboard.")

    @Slot(str)
    def copyText(self, raw_value: str) -> None:
        value = str(raw_value or "").strip()
        if not value:
            return
        self._copy_to_clipboard(value, success_message="Copied value to clipboard.")

    @Slot()
    def clearDiagnostics(self) -> None:
        self._diagnostics_lines = []
        self.diagnosticsChanged.emit()

    @Slot()
    def copySellingCsv(self) -> None:
        if not self._selling_csv:
            self._set_list_action_text("Selling CSV is empty.")
            return
        self._copy_to_clipboard(self._selling_csv, success_message="Selling CSV copied to clipboard.")

    @Slot()
    def copyResultsCsv(self) -> None:
        if not self._results_csv:
            self._set_list_action_text("Results CSV is empty.")
            return
        self._copy_to_clipboard(self._results_csv, success_message="Results CSV copied to clipboard.")

    @Slot(str)
    def exportShoppingCsv(self, raw_path: str) -> None:
        self._export_csv(raw_path=raw_path, payload=self._shopping_csv, label="Shopping")

    @Slot(str)
    def exportSellingCsv(self, raw_path: str) -> None:
        self._export_csv(raw_path=raw_path, payload=self._selling_csv, label="Selling")

    @Slot(str)
    def exportResultsCsv(self, raw_path: str) -> None:
        self._export_csv(raw_path=raw_path, payload=self._results_csv, label="Results")

    @Slot()
    def exportShoppingCsvInteractive(self) -> None:
        self._export_csv_interactive(payload=self._shopping_csv, label="Shopping", suggested_name="acd-shopping.csv")

    @Slot()
    def exportSellingCsvInteractive(self) -> None:
        self._export_csv_interactive(payload=self._selling_csv, label="Selling", suggested_name="acd-selling.csv")

    @Slot()
    def exportResultsCsvInteractive(self) -> None:
        self._export_csv_interactive(payload=self._results_csv, label="Results", suggested_name="acd-results.csv")

    def to_setup(self) -> CraftSetup:
        return sanitized_setup(self._setup)

    def close(self) -> None:
        if self._service is not None:
            self._service.close()

    def _replace(self, **kwargs) -> None:
        premium_value = bool(kwargs.get("premium", self._setup.premium))
        market_tax_value = kwargs.get("market_tax_percent", self._default_market_tax_percent(premium_value))
        setup = CraftSetup(
            region=kwargs.get("region", self._setup.region),
            craft_city=kwargs.get("craft_city", self._setup.craft_city),
            default_buy_city=kwargs.get("default_buy_city", self._setup.default_buy_city),
            default_sell_city=kwargs.get("default_sell_city", self._setup.default_sell_city),
            premium=premium_value,
            focus_enabled=bool(kwargs.get("focus_enabled", self._setup.focus_enabled)),
            station_fee_percent=kwargs.get("station_fee_percent", self._setup.station_fee_percent),
            market_tax_percent=market_tax_value,
            daily_bonus_percent=kwargs.get("daily_bonus_percent", self._setup.daily_bonus_percent),
            return_rate_percent=kwargs.get("return_rate_percent", self._setup.return_rate_percent),
            hideout_power_percent=kwargs.get("hideout_power_percent", self._setup.hideout_power_percent),
            quality=kwargs.get("quality", self._setup.quality),
        )
        self._setup = sanitized_setup(setup)
        self._rebuild_preview(force_price_refresh=False)
        self.setupChanged.emit()
        self.validationChanged.emit()

    def _sync_craft_plan_model(self) -> None:
        self._craft_plan_model.set_items(self._sorted_craft_plan_rows(self._craft_plan_rows))

    def _family_recipe_ids(self, recipe_id: str) -> list[str]:
        return selection_ops.family_recipe_ids(
            self._catalog,
            recipe_id,
            recipe_tier_filters=self._recipe_tier_filters,
            recipe_enchant_filters=self._recipe_enchant_filters,
            is_recipe_plan_candidate=_is_recipe_plan_candidate,
            item_family_key=_item_family_key,
            recipe_display_label=_recipe_display_label,
            recipe_identity=_recipe_identity,
        )

    def _family_recipe_ids_for_filtered(self, recipe_ids: list[str]) -> list[str]:
        return selection_ops.family_recipe_ids_for_filtered(
            self._catalog,
            recipe_ids,
            family_recipe_ids_for_recipe=self._family_recipe_ids,
            item_family_key=_item_family_key,
            recipe_identity=_recipe_identity,
        )

    def _station_recipe_ids(self, recipe_id: str) -> list[str]:
        return selection_ops.station_recipe_ids(
            self._catalog,
            recipe_id,
            recipe_tier_filters=self._recipe_tier_filters,
            recipe_enchant_filters=self._recipe_enchant_filters,
            is_recipe_plan_candidate=_is_recipe_plan_candidate,
            recipe_display_label=_recipe_display_label,
            recipe_identity=_recipe_identity,
        )

    def _station_recipe_ids_for_filtered(self, recipe_ids: list[str]) -> list[str]:
        return selection_ops.station_recipe_ids_for_filtered(
            self._catalog,
            recipe_ids,
            station_recipe_ids_for_recipe=self._station_recipe_ids,
            recipe_identity=_recipe_identity,
        )

    def _sorted_craft_plan_rows(self, rows: list[CraftPlanRow]) -> list[CraftPlanRow]:
        return selection_ops.sorted_craft_plan_rows(
            rows,
            sort_key=self._craft_plan_sort_key,
            reverse=bool(self._craft_plan_sort_desc),
        )

    def _add_recipe_to_plan_internal(self, recipe_id: str, *, runs: int, enabled: bool) -> bool:
        recipe = self._catalog.get(recipe_id)
        if recipe is None:
            return False
        if not _is_recipe_plan_candidate(recipe):
            return False
        if self._find_plan_row_by_recipe(recipe_id) is not None:
            return False
        self._ensure_price_preferences_for_recipe(recipe)
        row = CraftPlanRow(
            row_id=self._next_plan_row_id,
            recipe_id=_recipe_identity(recipe),
            display_name=_recipe_display_label(recipe),
            tier=int(recipe.item.tier or 0),
            enchant=int(recipe.item.enchantment or 0),
            variant_label=str(recipe.variant_label or ""),
            uses_crystallized=bool(recipe.uses_crystallized),
            craft_city=self._setup.craft_city or "Bridgewatch",
            daily_bonus_percent=float(self._normalize_daily_bonus_percent(self._setup.daily_bonus_percent)),
            return_rate_percent=None,
            runs=max(1, int(runs)),
            enabled=bool(enabled),
            profit_percent=None,
            has_fresh_component_prices=True,
        )
        self._next_plan_row_id += 1
        self._craft_plan_rows.append(row)
        self._sync_craft_plan_model()
        return True

    def _find_plan_row(self, row_id: int) -> CraftPlanRow | None:
        for row in self._craft_plan_rows:
            if int(row.row_id) == int(row_id):
                return row
        return None

    def _find_plan_row_by_recipe(self, recipe_id: str) -> CraftPlanRow | None:
        for row in self._craft_plan_rows:
            if row.recipe_id == recipe_id:
                return row
        return None

    def _update_plan_row(
        self,
        row_id: int,
        *,
        runs: int | None = None,
        enabled: bool | None = None,
        craft_city: str | None = None,
        daily_bonus_percent: float | None = None,
    ) -> bool:
        changed = False
        next_rows: list[CraftPlanRow] = []
        changed_city = False
        changed_profit_drivers = False
        for row in self._craft_plan_rows:
            if int(row.row_id) != int(row_id):
                next_rows.append(row)
                continue
            next_runs = max(1, int(runs)) if runs is not None else row.runs
            next_enabled = bool(enabled) if enabled is not None else row.enabled
            next_craft_city = craft_city.strip() if craft_city is not None else row.craft_city
            if not next_craft_city:
                next_craft_city = row.craft_city or self._setup.craft_city or "Bridgewatch"
            next_daily_bonus = (
                float(self._normalize_daily_bonus_percent(daily_bonus_percent))
                if daily_bonus_percent is not None
                else float(row.daily_bonus_percent)
            )
            next_row = CraftPlanRow(
                row_id=row.row_id,
                recipe_id=row.recipe_id,
                display_name=row.display_name,
                tier=row.tier,
                enchant=row.enchant,
                variant_label=row.variant_label,
                uses_crystallized=bool(row.uses_crystallized),
                craft_city=next_craft_city,
                daily_bonus_percent=next_daily_bonus,
                return_rate_percent=row.return_rate_percent,
                runs=next_runs,
                enabled=next_enabled,
                profit_percent=row.profit_percent,
                has_fresh_component_prices=row.has_fresh_component_prices,
            )
            changed = next_row != row
            changed_city = changed_city or (next_row.craft_city != row.craft_city)
            changed_profit_drivers = changed_profit_drivers or (
                next_row.enabled != row.enabled
                or next_row.runs != row.runs
                or float(next_row.daily_bonus_percent) != float(row.daily_bonus_percent)
            )
            next_rows.append(next_row)
        if changed:
            self._craft_plan_rows = next_rows
            sort_key = str(self._craft_plan_sort_key or "")
            needs_resort = (sort_key == "city" and changed_city) or (sort_key == "pl" and changed_profit_drivers)
            if needs_resort:
                self._sync_craft_plan_model()
            else:
                self._craft_plan_model.set_items_in_place(self._sorted_craft_plan_rows(self._craft_plan_rows))
        return changed

    def _ensure_price_preferences_for_recipe(self, recipe: Recipe) -> None:
        for component in recipe.components:
            self._input_price_types.setdefault(component.item.unique_name, PriceType.SELL_ORDER)
        for output in recipe.outputs:
            self._output_price_types.setdefault(output.item.unique_name, PriceType.SELL_ORDER)

    def _recipes_for_preview(self) -> list[tuple[CraftPlanRow, Recipe]]:
        rows: list[tuple[CraftPlanRow, Recipe]] = []
        for row in self._craft_plan_rows:
            recipe = self._catalog.get(row.recipe_id)
            if recipe is None:
                continue
            rows.append((row, recipe))
        return rows

    @staticmethod
    def _setup_for_plan_row(setup: CraftSetup, row: CraftPlanRow) -> CraftSetup:
        return CraftSetup(
            region=setup.region,
            craft_city=row.craft_city,
            default_buy_city=setup.default_buy_city,
            default_sell_city=setup.default_sell_city,
            premium=setup.premium,
            focus_enabled=setup.focus_enabled,
            station_fee_percent=setup.station_fee_percent,
            market_tax_percent=setup.market_tax_percent,
            daily_bonus_percent=float(row.daily_bonus_percent),
            return_rate_percent=setup.return_rate_percent,
            hideout_power_percent=setup.hideout_power_percent,
            quality=setup.quality,
        )

    def _recipes_for_pricing(self) -> list[Recipe]:
        recipes: list[Recipe] = []
        seen: set[str] = set()
        for row in self._craft_plan_rows:
            recipe = self._catalog.get(row.recipe_id)
            if recipe is None:
                continue
            recipe_key = _recipe_identity(recipe)
            if recipe_key in seen:
                continue
            seen.add(recipe_key)
            recipes.append(recipe)
        return recipes

    def _collect_pricing_item_ids(self) -> list[str]:
        item_ids: set[str] = set()
        for recipe in self._recipes_for_pricing():
            for component in recipe.components:
                item_ids.update(_item_id_query_candidates(component.item.unique_name))
            for output in recipe.outputs:
                item_ids.update(_item_id_query_candidates(output.item.unique_name))
            journal_rule = _journal_rule_for_item(recipe.item.unique_name)
            if journal_rule is not None:
                # Market IDs for journals are not fully consistent across dumps; query all common variants.
                item_ids.add(journal_rule.empty_item_id)
                item_ids.add(f"{journal_rule.empty_item_id}_EMPTY")
                item_ids.add(journal_rule.full_item_id)
        return sorted(item_ids)

    def _collect_locations(self, setup: CraftSetup) -> list[str]:
        location_set = {
            setup.craft_city.strip(),
            setup.default_buy_city.strip(),
            setup.default_sell_city.strip(),
        }
        for row in self._craft_plan_rows:
            city_value = row.craft_city.strip()
            if city_value:
                location_set.add(city_value)
        locations = sorted(
            location
            for location in (location_set - {""})
            if self._is_market_location(location)
        )
        if not locations:
            locations = ["Bridgewatch"]
        return locations

    def _clear_preview_state(self, note: str) -> None:
        self._inputs_model.set_items([])
        self._inputs_on_model.set_items([])
        self._outputs_model.set_items([])
        self._outputs_on_model.set_items([])
        self._shopping_model.set_items([])
        self._selling_model.set_items([])
        self._results_items_model.set_items([])
        self._breakdown_model.set_items([])
        self._set_plan_profit_map({}, fresh_component_prices={})
        self._shopping_csv = ""
        self._selling_csv = ""
        self._results_csv = ""
        self._breakdown = ProfitBreakdown(notes=[note] if note else [])
        self._base_input_total_cost = 0.0
        self._journal_totals = _JournalTotals()
        self._results_journal_totals = _JournalTotals()
        self._selected_material_input_total_cost = 0.0
        self._selected_input_total_cost = 0.0
        self._selected_output_total_value = 0.0
        self._selected_output_net_value = 0.0
        self._selected_net_profit_value = 0.0
        self._selected_margin_percent = 0.0
        self._selected_input_item_ids = []
        self._selected_output_item_ids = []
        self.inputsChanged.emit()
        self.outputsChanged.emit()
        self.resultsChanged.emit()
        self.listsChanged.emit()
        self.resultsDetailsChanged.emit()

    def _rebuild_preview(self, *, force_price_refresh: bool) -> None:
        setup = self.to_setup()
        planned_recipes = self._recipes_for_preview()
        if not planned_recipes:
            self._clear_preview_state("no enabled recipes in craft plan")
            return
        allow_live_fetch = force_price_refresh or (
            self._active_market_tab_index >= 1 and not self._market_data_tabs_live_bootstrap_done
        )
        if allow_live_fetch and not force_price_refresh:
            # One automatic live fetch when first entering data tabs; next refreshes are manual.
            self._market_data_tabs_live_bootstrap_done = True
        price_index = self._current_price_index(
            setup,
            force_refresh=force_price_refresh,
            allow_live=allow_live_fetch,
        )
        runs: list[CraftRun] = []
        prepared_recipes: list[tuple[CraftPlanRow, Recipe]] = []
        skipped_rows: list[str] = []
        for row, recipe in planned_recipes:
            self._ensure_price_preferences_for_recipe(recipe)
            row_setup = self._setup_for_plan_row(setup, row)
            try:
                run = build_craft_run(
                    recipe=recipe,
                    quantity=max(1, int(row.runs)),
                    setup=row_setup,
                    price_index=price_index,
                    input_price_types=dict(self._input_price_types),
                    output_cities=dict(self._output_cities),
                    output_price_types=dict(self._output_price_types),
                    manual_input_prices=dict(self._manual_input_prices),
                    manual_output_prices=dict(self._manual_output_prices),
                )
            except Exception as exc:
                recipe_id = _recipe_identity(recipe)
                skipped_rows.append(recipe_id)
                self._append_diag(
                    f"Preview build skipped recipe {recipe_id}: {exc}",
                    level="WARN",
                )
                continue
            runs.append(run)
            prepared_recipes.append((row, recipe))

        if not runs:
            self._clear_preview_state("preview build failed")
            return

        run_profit_by_row: dict[int, float] = {}
        run_rrr_by_row: dict[int, float] = {}
        run_fresh_by_row: dict[int, bool] = {}
        for (plan_row, recipe), run in zip(prepared_recipes, runs):
            breakdown = compute_run_profit(run)
            run_profit_by_row[int(plan_row.row_id)] = float(breakdown.margin_percent)
            row_setup = self._setup_for_plan_row(setup, plan_row)
            run_rrr_by_row[int(plan_row.row_id)] = float(
                effective_return_fraction(setup=row_setup, recipe=recipe) * 100.0
            )
            run_fresh_by_row[int(plan_row.row_id)] = self._run_has_fresh_component_prices(run)
        self._set_plan_profit_map(run_profit_by_row, run_rrr_by_row, run_fresh_by_row)

        visible_runs: list[CraftRun] = list(runs)
        visible_prepared_recipes: list[tuple[CraftPlanRow, Recipe]] = list(prepared_recipes)
        if self._hide_rows_without_fresh_prices:
            visible_runs = []
            visible_prepared_recipes = []
            for (plan_row, recipe), run in zip(prepared_recipes, runs):
                if run_fresh_by_row.get(int(plan_row.row_id), True):
                    visible_prepared_recipes.append((plan_row, recipe))
                    visible_runs.append(run)
            hidden_count = len(runs) - len(visible_runs)
            if hidden_count > 0:
                self._append_diag(
                    f"Hidden {hidden_count} craft row(s) missing fresh AO Data component prices.",
                    level="INFO",
                )

        selected_visible_runs: list[CraftRun] = []
        selected_visible_prepared_recipes: list[tuple[CraftPlanRow, Recipe]] = []
        for (plan_row, recipe), run in zip(visible_prepared_recipes, visible_runs):
            if not plan_row.enabled:
                continue
            selected_visible_prepared_recipes.append((plan_row, recipe))
            selected_visible_runs.append(run)
        selected_journal_totals = self._estimate_journal_totals(
            runs=selected_visible_runs,
            setup=setup,
            price_index=price_index,
        )
        self._results_journal_totals = selected_journal_totals
        selected_inputs = [line for run in selected_visible_runs for line in run.inputs]
        selected_input_item_ids: set[str] = {str(line.item.unique_name) for line in selected_inputs}
        for journal_line in selected_journal_totals.lines:
            if journal_line.empty_quantity > 0:
                selected_input_item_ids.add(str(journal_line.empty_item_id))
        self._selected_input_item_ids = sorted(selected_input_item_ids)
        selected_material_input_total = self._compute_input_total_from_lines(
            input_lines=selected_inputs,
            prepared_recipes=selected_visible_prepared_recipes,
        )
        selected_input_total = float(selected_material_input_total + float(selected_journal_totals.input_cost))

        all_inputs = [line for run in visible_runs for line in run.inputs]
        all_outputs = [line for run in visible_runs for line in run.outputs]
        self._journal_totals = self._estimate_journal_totals(runs=visible_runs, setup=setup, price_index=price_index)
        input_acc = self._accumulate_input_preview_rows(
            prepared_recipes=visible_prepared_recipes,
            runs=visible_runs,
        )

        journal_buy_city = (setup.default_buy_city or setup.craft_city or "").strip()
        journal_sell_city = (setup.default_sell_city or setup.craft_city or "").strip()
        for journal_line in self._journal_totals.lines:
            if journal_line.empty_quantity <= 0:
                continue
            empty_unit_price = float(journal_line.input_cost) / float(journal_line.empty_quantity)
            empty_item_id = str(journal_line.empty_item_id)
            empty_name = f"{_journal_display_name(journal_line.kind, journal_line.tier)} (empty)"
            journal_input_price_type = str(journal_line.input_price_mode or PriceType.SELL_ORDER.value)
            key = (
                empty_item_id,
                journal_buy_city,
                journal_input_price_type,
                float(empty_unit_price),
            )
            row = input_acc.get(key)
            journal_input_age = self._price_age_text_for_item_ids(
                item_ids=[
                    str(journal_line.empty_price_item_id or ""),
                    f"{empty_item_id}_EMPTY",
                    empty_item_id,
                ],
                city=journal_buy_city,
                quality=self._setup.quality,
                price_type=journal_input_price_type,
            )
            if journal_input_age.strip().lower() in {"", "n/a", "unknown"}:
                journal_input_age = "npc"
            if row is None:
                input_acc[key] = {
                    "item_id": empty_item_id,
                    "item": empty_name,
                    "item_ref": ItemRef(
                        unique_name=empty_item_id,
                        display_name=empty_name,
                        tier=int(journal_line.tier),
                        enchantment=0,
                    ),
                    "city": journal_buy_city,
                    "price_type": journal_input_price_type,
                    "price_age_text": journal_input_age,
                    "unit_price": float(empty_unit_price),
                    "quantity": float(journal_line.empty_quantity),
                    "total_cost": float(journal_line.input_cost),
                    "returnable": False,
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(journal_line.empty_quantity)
                row["total_cost"] = float(row["total_cost"]) + float(journal_line.input_cost)
            self._input_price_types.setdefault(empty_item_id, self._to_price_type(journal_input_price_type))

        input_rows: list[InputPreviewRow] = []
        adjusted_inputs: list[InputLine] = []
        for row in input_acc.values():
            item_id = str(row["item_id"])
            quantity_raw = float(row["quantity"])
            is_returnable = bool(row.get("returnable", False))
            need_qty = float(max(0, _need_quantity_with_safety_buffer(quantity_raw, is_returnable)))
            stock_qty = float(max(0.0, self._input_stock_quantities.get(item_id, 0.0)))
            stock_qty = min(stock_qty, need_qty)
            buy_qty = max(0.0, need_qty - stock_qty)
            unit_price = float(row["unit_price"])
            total_cost = float(buy_qty * unit_price)
            input_rows.append(
                InputPreviewRow(
                    item_id=item_id,
                    row_key=_input_preview_row_key(item_id, str(row["city"]), str(row["price_type"])),
                    item=str(row["item"]),
                    quantity=need_qty,
                    stock_quantity=stock_qty,
                    buy_quantity=buy_qty,
                    city=str(row["city"]),
                    price_type=str(row["price_type"]),
                    price_age_text=str(row["price_age_text"]),
                    manual_price=self._manual_input_prices.get(item_id, 0),
                    unit_price=unit_price,
                    total_cost=total_cost,
                    completed=item_id in self._completed_input_item_ids or buy_qty <= 0.0,
                )
            )
            item_ref = row.get("item_ref")
            if isinstance(item_ref, ItemRef):
                adjusted_inputs.append(
                    InputLine(
                        item=item_ref,
                        quantity=buy_qty,
                        city=str(row["city"]),
                        price_type=PriceType(str(row["price_type"])),
                        unit_price=unit_price,
                    )
                )
        input_rows.sort(key=_input_preview_sort_key)

        selected_input_acc = self._accumulate_input_preview_rows(
            prepared_recipes=selected_visible_prepared_recipes,
            runs=selected_visible_runs,
        )

        for journal_line in selected_journal_totals.lines:
            if journal_line.empty_quantity <= 0:
                continue
            empty_unit_price = float(journal_line.input_cost) / float(journal_line.empty_quantity)
            empty_item_id = str(journal_line.empty_item_id)
            empty_name = f"{_journal_display_name(journal_line.kind, journal_line.tier)} (empty)"
            selected_journal_input_price_type = str(journal_line.input_price_mode or PriceType.SELL_ORDER.value)
            key = (
                empty_item_id,
                journal_buy_city,
                selected_journal_input_price_type,
                float(empty_unit_price),
            )
            row = selected_input_acc.get(key)
            selected_journal_input_age = self._price_age_text_for_item_ids(
                item_ids=[
                    str(journal_line.empty_price_item_id or ""),
                    f"{empty_item_id}_EMPTY",
                    empty_item_id,
                ],
                city=journal_buy_city,
                quality=self._setup.quality,
                price_type=selected_journal_input_price_type,
            )
            if selected_journal_input_age.strip().lower() in {"", "n/a", "unknown"}:
                selected_journal_input_age = "npc"
            if row is None:
                selected_input_acc[key] = {
                    "item_id": empty_item_id,
                    "item": empty_name,
                    "city": journal_buy_city,
                    "price_type": selected_journal_input_price_type,
                    "price_age_text": selected_journal_input_age,
                    "unit_price": float(empty_unit_price),
                    "quantity": float(journal_line.empty_quantity),
                    "returnable": False,
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(journal_line.empty_quantity)

        selected_input_rows: list[InputPreviewRow] = []
        for row in selected_input_acc.values():
            item_id = str(row["item_id"])
            quantity_raw = float(row["quantity"])
            is_returnable = bool(row.get("returnable", False))
            need_qty = float(max(0, _need_quantity_with_safety_buffer(quantity_raw, is_returnable)))
            stock_qty = float(max(0.0, self._input_stock_quantities.get(item_id, 0.0)))
            stock_qty = min(stock_qty, need_qty)
            buy_qty = max(0.0, need_qty - stock_qty)
            unit_price = float(row["unit_price"])
            selected_input_rows.append(
                InputPreviewRow(
                    item_id=item_id,
                    row_key=_input_preview_row_key(item_id, str(row["city"]), str(row["price_type"])),
                    item=str(row["item"]),
                    quantity=need_qty,
                    stock_quantity=stock_qty,
                    buy_quantity=buy_qty,
                    city=str(row["city"]),
                    price_type=str(row["price_type"]),
                    price_age_text=str(row["price_age_text"]),
                    manual_price=self._manual_input_prices.get(item_id, 0),
                    unit_price=unit_price,
                    total_cost=float(buy_qty * unit_price),
                    completed=item_id in self._completed_input_item_ids or buy_qty <= 0.0,
                )
            )
        selected_input_rows.sort(key=_input_preview_sort_key)

        self._base_input_total_cost = float(sum(row.total_cost for row in input_rows))
        valuations = compute_output_valuations(
            output_lines=all_outputs,
            station_fee_percent=setup.station_fee_percent,
            market_tax_percent=setup.market_tax_percent,
        )

        output_acc: dict[tuple[str, str, str, float], dict[str, float | str]] = {}
        for valuation in valuations:
            line = valuation.line
            key = (line.item.unique_name, line.city, line.price_type.value, float(line.unit_price))
            row = output_acc.get(key)
            if row is None:
                output_acc[key] = {
                    "item_id": line.item.unique_name,
                    "item": _friendly_item_label(line.item.display_name, line.item.unique_name),
                    "city": line.city,
                    "price_type": line.price_type.value,
                    "price_age_text": self._price_age_text(
                        item_id=line.item.unique_name,
                        city=line.city,
                        quality=self._setup.quality,
                        price_type=line.price_type.value,
                    ),
                    "unit_price": float(line.unit_price),
                    "quantity": float(line.quantity),
                    "total_value": float(valuation.gross_value),
                    "fee_value": float(valuation.fee_value),
                    "tax_value": float(valuation.tax_value),
                    "net_value": float(valuation.net_value),
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(line.quantity)
                row["total_value"] = float(row["total_value"]) + float(valuation.gross_value)
                row["fee_value"] = float(row["fee_value"]) + float(valuation.fee_value)
                row["tax_value"] = float(row["tax_value"]) + float(valuation.tax_value)
                row["net_value"] = float(row["net_value"]) + float(valuation.net_value)

        for journal_line in self._journal_totals.lines:
            if journal_line.full_quantity <= 0:
                continue
            full_item_id = str(journal_line.full_item_id)
            full_name = f"{_journal_display_name(journal_line.kind, journal_line.tier)} (full)"
            full_unit_price = float(journal_line.output_value) / float(journal_line.full_quantity)
            journal_output_price_type = str(journal_line.output_price_mode or PriceType.SELL_ORDER.value)
            key = (
                full_item_id,
                journal_sell_city,
                journal_output_price_type,
                float(full_unit_price),
            )
            row = output_acc.get(key)
            if row is None:
                output_acc[key] = {
                    "item_id": full_item_id,
                    "item": full_name,
                    "city": journal_sell_city,
                    "price_type": journal_output_price_type,
                    "price_age_text": self._price_age_text_for_item_ids(
                        item_ids=[str(journal_line.full_price_item_id or ""), full_item_id],
                        city=journal_sell_city,
                        quality=self._setup.quality,
                        price_type=journal_output_price_type,
                    ),
                    "unit_price": float(full_unit_price),
                    "quantity": float(journal_line.full_quantity),
                    "total_value": float(journal_line.output_value),
                    "fee_value": 0.0,
                    "tax_value": float(journal_line.market_tax),
                    "net_value": float(journal_line.output_value - journal_line.market_tax),
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(journal_line.full_quantity)
                row["total_value"] = float(row["total_value"]) + float(journal_line.output_value)
                row["tax_value"] = float(row["tax_value"]) + float(journal_line.market_tax)
                row["net_value"] = float(row["net_value"]) + float(journal_line.output_value - journal_line.market_tax)
            self._output_price_types.setdefault(full_item_id, self._to_price_type(journal_output_price_type))
            if journal_sell_city:
                self._output_cities.setdefault(full_item_id, journal_sell_city)

        output_rows = [
            OutputPreviewRow(
                item_id=str(row["item_id"]),
                item=str(row["item"]),
                quantity=float(row["quantity"]),
                city=str(row["city"]),
                price_type=str(row["price_type"]),
                price_age_text=str(row.get("price_age_text", "n/a")),
                manual_price=self._manual_output_prices.get(str(row["item_id"]), 0),
                unit_price=float(row["unit_price"]),
                total_value=float(row["total_value"]),
                fee_value=float(row["fee_value"]),
                tax_value=float(row["tax_value"]),
                net_value=float(row["net_value"]),
                completed=str(row["item_id"]) in self._completed_output_item_ids,
            )
            for row in output_acc.values()
        ]
        output_rows.sort(key=lambda x: (x.item.lower(), x.city.lower()))

        self._inputs_model.set_items(input_rows)
        self._inputs_on_model.set_items(selected_input_rows)
        self._outputs_model.set_items(output_rows)

        shopping_rows = [
            ShoppingPreviewRow(
                item_id=entry.item_id,
                item=_friendly_item_label(entry.item_name, entry.item_id),
                quantity=float(max(0, math.ceil(float(entry.quantity)))),
                city=entry.city,
                price_type=entry.price_type,
                unit_price=float(entry.unit_price),
                total_cost=float(max(0, math.ceil(float(entry.quantity))) * float(entry.unit_price)),
            )
            for entry in build_shopping_entries(adjusted_inputs)
        ]
        selling_rows = [
            SellingPreviewRow(
                item_id=entry.item_id,
                item=_friendly_item_label(entry.item_name, entry.item_id),
                quantity=float(entry.quantity),
                city=entry.city,
                price_type=entry.price_type,
                unit_price=float(entry.unit_price),
                total_value=float(entry.total_value),
            )
            for entry in build_selling_entries(all_outputs)
        ]

        self._shopping_model.set_items(shopping_rows)
        self._selling_model.set_items(selling_rows)
        self._shopping_csv = self._rows_to_csv(
            header=["item_id", "item_name", "quantity", "city", "price_type", "unit_price", "total_cost"],
            rows=[
                [
                    row.item_id,
                    row.item,
                    f"{row.quantity:.4f}",
                    row.city,
                    row.price_type,
                    f"{row.unit_price:.2f}",
                    f"{row.total_cost:.2f}",
                ]
                for row in shopping_rows
            ],
        )
        self._selling_csv = self._rows_to_csv(
            header=["item_id", "item_name", "quantity", "city", "price_type", "unit_price", "total_value"],
            rows=[
                [
                    row.item_id,
                    row.item,
                    f"{row.quantity:.4f}",
                    row.city,
                    row.price_type,
                    f"{row.unit_price:.2f}",
                    f"{row.total_value:.2f}",
                ]
                for row in selling_rows
            ],
        )

        selected_outputs = [line for run in selected_visible_runs for line in run.outputs]
        selected_valuations = compute_output_valuations(
            output_lines=selected_outputs,
            station_fee_percent=setup.station_fee_percent,
            market_tax_percent=setup.market_tax_percent,
        )
        selected_output_acc: dict[tuple[str, str, str, float], dict[str, float | str]] = {}
        for valuation in selected_valuations:
            line = valuation.line
            key = (line.item.unique_name, line.city, line.price_type.value, float(line.unit_price))
            row = selected_output_acc.get(key)
            if row is None:
                selected_output_acc[key] = {
                    "item_id": line.item.unique_name,
                    "item": _friendly_item_label(line.item.display_name, line.item.unique_name),
                    "city": line.city,
                    "price_type": line.price_type.value,
                    "price_age_text": self._price_age_text(
                        item_id=line.item.unique_name,
                        city=line.city,
                        quality=self._setup.quality,
                        price_type=line.price_type.value,
                    ),
                    "unit_price": float(line.unit_price),
                    "quantity": float(line.quantity),
                    "total_value": float(valuation.gross_value),
                    "fee_value": float(valuation.fee_value),
                    "tax_value": float(valuation.tax_value),
                    "net_value": float(valuation.net_value),
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(line.quantity)
                row["total_value"] = float(row["total_value"]) + float(valuation.gross_value)
                row["fee_value"] = float(row["fee_value"]) + float(valuation.fee_value)
                row["tax_value"] = float(row["tax_value"]) + float(valuation.tax_value)
                row["net_value"] = float(row["net_value"]) + float(valuation.net_value)

        for journal_line in selected_journal_totals.lines:
            if journal_line.full_quantity <= 0:
                continue
            full_item_id = str(journal_line.full_item_id)
            full_name = f"{_journal_display_name(journal_line.kind, journal_line.tier)} (full)"
            full_unit_price = float(journal_line.output_value) / float(journal_line.full_quantity)
            selected_journal_output_price_type = str(journal_line.output_price_mode or PriceType.SELL_ORDER.value)
            key = (
                full_item_id,
                journal_sell_city,
                selected_journal_output_price_type,
                float(full_unit_price),
            )
            row = selected_output_acc.get(key)
            if row is None:
                selected_output_acc[key] = {
                    "item_id": full_item_id,
                    "item": full_name,
                    "city": journal_sell_city,
                    "price_type": selected_journal_output_price_type,
                    "price_age_text": self._price_age_text_for_item_ids(
                        item_ids=[str(journal_line.full_price_item_id or ""), full_item_id],
                        city=journal_sell_city,
                        quality=self._setup.quality,
                        price_type=selected_journal_output_price_type,
                    ),
                    "unit_price": float(full_unit_price),
                    "quantity": float(journal_line.full_quantity),
                    "total_value": float(journal_line.output_value),
                    "fee_value": 0.0,
                    "tax_value": float(journal_line.market_tax),
                    "net_value": float(journal_line.output_value - journal_line.market_tax),
                }
            else:
                row["quantity"] = float(row["quantity"]) + float(journal_line.full_quantity)
                row["total_value"] = float(row["total_value"]) + float(journal_line.output_value)
                row["tax_value"] = float(row["tax_value"]) + float(journal_line.market_tax)
                row["net_value"] = float(row["net_value"]) + float(journal_line.output_value - journal_line.market_tax)

        selected_output_rows = [
            OutputPreviewRow(
                item_id=str(row["item_id"]),
                item=str(row["item"]),
                quantity=float(row["quantity"]),
                city=str(row["city"]),
                price_type=str(row["price_type"]),
                price_age_text=str(row.get("price_age_text", "n/a")),
                manual_price=self._manual_output_prices.get(str(row["item_id"]), 0),
                unit_price=float(row["unit_price"]),
                total_value=float(row["total_value"]),
                fee_value=float(row["fee_value"]),
                tax_value=float(row["tax_value"]),
                net_value=float(row["net_value"]),
                completed=str(row["item_id"]) in self._completed_output_item_ids,
            )
            for row in selected_output_acc.values()
        ]
        selected_output_rows.sort(key=lambda x: (x.item.lower(), x.city.lower()))
        self._selected_output_item_ids = sorted({str(row.item_id) for row in selected_output_rows})

        selected_output_total_value = float(sum(row.total_value for row in selected_output_rows))
        selected_output_net_value = float(sum(row.net_value for row in selected_output_rows))
        selected_station_fee = float(sum(row.fee_value for row in selected_output_rows))
        selected_market_tax = float(sum(row.tax_value for row in selected_output_rows))
        selected_run_breakdown = compute_batch_profit(tuple(selected_visible_runs))
        self._breakdown = ProfitBreakdown(
            input_cost=float(selected_input_total),
            output_value=selected_output_total_value,
            station_fee=selected_station_fee,
            market_tax=selected_market_tax,
            focus_used=float(selected_run_breakdown.focus_used),
            notes=list(selected_run_breakdown.notes),
        )
        self._selected_input_total_cost = float(selected_input_total)
        self._selected_material_input_total_cost = float(selected_material_input_total)
        self._selected_output_total_value = selected_output_total_value
        self._selected_output_net_value = selected_output_net_value
        self._selected_net_profit_value = float(self._breakdown.net_profit)
        self._selected_margin_percent = float(self._breakdown.margin_percent)

        results_rows = self._build_results_rows_from_runs(
            runs=selected_visible_runs,
            input_total=selected_input_total,
        )
        self._results_items_model.set_items(results_rows)
        self._results_csv = self._rows_to_csv(
            header=["item_id", "item_name", "city", "quantity", "revenue", "cost", "fee", "tax", "profit", "margin_percent", "demand_proxy"],
            rows=[
                [
                    row.item_id,
                    row.item,
                    row.city,
                    f"{row.quantity:.4f}",
                    f"{row.revenue:.2f}",
                    f"{row.allocated_cost:.2f}",
                    f"{row.fee_value:.2f}",
                    f"{row.tax_value:.2f}",
                    f"{row.profit:.2f}",
                    f"{row.margin_percent:.2f}",
                    f"{row.demand_proxy:.2f}",
                ]
                for row in results_rows
            ],
        )
        self._outputs_on_model.set_items(selected_output_rows)
        breakdown_rows = self._build_breakdown_rows()
        self._breakdown_model.set_items(breakdown_rows)

        self.inputsChanged.emit()
        self.outputsChanged.emit()
        self.resultsChanged.emit()
        self.listsChanged.emit()
        self.resultsDetailsChanged.emit()
        if skipped_rows:
            self._set_fallback_status(
                f"Skipped {len(skipped_rows)} recipe(s) that could not be previewed."
            )

    def _build_results_rows_from_runs(
        self,
        *,
        runs: list[CraftRun],
        input_total: float,
    ) -> list[ResultItemRow]:
        _ = input_total
        return build_results_rows_from_runs(
            runs=runs,
            setup=self._setup,
            results_sort_key=self._results_sort_key,
            estimate_journal_totals=lambda selected_runs: self._estimate_journal_totals(
                runs=selected_runs,
                setup=self._setup,
                price_index=self._price_index,
            ),
            demand_proxy_percent=lambda item_id, city: self._demand_proxy_percent(
                item_id=item_id,
                city=city,
                quality=self._setup.quality,
            ),
            item_label=_friendly_item_label,
            result_row_profit_and_margin=lambda allocated_cost, net_value: _result_row_profit_and_margin(
                allocated_cost=allocated_cost,
                net_value=net_value,
            ),
        )

    def _accumulate_input_preview_rows(
        self,
        *,
        prepared_recipes: list[tuple[CraftPlanRow, Recipe]],
        runs: list[CraftRun],
    ) -> dict[tuple[str, str, str, float], dict[str, object]]:
        return accumulate_input_preview_rows(
            prepared_recipes=prepared_recipes,
            runs=runs,
            price_age_text=lambda item_id, city, price_type: self._price_age_text(
                item_id=item_id,
                city=city,
                quality=self._setup.quality,
                price_type=price_type,
            ),
            item_label=_friendly_item_label,
            minimal_upfront_quantity_for_batches=_minimal_upfront_quantity_for_batches,
            upfront_return_safety_units=_upfront_return_safety_units,
        )

    def _build_breakdown_rows(self) -> list[BreakdownRow]:
        return build_breakdown_rows(
            selected_material_input_total_cost=self._selected_material_input_total_cost,
            journal_totals=self._results_journal_totals,
            breakdown=self._breakdown,
        )

    def _compute_input_total_from_lines(
        self,
        *,
        input_lines: list[InputLine] | tuple[InputLine, ...],
        prepared_recipes: list[tuple[CraftPlanRow, Recipe]],
    ) -> float:
        _ = prepared_recipes
        return compute_input_total_from_lines(
            input_lines=input_lines,
            input_stock_quantities=self._input_stock_quantities,
        )

    def _demand_proxy_percent(self, *, item_id: str, city: str, quality: int) -> float:
        quote = _find_price_quote(
            self._price_index,
            item_id=item_id,
            city=city,
            quality=quality,
            preferred_mode=None,
        )
        if quote is None:
            return 0.0
        if quote.sell_price_min <= 0 or quote.buy_price_max <= 0:
            return 0.0
        return (float(quote.buy_price_max) / float(quote.sell_price_min)) * 100.0

    def _set_plan_profit_map(
        self,
        values: dict[int, float],
        return_rates: dict[int, float] | None = None,
        fresh_component_prices: dict[int, bool] | None = None,
    ) -> None:
        rates = return_rates or {}
        freshness = fresh_component_prices or {}
        next_rows: list[CraftPlanRow] = []
        changed = False
        for row in self._craft_plan_rows:
            next_profit = values.get(int(row.row_id))
            next_rrr = rates.get(int(row.row_id), row.return_rate_percent)
            if int(row.row_id) in freshness:
                next_has_fresh = bool(freshness[int(row.row_id)])
            elif row.enabled and fresh_component_prices is not None:
                next_has_fresh = False
            else:
                next_has_fresh = bool(row.has_fresh_component_prices)
            next_row = CraftPlanRow(
                row_id=row.row_id,
                recipe_id=row.recipe_id,
                display_name=row.display_name,
                tier=row.tier,
                enchant=row.enchant,
                variant_label=row.variant_label,
                uses_crystallized=bool(row.uses_crystallized),
                craft_city=row.craft_city,
                daily_bonus_percent=row.daily_bonus_percent,
                return_rate_percent=next_rrr,
                runs=row.runs,
                enabled=row.enabled,
                profit_percent=next_profit,
                has_fresh_component_prices=next_has_fresh,
            )
            if next_row != row:
                changed = True
            next_rows.append(next_row)
        if changed:
            self._craft_plan_rows = next_rows
            if str(self._craft_plan_sort_key or "") == "pl":
                self._sync_craft_plan_model()
            else:
                self._craft_plan_model.set_items_in_place(self._sorted_craft_plan_rows(self._craft_plan_rows))

    def _price_age_text(self, *, item_id: str, city: str, quality: int, price_type: str) -> str:
        normalized = str(price_type).strip().lower()
        if normalized == PriceType.MANUAL.value:
            return "manual"
        quote = _find_price_quote(
            self._price_index,
            item_id=item_id,
            city=city,
            quality=quality,
            preferred_mode=normalized,
        )
        if quote is None:
            return "n/a"

        if normalized == PriceType.BUY_ORDER.value:
            if int(quote.buy_price_max or 0) <= 0:
                return "n/a"
            dt = _parse_iso_datetime(quote.buy_price_max_date)
        elif normalized == PriceType.SELL_ORDER.value:
            if int(quote.sell_price_min or 0) <= 0:
                return "n/a"
            dt = _parse_iso_datetime(quote.sell_price_min_date)
        else:
            dt_buy = _parse_iso_datetime(quote.buy_price_max_date) if int(quote.buy_price_max or 0) > 0 else None
            dt_sell = _parse_iso_datetime(quote.sell_price_min_date) if int(quote.sell_price_min or 0) > 0 else None
            dt = max([x for x in [dt_buy, dt_sell] if x is not None], default=None)

        if dt is None:
            return "n/a"
        return _format_age(dt)

    def _run_has_fresh_component_prices(self, run: CraftRun) -> bool:
        checked: set[tuple[str, str, str]] = set()
        for line in run.inputs:
            key = (str(line.item.unique_name), str(line.city), str(line.price_type.value))
            if key in checked:
                continue
            checked.add(key)
            if not self._has_fresh_price(
                item_id=str(line.item.unique_name),
                city=str(line.city),
                quality=int(self._setup.quality),
                price_type=str(line.price_type.value),
            ):
                return False
        return True

    def _has_fresh_price(self, *, item_id: str, city: str, quality: int, price_type: str) -> bool:
        normalized = str(price_type).strip().lower()
        if normalized == PriceType.MANUAL.value:
            return True
        quote = _find_price_quote(
            self._price_index,
            item_id=item_id,
            city=city,
            quality=quality,
            preferred_mode=normalized,
        )
        if quote is None:
            return False
        if normalized == PriceType.BUY_ORDER.value:
            return int(quote.buy_price_max or 0) > 0 and _parse_iso_datetime(quote.buy_price_max_date) is not None
        if normalized == PriceType.SELL_ORDER.value:
            return int(quote.sell_price_min or 0) > 0 and _parse_iso_datetime(quote.sell_price_min_date) is not None
        has_buy = int(quote.buy_price_max or 0) > 0 and _parse_iso_datetime(quote.buy_price_max_date) is not None
        has_sell = int(quote.sell_price_min or 0) > 0 and _parse_iso_datetime(quote.sell_price_min_date) is not None
        return bool(has_buy or has_sell)

    def _estimate_journal_totals(
        self,
        *,
        runs: list[Any],
        setup: CraftSetup,
        price_index: dict[tuple[str, str, int], MarketPriceRecord],
    ) -> _JournalTotals:
        return journal_ops.estimate_journal_totals(
            runs=runs,
            setup=setup,
            price_index=price_index,
            resolve_market_price_for_item_ids=lambda price_index_value, item_ids, city, quality, preferred_mode: self._resolve_market_price_for_item_ids(
                price_index=price_index_value,
                item_ids=item_ids,
                city=city,
                quality=quality,
                preferred_mode=preferred_mode,
            ),
            journal_rule_for_item=_journal_rule_for_item,
            journal_fame_factor_for_item=_journal_fame_factor_for_item,
            tier_from_item_id=_tier_from_item_id,
        )

    def _resolve_market_price_for_item_ids(
        self,
        *,
        price_index: dict[tuple[str, str, int], MarketPriceRecord],
        item_ids: list[str],
        city: str,
        quality: int,
        preferred_mode: str,
    ) -> tuple[float, str, str]:
        normalized_mode = str(preferred_mode).strip().lower()
        fallback_modes: list[str] = []
        if normalized_mode != PriceType.SELL_ORDER.value:
            fallback_modes.append(PriceType.SELL_ORDER.value)
        if normalized_mode != PriceType.BUY_ORDER.value:
            fallback_modes.append(PriceType.BUY_ORDER.value)
        mode_order = [normalized_mode] + fallback_modes
        for mode in mode_order:
            for item_id in item_ids:
                quote = _find_price_quote(
                    price_index,
                    item_id=item_id,
                    city=city,
                    quality=quality,
                    preferred_mode=mode,
                )
                if quote is None:
                    continue
                if mode == PriceType.BUY_ORDER.value:
                    value = int(quote.buy_price_max or 0)
                else:
                    value = int(quote.sell_price_min or 0)
                if value > 0:
                    return float(value), mode, str(item_id)
        return 0.0, normalized_mode, (str(item_ids[0]) if item_ids else "")

    def _price_age_text_for_item_ids(
        self,
        *,
        item_ids: Sequence[str],
        city: str,
        quality: int,
        price_type: str,
    ) -> str:
        seen: set[str] = set()
        for item_id in item_ids:
            normalized_item_id = str(item_id).strip()
            if not normalized_item_id or normalized_item_id in seen:
                continue
            seen.add(normalized_item_id)
            age_text = self._price_age_text(
                item_id=normalized_item_id,
                city=city,
                quality=quality,
                price_type=price_type,
            )
            if age_text.strip().lower() not in {"", "n/a", "unknown"}:
                return age_text
        return "n/a"

    def _set_list_action_text(self, text: str) -> None:
        self._list_action_text = text
        self.listsChanged.emit()

    def _build_aodata_url(self) -> str | None:
        setup = self.to_setup()
        item_ids = self._collect_pricing_item_ids()
        if not item_ids:
            self._set_list_action_text("Select a recipe in Craft Plan to build AOData URL.")
            return None
        locations = self._collect_locations(setup)
        if not locations:
            self._set_list_action_text("No market locations selected.")
            return None
        qualities = [setup.quality]
        params = urlencode(
            {
                "locations": ",".join(locations),
                "qualities": ",".join(str(x) for x in qualities),
            }
        )
        host = REGION_HOSTS.get(setup.region)
        if not host:
            self._set_list_action_text("Unknown AOData region.")
            return None
        joined_ids = ",".join(item_ids)
        return f"https://{host}/api/v2/stats/prices/{joined_ids}.json?{params}"

    def _copy_to_clipboard(self, value: str, *, success_message: str) -> None:
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            self._set_list_action_text("Clipboard is not available.")
            return
        clipboard.setText(value)
        self._set_list_action_text(success_message)

    def _export_csv_interactive(self, *, payload: str, label: str, suggested_name: str) -> None:
        path = self._prompt_export_path(label=label, suggested_name=suggested_name)
        if not path:
            return
        self._export_csv(raw_path=path, payload=payload, label=label)

    def _prompt_export_path(self, *, label: str, suggested_name: str) -> str | None:
        try:
            from PySide6.QtWidgets import QFileDialog
        except Exception as exc:
            self._set_list_action_text(f"{label} export dialog unavailable: {exc}")
            return None
        base_dir = Path(self._default_export_dir).expanduser() if self._default_export_dir else Path.home()
        suggested_path = str((base_dir / suggested_name).resolve())
        selected_path, _selected_filter = QFileDialog.getSaveFileName(
            None,
            f"Export {label} CSV",
            suggested_path,
            "CSV Files (*.csv);;All Files (*)",
        )
        selected = str(selected_path or "").strip()
        if not selected:
            return None
        try:
            self._default_export_dir = str(Path(selected).expanduser().resolve().parent)
            self._persist_app_settings()
        except Exception:
            pass
        return selected

    def _export_csv(self, *, raw_path: str, payload: str, label: str) -> None:
        path_text = raw_path.strip()
        if not path_text:
            self._set_list_action_text(f"{label} export path is empty.")
            return
        if not payload:
            self._set_list_action_text(f"{label} CSV is empty.")
            return
        try:
            path = Path(path_text)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        except Exception as exc:
            self._set_list_action_text(f"{label} export failed: {exc}")
            return
        self._default_export_dir = str(path.parent)
        self._persist_app_settings()
        self._set_list_action_text(f"{label} CSV exported to {path}.")

    @staticmethod
    def _rows_to_csv(*, header: list[str], rows: list[list[str]]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
        return buf.getvalue()

    def _current_price_index(
        self,
        setup: CraftSetup,
        *,
        force_refresh: bool,
        allow_live: bool,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        return price_refresh_ops.current_price_index(
            self,
            setup,
            force_refresh=force_refresh,
            allow_live=allow_live,
        )

    def _refresh_price_index(
        self,
        setup: CraftSetup,
        *,
        force: bool,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        return price_refresh_ops.refresh_price_index(
            self,
            setup,
            force=force,
        )

    def _process_ui_events(self) -> None:
        price_refresh_ops.process_ui_events()

    def _should_defer_price_refresh(self) -> bool:
        return price_refresh_ops.should_defer_price_refresh(self)

    def _set_prices_status(self, source: str, message: str) -> None:
        price_refresh_ops.set_prices_status(self, source, message)

    def _set_fallback_status(self, message: str) -> None:
        price_refresh_ops.set_fallback_status(self, message)

    def _append_diag(self, message: str, *, level: str = "INFO") -> None:
        price_refresh_ops.append_diag(self, message, level=level)

    def _schedule_deferred_price_refresh(self, delay_seconds: float, *, force: bool = False) -> None:
        price_refresh_ops.schedule_deferred_price_refresh(self, delay_seconds, force=force)

    @Slot()
    def _on_deferred_price_refresh_timeout(self) -> None:
        price_refresh_ops.on_deferred_price_refresh_timeout(self)

    def _set_next_live_fetch_cooldown(self, seconds: float) -> None:
        price_refresh_ops.set_next_live_fetch_cooldown(self, seconds)

    @Slot()
    def _on_refresh_cooldown_tick(self) -> None:
        price_refresh_ops.on_refresh_cooldown_tick(self)

    def _load_presets(self) -> dict[str, dict[str, object]]:
        path = self._preset_path
        try:
            return preset_ops.load_presets(path)
        except Exception as exc:
            self._log.warning("Market preset load failed: %s", exc)
            return {}

    def _save_presets(self) -> bool:
        path = self._preset_path
        try:
            preset_ops.save_presets(path, self._presets)
        except Exception as exc:
            self._log.warning("Market preset save failed: %s", exc)
            self._set_list_action_text(f"Preset save failed: {exc}")
            return False
        return True

    def _price_key(self, setup: CraftSetup) -> tuple[str, int, tuple[str, ...], tuple[str, ...]]:
        return pricing_ops.price_key(
            setup,
            item_ids=tuple(self._collect_pricing_item_ids()),
            locations=tuple(self._collect_locations(setup)),
        )

    @staticmethod
    def _default_market_tax_percent(premium: bool) -> float:
        return pricing_ops.default_market_tax_percent(premium)

    @staticmethod
    def _normalize_daily_bonus_percent(value: float) -> float:
        raw = int(round(float(value)))
        if raw >= 15:
            return 20.0
        if raw >= 5:
            return 10.0
        return 0.0

    @staticmethod
    def _normalize_int_filter_list(
        values: Sequence[object] | None,
        *,
        minimum: int,
        maximum: int,
    ) -> list[int]:
        return _normalize_int_values(values, minimum=minimum, maximum=maximum)

    @staticmethod
    def _to_price_type(value: str) -> PriceType | None:
        normalized = value.strip().lower()
        if normalized == PriceType.BUY_ORDER.value:
            return PriceType.BUY_ORDER
        if normalized == PriceType.SELL_ORDER.value:
            return PriceType.SELL_ORDER
        if normalized == PriceType.AVERAGE.value:
            return PriceType.AVERAGE
        if normalized == PriceType.MANUAL.value:
            return PriceType.MANUAL
        return None

    @staticmethod
    def _is_market_location(location: str) -> bool:
        return pricing_ops.is_market_location(location)

    def _load_catalog(self) -> RecipeCatalog:
        return catalog_ops.load_catalog(self._log)

    def _build_recipe_options(self) -> list[RecipeOptionRow]:
        return selection_ops.build_recipe_options(
            self._catalog,
            is_recipe_plan_candidate=_is_recipe_plan_candidate,
            recipe_identity=_recipe_identity,
            recipe_display_label=_recipe_display_label,
        )

    def _resolve_recipe(self, recipe_id: str) -> Recipe:
        recipe = catalog_ops.resolve_recipe(self._catalog, recipe_id)
        if recipe is not None:
            return recipe
        self._log.warning("Market catalog empty, using builtin fallback recipe.")
        return self._build_builtin_recipe()

    @staticmethod
    def _build_builtin_recipe() -> Recipe:
        return catalog_ops.build_builtin_recipe()

    def _build_fallback_price_index(
        self,
        setup: CraftSetup,
    ) -> dict[tuple[str, str, int], MarketPriceRecord]:
        locations = set(self._collect_locations(setup))
        locations.add("Bridgewatch")
        return pricing_ops.build_fallback_price_index(
            setup=setup,
            locations=locations,
            prices=self._estimate_fallback_prices(),
        )

    def _estimate_fallback_prices(self) -> dict[str, tuple[int, int]]:
        return pricing_ops.estimate_fallback_prices(
            recipes=self._recipes_for_pricing(),
        )

    @staticmethod
    def _price_by_tier(tier: int | None) -> tuple[int, int]:
        return pricing_ops.price_by_tier(tier)


def _parse_price(raw_value: str) -> int:
    text = raw_value.strip().replace(",", ".")
    if not text:
        return 0
    try:
        parsed = int(float(text))
    except ValueError:
        return 0
    return max(0, parsed)


def _parse_float(raw_value: str) -> float:
    text = str(raw_value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    try:
        parsed = float(text)
    except ValueError:
        return 0.0
    return max(0.0, parsed)


def _parse_bool(raw_value: object, *, default: bool) -> bool:
    if isinstance(raw_value, bool):
        return raw_value
    if raw_value is None:
        return default
    if isinstance(raw_value, (int, float)):
        return bool(raw_value)
    normalized = str(raw_value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _default_preset_path() -> Path:
    return preset_ops.default_preset_path()


def _sanitize_preset_name(raw_value: str) -> str:
    return preset_ops.sanitize_preset_name(raw_value)


def _setup_to_dict(setup: CraftSetup) -> dict[str, object]:
    return preset_ops.setup_to_dict(setup)


def _setup_from_dict(payload: dict[str, object], *, fallback: CraftSetup) -> CraftSetup:
    return preset_ops.setup_from_dict(payload, fallback=fallback)


def _craft_plan_row_to_dict(row: CraftPlanRow) -> dict[str, object]:
    return preset_ops.craft_plan_row_to_dict(row)


def _craft_plan_rows_from_payload(
    payload: object,
    *,
    catalog: RecipeCatalog,
    fallback_city: str,
    fallback_daily_bonus_percent: float,
) -> list[CraftPlanRow] | None:
    return preset_ops.craft_plan_rows_from_payload(
        payload,
        catalog=catalog,
        fallback_city=fallback_city,
        fallback_daily_bonus_percent=fallback_daily_bonus_percent,
        normalize_daily_bonus_percent=MarketSetupState._normalize_daily_bonus_percent,
        parse_price=_parse_price,
        parse_float=_parse_float,
        parse_bool=lambda raw_value, default: _parse_bool(raw_value, default=default),
        recipe_display_label=_recipe_display_label,
        recipe_identity=_recipe_identity,
    )


def _base_item_id(item_id: str) -> str:
    return common_ops.base_item_id(item_id)


def _tier_from_item_id(item_id: str) -> int:
    return common_ops.tier_from_item_id(item_id)


def _input_group_rank(item_id: str) -> int:
    return common_ops.input_group_rank(item_id)


def _input_preview_sort_key(row: InputPreviewRow) -> tuple[int, int, str, str, str]:
    return common_ops.input_preview_sort_key(
        row,
        item_family_key=_item_family_key,
    )


def _journal_maps() -> tuple[dict[str, _JournalRule], dict[str, float]]:
    return journal_ops.journal_maps()


def _journal_rule_templates() -> dict[tuple[int, str], _JournalRule]:
    return journal_ops.journal_rule_templates()


def _item_metadata_map() -> dict[str, dict[str, str]]:
    return journal_ops.item_metadata_map()


def _infer_journal_kind_for_item(item_id: str) -> str | None:
    return journal_ops.infer_journal_kind_for_item(item_id)


def _journal_rule_fallback_for_item(item_id: str) -> _JournalRule | None:
    tier = _tier_from_item_id(item_id)
    kind = _infer_journal_kind_for_item(item_id)
    if tier <= 0 or not kind:
        return None
    return _journal_rule_templates().get((tier, kind.upper()))


def _journal_rule_for_item(item_id: str) -> _JournalRule | None:
    journal_by_item, _ = _journal_maps()
    rule = journal_by_item.get(_base_item_id(item_id))
    if rule is not None:
        return rule
    return _journal_rule_fallback_for_item(item_id)


def _journal_fame_factor_for_item(item_id: str) -> float:
    _, fame_factor_by_item = _journal_maps()
    return float(fame_factor_by_item.get(_base_item_id(item_id), 1.0))


def _journal_display_name(kind: str, tier: int) -> str:
    return journal_ops.journal_display_name(kind, tier)


def _friendly_item_label(display_name: str, item_id: str) -> str:
    return recipe_ops.friendly_item_label(display_name, item_id)


def _recipe_identity(recipe: Recipe) -> str:
    return recipe_ops.recipe_identity(recipe)


def _recipe_output_item(recipe: Recipe) -> ItemRef:
    return recipe_ops.recipe_output_item(recipe)


def _recipe_display_label(recipe: Recipe) -> str:
    return recipe_ops.recipe_display_label(recipe)


def _item_family_key(item_id: str) -> str:
    return recipe_ops.item_family_key(item_id)


def _is_recipe_plan_candidate(recipe: Recipe) -> bool:
    return recipe_ops.is_recipe_plan_candidate(recipe)


def _humanize_item_id(item_id: str) -> str:
    return recipe_ops.humanize_item_id(item_id)


def _item_id_candidates(item_id: str) -> tuple[str, ...]:
    return recipe_ops.item_id_candidates(item_id)


def _item_id_query_candidates(item_id: str) -> tuple[str, ...]:
    return recipe_ops.item_id_query_candidates(item_id)


def _mode_has_price(quote: MarketPriceRecord, preferred_mode: str | None) -> bool:
    return common_ops.mode_has_price(quote, preferred_mode)


def _find_price_quote(
    price_index: dict[tuple[str, str, int], MarketPriceRecord],
    *,
    item_id: str,
    city: str,
    quality: int,
    preferred_mode: str | None,
) -> MarketPriceRecord | None:
    return common_ops.find_price_quote(
        price_index,
        item_id=item_id,
        city=city,
        quality=quality,
        preferred_mode=preferred_mode,
        item_id_candidates=_item_id_candidates,
    )


def _parse_iso_datetime(raw_value: str) -> datetime | None:
    return common_ops.parse_iso_datetime(raw_value)


def _result_row_profit_and_margin(*, allocated_cost: float, net_value: float) -> tuple[float, float]:
    return common_ops.result_row_profit_and_margin(
        allocated_cost=allocated_cost,
        net_value=net_value,
    )


def _format_age(updated_at: datetime) -> str:
    return common_ops.format_age(updated_at)


def _need_quantity_with_safety_buffer(quantity_raw: float, is_returnable: bool) -> int:
    return common_ops.need_quantity_with_safety_buffer(quantity_raw, is_returnable)


def _minimal_upfront_quantity_for_batches(batches: Sequence[tuple[float, float]]) -> float:
    return common_ops.minimal_upfront_quantity_for_batches(batches)


def _upfront_return_safety_units(batches: Sequence[tuple[float, float]]) -> int:
    return common_ops.upfront_return_safety_units(batches)


def _input_preview_row_key(item_id: str, city: str, price_type: str) -> str:
    return common_ops.input_preview_row_key(item_id, city, price_type)


def _normalize_int_values(
    values: Sequence[object] | None,
    *,
    minimum: int,
    maximum: int,
) -> list[int]:
    return common_ops.normalize_int_values(
        values,
        minimum=minimum,
        maximum=maximum,
    )
