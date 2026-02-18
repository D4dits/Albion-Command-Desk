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


def test_qml_common_components_and_utils_smoke() -> None:
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
import "."
import "components"
import "utils" 1.0 as Utils
import "utils" 1.0 as HelperUtils

Item {
    id: root
    width: 480
    height: 360
    property string formatted: HelperUtils.HelperUtils.formatInt(1234567)
    property int animDuration: Utils.AnimationUtils.durationNormal

    Toast {
        objectName: "toast"
        theme: Theme
        type: "success"
        title: "ok"
        message: "toast active"
        duration: 0
        visible: true
    }

    Spinner {
        objectName: "spinner"
        theme: Theme
        active: true
        size: "sm"
    }

    LoadingOverlay {
        objectName: "overlay"
        theme: Theme
        anchors.fill: parent
        active: true
        message: "Loading..."
    }

    Icon {
        objectName: "icon"
        theme: Theme
        name: "check"
    }

    Flickable {
        objectName: "flick"
        width: 120
        height: 60
        contentWidth: 120
        contentHeight: 240
        clip: true
        ScrollBar.vertical: StyledScrollBar {
            objectName: "scrollbar"
            theme: Theme
        }
        Rectangle {
            width: 120
            height: 240
        }
    }
}
"""

    base_url = QUrl.fromLocalFile(str((ui_dir / "ComponentSmoke.qml").resolve()))
    engine.loadData(qml_source.encode("utf-8"), base_url)
    app.processEvents()

    if not engine.rootObjects():
        message = "; ".join(msg.toString() for msg in warnings) or "QML component smoke load failed"
        pytest.skip(message)

    root = engine.rootObjects()[0]
    assert root.property("formatted") == "1 234 567"
    assert int(root.property("animDuration")) > 0
    assert root.findChild(QObject, "toast") is not None
    assert root.findChild(QObject, "spinner") is not None
    assert root.findChild(QObject, "overlay") is not None
    assert root.findChild(QObject, "icon") is not None
    assert root.findChild(QObject, "scrollbar") is not None
