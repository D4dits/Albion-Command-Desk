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


def test_loot_tab_qml_loads() -> None:
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

LootTab {
    width: 1120
    height: 760
    theme: Theme
    compactLayout: false
    eventCount: 2
    totalQuantity: 3
    uniqueLooters: 2
    uniqueItems: 2
    latestLootSummary: "Alice looted 2x Journeyman's Bag from Enemy"
    logPath: "artifacts/loot/loot-events-2026-04-10-12-34-56.txt"
    logDirectoryUrl: "file:///C:/Users/Users/Documents/DPS_Master/DPS_Meter_AO/artifacts/loot"
    searchQuery: ""
    sourceFilter: "all"
    sourceFilterOptions: ["all", "player", "mob", "silver", "system"]
    eventsModel: ListModel {
        ListElement {
            timestampText: "01:01:01"
            lootedByName: "Alice"
            lootedByGuild: "Guild A"
            lootedByAlliance: "AAA"
            itemId: "T3_BAG"
            itemName: "Journeyman's Bag"
            quantity: 2
            sourceName: "Enemy"
            sourceKind: "player"
            isSilver: false
            summary: "Alice looted 2x Journeyman's Bag from Enemy"
        }
    }
    topLootersModel: ListModel {
        ListElement { label: "Alice"; sublabel: "Guild A"; quantity: 2; eventCount: 1 }
    }
    topItemsModel: ListModel {
        ListElement { label: "Journeyman's Bag"; sublabel: "T3_BAG"; quantity: 2; eventCount: 1 }
    }
}
"""

    base_url = QUrl.fromLocalFile(str((ui_dir / "LootTabSmoke.qml").resolve()))
    engine.loadData(qml_source.encode("utf-8"), base_url)
    app.processEvents()

    assert engine.rootObjects(), "; ".join(msg.toString() for msg in warnings) or "LootTab QML load failed"
