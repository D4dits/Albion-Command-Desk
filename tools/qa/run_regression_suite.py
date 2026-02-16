from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


GROUP_TESTS: dict[str, list[str]] = {
    "meter": [
        "tests/test_meter.py",
        "tests/test_session_meter.py",
        "tests/test_hps_pcap24.py",
        "tests/test_combat_state.py",
    ],
    "scanner": [
        "tests/test_udp_decode.py",
        "tests/test_protocol16_event.py",
        "tests/test_operation_response_join.py",
    ],
    "market": [
        "tests/test_market_engine.py",
        "tests/test_market_service.py",
        "tests/test_market_qt_state.py",
        "tests/test_market_dataset_regression.py",
    ],
    "live": [
        "tests/test_party_registry.py",
        "tests/test_party_pcap31_includes_party_member.py",
        "tests/test_party_pcap35_solo_excludes_non_party.py",
    ],
    "replay": [
        "tests/test_party_pcap39_disband_clears_roster.py",
        "tests/test_party_pcap42_party_member_ids.py",
        "tests/test_qt_smoke.py",
        "tests/test_cli_qt_only.py",
    ],
}


@dataclass
class GroupResult:
    name: str
    returncode: int
    elapsed_seconds: float


def _run_group(group: str, tests: list[str]) -> GroupResult:
    start = time.monotonic()
    base_temp = Path(".state") / "qa_pytest" / f"{group}_{int(time.time() * 1000)}"
    base_temp.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        f"--basetemp={base_temp}",
        *tests,
    ]
    env = dict(os.environ)
    env["TEMP"] = str(base_temp)
    env["TMP"] = str(base_temp)
    print(f"\n[qa] running {group}: {' '.join(tests)}", flush=True)
    completed = subprocess.run(command, check=False, env=env)
    elapsed = time.monotonic() - start
    return GroupResult(name=group, returncode=completed.returncode, elapsed_seconds=elapsed)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run grouped regression checks for QA-001 (meter/scanner/market/live/replay)."
    )
    parser.add_argument(
        "--group",
        action="append",
        choices=sorted(GROUP_TESTS.keys()),
        help="Run only selected group(s). Can be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    groups = args.group if args.group else list(GROUP_TESTS.keys())
    results: list[GroupResult] = []

    for group in groups:
        results.append(_run_group(group, GROUP_TESTS[group]))

    failed = [result for result in results if result.returncode != 0]
    print("\n[qa] summary", flush=True)
    for result in results:
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"- {result.name}: {status} ({result.elapsed_seconds:.1f}s)", flush=True)

    if failed:
        print(f"[qa] failed groups: {', '.join(result.name for result in failed)}", flush=True)
        return 1
    print("[qa] all selected groups passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
