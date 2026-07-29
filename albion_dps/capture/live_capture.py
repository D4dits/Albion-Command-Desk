from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
from pathlib import Path
import logging
import math
import os
import shutil
import socket
import subprocess
import threading
import time

from albion_dps.capture.raw_dump import dump_raw
from albion_dps.capture.replay_pcap import read_pcap_stream
from albion_dps.capture.udp_decode import decode_udp_frame, is_photon_packet
from albion_dps.models import RawPacket

try:
    import pcapy
except ImportError:  # pragma: no cover
    pcapy = None

LOGGER = logging.getLogger(__name__)


def capture_backend_available() -> bool:
    return pcapy is not None


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


def rank_interfaces(interfaces: list[str]) -> list[str]:
    return [
        item[1]
        for item in sorted(
            enumerate(interfaces),
            key=lambda item: (_interface_rank(item[1]), item[0]),
        )
    ]


def _interface_rank(interface: str) -> int:
    lowered = str(interface or "").lower()
    if lowered.strip() in {"lo", "lo0"} or "loopback" in lowered or "npf_loopback" in lowered:
        return 90
    if lowered.strip() == "any":
        return 70
    if _looks_virtual_or_secondary(lowered):
        return 80
    if lowered.strip() == "ethernet":
        return 0
    if "ethernet" in lowered:
        return 1
    if lowered.strip() in {"wi-fi", "wifi"}:
        return 2
    if "wi-fi" in lowered or "wifi" in lowered or "wireless" in lowered or "wlan" in lowered:
        return 3
    if lowered.startswith(("wl", "wlp")):
        return 3
    if lowered.startswith(("en", "eth")):
        return 1
    if "lan" in lowered:
        return 4
    return 10


def _looks_virtual_or_secondary(lowered: str) -> bool:
    if "*" in lowered and ("połączenie lokalne" in lowered or "local area connection" in lowered):
        return True
    return any(
        token in lowered
        for token in (
            "bluetooth",
            "docker",
            "hyper-v",
            "isatap",
            "npf_loopback",
            "pseudo",
            "teredo",
            "tunnel",
            "virtual",
            "virtualbox",
            "vmware",
            "vethernet",
        )
    )


def _interface_is_up(interface: str) -> bool:
    operstate = Path("/sys/class/net") / str(interface) / "operstate"
    try:
        return operstate.read_text(encoding="ascii").strip().lower() == "up"
    except OSError:
        return True


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

    permission_denied: list[str] = []
    ranked = rank_interfaces(interfaces)
    for interface in ranked:
        try:
            capture = pcapy.open_live(interface, snaplen, int(promisc), timeout_ms)
            if bpf_filter:
                capture.setfilter(bpf_filter)
        except Exception as exc:
            if _is_permission_error(exc):
                permission_denied.append(interface)
            continue

        if _probe_capture(capture, probe_seconds, max_packets):
            return interface

    if permission_denied and shutil.which("dumpcap"):
        physical = [
            interface
            for interface in permission_denied
            if _interface_rank(interface) < 70
        ]
        physical.sort(key=lambda interface: not _interface_is_up(interface))
        for interface in physical or permission_denied:
            if _probe_interface_with_dumpcap(
                interface,
                bpf_filter=bpf_filter,
                snaplen=snaplen,
                promisc=promisc,
                probe_seconds=probe_seconds,
                max_packets=max_packets,
            ):
                LOGGER.info("Auto-detected %s using dumpcap", interface)
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

    try:
        capture = pcapy.open_live(interface, snaplen, int(promisc), timeout_ms)
    except Exception as exc:
        if _is_permission_error(exc) and shutil.which("dumpcap"):
            LOGGER.info("Using dumpcap backend for live capture on %s", interface)
            yield from _dumpcap_live_capture(
                interface,
                bpf_filter=bpf_filter,
                snaplen=snaplen,
                promisc=promisc,
                dump_raw_dir=dump_raw_dir,
            )
            return
        raise
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


def _is_permission_error(exc: Exception) -> bool:
    detail = str(exc).lower()
    return any(
        token in detail
        for token in ("operation not permitted", "permission denied", "not permitted")
    )


def _dumpcap_live_capture(
    interface: str,
    *,
    bpf_filter: str,
    snaplen: int,
    promisc: bool,
    dump_raw_dir: str | Path | None,
) -> Iterable[RawPacket]:
    dumpcap = shutil.which("dumpcap")
    if not dumpcap:
        raise RuntimeError("Packet capture requires permissions and dumpcap is unavailable")
    command = [
        dumpcap,
        "-q",
        "-P",
        "-i",
        str(interface),
        "-s",
        str(max(1, int(snaplen))),
        "-w",
        "-",
    ]
    if bpf_filter:
        command[2:2] = ["-f", str(bpf_filter)]
    if not promisc:
        command[2:2] = ["-p"]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
    )
    assert process.stdout is not None
    assert process.stderr is not None
    stderr_lines: list[str] = []

    def drain_stderr() -> None:
        for raw_line in iter(process.stderr.readline, b""):
            line = raw_line.decode("utf-8", errors="replace").strip()
            if line:
                stderr_lines.append(line)
                LOGGER.debug("dumpcap: %s", line)

    stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
    stderr_thread.start()
    try:
        for raw in read_pcap_stream(process.stdout):
            if not is_photon_packet(raw):
                continue
            if dump_raw_dir is not None:
                dump_raw(raw, output_dir=dump_raw_dir)
            yield raw
        return_code = process.poll()
        if return_code not in (None, 0):
            detail = stderr_lines[-1] if stderr_lines else f"exit code {return_code}"
            raise RuntimeError(f"dumpcap capture failed: {detail}")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        process.stdout.close()
        process.stderr.close()


def _probe_interface_with_dumpcap(
    interface: str,
    *,
    bpf_filter: str,
    snaplen: int,
    promisc: bool,
    probe_seconds: float,
    max_packets: int,
) -> bool:
    dumpcap = shutil.which("dumpcap")
    if not dumpcap:
        return False
    command = [
        dumpcap,
        "-q",
        "-P",
        "-i",
        str(interface),
        "-s",
        str(max(1, int(snaplen))),
        "-a",
        f"duration:{max(1, math.ceil(probe_seconds))}",
        "-c",
        str(max(1, int(max_packets))),
        "-w",
        "-",
    ]
    if bpf_filter:
        command[2:2] = ["-f", str(bpf_filter)]
    if not promisc:
        command[2:2] = ["-p"]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=max(3.0, float(probe_seconds) + 3.0),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        LOGGER.debug("dumpcap probe failed for %s: %s", interface, exc)
        return False
    if result.returncode != 0 or not result.stdout:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        LOGGER.debug("dumpcap probe failed for %s: %s", interface, detail)
        return False
    try:
        return any(is_photon_packet(raw) for raw in read_pcap_stream(BytesIO(result.stdout)))
    except ValueError as exc:
        LOGGER.debug("Invalid dumpcap probe stream for %s: %s", interface, exc)
        return False


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
