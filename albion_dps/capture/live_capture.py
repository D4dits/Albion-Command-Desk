from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import logging
import socket
import time

from albion_dps.capture.raw_dump import dump_raw
from albion_dps.capture.udp_decode import decode_udp_frame, is_photon_packet
from albion_dps.models import RawPacket

try:
    import pcapy
except ImportError:  # pragma: no cover
    pcapy = None

LOGGER = logging.getLogger(__name__)


def _system_interfaces() -> list[str]:
    try:
        return [name for _, name in socket.if_nameindex()]
    except Exception:
        return []


def list_interfaces() -> list[str]:
    if pcapy is None:  # pragma: no cover
        raise RuntimeError("pcapy is required for live capture (install pcapy or pcapy-ng)")
    try:
        return pcapy.findalldevs()
    except Exception as exc:
        LOGGER.warning("pcapy.findalldevs failed (%s); falling back to system interfaces", exc)
        return _system_interfaces()


def auto_detect_interface(
    *,
    bpf_filter: str = "(ip or ip6) and udp",
    snaplen: int = 65535,
    promisc: bool = False,
    timeout_ms: int = 1000,
    probe_seconds: float = 2.0,
    max_packets: int = 5,
) -> str | None:
    if pcapy is None:  # pragma: no cover
        raise RuntimeError("pcapy is required for live capture (install pcapy or pcapy-ng)")

    try:
        interfaces = pcapy.findalldevs()
    except Exception as exc:
        LOGGER.warning("pcapy.findalldevs failed (%s); falling back to system interfaces", exc)
        interfaces = _system_interfaces()
    if not interfaces:
        return None
    if len(interfaces) == 1:
        return interfaces[0]

    for interface in interfaces:
        try:
            capture = pcapy.open_live(interface, snaplen, int(promisc), timeout_ms)
            if bpf_filter:
                capture.setfilter(bpf_filter)
        except Exception:
            continue

        if _probe_capture(capture, probe_seconds, max_packets):
            return interface

    return None


def live_capture(
    interface: str,
    *,
    bpf_filter: str = "(ip or ip6) and udp",
    snaplen: int = 65535,
    promisc: bool = False,
    timeout_ms: int = 1000,
    dump_raw_dir: str | Path | None = None,
) -> Iterable[RawPacket]:
    if pcapy is None:  # pragma: no cover
        raise RuntimeError("pcapy is required for live capture (install pcapy or pcapy-ng)")

    capture = pcapy.open_live(interface, snaplen, int(promisc), timeout_ms)
    if bpf_filter:
        capture.setfilter(bpf_filter)

    while True:
        header, frame = _next_capture(capture)
        if header is None or frame is None:
            continue
        ts_sec, ts_subsec = header.getts()
        timestamp = ts_sec + ts_subsec / 1_000_000
        raw = decode_udp_frame(frame, timestamp)
        if raw is None or not is_photon_packet(raw):
            continue
        if dump_raw_dir is not None:
            dump_raw(raw, output_dir=dump_raw_dir)
        yield raw


def _probe_capture(capture: object, probe_seconds: float, max_packets: int) -> bool:
    deadline = time.monotonic() + probe_seconds
    seen = 0
    while time.monotonic() < deadline and seen < max_packets:
        header, frame = _next_capture(capture)
        if header is None or frame is None:
            continue
        seen += 1
        ts_sec, ts_subsec = header.getts()
        timestamp = ts_sec + ts_subsec / 1_000_000
        raw = decode_udp_frame(frame, timestamp)
        if raw is not None and is_photon_packet(raw):
            return True
    return False


def _next_capture(capture: object) -> tuple[object | None, object | None]:
    try:
        if hasattr(capture, "next"):
            return capture.next()
    except Exception:
        return None, None
    try:
        return next(capture)
    except Exception:
        return None, None
