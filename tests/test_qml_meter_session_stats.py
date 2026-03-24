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


def test_meter_session_stats_qml_loads_in_narrow_width() -> None:
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

MeterSessionStatsPanel {
    width: 220
    height: 160
    theme: Theme
    fameText: "43094"
    famePerHourText: "160400"
    silverText: "2322"
    silverPerHourText: "116974"
}
"""

    base_url = QUrl.fromLocalFile(str((ui_dir / "MeterSessionStatsSmoke.qml").resolve()))
    engine.loadData(qml_source.encode("utf-8"), base_url)
    app.processEvents()

    assert engine.rootObjects(), "; ".join(msg.toString() for msg in warnings) or "MeterSessionStatsPanel QML load failed"
