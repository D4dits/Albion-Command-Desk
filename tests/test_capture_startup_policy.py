from __future__ import annotations

from albion_dps.capture.npcap_runtime import (
    NPCAP_DOWNLOAD_URL,
    RUNTIME_STATE_AVAILABLE,
    RUNTIME_STATE_BLOCKED,
    RUNTIME_STATE_MISSING,
    RUNTIME_STATE_UNKNOWN,
    NpcapRuntimeStatus,
)
from albion_dps.capture.startup_policy import decide_live_startup


def test_decide_live_startup_posix_backend_missing_falls_back_to_core() -> None:
    decision = decide_live_startup(os_name="posix", backend_available=False, runtime_status=None)
    assert decision.mode == "core"
    assert "Falling back to core mode" in decision.message
    assert decision.action_url is None


def test_decide_live_startup_windows_missing_runtime_falls_back_to_core() -> None:
    decision = decide_live_startup(
        os_name="nt",
        backend_available=True,
        runtime_status=NpcapRuntimeStatus(
            state=RUNTIME_STATE_MISSING,
            available=False,
            detail="missing",
            action_url=NPCAP_DOWNLOAD_URL,
        ),
    )
    assert decision.mode == "core"
    assert "Npcap Runtime is missing" in decision.message
    assert decision.action_url == NPCAP_DOWNLOAD_URL


def test_decide_live_startup_windows_available_runtime_and_backend_stays_live() -> None:
    decision = decide_live_startup(
        os_name="nt",
        backend_available=True,
        runtime_status=NpcapRuntimeStatus(
            state=RUNTIME_STATE_AVAILABLE,
            available=True,
            detail="ok",
        ),
    )
    assert decision.mode == "live"
    assert "available" in decision.message.lower()


def test_decide_live_startup_windows_backend_missing_falls_back_to_core() -> None:
    decision = decide_live_startup(
        os_name="nt",
        backend_available=False,
        runtime_status=NpcapRuntimeStatus(
            state=RUNTIME_STATE_AVAILABLE,
            available=True,
            detail="runtime ok",
        ),
    )
    assert decision.mode == "core"
    assert "backend is missing" in decision.message
    assert decision.action_url == NPCAP_DOWNLOAD_URL


def test_decide_live_startup_windows_unknown_state_falls_back_to_core() -> None:
    decision = decide_live_startup(
        os_name="nt",
        backend_available=True,
        runtime_status=NpcapRuntimeStatus(
            state=RUNTIME_STATE_UNKNOWN,
            available=False,
            detail="unknown status",
        ),
    )
    assert decision.mode == "core"
    assert "unknown" in decision.message.lower()
    assert decision.action_url == NPCAP_DOWNLOAD_URL


def test_decide_live_startup_windows_blocked_state_falls_back_to_core() -> None:
    decision = decide_live_startup(
        os_name="nt",
        backend_available=True,
        runtime_status=NpcapRuntimeStatus(
            state=RUNTIME_STATE_BLOCKED,
            available=False,
            detail="permission denied",
            action_url=NPCAP_DOWNLOAD_URL,
        ),
    )
    assert decision.mode == "core"
    assert "blocked" in decision.message.lower()
    assert decision.action_url == NPCAP_DOWNLOAD_URL
