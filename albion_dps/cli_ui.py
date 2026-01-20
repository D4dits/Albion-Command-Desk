from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Callable, Iterable

from albion_dps.models import MeterSnapshot

_SORT_KEYS = {"dmg": "damage", "heal": "heal", "dps": "dps", "hps": "hps"}
_BAR_WIDTH = 20


def format_table(
    snapshot: MeterSnapshot,
    sort_key: str = "dps",
    top_n: int | None = 10,
    *,
    include_header: bool = True,
) -> str:
    entries, total_entries = _group_entries(snapshot, sort_key, top_n)

    header = ["source", "damage", "heal", "dps", "hps", "bar"]
    rows: list[list[str]] = []
    metric_key = _SORT_KEYS.get(sort_key, "dps")
    metric_index = {"damage": 1, "heal": 2, "dps": 3, "hps": 4}[metric_key]
    metric_values = [row[metric_index] for row in entries]
    max_metric = max(metric_values) if metric_values else 0.0
    for source_label, damage, heal, dps, hps in entries:
        metric_value = {"damage": damage, "heal": heal, "dps": dps, "hps": hps}[metric_key]
        rows.append(
            [
                source_label,
                _format_total(damage),
                _format_total(heal),
                _format_dps(dps),
                _format_dps(hps),
                _render_bar(metric_value, max_metric, _BAR_WIDTH),
            ]
        )

    total_damage = sum(stats.get("damage", 0.0) for stats in snapshot.totals.values())
    total_heal = sum(stats.get("heal", 0.0) for stats in snapshot.totals.values())
    lines: list[str] = []
    if include_header:
        shown_entries = len(entries)
        top_label = "all" if not top_n or top_n <= 0 else str(top_n)
        lines.extend(
            [
                "Albion DPS Meter",
                f"Timestamp: {snapshot.timestamp:.3f}",
                f"Sort: {sort_key}  Top: {top_label}  Players: {shown_entries}/{total_entries}",
            ]
        )

    if not rows:
        if include_header:
            lines.append("")
        lines.append("(no data)")
        return "\n".join(lines)

    if include_header:
        lines.append("")
    lines.extend(_render_table(header, rows))
    lines.append("")
    lines.append(
        f"Totals: damage {_format_total(total_damage)} | heal {_format_total(total_heal)}"
    )

    return "\n".join(lines)


def render_loop(
    snapshots: Iterable[MeterSnapshot],
    *,
    sort_key: str = "dps",
    top_n: int | None = 10,
    snapshot_path: str | None = None,
    refresh_seconds: float = 1.0,
    view_builder: Callable[[MeterSnapshot], str] | None = None,
    key_handler: Callable[[str], None] | None = None,
) -> None:
    previous_lines = 0
    ansi_ok = _enable_virtual_terminal()
    use_in_place = sys.stdout.isatty() and ansi_ok
    for snapshot in snapshots:
        if snapshot_path:
            write_snapshot(snapshot, snapshot_path)
        if view_builder is None:
            output = format_table(snapshot, sort_key=sort_key, top_n=top_n)
        else:
            output = view_builder(snapshot)
        if use_in_place:
            previous_lines = _render_in_place(output, previous_lines)
        else:
            sys.stdout.write(output)
            sys.stdout.write("\n")
        sys.stdout.flush()
        if key_handler is not None:
            key = _read_key()
            if key:
                key_handler(key)
        if refresh_seconds > 0:
            time.sleep(refresh_seconds)


def write_snapshot(snapshot: MeterSnapshot, path: str | Path) -> None:
    output = Path(path)
    payload = {"timestamp": snapshot.timestamp, "totals": snapshot.totals}
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )


def _render_table(header: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(col) for col in header]
    for row in rows:
        for idx, col in enumerate(row):
            widths[idx] = max(widths[idx], len(col))
    aligns = ["left", "right", "right", "right", "left"]
    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    lines = [border, _render_row(header, widths, aligns), border]
    for row in rows:
        lines.append(_render_row(row, widths, aligns))
    lines.append(border)
    return lines


def _render_row(columns: list[str], widths: list[int], aligns: list[str]) -> str:
    padded: list[str] = []
    for idx, col in enumerate(columns):
        align = aligns[idx] if idx < len(aligns) else "left"
        if align == "right":
            padded.append(col.rjust(widths[idx]))
        else:
            padded.append(col.ljust(widths[idx]))
    return " " + " | ".join(padded).rstrip()


def _format_total(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.1f}"


def _format_dps(value: float) -> str:
    return f"{value:.1f}"


def _render_bar(value: float, max_value: float, width: int) -> str:
    if width <= 0:
        return ""
    if max_value <= 0:
        return "." * width
    ratio = value / max_value
    filled = int(round(ratio * width))
    if filled < 0:
        filled = 0
    if filled > width:
        filled = width
    return "#" * filled + "." * (width - filled)


def _clear_screen() -> None:
    sys.stdout.write("\x1b[2J\x1b[H")


def _shown_entry_count(snapshot: MeterSnapshot, top_n: int | None) -> int:
    if not top_n or top_n <= 0:
        return len(_group_entries(snapshot, "dps", None)[0])
    return min(len(_group_entries(snapshot, "dps", None)[0]), top_n)


def _enable_virtual_terminal() -> bool:
    if os.name != "nt":
        return True
    try:
        import ctypes
    except Exception:
        return False
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    if handle == 0 or handle == -1:
        return False
    mode = ctypes.c_uint()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)) == 0:
        return False
    enable_vt = 0x0004
    if mode.value & enable_vt:
        return True
    if kernel32.SetConsoleMode(handle, mode.value | enable_vt) == 0:
        return False
    return True


def _read_key() -> str | None:
    if os.name != "nt":
        return None
    try:
        import msvcrt
    except Exception:
        return None
    if not msvcrt.kbhit():
        return None
    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        if msvcrt.kbhit():
            msvcrt.getwch()
        return None
    return key


def _render_in_place(text: str, previous_lines: int) -> int:
    lines = text.splitlines()
    total_lines = max(len(lines), previous_lines)
    if previous_lines > 0:
        sys.stdout.write(f"\x1b[{previous_lines}A")
    for line in lines:
        sys.stdout.write("\x1b[2K")
        sys.stdout.write(line)
        sys.stdout.write("\n")
    for _ in range(total_lines - len(lines)):
        sys.stdout.write("\x1b[2K\n")
    return total_lines


def format_dashboard(
    snapshot: MeterSnapshot,
    *,
    mode: str,
    zone_label: str | None,
    manual_active: bool,
    fame_total: int,
    fame_per_hour: float,
    history_lines: list[str],
    sort_key: str,
    top_n: int | None,
    status_line: str | None = None,
) -> str:
    lines = []
    _, total_entries = _group_entries(snapshot, sort_key, None)
    mode_label = mode
    if mode == "manual":
        mode_label = "manual:on" if manual_active else "manual:off"
    title = f"Albion DPS Meter  [{mode_label}]"
    if zone_label:
        title = f"{title}  [zone {zone_label}]"
    lines.append(title)
    lines.append(f"Timestamp: {snapshot.timestamp:.3f}")
    shown_entries = _shown_entry_count(snapshot, top_n)
    top_label = "all" if not top_n or top_n <= 0 else str(top_n)
    lines.append(f"Sort: {sort_key}  Top: {top_label}  Players: {shown_entries}/{total_entries}")
    lines.append(f"Fame: {fame_total}  |  fame/h {fame_per_hour:.1f}")
    if status_line:
        lines.append(status_line)
    lines.append("")
    lines.extend(
        format_table(snapshot, sort_key=sort_key, top_n=top_n, include_header=False).splitlines()
    )
    lines.append("")
    if history_lines:
        lines.extend(history_lines)
    else:
        lines.append("History: (empty)")
    lines.append(
        "Keys: 1-9 copy | b/z/m mode | space start/stop | n end | r reset fame"
    )
    return "\n".join(lines)


def format_history_lines(lines: Iterable[str], limit: int | None = None) -> list[str]:
    output: list[str] = ["History:"]
    for idx, line in enumerate(lines, 1):
        if limit is not None and limit > 0 and idx > limit:
            break
        output.append(f"[{idx}] {line}")
    if len(output) == 1:
        output.append("(empty)")
    return output


def _group_entries(
    snapshot: MeterSnapshot, sort_key: str, top_n: int | None
) -> tuple[list[tuple[str, float, float, float, float]], int]:
    names = snapshot.names or {}
    grouped: dict[str, list[float]] = {}
    for source_id, stats in snapshot.totals.items():
        label = names.get(source_id) or str(source_id)
        damage = float(stats.get("damage", 0.0))
        heal = float(stats.get("heal", 0.0))
        dps = float(stats.get("dps", 0.0))
        hps = float(stats.get("hps", 0.0))
        if label not in grouped:
            grouped[label] = [0.0, 0.0, 0.0, 0.0]
        grouped[label][0] += damage
        grouped[label][1] += heal
        grouped[label][2] += dps
        grouped[label][3] += hps

    entries = [
        (label, values[0], values[1], values[2], values[3]) for label, values in grouped.items()
    ]
    key = _SORT_KEYS.get(sort_key, "dps")
    key_index = {"damage": 1, "heal": 2, "dps": 3, "hps": 4}[key]
    entries.sort(key=lambda row: row[key_index], reverse=True)
    total_entries = len(entries)
    if top_n is not None and top_n > 0:
        entries = entries[:top_n]
    return entries, total_entries
