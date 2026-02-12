from __future__ import annotations

import argparse
import sys

from albion_dps.logging_config import configure_logging
from albion_dps.qt.runner import run_qt

_COMMANDS = ("live", "replay")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="albion-command-desk",
        description="Albion Command Desk (Qt GUI only).",
    )
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--version", action="version", version="0.1.0")

    subparsers = parser.add_subparsers(dest="command")
    live = subparsers.add_parser("live", help="Run GUI with live capture")
    replay = subparsers.add_parser("replay", help="Run GUI with PCAP replay")
    _add_common_gui_args(live)
    _add_common_gui_args(replay)

    live.add_argument("--interface")
    live.add_argument("--list-interfaces", action="store_true")
    live.add_argument("--bpf", default="(ip or ip6) and udp")
    live.add_argument("--promisc", action="store_true")
    live.add_argument("--snaplen", type=int, default=65535)
    live.add_argument("--timeout-ms", type=int, default=1000)
    live.add_argument("--dump-raw")

    replay.add_argument("pcap")
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    normalized_argv = _normalize_argv(list(argv))
    args = parser.parse_args(normalized_argv)

    log_level = "DEBUG" if args.debug else args.log_level
    configure_logging(log_level)

    args.qt_command = args.command
    return run_qt(args)


def _add_common_gui_args(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--sort", choices=["dmg", "dps", "heal", "hps"], default="dps")
    subparser.add_argument("--top", type=int, default=10)
    subparser.add_argument("--snapshot")
    subparser.add_argument("--self-name")
    subparser.add_argument("--self-id", type=int)
    subparser.add_argument("--mode", choices=["battle", "zone", "manual"], default="battle")
    subparser.add_argument("--history", type=int, default=5)
    subparser.add_argument("--battle-timeout", type=float, default=20.0)


def _normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return ["live"]

    if any(token in ("-h", "--help", "--version") for token in argv):
        return argv

    if _contains_command(argv):
        return argv

    insert_at = _find_command_insert_index(argv)
    return [*argv[:insert_at], "live", *argv[insert_at:]]


def _contains_command(argv: list[str]) -> bool:
    for token in argv:
        if token.startswith("-"):
            continue
        if token in _COMMANDS:
            return True
    return False


def _find_command_insert_index(argv: list[str]) -> int:
    idx = 0
    while idx < len(argv):
        token = argv[idx]
        if token == "--log-level":
            idx += 2
            continue
        if token.startswith("--log-level="):
            idx += 1
            continue
        if token == "--debug":
            idx += 1
            continue
        break
    return min(idx, len(argv))
