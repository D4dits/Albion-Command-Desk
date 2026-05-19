from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
except ImportError as exc:  # pragma: no cover
    pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)


def test_flipper_tab_qml_loads_at_minimum_window_width() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    warnings: list = []
    engine.warnings.connect(lambda messages: warnings.extend(messages))

    ui_dir = Path(__file__).resolve().parents[1] / "albion_dps" / "qt" / "ui"
    qml_source = """
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

FlipperTab {
    width: 1120
    height: 760
    theme: Theme
    region: "europe"
    sourceCity: "Caerleon"
    quality: 1
    minProfit: 10000
    minRoiPercent: 5
    riskBufferPercent: 0
    saleTaxPercent: 4
    refreshStatusText: "Ready"
    pricesSource: "live"
    resultsCount: 1
    validCount: 1
    missingCount: 0
    selectedTotalProfit: 18000
    resultsModel: ListModel {
        ListElement {
            rowKey: "T4_MAIN_SWORD|1|Caerleon|Black Market"
            itemId: "T4_MAIN_SWORD"
            itemName: "Broadsword"
            tier: 4
            enchant: 0
            quality: 1
            sourceCity: "Caerleon"
            targetCity: "Black Market"
            sourceSellPrice: 10000
            sourceAgeText: "10m"
            blackMarketBuyPrice: 30000
            blackMarketAgeText: "5m"
            taxValue: 1200
            bufferValue: 0
            netProfit: 18800
            roiPercent: 188.0
            valid: true
            staleReason: ""
            checked: false
        }
    }
}
"""
    base_url = QUrl.fromLocalFile(str((ui_dir / "FlipperTabSmoke.qml").resolve()))
    engine.loadData(qml_source.encode("utf-8"), base_url)
    app.processEvents()

    assert engine.rootObjects(), "; ".join(msg.toString() for msg in warnings) or "FlipperTab QML load failed"
