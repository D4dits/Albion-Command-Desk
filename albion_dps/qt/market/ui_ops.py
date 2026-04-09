from __future__ import annotations

import csv
import io
from pathlib import Path
from urllib.parse import urlencode

from albion_dps.market.aod_client import REGION_HOSTS


def build_aodata_url(state) -> str | None:
    setup = state.to_setup()
    item_ids = state._collect_pricing_item_ids()
    if not item_ids:
        state._set_list_action_text("Select a recipe in Craft Plan to build AOData URL.")
        return None
    locations = state._collect_locations(setup)
    if not locations:
        state._set_list_action_text("No market locations selected.")
        return None
    qualities = [setup.quality]
    params = urlencode(
        {
            "locations": ",".join(locations),
            "qualities": ",".join(str(x) for x in qualities),
        }
    )
    host = REGION_HOSTS.get(setup.region)
    if not host:
        state._set_list_action_text("Unknown AOData region.")
        return None
    joined_ids = ",".join(item_ids)
    return f"https://{host}/api/v2/stats/prices/{joined_ids}.json?{params}"


def copy_to_clipboard(state, value: str, *, success_message: str) -> None:
    from PySide6.QtGui import QGuiApplication

    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        state._set_list_action_text("Clipboard is not available.")
        return
    clipboard.setText(value)
    state._set_list_action_text(success_message)


def export_csv_interactive(state, *, payload: str, label: str, suggested_name: str) -> None:
    path = prompt_export_path(state, label=label, suggested_name=suggested_name)
    if not path:
        return
    export_csv(state, raw_path=path, payload=payload, label=label)


def prompt_export_path(state, *, label: str, suggested_name: str) -> str | None:
    try:
        from PySide6.QtWidgets import QFileDialog
    except Exception as exc:
        state._set_list_action_text(f"{label} export dialog unavailable: {exc}")
        return None
    base_dir = Path(state._default_export_dir).expanduser() if state._default_export_dir else Path.home()
    suggested_path = str((base_dir / suggested_name).resolve())
    selected_path, _selected_filter = QFileDialog.getSaveFileName(
        None,
        f"Export {label} CSV",
        suggested_path,
        "CSV Files (*.csv);;All Files (*)",
    )
    selected = str(selected_path or "").strip()
    if not selected:
        return None
    try:
        state._default_export_dir = str(Path(selected).expanduser().resolve().parent)
        state._persist_app_settings()
    except Exception:
        pass
    return selected


def export_csv(state, *, raw_path: str, payload: str, label: str) -> None:
    path_text = raw_path.strip()
    if not path_text:
        state._set_list_action_text(f"{label} export path is empty.")
        return
    if not payload:
        state._set_list_action_text(f"{label} CSV is empty.")
        return
    try:
        path = Path(path_text)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    except Exception as exc:
        state._set_list_action_text(f"{label} export failed: {exc}")
        return
    state._default_export_dir = str(path.parent)
    state._persist_app_settings()
    state._set_list_action_text(f"{label} CSV exported to {path}.")


def rows_to_csv(*, header: list[str], rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()
