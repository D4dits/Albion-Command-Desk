from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import socket
import struct
import threading
from dataclasses import dataclass
from urllib.parse import urlparse

from albion_dps.market.local_store import LocalMarketStore, parse_market_upload_message
from albion_dps.market.models import MarketRegion


@dataclass(frozen=True)
class LocalIngestSnapshot:
    running: bool
    connected: bool
    messages_seen: int
    orders_stored: int
    last_error: str


class MarketWebSocketIngestor:
    def __init__(
        self,
        *,
        store: LocalMarketStore,
        url: str = "ws://127.0.0.1:8099/ws",
        origin: str = "http://127.0.0.1",
        region: MarketRegion = MarketRegion.EUROPE,
        reconnect_seconds: float = 2.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._store = store
        self._url = url
        self._origin = origin
        self._region = region
        self._reconnect_seconds = max(0.2, float(reconnect_seconds))
        self._log = logger or logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._connected = False
        self._messages_seen = 0
        self._orders_stored = 0
        self._last_error = ""

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="market-local-ingest", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive() and self._thread is not threading.current_thread():
            self._thread.join(timeout=1.0)

    def snapshot(self) -> LocalIngestSnapshot:
        with self._lock:
            return LocalIngestSnapshot(
                running=bool(self._thread and self._thread.is_alive()),
                connected=self._connected,
                messages_seen=self._messages_seen,
                orders_stored=self._orders_stored,
                last_error=self._last_error,
            )

    def _run(self) -> None:
        while not self._stop_event.is_set():
            sock: socket.socket | None = None
            try:
                sock = _connect_websocket(self._url, origin=self._origin, timeout=5.0)
                self._set_connected(True, "")
                self._read_loop(sock)
            except Exception as exc:
                self._set_connected(False, str(exc))
                self._log.debug("Local market ingest websocket disconnected: %s", exc)
            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass
                self._set_connected(False, self._last_error)
            if not self._stop_event.wait(self._reconnect_seconds):
                continue

    def _read_loop(self, sock: socket.socket) -> None:
        while not self._stop_event.is_set():
            frame = _read_frame(sock)
            if frame.opcode == 0x8:
                return
            if frame.opcode == 0x9:
                _send_frame(sock, 0xA, frame.payload)
                continue
            if frame.opcode != 0x1:
                continue
            text = frame.payload.decode("utf-8", errors="replace")
            for part in text.splitlines():
                self._handle_message(part)

    def _handle_message(self, text: str) -> None:
        try:
            upload = parse_market_upload_message(text)
        except json.JSONDecodeError:
            return
        if upload is None:
            return
        stats = self._store.upsert_market_upload(upload, region=self._region)
        with self._lock:
            self._messages_seen += 1
            self._orders_stored += stats.orders_stored

    def _set_connected(self, value: bool, error: str) -> None:
        with self._lock:
            self._connected = value
            if error:
                self._last_error = error


@dataclass(frozen=True)
class _Frame:
    opcode: int
    payload: bytes


def _connect_websocket(url: str, *, origin: str, timeout: float) -> socket.socket:
    parsed = urlparse(url)
    if parsed.scheme != "ws":
        raise ValueError(f"Only ws:// websocket URLs are supported: {url}")
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 80
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    sock = socket.create_connection((host, port), timeout=timeout)
    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        f"Origin: {origin}\r\n"
        "\r\n"
    )
    sock.sendall(request.encode("ascii"))
    response = _read_http_headers(sock)
    if " 101 " not in response.split("\r\n", 1)[0]:
        raise ConnectionError(f"WebSocket handshake failed: {response.splitlines()[0] if response else 'empty response'}")
    accept = _header_value(response, "Sec-WebSocket-Accept")
    expected = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()).decode("ascii")
    if accept != expected:
        raise ConnectionError("WebSocket handshake returned invalid accept key")
    return sock


def _read_http_headers(sock: socket.socket) -> str:
    chunks: list[bytes] = []
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
        data = b"".join(chunks)
        if len(data) > 65536:
            raise ConnectionError("WebSocket handshake response is too large")
    return data.decode("iso-8859-1", errors="replace")


def _header_value(response: str, name: str) -> str:
    prefix = name.lower() + ":"
    for line in response.split("\r\n")[1:]:
        if line.lower().startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _read_frame(sock: socket.socket) -> _Frame:
    first = _recv_exact(sock, 2)
    b1, b2 = first[0], first[1]
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    length = b2 & 0x7F
    if length == 126:
        length = struct.unpack("!H", _recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact(sock, 8))[0]
    mask = _recv_exact(sock, 4) if masked else b""
    payload = _recv_exact(sock, length) if length else b""
    if masked:
        payload = bytes(byte ^ mask[idx % 4] for idx, byte in enumerate(payload))
    return _Frame(opcode=opcode, payload=payload)


def _send_frame(sock: socket.socket, opcode: int, payload: bytes = b"") -> None:
    payload = payload or b""
    header = bytearray([0x80 | (opcode & 0x0F)])
    length = len(payload)
    if length < 126:
        header.append(0x80 | length)
    elif length <= 0xFFFF:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", length))
    mask = os.urandom(4)
    header.extend(mask)
    masked = bytes(byte ^ mask[idx % 4] for idx, byte in enumerate(payload))
    sock.sendall(bytes(header) + masked)


def _recv_exact(sock: socket.socket, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("WebSocket connection closed")
        data.extend(chunk)
    return bytes(data)
