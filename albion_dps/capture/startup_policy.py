from __future__ import annotations

from dataclasses import dataclass

from albion_dps.capture.npcap_runtime import (
    NPCAP_DOWNLOAD_URL,
    RUNTIME_STATE_AVAILABLE,
    RUNTIME_STATE_BLOCKED,
    RUNTIME_STATE_MISSING,
    RUNTIME_STATE_UNKNOWN,
    NpcapRuntimeStatus,
)


@dataclass(frozen=True)
class LiveStartupDecision:
    mode: str
    message: str
    action_url: str | None = None


def decide_live_startup(
    *,
    os_name: str,
    backend_available: bool,
    runtime_status: NpcapRuntimeStatus | None = None,
) -> LiveStartupDecision:
    if os_name != "nt":
        if backend_available:
            return LiveStartupDecision(mode="live", message="Capture backend available.")
        return LiveStartupDecision(
            mode="core",
            message=(
                "Live capture backend is missing. Falling back to core mode. "
                "Reinstall with capture profile: pip install -e \".[capture]\""
            ),
        )

    status = runtime_status or NpcapRuntimeStatus(
        state=RUNTIME_STATE_UNKNOWN,
        available=False,
        detail="Npcap runtime status is unknown.",
        action_url=NPCAP_DOWNLOAD_URL,
    )
    if status.state == RUNTIME_STATE_AVAILABLE and backend_available:
        return LiveStartupDecision(mode="live", message="Npcap runtime and capture backend available.")
    if status.state == RUNTIME_STATE_MISSING:
        return LiveStartupDecision(
            mode="core",
            message=(
                "Npcap Runtime is missing. Falling back to core mode. "
                f"Install Npcap Runtime from {NPCAP_DOWNLOAD_URL}"
            ),
            action_url=status.action_url or NPCAP_DOWNLOAD_URL,
        )
    if status.state == RUNTIME_STATE_BLOCKED:
        return LiveStartupDecision(
            mode="core",
            message=(
                "Npcap Runtime check is blocked. Falling back to core mode. "
                f"Details: {status.detail}"
            ),
            action_url=status.action_url or NPCAP_DOWNLOAD_URL,
        )
    if status.state == RUNTIME_STATE_AVAILABLE and not backend_available:
        return LiveStartupDecision(
            mode="core",
            message=(
                "Npcap Runtime detected, but Python capture backend is missing. "
                "Falling back to core mode. Reinstall with capture profile: pip install -e \".[capture]\""
            ),
            action_url=status.action_url or NPCAP_DOWNLOAD_URL,
        )
    return LiveStartupDecision(
        mode="core",
        message=(
            "Npcap Runtime status is unknown. Falling back to core mode. "
            f"Details: {status.detail}"
        ),
        action_url=status.action_url or NPCAP_DOWNLOAD_URL,
    )
