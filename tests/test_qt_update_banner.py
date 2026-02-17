from __future__ import annotations

from albion_dps.qt.models import UiState


def _state() -> UiState:
    return UiState(sort_key="dps", top_n=10, history_limit=25)


def test_set_update_status_shows_banner() -> None:
    state = _state()
    state.setUpdateStatus(
        True,
        "0.1.13",
        "0.1.14",
        "https://example.com/release",
    )
    assert state.updateBannerVisible is True
    assert state.updateBannerUrl == "https://example.com/release"
    assert state.updateCheckStatus == "Update available: 0.1.13 -> 0.1.14"


def test_set_update_status_ignores_unavailable() -> None:
    state = _state()
    state.setUpdateStatus(False, "0.1.13", "0.1.14", "https://example.com/release")
    assert state.updateBannerVisible is False
    assert state.updateBannerText == ""
    assert state.updateBannerUrl == ""


def test_dismiss_update_banner_hides_banner() -> None:
    state = _state()
    state.setUpdateStatus(True, "0.1.13", "0.1.14", "https://example.com/release")
    state.dismissUpdateBanner()
    assert state.updateBannerVisible is False
