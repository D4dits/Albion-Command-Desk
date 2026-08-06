from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
except ImportError as exc:  # pragma: no cover - depends on system Qt libs
    pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)


def test_market_tab_qml_loads_at_minimum_window_width() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    warnings: list = []

    def handle_warnings(messages) -> None:
        warnings.extend(messages)

    engine.warnings.connect(handle_warnings)

    ui_dir = Path(__file__).resolve().parents[1] / "albion_dps" / "qt" / "ui"
    qml_source = """
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

MarketTab {
    width: 1120
    height: 760
    theme: Theme
    region: "europe"
    validationText: "Status: ok"
    pricesSource: "live"
    listActionText: ""
    pricesStatusText: "Ready"
    diagnosticsText: "Diagnostics"
    inputsModel: ListModel {
        ListElement {
            item: "Metal Bar"
            itemId: "T4_METALBAR"
            quantity: 16
            stockQuantity: 0
            buyQuantity: 16
            city: "Bridgewatch"
            priceType: "sell_order"
            manualPrice: 0
            unitPrice: 100
            priceAgeText: "5m"
            totalCost: 1600
        }
    }
    outputsModel: ListModel {
        ListElement {
            item: "Broadsword"
            itemId: "T4_MAIN_SWORD"
            quantity: 1
            city: "Bridgewatch"
            priceType: "sell_order"
            manualPrice: 0
            unitPrice: 2500
            priceAgeText: "5m"
            totalValue: 2500
            feeValue: 100
            taxValue: 200
            netValue: 2200
        }
    }
    resultsItemsModel: ListModel {
        ListElement {
            item: "Broadsword"
            itemId: "T4_MAIN_SWORD"
            city: "Bridgewatch"
            quantity: 1
            revenue: 2500
            cost: 1600
            feeValue: 100
            taxValue: 200
            profit: 600
            marginPercent: 37.5
            demandProxy: 0.0
        }
    }
}
"""

    base_url = QUrl.fromLocalFile(str((ui_dir / "MarketTabSmoke.qml").resolve()))
    engine.loadData(qml_source.encode("utf-8"), base_url)
    app.processEvents()

    assert engine.rootObjects(), "; ".join(msg.toString() for msg in warnings) or "MarketTab QML load failed"
    root = engine.rootObjects()[0]
    assert root.property("marketSetupStackedLayout") is False
    assert int(root.property("marketSetupPanelActiveWidth")) == int(root.property("marketSetupPanelWidth"))


def test_market_setup_sell_city_includes_black_market() -> None:
    ui_dir = Path(__file__).resolve().parents[1] / "albion_dps" / "qt" / "ui"
    source = (ui_dir / "MarketSetupPanel.qml").read_text(encoding="utf-8")

    sell_city_section = source.split('Text { text: "Sell City"', maxsplit=1)[1]
    sell_city_section = sell_city_section.split('Text { text: "Default Runs"', maxsplit=1)[0]

    assert '"Black Market"' in sell_city_section


def test_market_loading_overlay_does_not_block_cached_rows() -> None:
    ui_dir = Path(__file__).resolve().parents[1] / "albion_dps" / "qt" / "ui"
    source = (ui_dir / "MarketTab.qml").read_text(encoding="utf-8")

    overlay_section = source.split("visible: root.priceFetchPending", maxsplit=1)[1]
    overlay_section = overlay_section.split("z: 200", maxsplit=1)[0]

    assert "root.inputsModel.count === 0" in overlay_section
    assert "root.outputsModel.count === 0" in overlay_section
    assert "root.resultsItemsModel.count === 0" in overlay_section
