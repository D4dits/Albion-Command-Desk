from __future__ import annotations

import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser
import logging
import zipfile
from collections import deque
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot

from albion_dps.capture import capture_backend_available
from albion_dps.capture.npcap_runtime import (
    NPCAP_DOWNLOAD_URL,
    RUNTIME_STATE_AVAILABLE,
    RUNTIME_STATE_BLOCKED,
    RUNTIME_STATE_MISSING,
    RUNTIME_STATE_UNKNOWN,
    detect_npcap_runtime,
)
from albion_dps.domain.item_db import ensure_game_databases, get_game_database_health
from albion_dps.settings import load_app_settings, settings_dir, settings_path, update_app_settings
from albion_dps.versioning import resolve_app_version


DEFAULT_REPO_URL = "https://github.com/ao-data/albiondata-client.git"
DEFAULT_PUBLIC_INGEST_URL = "https+pow://albion-online-data.com"
GIT_WINDOWS_DOWNLOAD_URL = "https://git-scm.com/download/win"
GIT_DOWNLOADS_URL = "https://git-scm.com/downloads"
_ALBION_LOG_RE = re.compile(
    r"^[A-Z]{4,5}\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^\]]*\]\s"
)
_ANSI_ESC_RE = re.compile(r"\x1b\[[0-9;]*m")
_ANSI_BARE_RE = re.compile(r"\[[0-9;]{1,6}m")
_LOGRUS_RE = re.compile(r'^time="([^"]+)"\s+level=([a-zA-Z]+)\s+msg="(.*)"$')


class ScannerState(QObject):
    statusChanged = Signal()
    updateChanged = Signal()
    logChanged = Signal()
    runningChanged = Signal()
    runtimeChanged = Signal()
    gitChanged = Signal()
    gameDataChanged = Signal()
    settingsChanged = Signal()

    _statusSignal = Signal(str)
    _updateSignal = Signal(str)
    _logSignal = Signal(str)
    _runningSignal = Signal(bool)
    _processExitSignal = Signal(int)
    _runtimeSignal = Signal(str, str, str, str)
    _gitSignal = Signal(bool, str, str, str)
    _gameDataSignal = Signal(bool, str, str, str, str)

    def __init__(self) -> None:
        super().__init__()
        self._repo_root = Path(__file__).resolve().parents[2]
        self._default_client_dir = self._repo_root / "artifacts" / "albiondata-client"
        self._settings = load_app_settings()
        configured_client_dir = str(self._settings.scanner_repo_dir or "").strip()
        self._client_dir = Path(configured_client_dir).expanduser() if configured_client_dir else self._default_client_dir
        self._repo_url = str(self._settings.scanner_repo_url or DEFAULT_REPO_URL).strip() or DEFAULT_REPO_URL
        self._app_log_level = str(self._settings.log_level or "INFO").strip().upper() or "INFO"
        self._config_dir = settings_dir()
        self._app_version = resolve_app_version()
        self._status_text = "idle"
        self._update_text = "not checked"
        self._log_lines: deque[str] = deque(maxlen=800)
        self._running = False
        self._runtime_state = RUNTIME_STATE_UNKNOWN
        self._runtime_detail = "Runtime status not checked yet."
        self._runtime_action_label = ""
        self._runtime_action_url = ""
        self._git_available = False
        self._git_detail = "Git status not checked yet."
        self._git_action_label = ""
        self._git_action_url = ""
        self._game_data_ready = False
        self._game_data_root = ""
        self._game_data_detail = "Game data status not checked yet."
        self._game_data_hint = ""
        self._game_data_action_label = "Select game folder"
        self._process: subprocess.Popen[str] | None = None
        self._process_lock = threading.Lock()
        self._op_lock = threading.Lock()
        self._capability_hint_shown = False
        self._stop_requested = False

        self._statusSignal.connect(self._set_status_text)
        self._updateSignal.connect(self._set_update_text)
        self._logSignal.connect(self._append_log_line)
        self._runningSignal.connect(self._set_running)
        self._processExitSignal.connect(self._handle_process_exit)
        self._runtimeSignal.connect(self._set_runtime)
        self._gitSignal.connect(self._set_git)
        self._gameDataSignal.connect(self._set_game_data)

        self._append_log("Scanner ready.")
        self.refreshCaptureRuntimeStatus()
        self.refreshGitStatus()
        self.refreshGameDataStatus()

    @Property(str, notify=statusChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(str, notify=updateChanged)
    def updateText(self) -> str:
        return self._update_text

    @Property(str, notify=logChanged)
    def logText(self) -> str:
        return "\n".join(self._log_lines)

    @Property(bool, notify=runningChanged)
    def running(self) -> bool:
        return self._running

    @Property(str, notify=runtimeChanged)
    def captureRuntimeState(self) -> str:
        return self._runtime_state

    @Property(str, notify=runtimeChanged)
    def captureRuntimeDetail(self) -> str:
        return self._runtime_detail

    @Property(str, notify=runtimeChanged)
    def captureRuntimeActionLabel(self) -> str:
        return self._runtime_action_label

    @Property(str, notify=runtimeChanged)
    def captureRuntimeActionUrl(self) -> str:
        return self._runtime_action_url

    @Property(bool, notify=runtimeChanged)
    def captureRuntimeNeedsAction(self) -> bool:
        return self._runtime_state in {RUNTIME_STATE_MISSING, RUNTIME_STATE_BLOCKED, RUNTIME_STATE_UNKNOWN}

    @Property(str, notify=runtimeChanged)
    def captureRuntimeInstallHint(self) -> str:
        if _is_windows():
            if self._runtime_state == RUNTIME_STATE_MISSING:
                return "Install Npcap Runtime (Npcap installer). Npcap SDK is not required for regular users."
            if self._runtime_state == RUNTIME_STATE_BLOCKED:
                return "Runtime found, but this installation does not include the Windows live capture component."
            if self._runtime_state == RUNTIME_STATE_UNKNOWN:
                return "Runtime status is unknown. Re-run runtime check or open help page."
            return "Capture runtime is ready."
        if self._runtime_state == RUNTIME_STATE_MISSING:
            return "Capture backend is missing from this installation."
        return "Capture runtime is ready."

    @Property(str, notify=runtimeChanged)
    def captureRuntimeInstallCommand(self) -> str:
        if _is_windows() and self._runtime_state in {RUNTIME_STATE_MISSING, RUNTIME_STATE_BLOCKED, RUNTIME_STATE_UNKNOWN}:
            return "Start-Process 'https://npcap.com/#download'"
        return ""

    @Property(str, notify=settingsChanged)
    def clientDir(self) -> str:
        return str(self._client_dir)

    @Property(str, notify=settingsChanged)
    def scannerRepoDir(self) -> str:
        return str(self._client_dir)

    @Property(str, notify=settingsChanged)
    def scannerRepoUrl(self) -> str:
        return self._repo_url

    @Property(str, notify=settingsChanged)
    def appLogLevel(self) -> str:
        return self._app_log_level

    @Property(str, constant=True)
    def configDir(self) -> str:
        return str(self._config_dir)

    @Property(str, constant=True)
    def appVersion(self) -> str:
        return self._app_version

    @Property(bool, notify=gitChanged)
    def gitAvailable(self) -> bool:
        return self._git_available

    @Property(str, notify=gitChanged)
    def gitDetail(self) -> str:
        return self._git_detail

    @Property(str, notify=gitChanged)
    def gitActionLabel(self) -> str:
        return self._git_action_label

    @Property(str, notify=gitChanged)
    def gitActionUrl(self) -> str:
        return self._git_action_url

    @Property(bool, notify=gitChanged)
    def gitNeedsInstall(self) -> bool:
        return not self._git_available

    @Property(str, notify=gitChanged)
    def gitInstallHint(self) -> str:
        if self._git_available:
            return "Git is available."
        if _is_windows():
            return (
                "Install Git, restart Albion Command Desk, then run 'Sync repo'. "
                "Recommended command: winget install --id Git.Git -e --source winget"
            )
        return "Install Git from git-scm.com/downloads, restart app, then run 'Sync repo'."

    @Property(str, notify=gitChanged)
    def gitInstallCommand(self) -> str:
        if self._git_available:
            return ""
        if _is_windows():
            return "winget install --id Git.Git -e --source winget"
        return "xdg-open https://git-scm.com/downloads"

    @Property(bool, notify=gameDataChanged)
    def gameDataReady(self) -> bool:
        return self._game_data_ready

    @Property(str, notify=gameDataChanged)
    def gameDataState(self) -> str:
        return "ready" if self._game_data_ready else "missing"

    @Property(str, notify=gameDataChanged)
    def gameDataDetail(self) -> str:
        return self._game_data_detail

    @Property(str, notify=gameDataChanged)
    def gameDataHint(self) -> str:
        return self._game_data_hint

    @Property(str, notify=gameDataChanged)
    def gameDataActionLabel(self) -> str:
        return self._game_data_action_label

    @Property(str, notify=gameDataChanged)
    def gameDataRoot(self) -> str:
        return self._game_data_root

    @Slot()
    def clearLog(self) -> None:
        self._log_lines.clear()
        self.logChanged.emit()

    @Slot(str, str, str, result=str)
    def exportDiagnosticsBundle(self, update_status: str, market_status: str, market_diagnostics: str) -> str:
        target_dir = self._config_dir / "diagnostics"
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            target_dir = Path(tempfile.gettempdir()) / "AlbionCommandDesk" / "diagnostics"
            target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        bundle_path = target_dir / f"acd-diagnostics-{timestamp}.zip"
        summary = {
            "app_version": self._app_version,
            "platform": sys.platform,
            "python": sys.version,
            "config_dir": str(self._config_dir),
            "settings_path": str(settings_path()),
            "update_status": str(update_status or ""),
            "scanner": {
                "status": self._status_text,
                "update": self._update_text,
                "running": bool(self._running),
                "client_dir": str(self._client_dir),
                "repo_url": self._repo_url,
            },
            "capture_runtime": {
                "state": self._runtime_state,
                "detail": self._runtime_detail,
                "hint": self.captureRuntimeInstallHint,
            },
            "git": {
                "available": bool(self._git_available),
                "detail": self._git_detail,
                "hint": self.gitInstallHint,
            },
            "game_data": {
                "ready": bool(self._game_data_ready),
                "detail": self._game_data_detail,
                "hint": self._game_data_hint,
                "root": self._game_data_root,
            },
            "market": {
                "status": str(market_status or ""),
                "diagnostics_lines": len(str(market_diagnostics or "").splitlines()),
            },
        }
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("summary.json", json.dumps(summary, indent=2, sort_keys=True))
            archive.writestr("scanner.log.txt", self.logText or "")
            archive.writestr("market.diagnostics.txt", str(market_diagnostics or ""))
            settings_file = settings_path()
            if settings_file.exists():
                archive.write(settings_file, arcname="settings.json")
        self._append_log(f"Diagnostics bundle exported: {bundle_path}")
        return str(bundle_path)

    @Slot(str)
    def setScannerRepoDir(self, raw_path: str) -> None:
        text = str(raw_path or "").strip()
        new_path = Path(text).expanduser() if text else self._default_client_dir
        if new_path == self._client_dir:
            return
        self._client_dir = new_path
        self._persist_settings(scanner_repo_dir="" if new_path == self._default_client_dir else str(new_path))
        self.settingsChanged.emit()
        self.refreshGitStatus()

    @Slot()
    def resetScannerRepoDir(self) -> None:
        self.setScannerRepoDir("")

    @Slot(str)
    def setScannerRepoUrl(self, raw_url: str) -> None:
        text = str(raw_url or "").strip() or DEFAULT_REPO_URL
        if text == self._repo_url:
            return
        self._repo_url = text
        self._persist_settings(scanner_repo_url=text)
        self.settingsChanged.emit()
        self.refreshGitStatus()

    @Slot(str)
    def setAppLogLevel(self, raw_level: str) -> None:
        level = str(raw_level or "INFO").strip().upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            level = "INFO"
        if level == self._app_log_level:
            return
        self._app_log_level = level
        self._persist_settings(log_level=level)
        self.settingsChanged.emit()

    @Slot()
    def checkForUpdates(self) -> None:
        if self._scanner_process_active():
            self._append_warn("Stop scanner before checking repository updates.")
            return
        self._run_async(self._check_for_updates_impl, "check updates")

    @Slot()
    def syncClientRepo(self) -> None:
        if self._scanner_process_active():
            self._append_warn("Stop scanner before syncing the repository.")
            return
        self._run_async(self._sync_client_repo_impl, "sync repository")

    @Slot()
    def startScanner(self) -> None:
        self._start_scanner(use_sudo=False)

    @Slot()
    def startScannerSudo(self) -> None:
        self._start_scanner(use_sudo=True)

    @Slot()
    def stopScanner(self) -> None:
        process: subprocess.Popen[str] | None
        with self._process_lock:
            process = self._process
            stop_requested = self._stop_requested
        if process is None:
            self._append_warn("Scanner is not running.")
            return
        if stop_requested:
            self._append_warn("Scanner stop is already in progress.")
            return
        self._append_log("Stopping scanner...")
        self._statusSignal.emit("stopping scanner")
        self._stop_process(process)

    @Slot()
    def refreshCaptureRuntimeStatus(self) -> None:
        state, detail, action_label, action_url = self._detect_capture_runtime_status()
        self._runtimeSignal.emit(state, detail, action_label, action_url)

    @Slot()
    def openCaptureRuntimeAction(self) -> None:
        url = (self._runtime_action_url or "").strip()
        if not url:
            self._append_warn("No runtime action URL available.")
            return
        opened = webbrowser.open(url)
        if opened:
            self._append_log(f"Opened runtime help page: {url}")
        else:
            self._append_warn(f"Failed to open browser automatically: {url}")

    @Slot()
    def refreshGitStatus(self) -> None:
        available, detail, action_label, action_url = self._detect_git_status()
        self._gitSignal.emit(available, detail, action_label, action_url)

    @Slot()
    def openGitInstallAction(self) -> None:
        url = (self._git_action_url or "").strip()
        if not url:
            self._append_warn("No Git install URL available.")
            return
        opened = webbrowser.open(url)
        if opened:
            self._append_log(f"Opened Git install page: {url}")
        else:
            self._append_warn(f"Failed to open browser automatically: {url}")

    @Slot()
    def refreshGameDataStatus(self) -> None:
        health = get_game_database_health(logger=logging.getLogger(__name__))
        self._gameDataSignal.emit(
            bool(health.get("ready", False)),
            str(health.get("detail", "")),
            str(health.get("hint", "")),
            str(health.get("action_label", "Select game folder")),
            str(health.get("game_root", "") or ""),
        )

    @Slot()
    def setupGameData(self) -> None:
        self._append_log("Running game data setup...")
        try:
            ok = ensure_game_databases(logger=logging.getLogger(__name__), interactive=True)
        except Exception as exc:
            self._append_error(f"Game data setup failed: {exc}")
            self.refreshGameDataStatus()
            return
        if ok:
            self._append_log("Game data setup completed.")
        else:
            self._append_warn(
                "Game data is still missing or setup was canceled. Live mode can run with fallback names."
            )
        self.refreshGameDataStatus()

    @Slot(str)
    def copyText(self, text: str) -> None:
        value = str(text or "").strip()
        if not value:
            self._append_warn("Nothing to copy.")
            return
        try:
            from PySide6.QtGui import QGuiApplication

            clipboard = QGuiApplication.clipboard()
            clipboard.setText(value)
            self._append_log("Copied command to clipboard.")
        except Exception as exc:
            self._append_error(f"Failed to copy to clipboard: {exc}")

    def shutdown(self) -> None:
        process: subprocess.Popen[str] | None
        with self._process_lock:
            process = self._process
        if process is None:
            return
        self._stop_process(process)

    def _run_async(self, target, action_name: str) -> None:
        if not self._op_lock.acquire(blocking=False):
            self._append_warn("Another scanner operation is already running.")
            return

        self._append_log(f"Starting operation: {action_name}")

        def worker() -> None:
            try:
                target()
            finally:
                self._op_lock.release()

        threading.Thread(target=worker, daemon=True).start()

    def _check_for_updates_impl(self) -> None:
        if self._scanner_process_active():
            self._append_warn("Stop scanner before checking repository updates.")
            return
        self.refreshGitStatus()
        git_path = shutil.which("git")
        if not git_path:
            self._statusSignal.emit("git not found")
            self._updateSignal.emit("unknown")
            self._append_error("Git is not available in PATH.")
            if self._git_detail:
                self._append_warn(self._git_detail)
            return

        remote_head = self._git_remote_head()
        if remote_head is None:
            self._statusSignal.emit("update check failed")
            self._updateSignal.emit("unknown")
            return

        local_head = self._git_local_head()
        if local_head is None:
            self._statusSignal.emit("scanner repo missing")
            self._updateSignal.emit("not installed")
            self._append_warn("Local albiondata-client repository is not present.")
            return

        short_local = local_head[:8]
        short_remote = remote_head[:8]
        if local_head == remote_head:
            self._statusSignal.emit("up to date")
            self._updateSignal.emit(f"up to date ({short_local})")
            self._append_log(f"Repository is up to date: {short_local}")
        else:
            self._statusSignal.emit("update available")
            self._updateSignal.emit(f"update available ({short_local} -> {short_remote})")
            self._append_log(f"Update available: local {short_local}, remote {short_remote}")

    def _sync_client_repo_impl(self) -> None:
        if self._scanner_process_active():
            self._append_warn("Stop scanner before syncing the repository.")
            return
        self.refreshGitStatus()
        git_path = shutil.which("git")
        if not git_path:
            self._statusSignal.emit("git not found")
            self._append_error("Git is not available in PATH.")
            if self._git_detail:
                self._append_warn(self._git_detail)
            return

        self._client_dir.parent.mkdir(parents=True, exist_ok=True)
        if not (self._client_dir / ".git").exists():
            self._append_log("Cloning albiondata-client repository...")
            result = self._run_command(
                [git_path, "clone", "--depth", "1", self._repo_url, str(self._client_dir)],
                cwd=self._repo_root,
                timeout=120,
            )
            if result is None:
                self._statusSignal.emit("clone failed")
                return
            self._append_log("Repository cloned.")
        else:
            self._append_log("Fetching latest changes...")
            fetch_result = self._run_command(
                [git_path, "-C", str(self._client_dir), "fetch", "--depth", "1", "origin", "HEAD"],
                cwd=self._repo_root,
                timeout=120,
            )
            if fetch_result is None:
                self._statusSignal.emit("fetch failed")
                return
            relation_raw = self._run_command(
                [git_path, "-C", str(self._client_dir), "rev-list", "--left-right", "--count", "HEAD...FETCH_HEAD"],
                cwd=self._repo_root,
                timeout=30,
                log_stdout=False,
            )
            relation = _parse_rev_list_counts(relation_raw)
            if relation is None:
                self._statusSignal.emit("sync failed")
                self._append_error("Unable to determine local/remote git relation.")
                return

            local_only, remote_only = relation
            if local_only == 0 and remote_only == 0:
                self._append_log("Repository already up to date.")
            elif local_only == 0 and remote_only > 0:
                ff_result = self._run_command(
                    [git_path, "-C", str(self._client_dir), "merge", "--ff-only", "FETCH_HEAD"],
                    cwd=self._repo_root,
                    timeout=120,
                )
                if ff_result is None:
                    self._statusSignal.emit("pull failed")
                    return
                self._append_log("Repository updated (fast-forward).")
            else:
                self._append_warn(
                    "Local scanner repository is ahead/diverged from upstream; forcing sync to remote HEAD."
                )
                reset_result = self._run_command(
                    [git_path, "-C", str(self._client_dir), "reset", "--hard", "FETCH_HEAD"],
                    cwd=self._repo_root,
                    timeout=120,
                )
                if reset_result is None:
                    self._statusSignal.emit("sync failed")
                    return
                self._append_log("Repository reset to remote HEAD.")

        self._check_for_updates_impl()

    def _read_process_output(self, process: subprocess.Popen[str]) -> None:
        try:
            if process.stdout is not None:
                for line in process.stdout:
                    text = line.rstrip()
                    if text:
                        normalized = self._normalize_external_line(text)
                        if normalized:
                            self._logSignal.emit(normalized)
        finally:
            exit_code = process.wait()
            self._processExitSignal.emit(exit_code)

    def _handle_process_exit(self, code: int) -> None:
        stop_requested = self._stop_requested
        with self._process_lock:
            self._process = None
        self._stop_requested = False
        self._runningSignal.emit(False)
        if code == 0 or stop_requested:
            self._statusSignal.emit("scanner stopped")
            self._append_log("Scanner stopped.")
        else:
            self._statusSignal.emit(f"scanner exited ({code})")
            self._append_error(f"Scanner exited with code {code}.")

    def _stop_process(self, process: subprocess.Popen[str]) -> None:
        with self._process_lock:
            self._stop_requested = True
        if _is_windows():
            self._stop_process_windows(process)
            return
        self._stop_process_posix(process)

    def _stop_process_windows(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=2)
            return
        except Exception:
            pass

        taskkill_path = shutil.which("taskkill")
        if taskkill_path:
            try:
                subprocess.run(
                    [taskkill_path, "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=8,
                    check=False,
                )
                process.wait(timeout=2)
                return
            except Exception:
                pass

        try:
            process.kill()
        except Exception:
            return

    def _stop_process_posix(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=2)
            return
        except Exception:
            pass

        try:
            process.terminate()
            process.wait(timeout=2)
            return
        except Exception:
            pass

        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            try:
                process.kill()
            except Exception:
                return

    def _resolve_start_command(self) -> list[str] | None:
        binary_name = "albiondata-client.exe" if _is_windows() else "albiondata-client"
        candidates = [
            self._client_dir / binary_name,
            self._client_dir / "bin" / binary_name,
            self._client_dir / "dist" / binary_name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return [str(candidate)]
        go_path = shutil.which("go")
        if go_path and self._client_dir.exists():
            return [go_path, "run", "."]
        return None

    def _start_scanner(self, *, use_sudo: bool) -> None:
        if self._op_lock.locked():
            self._append_warn("Wait for the current scanner operation to finish before starting the scanner.")
            return
        self.refreshCaptureRuntimeStatus()
        with self._process_lock:
            if self._process is not None:
                if self._stop_requested:
                    self._append_warn("Scanner is still stopping. Wait a moment and try again.")
                else:
                    self._append_warn("Scanner already running.")
                return

        command = self._resolve_start_command()
        if command is None:
            if (self._client_dir / ".git").exists():
                self._append_error(
                    "No scanner executable found. Build with: go build -o albiondata-client ."
                )
                if not shutil.which("go"):
                    self._append_warn("Go is not available in PATH.")
            else:
                self._append_error(
                    "No scanner executable found. Sync repository first, then build tool."
                )
            return

        if use_sudo:
            if not shutil.which("sudo"):
                self._append_error("sudo is not available in PATH.")
                return
            if len(command) > 1 and Path(command[0]).name == "go":
                self._append_error(
                    "Sudo start requires a built scanner binary. Build with: go build -o albiondata-client ."
                )
                return
        else:
            self._maybe_log_capability_hint(command)

        command = self._build_runtime_command(command)
        if use_sudo:
            command = self._sudo_prefix() + command

        self._client_dir.mkdir(parents=True, exist_ok=True)
        self._append_log(f"Starting scanner: {' '.join(command)}")
        try:
            popen_kwargs = {
                "cwd": str(self._client_dir),
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "encoding": "utf-8",
                "errors": "replace",
                "bufsize": 1,
            }
            if not _is_windows():
                popen_kwargs["start_new_session"] = True
            process = subprocess.Popen(
                command,
                **popen_kwargs,
            )
        except Exception as exc:
            self._append_error(f"Failed to start scanner: {exc}")
            return

        with self._process_lock:
            self._process = process
            self._stop_requested = False
        self._runningSignal.emit(True)
        self._statusSignal.emit("scanner running")

        reader = threading.Thread(target=self._read_process_output, args=(process,), daemon=True)
        reader.start()

    def _sudo_prefix(self) -> list[str]:
        if sys.stdin.isatty() and sys.stdout.isatty():
            return ["sudo"]
        self._append_warn("No TTY detected; using sudo -n (non-interactive).")
        self._append_warn("If sudo fails, run `sudo -v` in a terminal and try again.")
        return ["sudo", "-n"]

    def _maybe_log_capability_hint(self, command: list[str]) -> None:
        if self._capability_hint_shown:
            return
        if _is_windows():
            return
        if os.geteuid() == 0:
            return
        if len(command) != 1:
            return
        binary = Path(command[0])
        if not binary.exists():
            return
        getcap = shutil.which("getcap")
        if getcap:
            try:
                result = subprocess.run(
                    [getcap, str(binary)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=5,
                    check=False,
                )
            except Exception:
                result = None
            if result and result.returncode == 0:
                output = (result.stdout or "").strip()
                if "cap_net_raw" in output and "cap_net_admin" in output:
                    self._capability_hint_shown = True
                    return
        self._append_warn(
            "Scanner capture may require permissions. If you see 'Operation not permitted', grant capabilities."
        )
        self._append_warn(f"Run: sudo setcap cap_net_raw,cap_net_admin=eip {binary}")
        self._append_warn("Or use the 'Start scanner (sudo)' button.")
        self._capability_hint_shown = True

    def _build_runtime_command(self, command: list[str]) -> list[str]:
        args = list(command)
        args.extend(["-i", DEFAULT_PUBLIC_INGEST_URL])
        return args

    def _git_local_head(self) -> str | None:
        if not (self._client_dir / ".git").exists():
            return None
        git_path = shutil.which("git")
        if not git_path:
            return None
        result = self._run_command(
            [git_path, "-C", str(self._client_dir), "rev-parse", "HEAD"],
            cwd=self._repo_root,
            timeout=20,
            log_stdout=False,
        )
        if not result:
            return None
        return result.strip()

    def _git_remote_head(self) -> str | None:
        git_path = shutil.which("git")
        if not git_path:
            return None
        result = self._run_command(
            [git_path, "ls-remote", self._repo_url, "HEAD"],
            cwd=self._repo_root,
            timeout=30,
            log_stdout=False,
        )
        if not result:
            return None
        return result.split()[0].strip()

    def _run_command(
        self,
        command: list[str],
        *,
        cwd: Path,
        timeout: int,
        log_stdout: bool = True,
        log_stderr: bool = True,
    ) -> str | None:
        try:
            result = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
        except Exception as exc:
            self._append_error(f"Command failed: {' '.join(command)}")
            self._append_error(str(exc))
            return None

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        if stdout and log_stdout:
            for line in stdout.splitlines():
                self._append_log(line)
        if stderr and log_stderr:
            for line in stderr.splitlines():
                self._append_warn(line)
        if result.returncode != 0:
            self._append_error(
                f"Command exited with code {result.returncode}: {' '.join(command)}"
            )
            return None
        return stdout

    def _scanner_process_active(self) -> bool:
        with self._process_lock:
            return self._process is not None

    def _append_log(self, message: str) -> None:
        self._logSignal.emit(self._format_line("INFO", message))

    def _append_warn(self, message: str) -> None:
        self._logSignal.emit(self._format_line("WARN", message))

    def _append_error(self, message: str) -> None:
        self._logSignal.emit(self._format_line("ERROR", message))

    def _append_log_line(self, message: str) -> None:
        self._log_lines.append(message)
        self.logChanged.emit()

    def _normalize_external_line(self, message: str) -> str:
        cleaned = self._clean_ansi(message)
        if not cleaned:
            return ""
        if self._looks_like_external_log(cleaned):
            return cleaned
        parsed = _LOGRUS_RE.match(cleaned)
        if parsed:
            timestamp, level, msg = parsed.groups()
            level_map = {"warning": "WARN", "warn": "WARN", "error": "ERROR", "info": "INFO"}
            normalized_level = level_map.get(level.lower(), level.upper())
            return f"{normalized_level}[{timestamp}] {msg}"
        return self._format_line("INFO", cleaned)

    def _format_line(self, level: str, message: str) -> str:
        cleaned = self._clean_ansi(message)
        if self._looks_like_external_log(cleaned):
            return cleaned
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        return f"{level}[{timestamp}] {cleaned}"

    def _looks_like_external_log(self, line: str) -> bool:
        return bool(_ALBION_LOG_RE.match(line))

    def _clean_ansi(self, text: str) -> str:
        cleaned = _ANSI_ESC_RE.sub("", text)
        cleaned = _ANSI_BARE_RE.sub("", cleaned)
        return cleaned.strip()

    def _set_status_text(self, text: str) -> None:
        if text == self._status_text:
            return
        self._status_text = text
        self.statusChanged.emit()

    def _set_update_text(self, text: str) -> None:
        if text == self._update_text:
            return
        self._update_text = text
        self.updateChanged.emit()

    def _set_running(self, running: bool) -> None:
        if running == self._running:
            return
        self._running = running
        self.runningChanged.emit()

    def _set_runtime(self, state: str, detail: str, action_label: str, action_url: str) -> None:
        changed = (
            state != self._runtime_state
            or detail != self._runtime_detail
            or action_label != self._runtime_action_label
            or action_url != self._runtime_action_url
        )
        if not changed:
            return
        self._runtime_state = state
        self._runtime_detail = detail
        self._runtime_action_label = action_label
        self._runtime_action_url = action_url
        self.runtimeChanged.emit()

    def _set_git(self, available: bool, detail: str, action_label: str, action_url: str) -> None:
        changed = (
            available != self._git_available
            or detail != self._git_detail
            or action_label != self._git_action_label
            or action_url != self._git_action_url
        )
        if not changed:
            return
        self._git_available = available
        self._git_detail = detail
        self._git_action_label = action_label
        self._git_action_url = action_url
        self.gitChanged.emit()

    def _set_game_data(self, ready: bool, detail: str, hint: str, action_label: str, game_root: str) -> None:
        changed = (
            ready != self._game_data_ready
            or game_root != self._game_data_root
            or detail != self._game_data_detail
            or hint != self._game_data_hint
            or action_label != self._game_data_action_label
        )
        if not changed:
            return
        self._game_data_ready = ready
        self._game_data_root = game_root
        self._game_data_detail = detail
        self._game_data_hint = hint
        self._game_data_action_label = action_label
        self.gameDataChanged.emit()

    def _persist_settings(self, **changes) -> None:
        self._settings = update_app_settings(**changes)

    def _detect_capture_runtime_status(self) -> tuple[str, str, str, str]:
        if _is_windows():
            runtime = detect_npcap_runtime()
            state = runtime.state
            detail = runtime.detail or "Npcap runtime check finished."
            action_url = (runtime.action_url or "").strip()

            if state == RUNTIME_STATE_AVAILABLE and not capture_backend_available():
                state = RUNTIME_STATE_BLOCKED
                detail = (
                    "Npcap Runtime detected, but this installation does not include the Windows live capture component. "
                    "Use a release that bundles the Windows capture backend."
                )
                action_url = ""

            if state == RUNTIME_STATE_MISSING:
                detail = (
                    "Npcap Runtime is missing. Install Npcap Runtime (Npcap installer) to enable live mode. "
                    "Npcap SDK is not required for normal users."
                )
                return state, detail, "Install runtime", action_url or NPCAP_DOWNLOAD_URL
            if state in (RUNTIME_STATE_BLOCKED, RUNTIME_STATE_UNKNOWN):
                return state, detail, "Open runtime page", action_url or NPCAP_DOWNLOAD_URL
            return state, detail, "", ""

        if capture_backend_available():
            return (
                RUNTIME_STATE_AVAILABLE,
                "Capture backend is available.",
                "",
                "",
            )
        return (
            RUNTIME_STATE_MISSING,
            "Capture backend module is missing from this installation.",
            "",
            "",
        )

    def _detect_git_status(self) -> tuple[bool, str, str, str]:
        git_path = shutil.which("git")
        if git_path:
            return True, f"Git detected: {git_path}", "", ""

        if _is_windows():
            return (
                False,
                "Git is required for Sync repository and Check updates. Install with: winget install --id Git.Git -e --source winget",
                "Install Git",
                GIT_WINDOWS_DOWNLOAD_URL,
            )

        return (
            False,
            "Git is required for Sync repository and Check updates.",
            "Install Git",
            GIT_DOWNLOADS_URL,
        )


def _is_windows() -> bool:
    import os

    return os.name == "nt"
def _parse_rev_list_counts(output: str | None) -> tuple[int, int] | None:
    if not output:
        return None
    parts = output.strip().split()
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None
