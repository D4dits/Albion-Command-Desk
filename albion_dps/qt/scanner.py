from __future__ import annotations

import shutil
import subprocess
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
import re

from PySide6.QtCore import QObject, Property, Signal, Slot


DEFAULT_REPO_URL = "https://github.com/ao-data/albiondata-client.git"
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
    configChanged = Signal()

    _statusSignal = Signal(str)
    _updateSignal = Signal(str)
    _logSignal = Signal(str)
    _runningSignal = Signal(bool)
    _processExitSignal = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._repo_root = Path(__file__).resolve().parents[2]
        self._client_dir = self._repo_root / "artifacts" / "albiondata-client"
        self._repo_url = DEFAULT_REPO_URL
        self._status_text = "idle"
        self._update_text = "not checked"
        self._log_lines: deque[str] = deque(maxlen=800)
        self._running = False
        self._disable_upload = False
        self._public_ingest_url = "https+pow://albion-online-data.com"
        self._listen_devices = ""
        self._process: subprocess.Popen[str] | None = None
        self._process_lock = threading.Lock()
        self._op_lock = threading.Lock()

        self._statusSignal.connect(self._set_status_text)
        self._updateSignal.connect(self._set_update_text)
        self._logSignal.connect(self._append_log_line)
        self._runningSignal.connect(self._set_running)
        self._processExitSignal.connect(self._handle_process_exit)

        self._append_log("Scanner ready.")

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

    @Property(bool, notify=configChanged)
    def disableUpload(self) -> bool:
        return self._disable_upload

    @Property(str, notify=configChanged)
    def publicIngestUrl(self) -> str:
        return self._public_ingest_url

    @Property(str, notify=configChanged)
    def listenDevices(self) -> str:
        return self._listen_devices

    @Property(str, constant=True)
    def clientDir(self) -> str:
        return str(self._client_dir)

    @Slot()
    def clearLog(self) -> None:
        self._log_lines.clear()
        self.logChanged.emit()

    @Slot(bool)
    def setDisableUpload(self, value: bool) -> None:
        if value == self._disable_upload:
            return
        self._disable_upload = value
        self.configChanged.emit()

    @Slot(str)
    def setPublicIngestUrl(self, value: str) -> None:
        val = value.strip()
        if not val:
            val = "https+pow://albion-online-data.com"
        if val == self._public_ingest_url:
            return
        self._public_ingest_url = val
        self.configChanged.emit()

    @Slot(str)
    def setListenDevices(self, value: str) -> None:
        val = value.strip()
        if val == self._listen_devices:
            return
        self._listen_devices = val
        self.configChanged.emit()

    @Slot()
    def checkForUpdates(self) -> None:
        self._run_async(self._check_for_updates_impl, "check updates")

    @Slot()
    def syncClientRepo(self) -> None:
        self._run_async(self._sync_client_repo_impl, "sync repository")

    @Slot()
    def startScanner(self) -> None:
        with self._process_lock:
            if self._process is not None:
                self._append_warn("Scanner already running.")
                return

        command = self._resolve_start_command()
        if command is None:
            self._append_error(
                "No scanner executable found. Sync repository first, then build tool."
            )
            return
        command = self._build_runtime_command(command)

        self._client_dir.mkdir(parents=True, exist_ok=True)
        self._append_log(f"Starting scanner: {' '.join(command)}")
        try:
            process = subprocess.Popen(
                command,
                cwd=str(self._client_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except Exception as exc:
            self._append_error(f"Failed to start scanner: {exc}")
            return

        with self._process_lock:
            self._process = process
        self._runningSignal.emit(True)
        self._statusSignal.emit("scanner running")

        reader = threading.Thread(target=self._read_process_output, args=(process,), daemon=True)
        reader.start()

    @Slot()
    def stopScanner(self) -> None:
        process: subprocess.Popen[str] | None
        with self._process_lock:
            process = self._process
        if process is None:
            self._append_warn("Scanner is not running.")
            return
        self._append_log("Stopping scanner...")
        process.terminate()

    def shutdown(self) -> None:
        process: subprocess.Popen[str] | None
        with self._process_lock:
            process = self._process
        if process is None:
            return
        process.terminate()
        try:
            process.wait(timeout=2)
        except Exception:
            process.kill()

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
        git_path = shutil.which("git")
        if not git_path:
            self._statusSignal.emit("git not found")
            self._updateSignal.emit("unknown")
            self._append_error("Git is not available in PATH.")
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
        git_path = shutil.which("git")
        if not git_path:
            self._statusSignal.emit("git not found")
            self._append_error("Git is not available in PATH.")
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
            pull_result = self._run_command(
                [git_path, "-C", str(self._client_dir), "pull", "--ff-only"],
                cwd=self._repo_root,
                timeout=120,
            )
            if pull_result is None:
                self._statusSignal.emit("pull failed")
                return
            self._append_log("Repository updated.")

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
        with self._process_lock:
            self._process = None
        self._runningSignal.emit(False)
        if code == 0:
            self._statusSignal.emit("scanner stopped")
            self._append_log("Scanner exited normally.")
        else:
            self._statusSignal.emit(f"scanner exited ({code})")
            self._append_error(f"Scanner exited with code {code}.")

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

    def _build_runtime_command(self, command: list[str]) -> list[str]:
        args = list(command)
        if self._disable_upload:
            args.append("-d")
        if self._public_ingest_url:
            args.extend(["-i", self._public_ingest_url])
        if self._listen_devices:
            args.extend(["-l", self._listen_devices])
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
        )
        if not result:
            return None
        return result.split()[0].strip()

    def _run_command(self, command: list[str], *, cwd: Path, timeout: int) -> str | None:
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
        if stdout:
            for line in stdout.splitlines():
                self._append_log(line)
        if stderr:
            for line in stderr.splitlines():
                self._append_warn(line)
        if result.returncode != 0:
            self._append_error(
                f"Command exited with code {result.returncode}: {' '.join(command)}"
            )
            return None
        return stdout

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


def _is_windows() -> bool:
    import os

    return os.name == "nt"
