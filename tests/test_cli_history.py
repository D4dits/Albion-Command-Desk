from __future__ import annotations

from albion_dps.cli import _format_history_copy, _format_history_line
from albion_dps.meter.session_meter import SessionEntry, SessionSummary


def _summary(label: str) -> SessionSummary:
    return SessionSummary(
        mode="battle",
        start_ts=0.0,
        end_ts=1.0,
        duration=1.0,
        label=None,
        entries=[SessionEntry(label=label, damage=10.0, heal=0.0, dps=10.0, hps=0.0)],
        total_damage=10.0,
        total_heal=0.0,
        reason="combat_state",
    )


def test_format_history_line_resolves_numeric_labels_via_snapshot_names() -> None:
    line = _format_history_line(_summary("1275179"), names={1275179: "D4dits"})
    assert "D4dits dmg" in line
    assert "1275179 dmg" not in line


def test_format_history_copy_resolves_numeric_labels_via_lookup() -> None:
    text = _format_history_copy(_summary("1275179"), name_lookup=lambda i: "D4dits" if i == 1275179 else None)
    assert "D4dits dmg" in text
    assert "1275179 dmg" not in text

