from __future__ import annotations

import pytest
import time
import os

pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication

from albion_dps.market.aod_client import MarketPriceRecord
from albion_dps.market.catalog import RecipeCatalog
from albion_dps.market.models import ItemRef, Recipe, RecipeOutput
from albion_dps.qt.flipper_state import MarketFlipperState


class FakeService:
    def __init__(self, price_index):
        self.price_index = price_index
        self.last_prices_meta = type("Meta", (), {"source": "live"})()
        self.calls = []

    def get_price_index(self, **kwargs):
        self.calls.append(kwargs)
        return self.price_index


def _record(item_id: str, city: str, *, sell: int = 0, buy: int = 0) -> MarketPriceRecord:
    return MarketPriceRecord(
        item_id=item_id,
        city=city,
        quality=1,
        sell_price_min=sell,
        buy_price_max=buy,
        sell_price_min_date="2099-05-19T10:30:00Z",
        buy_price_max_date="2099-05-19T11:30:00Z",
    )


def _catalog() -> RecipeCatalog:
    item = ItemRef(unique_name="T4_MAIN_SWORD", display_name="Broadsword", tier=4, enchantment=0)
    return RecipeCatalog(
        recipes={
            "T4_MAIN_SWORD": Recipe(
                item=item,
                station="warrior",
                outputs=(RecipeOutput(item=item, quantity=1),),
                recipe_id="T4_MAIN_SWORD",
            )
        }
    )


def _many_bow_catalog(count: int = 120) -> RecipeCatalog:
    recipes = {}
    for idx in range(count):
        tier = 4 + (idx % 5)
        enchant = idx % 5
        suffix = f"_{idx}"
        item = ItemRef(
            unique_name=f"T{tier}_2H_BOW{suffix}" + (f"@{enchant}" if enchant else ""),
            display_name=f"Bow {idx}",
            tier=tier,
            enchantment=enchant,
        )
        recipes[item.unique_name] = Recipe(
            item=item,
            station="bow",
            outputs=(RecipeOutput(item=item, quantity=1),),
            recipe_id=item.unique_name,
        )
    return RecipeCatalog(recipes=recipes)


def test_flipper_state_refresh_builds_profitable_rows() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QGuiApplication.instance() or QGuiApplication([])
    service = FakeService(
        {
            ("T4_MAIN_SWORD", "Caerleon", 1): _record("T4_MAIN_SWORD", "Caerleon", sell=10_000),
            ("T4_MAIN_SWORD", "Black Market", 1): _record("T4_MAIN_SWORD", "Black Market", buy=30_000),
        }
    )
    state = MarketFlipperState(service=service, catalog=_catalog())
    state.setSearchQuery("sword")
    state.setMinProfit(0)
    state.setMinRoiPercent(0)

    state.refreshFlips()
    _wait_for(lambda: not state.refreshInProgress)

    model = state.resultsModel
    assert model.rowCount() == 1
    idx = model.index(0, 0)
    assert model.data(idx, model.ItemIdRole) == "T4_MAIN_SWORD"
    assert model.data(idx, model.ValidRole) is True
    assert state.validCount == 1
    assert service.calls[0]["locations"] == ["Caerleon", "Black Market"]
    assert service.calls[0]["qualities"] == [1, 2, 3, 4, 5]
    assert service.calls[0]["allow_stale"] is False
    assert service.calls[0]["ttl_seconds"] == 30.0


def test_flipper_state_uses_selected_source_city() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QGuiApplication.instance() or QGuiApplication([])
    service = FakeService(
        {
            ("T4_MAIN_SWORD", "Martlock", 1): _record("T4_MAIN_SWORD", "Martlock", sell=10_000),
            ("T4_MAIN_SWORD", "Black Market", 1): _record("T4_MAIN_SWORD", "Black Market", buy=30_000),
        }
    )
    state = MarketFlipperState(service=service, catalog=_catalog())
    state.setSearchQuery("sword")
    state.setSourceCity("Martlock")
    state.setMinProfit(0)
    state.setMinRoiPercent(0)

    state.refreshFlips()
    _wait_for(lambda: not state.refreshInProgress)

    assert service.calls[0]["locations"] == ["Martlock", "Black Market"]
    assert state.validCount == 1


def test_flipper_state_checked_rows_update_selected_profit() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QGuiApplication.instance() or QGuiApplication([])
    service = FakeService(
        {
            ("T4_MAIN_SWORD", "Caerleon", 1): _record("T4_MAIN_SWORD", "Caerleon", sell=10_000),
            ("T4_MAIN_SWORD", "Black Market", 1): _record("T4_MAIN_SWORD", "Black Market", buy=30_000),
        }
    )
    state = MarketFlipperState(service=service, catalog=_catalog())
    state.setSearchQuery("sword")
    state.setMinProfit(0)
    state.setMinRoiPercent(0)
    state.refreshFlips()
    _wait_for(lambda: not state.refreshInProgress)

    model = state.resultsModel
    row_key = str(model.data(model.index(0, 0), model.RowKeyRole))
    state.setRowChecked(row_key, True)

    assert state.selectedTotalProfit > 0


def test_flipper_state_empty_search_runs_broad_scan() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QGuiApplication.instance() or QGuiApplication([])
    service = FakeService({})
    state = MarketFlipperState(service=service, catalog=_many_bow_catalog())

    state.refreshFlips()
    _wait_for(lambda: not state.refreshInProgress)

    assert service.calls
    assert state.resultsModel.rowCount() == 120
    assert "broad market scan" in state.refreshStatusText
    queried = service.calls[0]["item_ids"]
    assert any(item_id.startswith("T4_") for item_id in queried)
    assert any(item_id.startswith("T8_") for item_id in queried)


def test_flipper_state_search_scans_beyond_first_t4_page() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QGuiApplication.instance() or QGuiApplication([])
    service = FakeService({})
    state = MarketFlipperState(service=service, catalog=_many_bow_catalog())
    state.setSearchQuery("bow")

    state.refreshFlips()
    _wait_for(lambda: not state.refreshInProgress)

    assert state.resultsModel.rowCount() == 120
    queried = service.calls[0]["item_ids"]
    assert any(item_id.startswith("T8_") for item_id in queried)


def _wait_for(predicate, timeout: float = 3.0) -> None:
    app = QGuiApplication.instance()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        if app is not None:
            app.processEvents()
        time.sleep(0.01)
    raise AssertionError("timed out waiting for flipper refresh")
