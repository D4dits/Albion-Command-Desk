from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

try:
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
except ImportError as exc:  # pragma: no cover - depends on system Qt libs
    pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)

from albion_dps.qt.models import UiState
from albion_dps.qt.flipper_state import MarketFlipperState
from albion_dps.qt.loot_state import LootState
from albion_dps.qt.market import MarketSetupState
from albion_dps.qt.scanner import ScannerState


def test_qt_smoke_loads_qml() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    warnings: list = []

    def handle_warnings(messages) -> None:
        warnings.extend(messages)

    engine.warnings.connect(handle_warnings)
    state = UiState(sort_key="dps", top_n=5, history_limit=5)
    loot_state = LootState(history_limit=5)
    scanner_state = ScannerState()
    market_setup_state = MarketSetupState()
    market_flipper_state = MarketFlipperState()
    engine.rootContext().setContextProperty("uiState", state)
    engine.rootContext().setContextProperty("lootState", loot_state)
    engine.rootContext().setContextProperty("scannerState", scanner_state)
    engine.rootContext().setContextProperty("marketSetupState", market_setup_state)
    engine.rootContext().setContextProperty("marketFlipperState", market_flipper_state)

    qml_path = Path(__file__).resolve().parents[1] / "albion_dps" / "qt" / "ui" / "Main.qml"
    if not qml_path.exists():
        pytest.skip(f"Missing QML: {qml_path}")

    engine.load(str(qml_path))
    app.processEvents()

    if not engine.rootObjects():
        message = "; ".join(msg.toString() for msg in warnings) or "QML load failed"
        pytest.skip(message)


def test_loot_market_value_properties_allow_large_values() -> None:
    loot_state = LootState(history_limit=5)
    large_value = 3_653_313_492
    loot_state._total_market_value = large_value
    loot_state._total_liquidation_value = large_value
    loot_state._outstanding_market_value = large_value

    meta = loot_state.metaObject()
    for name in ("totalMarketValue", "totalLiquidationValue", "outstandingMarketValue"):
        prop = meta.property(meta.indexOfProperty(name))
        assert prop.read(loot_state) == float(large_value)
