from __future__ import annotations

import json
from pathlib import Path

from albion_dps.meter.session_meter import SessionEntry, SessionSummary
from albion_dps.models import MeterSnapshot
from albion_dps.qt.models import UiState, _history_to_csv, _history_to_json, _history_to_txt


def _summary(
    *,
    mode: str,
    start_ts: float,
    end_ts: float,
    duration: float,
    total_damage: float,
    total_heal: float,
    entries: list[SessionEntry],
    label: str | None = None,
) -> SessionSummary:
    return SessionSummary(
        mode=mode,
        start_ts=start_ts,
        end_ts=end_ts,
        duration=duration,
        label=label,
        entries=entries,
        total_damage=total_damage,
        total_heal=total_heal,
        reason="timeout",
        totals_by_id={},
    )


def test_ui_state_exports_history_txt_csv_json(monkeypatch) -> None:
    tmp_dir = Path("artifacts/tmp/session_export_test")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", str(tmp_dir / "config"))
    state = UiState(sort_key="dps", top_n=10, history_limit=10)
    snapshot = MeterSnapshot(timestamp=10.0, totals={}, names={})
    names = {101: "D4dits", 202: "Healer"}
    history = [
        _summary(
            mode="battle",
            start_ts=1.0,
            end_ts=11.0,
            duration=10.0,
            total_damage=1500.0,
            total_heal=300.0,
            entries=[
                SessionEntry(label="D4dits", damage=1200.0, heal=0.0, dps=120.0, hps=0.0, source_id=101),
                SessionEntry(label="Healer", damage=300.0, heal=300.0, dps=30.0, hps=30.0, source_id=202),
            ],
        ),
        _summary(
            mode="battle",
            start_ts=20.0,
            end_ts=32.0,
            duration=12.0,
            total_damage=1000.0,
            total_heal=100.0,
            entries=[
                SessionEntry(label="D4dits", damage=900.0, heal=0.0, dps=75.0, hps=0.0, source_id=101),
                SessionEntry(label="Healer", damage=100.0, heal=100.0, dps=8.3, hps=8.3, source_id=202),
            ],
        ),
    ]
    state.update(
        snapshot,
        names=names,
        history=history,
        mode="battle",
        zone="-",
        fame_total=0,
        fame_per_hour=0.0,
        silver_total=0,
        silver_per_hour=0.0,
    )

    txt_payload = _history_to_txt(history, names=names)
    csv_payload = _history_to_csv(history, names=names)
    json_payload_raw = _history_to_json(history, names=names)

    paths = {
        "txt": tmp_dir / "history.txt",
        "csv": tmp_dir / "history.csv",
        "json": tmp_dir / "history.json",
    }
    assert state._write_meter_export(raw_path=str(paths["txt"]), payload=txt_payload) is True
    assert state._write_meter_export(raw_path=str(paths["csv"]), payload=csv_payload) is True
    assert state._write_meter_export(raw_path=str(paths["json"]), payload=json_payload_raw) is True

    assert "battle 00:10 | total dmg 1500 heal 300 | players 2" in paths["txt"].read_text(encoding="utf-8")
    csv_payload = paths["csv"].read_text(encoding="utf-8")
    assert "session_index,encounter_id,source,mode,label,duration_seconds,total_damage,total_heal,player_count,player_rank,player_name,damage,heal,dps,hps" in csv_payload
    assert "1,,live,battle,,10.0,1500,300,2,1,D4dits,1200,0,120.0,0.0" in csv_payload
    json_payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert json_payload[0]["total_damage"] == 1500
    assert json_payload[0]["entries"][0]["player_name"] == "D4dits"


def test_ui_state_builds_compare_text_for_selected_history(monkeypatch) -> None:
    tmp_dir = Path("artifacts/tmp/session_compare_test")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ALBION_COMMAND_DESK_CONFIG_DIR", str(tmp_dir / "config"))
    state = UiState(sort_key="dps", top_n=10, history_limit=10)
    snapshot = MeterSnapshot(timestamp=10.0, totals={}, names={})
    history = [
        _summary(
            mode="battle",
            start_ts=1.0,
            end_ts=11.0,
            duration=10.0,
            total_damage=1500.0,
            total_heal=300.0,
            entries=[SessionEntry(label="D4dits", damage=1200.0, heal=0.0, dps=120.0, hps=0.0, source_id=101)],
        ),
        _summary(
            mode="battle",
            start_ts=20.0,
            end_ts=32.0,
            duration=12.0,
            total_damage=900.0,
            total_heal=50.0,
            entries=[SessionEntry(label="D4dits", damage=900.0, heal=0.0, dps=75.0, hps=0.0, source_id=101)],
        ),
    ]
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

    assert state.sessionCompareAvailable is True
    assert state.sessionCompareTitle == "Compare history #1 vs older #2"
    assert "Total damage: 1500 vs 900 (+600)" in state.sessionCompareText
    assert "Top DPS: D4dits (120.0) vs D4dits (75.0)" in state.sessionCompareText
