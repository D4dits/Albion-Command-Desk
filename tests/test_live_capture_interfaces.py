from __future__ import annotations

import importlib

from albion_dps.capture.live_capture import auto_detect_interface, live_capture, rank_interfaces
from albion_dps.models import RawPacket
from albion_dps.qt import runner


live_capture_module = importlib.import_module("albion_dps.capture.live_capture")


def test_rank_interfaces_prefers_physical_adapters_before_windows_local_star() -> None:
    ranked = rank_interfaces(
        [
            "Połączenie lokalne* 8",
            "Połączenie lokalne* 7",
            "Ethernet 3",
            "Ethernet",
            r"\Device\NPF_Loopback",
        ]
    )

    assert ranked[:2] == ["Ethernet", "Ethernet 3"]
    assert ranked[-1] == r"\Device\NPF_Loopback"


def test_runner_fallback_prefers_ranked_physical_interface(monkeypatch) -> None:
    monkeypatch.setattr(
        runner,
        "list_interfaces",
        lambda: [
            "Połączenie lokalne* 8",
            "Połączenie lokalne* 7",
            "Ethernet",
            r"\Device\NPF_Loopback",
        ],
    )

    assert runner._fallback_interface() == "Ethernet"


def test_live_capture_uses_dumpcap_when_pcapy_lacks_permission(monkeypatch) -> None:
    class _Pcapy:
        @staticmethod
        def open_live(*_args):
            raise RuntimeError("socket: Operation not permitted")

    expected = RawPacket(1.0, "10.0.0.1", 5055, "10.0.0.2", 5056, b"\xfe\x00\x00")
    monkeypatch.setattr(live_capture_module, "pcapy", _Pcapy())
    monkeypatch.setattr(live_capture_module.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        live_capture_module,
        "_dumpcap_live_capture",
        lambda *_args, **_kwargs: iter([expected]),
    )

    assert list(live_capture("wlp3s0")) == [expected]


def test_auto_detect_uses_dumpcap_probe_when_pcapy_lacks_permission(monkeypatch) -> None:
    class _Pcapy:
        @staticmethod
        def findalldevs():
            return ["wlp3s0", "enp2s0", "lo"]

        @staticmethod
        def open_live(*_args):
            raise RuntimeError("socket: Operation not permitted")

    probed: list[str] = []
    monkeypatch.setattr(live_capture_module, "pcapy", _Pcapy())
    monkeypatch.setattr(live_capture_module.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        live_capture_module,
        "_interface_is_up",
        lambda interface: interface == "wlp3s0",
    )
    monkeypatch.setattr(
        live_capture_module,
        "_probe_interface_with_dumpcap",
        lambda interface, **_kwargs: probed.append(interface) or interface == "wlp3s0",
    )

    assert auto_detect_interface() == "wlp3s0"
    assert probed == ["wlp3s0"]
