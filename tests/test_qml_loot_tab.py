from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickItem
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
    itemEventCount: 2
    itemTotalQuantity: 3
    silverEventCount: 0
    silverTotalQuantity: 0
    uniqueLooters: 2
    uniqueItems: 2
    importedLogActive: false
    latestLootSummary: "Alice looted 2x Journeyman's Bag from Enemy"
    logPath: "artifacts/loot/loot-events-2026-04-10-12-34-56.txt"
    logDirectoryUrl: "file:///C:/Users/Users/Documents/DPS_Master/DPS_Meter_AO/artifacts/loot"
    searchQuery: ""
    sourceFilter: "all"
    sourceNameFilter: ""
    looterFilter: "all"
    categoryFilter: "all"
    kindFilter: "items"
    sourceFilterOptions: ["all", "player", "mob", "system"]
    looterFilterOptions: ["all", "Alice"]
    categoryFilterOptions: ["all", "weapon", "armor", "bag", "cape", "mount", "consumable", "resource", "artifact", "other"]
    kindFilterOptions: ["items"]
    eventsModel: ListModel {
        ListElement {
            timestampText: "01:01:01"
            lootedByName: "Alice"
            lootedByGuild: "Guild A"
            lootedByAlliance: "AAA"
            itemId: "T3_BAG"
                itemName: "Journeyman's Bag"
                iconUrl: "https://render.albiononline.com/v1/item/T3_BAG?size=64"
                category: "bag"
                eventId: "event-1"
                qualityText: "Q1"
                quantity: 2
                marketValue: 1000
                valueEstimated: false
                settlementStatus: "pending"
                outstandingQuantity: 2
                eligibilityReason: "party"
                sourceName: "Enemy"
            sourceKind: "player"
            isSilver: false
            summary: "Alice looted 2x Journeyman's Bag from Enemy"
        }
        }
        topLootersModel: ListModel {
            ListElement { label: "Alice"; sublabel: "Guild A"; iconUrl: ""; quantity: 2; eventCount: 1; marketValue: 1000; liquidationValue: 800; outstandingValue: 1000 }
    }
    topItemsModel: ListModel {
        ListElement { label: "Journeyman's Bag"; sublabel: "T3_BAG"; iconUrl: "https://render.albiononline.com/v1/item/T3_BAG?size=64"; quantity: 2; eventCount: 1 }
    }
    topSourcesModel: ListModel {
        ListElement { label: "Enemy"; sublabel: "looted from player"; iconUrl: ""; quantity: 2; eventCount: 1 }
    }
    topSilverLootersModel: ListModel {
    }
}
"""

    base_url = QUrl.fromLocalFile(str((ui_dir / "LootTabSmoke.qml").resolve()))
    engine.loadData(qml_source.encode("utf-8"), base_url)
    app.processEvents()

    assert engine.rootObjects(), "; ".join(msg.toString() for msg in warnings) or "LootTab QML load failed"
    root = engine.rootObjects()[0]

    def find_visual(item: QQuickItem, name: str) -> QQuickItem | None:
        for child in item.childItems():
            if child.objectName() == name:
                return child
            found = find_visual(child, name)
            if found is not None:
                return found
        return None

    for header_name, row_name in (
        ("lootHeaderQuality", "lootRowQuality"),
        ("lootHeaderQuantity", "lootRowQuantity"),
        ("lootHeaderValue", "lootRowValue"),
        ("lootHeaderStatus", "lootRowStatus"),
    ):
        header = find_visual(root, header_name)
        row = find_visual(root, row_name)
        assert header is not None
        assert row is not None
        assert abs(float(header.property("x")) - float(row.property("x"))) <= 1
        assert float(header.property("width")) == float(row.property("width"))

    root.setProperty("activeView", 1)
    app.processEvents()
    players_header = find_visual(root, "playersHeaderItems")
    players_row = find_visual(root, "playersRowItems")
    assert players_header is not None
    assert players_row is not None
    assert abs(float(players_header.property("x")) - float(players_row.property("x"))) <= 1
    assert float(players_header.property("width")) == float(players_row.property("width"))
