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


@pytest.mark.parametrize(
    ("component_name", "qml_source"),
    [
        (
            "SettingsTabSmoke.qml",
            """
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

SettingsTab {
    width: 1180
    height: 760
    theme: Theme
    updateCheckStatus: "Up to date"
    updateAutoCheck: true
    scannerRepoDir: "C:/repo/albiondata-client"
    scannerRepoUrl: "https://github.com/ao-data/albiondata-client"
    appLogLevel: "INFO"
    configDir: "C:/Users/test/AppData/Local/AlbionCommandDesk"
    captureRuntimeState: "available"
    captureRuntimeDetail: "Found wpcap.dll"
    gitAvailable: true
    gitDetail: "Git detected in PATH"
    gameDataReady: true
    gameDataDetail: "Local game databases are present."
    gameDataRoot: "C:/Games/Albion Online"
}
""",
        ),
        (
            "HelpTabSmoke.qml",
            """
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

HelpTab {
    width: 1180
    height: 760
    theme: Theme
    appVersion: "0.1.19"
    updateCheckStatus: "Up to date"
    configDir: "C:/Users/test/AppData/Local/AlbionCommandDesk"
    captureRuntimeState: "available"
    gitDetail: "Git detected in PATH"
    gameDataDetail: "Local game databases are present."
}
""",
        ),
    ],
)
def test_settings_and_help_tabs_qml_load(component_name: str, qml_source: str) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    warnings: list = []

    def handle_warnings(messages) -> None:
        warnings.extend(messages)

    engine.warnings.connect(handle_warnings)

    ui_dir = Path(__file__).resolve().parents[1] / "albion_dps" / "qt" / "ui"
    base_url = QUrl.fromLocalFile(str((ui_dir / component_name).resolve()))
    engine.loadData(qml_source.encode("utf-8"), base_url)
    app.processEvents()

    assert engine.rootObjects(), "; ".join(msg.toString() for msg in warnings) or f"{component_name} QML load failed"
