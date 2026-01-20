from __future__ import annotations

from albion_dps.cli_ui import format_table
from albion_dps.models import MeterSnapshot


def test_format_table_sort_and_top() -> None:
    snapshot = MeterSnapshot(
        1.0,
        {
            1: {"damage": 100.0, "heal": 0.0, "dps": 10.0},
            2: {"damage": 200.0, "heal": 5.0, "dps": 5.0},
        },
    )

    table = format_table(snapshot, sort_key="dmg", top_n=1)
    rows = [
        line
        for line in table.splitlines()
        if line.strip() and line.strip().split()[0].isdigit()
    ]

    assert len(rows) == 1
    assert rows[0].lstrip().startswith("2")
