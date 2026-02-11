from __future__ import annotations

from albion_dps import cli


def test_main_defaults_to_live_qt(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_qt(args) -> int:
        captured["command"] = getattr(args, "command", None)
        captured["qt_command"] = getattr(args, "qt_command", None)
        return 0

    monkeypatch.setattr(cli, "run_qt", fake_run_qt)
    exit_code = cli.main([])
    assert exit_code == 0
    assert captured["command"] == "live"
    assert captured["qt_command"] == "live"


def test_main_supports_global_args_before_default_command(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_qt(args) -> int:
        captured["command"] = getattr(args, "command", None)
        captured["log_level"] = getattr(args, "log_level", None)
        return 0

    monkeypatch.setattr(cli, "run_qt", fake_run_qt)
    exit_code = cli.main(["--log-level", "DEBUG"])
    assert exit_code == 0
    assert captured["command"] == "live"
    assert captured["log_level"] == "DEBUG"


def test_main_supports_replay(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_qt(args) -> int:
        captured["command"] = getattr(args, "command", None)
        captured["qt_command"] = getattr(args, "qt_command", None)
        captured["pcap"] = getattr(args, "pcap", None)
        return 0

    monkeypatch.setattr(cli, "run_qt", fake_run_qt)
    exit_code = cli.main(["replay", "sample.pcap"])
    assert exit_code == 0
    assert captured["command"] == "replay"
    assert captured["qt_command"] == "replay"
    assert captured["pcap"] == "sample.pcap"


def test_main_uses_sys_argv_when_no_explicit_argv(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_qt(args) -> int:
        captured["command"] = getattr(args, "command", None)
        captured["pcap"] = getattr(args, "pcap", None)
        return 0

    monkeypatch.setattr(cli, "run_qt", fake_run_qt)
    monkeypatch.setattr(cli.sys, "argv", ["albion-command-desk", "replay", "from_sys.pcap"])
    exit_code = cli.main()
    assert exit_code == 0
    assert captured["command"] == "replay"
    assert captured["pcap"] == "from_sys.pcap"
