from __future__ import annotations

import json
import logging

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtWebSockets import QWebSocket

from albion_dps.market.models import MarketRegion
from albion_dps.market.price_store import LocalMarketPriceStore


class MarketScannerWebSocketBridge(QObject):
    def __init__(
        self,
        *,
        store: LocalMarketPriceStore,
        region: MarketRegion = MarketRegion.EUROPE,
        url: str = "ws://127.0.0.1:8099/ws",
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()
        self._store = store
        self._region = region
        self._url = str(url)
        self._log = logger or logging.getLogger(__name__)
        self._socket = QWebSocket()
        self._connected = False
        self._started = False
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(5000)
        self._reconnect_timer.timeout.connect(self._connect)
        self._cleanup_timer = QTimer(self)
        self._cleanup_timer.setInterval(5 * 60 * 1000)
        self._cleanup_timer.timeout.connect(self._cleanup)

        self._socket.connected.connect(self._on_connected)
        self._socket.disconnected.connect(self._on_disconnected)
        self._socket.textMessageReceived.connect(self._on_text_message)
        self._socket.errorOccurred.connect(self._on_error)

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._cleanup_timer.start()
        self._connect()

    def stop(self) -> None:
        self._started = False
        self._reconnect_timer.stop()
        self._cleanup_timer.stop()
        self._socket.close()

    def _connect(self) -> None:
        if not self._started or self._connected:
            return
        request = QNetworkRequest(QUrl(self._url))
        request.setRawHeader(b"Origin", b"http://localhost")
        self._socket.open(request)

    def _on_connected(self) -> None:
        self._connected = True
        self._reconnect_timer.stop()
        self._log.info("Connected to local Albion Data websocket for market capture.")

    def _on_disconnected(self) -> None:
        was_connected = self._connected
        self._connected = False
        if was_connected:
            self._log.info("Local Albion Data websocket disconnected.")
        if self._started and not self._reconnect_timer.isActive():
            self._reconnect_timer.start()

    def _on_error(self, _error) -> None:
        if self._started and not self._reconnect_timer.isActive():
            self._reconnect_timer.start()

    def _on_text_message(self, message: str) -> None:
        for line in str(message or "").splitlines():
            self._handle_message(line)

    def _handle_message(self, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return
        topic = str(payload.get("topic") or "")
        if topic != "marketorders.ingest":
            return
        stored = self._store.upsert_scanner_payload(
            region=self._region,
            payload=payload.get("data"),
            source="scanner_ws",
        )
        if stored:
            self._log.debug("Stored %d local scanner market quote(s).", stored)

    def _cleanup(self) -> None:
        removed = self._store.clear_old_quotes()
        if removed:
            self._log.debug("Removed %d stale local market quote(s).", removed)
