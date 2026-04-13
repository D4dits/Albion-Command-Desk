from __future__ import annotations

from albion_dps.capture.live_capture import rank_interfaces
from albion_dps.qt import runner


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
