from __future__ import annotations

from albion_dps.models import MeterSnapshot
from albion_dps.qt.models import UiState
from albion_dps.qt.models import _build_player_rows, _is_player_label


def test_build_player_rows_respects_allowed_player_names() -> None:
    totals = {
        101: {"damage": 1000.0, "heal": 0.0, "dps": 50.0, "hps": 0.0},
        202: {"damage": 700.0, "heal": 0.0, "dps": 35.0, "hps": 0.0},
    }
    names = {
        101: "D4dits",
        202: "OutsidePlayer",
    }

    rows = _build_player_rows(
        totals,
        names=names,
        sort_key="dps",
        top_n=10,
        allowed_player_names={"D4dits"},
    )

    assert [row.name for row in rows] == ["D4dits"]


def test_is_player_label_rejects_mob_prefix_without_at() -> None:
    assert not _is_player_label("MOB_MORGANA_CULTIST")
    assert not _is_player_label("NPC_VENDOR")
    assert _is_player_label("D4dits")


def test_ui_state_update_populates_live_rows() -> None:
    state = UiState(sort_key="dps", top_n=10, history_limit=20)
    snapshot = MeterSnapshot(
        timestamp=1.0,
        totals={101: {"damage": 1000.0, "heal": 100.0, "dps": 50.0, "hps": 5.0}},
        names={101: "D4dits"},
    )

    state.update(
        snapshot,
        names={101: "D4dits"},
        history=[],
        mode="battle",
        zone="-",
        fame_total=0,
        fame_per_hour=0.0,
        silver_total=0,
        silver_per_hour=0.0,
        allowed_player_names={"D4dits"},
    )

    assert state.playersModel.rowCount() == 1
