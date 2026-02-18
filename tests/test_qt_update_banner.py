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
        "https://example.com/changelog",
    )
    assert state.updateBannerVisible is True
    assert state.updateBannerUrl == "https://example.com/release"
    assert state.updateBannerNotesUrl == "https://example.com/changelog"
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


def test_dismissed_version_is_not_shown_again() -> None:
    state = _state()
    state.setUpdateStatus(True, "0.1.13", "0.1.14", "https://example.com/release")
    state.dismissUpdateBanner()
    state.setUpdateStatus(True, "0.1.13", "0.1.14", "https://example.com/release")
    assert state.updateBannerVisible is False


def test_newer_version_reappears_after_previous_dismiss() -> None:
    state = _state()
    state.setUpdateStatus(True, "0.1.13", "0.1.14", "https://example.com/release")
    state.dismissUpdateBanner()
    state.setUpdateStatus(True, "0.1.13", "0.1.15", "https://example.com/release")
    assert state.updateBannerVisible is True
