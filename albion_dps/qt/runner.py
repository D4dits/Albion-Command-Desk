from __future__ import annotations

import argparse
import importlib.metadata
import logging
import os
import queue
import threading
from collections.abc import Iterable
from pathlib import Path

from albion_dps.capture import auto_detect_interface, list_interfaces
from albion_dps.domain import FameTracker, NameRegistry, PartyRegistry, load_item_resolver
from albion_dps.domain.item_db import ensure_game_databases
from albion_dps.domain.map_resolver import load_map_resolver
from albion_dps.market.service import MarketDataService
from albion_dps.meter.session_meter import SessionMeter
from albion_dps.models import MeterSnapshot
from albion_dps.pipeline import live_snapshots, replay_snapshots
from albion_dps.protocol.combat_mapper import CombatEventMapper
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.registry import default_registry
from albion_dps.settings import AppSettings, load_app_settings, save_app_settings
from albion_dps.update import check_for_updates


SnapshotQueue = queue.Queue[MeterSnapshot | None]
_UPDATE_CHECK_LOCK = threading.Lock()


def run_qt(args: argparse.Namespace) -> int:
    if args.qt_command == "live" and args.list_interfaces:
        for interface in list_interfaces():
            print(interface)
        return 0
    _ensure_pyside6_paths()
    try:
        from PySide6.QtCore import QObject, QTimer, Signal
        from PySide6.QtGui import QGuiApplication, QIcon
        from PySide6.QtQml import QQmlApplicationEngine
    except Exception:  # pragma: no cover - optional dependency
        logging.getLogger(__name__).exception(
            "PySide6 is not available. Install GUI deps with: pip install -e \".[gui-qt]\""
        )
        return 1

    from albion_dps.qt.models import UiState
    from albion_dps.qt.market import MarketSetupState
    from albion_dps.qt.scanner import ScannerState

    names, party, fame, meter, decoder, mapper = _build_runtime(args)
    ensure_game_databases(logger=logging.getLogger(__name__), interactive=True)
    item_resolver = load_item_resolver(logger=logging.getLogger(__name__))
    map_resolver = load_map_resolver(logger=logging.getLogger(__name__))
    meter.map_lookup = map_resolver.name_for_index

    def role_lookup(entity_id: int) -> str | None:
        items = names.items_for(entity_id)
        weapon = item_resolver.weapon_category_for_items(items)
        if weapon:
            return weapon
        return item_resolver.role_for_items(items)

    def weapon_lookup(entity_id: int):
        items = names.items_for(entity_id)
        return item_resolver.weapon_info_for_items(items)
    snapshots = _build_snapshot_stream(args, names, party, fame, meter, decoder, mapper)
    if snapshots is None:
        return 1

    qml_path = Path(__file__).resolve().parent / "ui" / "Main.qml"
    if not qml_path.exists():
        logging.getLogger(__name__).error("QML not found: %s", qml_path)
        return 1

    snapshot_queue: SnapshotQueue = queue.Queue()
    stop_event = threading.Event()
    producer = threading.Thread(
        target=_produce_snapshots,
        args=(snapshots, snapshot_queue, stop_event),
        daemon=True,
    )
    producer.start()

    _configure_windows_taskbar_identity("albion.command.desk")
    app = QGuiApplication([])
    icon_dir = Path(__file__).resolve().parent / "ui"
    icon_candidates = (
        icon_dir / "command_desk_icon.png",
        icon_dir / "command_desk_icon.ico",
        icon_dir / "command_desk_icon.xpm",
    )
    icon_path = next((path for path in icon_candidates if path.exists()), None)
    app_icon = QIcon(str(icon_path)) if icon_path is not None else QIcon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    engine = QQmlApplicationEngine()
    warnings: list = []

    def handle_warnings(messages) -> None:
        warnings.extend(messages)
        for message in messages:
            logging.getLogger(__name__).error("QML: %s", message.toString())

    engine.warnings.connect(handle_warnings)
    state = UiState(
        sort_key=args.sort,
        top_n=args.top,
        history_limit=max(args.history, 1),
        set_mode_callback=meter.set_mode,
        role_lookup=role_lookup,
        weapon_lookup=weapon_lookup,
        update_auto_check=load_app_settings().update_auto_check,
    )
    class _UpdateNotifier(QObject):
        updateReady = Signal(bool, str, str, str)
        updateStatus = Signal(str)

    update_notifier = _UpdateNotifier()
    update_notifier.updateReady.connect(state.setUpdateStatus)
    update_notifier.updateStatus.connect(state.setUpdateCheckStatus)
    state.updateAutoCheckToggled.connect(_save_update_preference)
    state.manualUpdateCheckRequested.connect(lambda: _start_update_check(update_notifier))
    scanner_state = ScannerState()
    market_cache_path = Path("data") / "market_cache.sqlite3"
    market_cache_path.parent.mkdir(parents=True, exist_ok=True)
    market_service = MarketDataService.with_default_cache(cache_path=market_cache_path)
    market_setup_state = MarketSetupState(
        service=market_service,
        logger=logging.getLogger(__name__),
        auto_refresh_prices=True,
    )
    engine.rootContext().setContextProperty("uiState", state)
    engine.rootContext().setContextProperty("scannerState", scanner_state)
    engine.rootContext().setContextProperty("marketSetupState", market_setup_state)
    engine.load(str(qml_path))
    if not engine.rootObjects():
        logging.getLogger(__name__).error(
            "Failed to load QML UI. If QtQuick plugin is missing, reinstall PySide6 and restart the shell."
        )
        stop_event.set()
        return 1
    if not app_icon.isNull():
        for root in engine.rootObjects():
            set_icon = getattr(root, "setIcon", None)
            if callable(set_icon):
                set_icon(app_icon)
    if state.updateAutoCheck:
        _start_update_check(update_notifier)

    def drain_queue() -> None:
        _drain_snapshots(
            snapshot_queue,
            state,
            meter=meter,
            fame=fame,
            stop_event=stop_event,
        )

    timer = QTimer()
    timer.setInterval(100)
    timer.timeout.connect(drain_queue)
    timer.start()
    app.aboutToQuit.connect(scanner_state.shutdown)
    app.aboutToQuit.connect(market_setup_state.close)
    app.aboutToQuit.connect(stop_event.set)
    app.exec()
    return 0


def _configure_windows_taskbar_identity(app_id: str) -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(str(app_id))
    except Exception:
        logging.getLogger(__name__).debug("Could not set Windows AppUserModelID", exc_info=True)


def _build_snapshot_stream(
    args: argparse.Namespace,
    names: NameRegistry,
    party: PartyRegistry,
    fame: FameTracker,
    meter: SessionMeter,
    decoder: PhotonDecoder,
    mapper: CombatEventMapper,
) -> Iterable[MeterSnapshot] | None:
    if args.qt_command == "replay":
        return replay_snapshots(
            args.pcap,
            decoder,
            meter,
            name_registry=names,
            party_registry=party,
            fame_tracker=fame,
            event_mapper=mapper.map,
            snapshot_interval=1.0,
        )

    if args.qt_command == "live":
        if args.list_interfaces:
            for interface in list_interfaces():
                print(interface)
            return None
        interface = args.interface
        if not interface:
            interface = auto_detect_interface(
                bpf_filter=args.bpf,
                snaplen=args.snaplen,
                promisc=args.promisc,
                timeout_ms=args.timeout_ms,
            )
            if interface is None:
                interface = _fallback_interface()
                if interface is None:
                    logging.getLogger(__name__).error("No capture interfaces available")
                    return None
                logging.getLogger(__name__).warning(
                    "Auto-detect found no traffic; using fallback interface: %s",
                    interface,
                )
            else:
                logging.getLogger(__name__).info("Auto-detected interface: %s", interface)

        dump_raw_dir = args.dump_raw
        if args.debug and dump_raw_dir is None:
            dump_raw_dir = "artifacts/raw"

        return live_snapshots(
            interface,
            decoder=decoder,
            meter=meter,
            bpf_filter=args.bpf,
            snaplen=args.snaplen,
            promisc=args.promisc,
            timeout_ms=args.timeout_ms,
            dump_raw_dir=dump_raw_dir,
            name_registry=names,
            party_registry=party,
            fame_tracker=fame,
            event_mapper=mapper.map,
            snapshot_interval=1.0,
        )

    logging.getLogger(__name__).error("Unknown qt command")
    return None


def _ensure_pyside6_paths() -> None:
    try:
        import PySide6  # type: ignore
    except Exception:
        return
    base = Path(PySide6.__file__).resolve().parent
    bin_path = base / "bin"
    qml_path = base / "qml"
    plugins_path = base / "plugins"
    if os.name == "nt":
        path_entries = [str(base)]
        if bin_path.exists():
            path_entries.insert(0, str(bin_path))
        os.environ["PATH"] = f"{os.pathsep.join(path_entries)}{os.pathsep}{os.environ.get('PATH', '')}"
        if bin_path.exists():
            try:
                os.add_dll_directory(str(bin_path))
            except Exception:
                pass
        try:
            os.add_dll_directory(str(base))
        except Exception:
            pass
    os.environ.setdefault("QML2_IMPORT_PATH", str(qml_path))
    os.environ.setdefault("QT_PLUGIN_PATH", str(plugins_path))
    # Force a non-native style so custom backgrounds in Main.qml are applied
    # consistently and do not spam runtime warnings on some platforms.
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
    _append_qt_logging_rule("qt.qpa.mime=false")


def _append_qt_logging_rule(rule: str) -> None:
    current = os.environ.get("QT_LOGGING_RULES", "").strip()
    if not current:
        os.environ["QT_LOGGING_RULES"] = rule
        return
    parts = [part.strip() for part in current.split(";") if part.strip()]
    if rule in parts:
        return
    parts.append(rule)
    os.environ["QT_LOGGING_RULES"] = ";".join(parts)


def _build_runtime(
    args: argparse.Namespace,
) -> tuple[
    NameRegistry,
    PartyRegistry,
    FameTracker,
    SessionMeter,
    PhotonDecoder,
    CombatEventMapper,
]:
    decoder = PhotonDecoder(
        registry=default_registry(), debug=args.debug, dump_unknowns=True
    )
    mapper = CombatEventMapper(dump_unknowns=True, clamp_overkill=True)
    names = NameRegistry()
    party = PartyRegistry()
    fame = FameTracker()
    meter = SessionMeter(
        window_seconds=10.0,
        battle_timeout_seconds=args.battle_timeout,
        history_limit=max(args.history, 1),
        mode=args.mode,
        name_lookup=names.lookup,
    )
    if args.self_name:
        party.set_self_name(args.self_name, confirmed=True)
    if args.self_id is not None:
        party.seed_self_ids([args.self_id])
    return names, party, fame, meter, decoder, mapper


def _produce_snapshots(
    snapshots: Iterable[MeterSnapshot],
    snapshot_queue: SnapshotQueue,
    stop_event: threading.Event,
) -> None:
    try:
        for snapshot in snapshots:
            if stop_event.is_set():
                break
            snapshot_queue.put(snapshot)
    except Exception:
        logging.getLogger(__name__).exception("Snapshot stream terminated unexpectedly")
    finally:
        snapshot_queue.put(None)


def _drain_snapshots(
    snapshot_queue: SnapshotQueue,
    state,
    *,
    meter: SessionMeter,
    fame: FameTracker,
    stop_event: threading.Event,
) -> None:
    while True:
        try:
            snapshot = snapshot_queue.get_nowait()
        except queue.Empty:
            return
        if snapshot is None:
            stop_event.set()
            return
        names = snapshot.names or {}
        state.update(
            snapshot,
            names=names,
            history=meter.history(limit=state.historyLimit),
            mode=meter.mode,
            zone=meter.zone_label(),
            fame_total=fame.total(),
            fame_per_hour=fame.per_hour(),
        )


def _fallback_interface() -> str | None:
    try:
        interfaces = list_interfaces()
    except RuntimeError:
        return None
    if not interfaces:
        return None
    for candidate in interfaces:
        lowered = candidate.lower()
        if "loopback" in lowered or "npf_loopback" in lowered:
            continue
        return candidate
    return interfaces[0]


def _current_app_version() -> str:
    try:
        return importlib.metadata.version("albion-command-desk")
    except Exception:
        return "0.1.0"


def _start_update_check(notifier) -> None:
    current_version = _current_app_version()

    def worker() -> None:
        if not _UPDATE_CHECK_LOCK.acquire(blocking=False):
            return
        try:
            notifier.updateStatus.emit("Checking updates...")
            info = check_for_updates(current_version=current_version)
            if info.available:
                notifier.updateReady.emit(
                    True,
                    info.current_version,
                    info.latest_version,
                    info.release_url,
                )
                return
            if info.error:
                notifier.updateStatus.emit("Update check failed")
                return
            notifier.updateStatus.emit("Up to date")
        finally:
            _UPDATE_CHECK_LOCK.release()

    threading.Thread(target=worker, daemon=True, name="acd-update-check").start()


def _save_update_preference(enabled: bool) -> None:
    try:
        save_app_settings(AppSettings(update_auto_check=bool(enabled)))
    except Exception:
        logging.getLogger(__name__).warning("Failed to persist update preference", exc_info=True)
