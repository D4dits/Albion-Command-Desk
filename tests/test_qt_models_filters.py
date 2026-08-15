from __future__ import annotations

from albion_dps.models import MeterSnapshot
from albion_dps.qt.models import UiState
from albion_dps.qt.models import _build_player_rows, _is_player_label
from albion_dps.meter.session_meter import SessionEntry, SessionSummary


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


def test_build_player_rows_only_shows_party_members_with_stats() -> None:
    totals = {
        101: {"damage": 1000.0, "heal": 0.0, "dps": 50.0, "hps": 0.0},
    }
    names = {101: "D4dits"}

    rows = _build_player_rows(
        totals,
        names=names,
        sort_key="dps",
        top_n=10,
        allowed_player_names={"D4dits", "PartyOne", "PartyTwo"},
    )

    assert [row.name for row in rows] == ["D4dits"]
    assert rows[0].damage == 1000


def test_is_player_label_rejects_mob_prefix_without_at() -> None:
    assert not _is_player_label("MOB_MORGANA_CULTIST")
    assert not _is_player_label("NPC_VENDOR")
    assert not _is_player_label("58207")
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


def test_ui_state_updates_meter_limits_and_duration(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", str(tmp_path))
    captured_limits: list[int] = []
    state = UiState(
        sort_key="dps",
        top_n=10,
        history_limit=20,
        set_history_limit_callback=captured_limits.append,
    )
    snapshot = MeterSnapshot(
        timestamp=1.0,
        totals={idx: {"damage": float(idx), "heal": 0.0, "dps": float(idx), "hps": 0.0} for idx in range(30)},
        names={idx: f"Player{idx}" for idx in range(30)},
        duration=65.0,
    )

    state.setMeterTopN(20)
    state.setHistoryLimit(50)
    state.update(
        snapshot,
        names={idx: f"Player{idx}" for idx in range(30)},
        history=[],
        mode="battle",
        zone="-",
        fame_total=0,
        fame_per_hour=0.0,
        silver_total=0,
        silver_per_hour=0.0,
    )

    assert state.meterTopN == 20
    assert state.historyLimit == 50
    assert captured_limits == [50]
    assert state.durationText == "01:05"
    assert state.playersModel.rowCount() == 20


def test_ui_state_selected_history_uses_session_dps_not_expired_rolling_dps() -> None:
    state = UiState(sort_key="dps", top_n=10, history_limit=20)
    history = [
        SessionSummary(
            mode="battle",
            start_ts=10.0,
            end_ts=60.0,
            duration=50.0,
            label=None,
            entries=[
                SessionEntry(
                    label="D4dits",
                    damage=12_101.0,
                    heal=0.0,
                    dps=242.02,
                    hps=0.0,
                    source_id=101,
                )
            ],
            total_damage=12_101.0,
            total_heal=0.0,
            reason="combat_state",
            totals_by_id={101: {"damage": 12_101.0, "heal": 0.0, "dps": 0.0, "hps": 0.0}},
        )
    ]
    snapshot = MeterSnapshot(timestamp=61.0, totals={})

    state.update(
        snapshot,
        names={101: "D4dits"},
        history=history,
        mode="battle",
        zone="-",
        fame_total=0,
        fame_per_hour=0.0,
        silver_total=0,
        silver_per_hour=0.0,
    )
    state.selectHistory(0)

    model = state.playersModel
    idx = model.index(0, 0)
    assert model.data(idx, model.DpsRole) == 242.02
    assert model.data(idx, model.BarRole) == 1.0
