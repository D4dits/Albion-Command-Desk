from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

try:
    from PySide6.QtCore import QObject, QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
except ImportError as exc:  # pragma: no cover - depends on system Qt libs
    pytest.skip(f"Qt runtime unavailable: {exc}", allow_module_level=True)


def test_meter_tab_qml_loads_in_compact_width() -> None:
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

MeterTab {
    width: 980
    height: 720
    theme: Theme
    mode: "battle"
    sortKey: "dps"
    selectedHistoryIndex: 0
    playersModel: ListModel {
        ListElement {
            name: "D4dits"
            damage: 100
            heal: 0
            dps: 10.0
            hps: 0.0
            barRatio: 1.0
            role: "dps"
            barColor: "#ea5d5d"
            weaponName: "Sword"
            weaponTier: "T6.1"
            weaponIcon: ""
        }
    }
    historyModel: ListModel {
        ListElement {
            label: "battle 00:20"
            meta: "total dmg 100 heal 0 | players 1"
            players: "D4dits dmg 100 dps 10.0"
            copyText: "copy"
            selected: false
        }
    }
}
"""

    base_url = QUrl.fromLocalFile(str((ui_dir / "MeterTabSmoke.qml").resolve()))
    engine.loadData(qml_source.encode("utf-8"), base_url)
    app.processEvents()

    assert engine.rootObjects(), "; ".join(msg.toString() for msg in warnings) or "MeterTab QML load failed"
    root = engine.rootObjects()[0]
    chart = root.findChild(QObject, "meterHistoryChart")
    assert chart is not None
    assert chart.property("visible") is True
