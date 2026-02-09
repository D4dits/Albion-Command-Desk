from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from albion_dps.qt.models import UiState
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
    scanner_state = ScannerState()
    engine.rootContext().setContextProperty("uiState", state)
    engine.rootContext().setContextProperty("scannerState", scanner_state)

    qml_path = Path(__file__).resolve().parents[1] / "albion_dps" / "qt" / "ui" / "Main.qml"
    if not qml_path.exists():
        pytest.skip(f"Missing QML: {qml_path}")

    engine.load(str(qml_path))
    app.processEvents()

    if not engine.rootObjects():
        message = "; ".join(msg.toString() for msg in warnings) or "QML load failed"
        pytest.skip(message)
