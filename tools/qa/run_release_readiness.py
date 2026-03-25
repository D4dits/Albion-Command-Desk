from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    returncode: int
    elapsed_seconds: float


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_check(
    name: str,
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> CheckResult:
    print(f"[release] RUN {name}: {' '.join(command)}", flush=True)
    start = time.monotonic()
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    elapsed = time.monotonic() - start
    return CheckResult(name=name, returncode=completed.returncode, elapsed_seconds=elapsed)


def _pytest_env(base_temp_root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["TEMP"] = str(base_temp_root)
    env["TMP"] = str(base_temp_root)
    return env


def _powershell_parse_check(root: Path) -> CheckResult:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell is None:
        return CheckResult("powershell-parse", 0, 0.0)

    files = [
        root / "tools" / "install" / "windows" / "install.ps1",
        root / "tools" / "release" / "windows" / "build_bootstrap_setup.ps1",
    ]
    parse_script = (
        "$ErrorActionPreference='Stop';"
        "Add-Type -AssemblyName System.Management.Automation;"
        "$fail=$false;"
        + "".join(
            [
                f"$t=$null;$e=$null;"
                f"[System.Management.Automation.Language.Parser]::ParseFile('{str(path)}',[ref]$t,[ref]$e)|Out-Null;"
                f"if($e -and $e.Count -gt 0){{"
                f"Write-Error ('Parse errors in {path.name}: ' + (($e | ForEach-Object {{$_.Message}}) -join '; '));"
                f"$fail=$true;}}"
                for path in files
            ]
        )
        + "if($fail){exit 1}"
    )
    return _run_check(
        "powershell-parse",
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", parse_script],
        cwd=root,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local release-readiness gate set for Albion Command Desk."
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run pytest and QA helpers.",
    )
    parser.add_argument(
        "--skip-core-tests",
        action="store_true",
        help="Skip the broad core pytest pass.",
    )
    parser.add_argument(
        "--skip-powershell-parse",
        action="store_true",
        help="Skip Windows PowerShell parser checks.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip shared install smoke check.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    root = _repo_root()
    python = str(Path(args.python).resolve())
    temp_root = root / ".state" / "release_readiness" / str(int(time.time() * 1000))
    temp_root.mkdir(parents=True, exist_ok=True)
    env = _pytest_env(temp_root)
    results: list[CheckResult] = []

    if not args.skip_core_tests:
        results.append(
            _run_check(
                "pytest-core",
                [python, "-m", "pytest", "-q", "--ignore=tests/test_qt_smoke.py"],
                cwd=root,
                env=env,
            )
        )

    results.append(
        _run_check(
            "pytest-release-targeted",
            [
                python,
                "-m",
                "pytest",
                "-q",
                "tests/test_update_checker.py",
                "tests/test_settings.py",
                "tests/test_release_manifest_contract.py",
                "tests/test_qt_update_banner.py",
                "tests/test_verify_clean_machine_matrix.py",
            ],
            cwd=root,
            env=env,
        )
    )

    results.append(
        _run_check(
            "verify-release-update-flow",
            [python, "tools/qa/verify_release_update_flow.py"],
            cwd=root,
        )
    )

    if not args.skip_smoke:
        results.append(
            _run_check(
                "smoke-check-core",
                [
                    python,
                    "tools/install/common/smoke_check.py",
                    "--project-root",
                    ".",
                    "--profile",
                    "core",
                ],
                cwd=root,
            )
        )

    if not args.skip_powershell_parse:
        results.append(_powershell_parse_check(root))

    failed = [result for result in results if result.returncode != 0]
    print("\n[release] summary", flush=True)
    for result in results:
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"- {result.name}: {status} ({result.elapsed_seconds:.1f}s)", flush=True)

    if failed:
        print(
            "[release] failed checks: " + ", ".join(result.name for result in failed),
            flush=True,
        )
        print(f"[release] basetemp kept at: {temp_root}", flush=True)
        return 1

    print(f"[release] basetemp kept at: {temp_root}", flush=True)
    print("[release] all local release-readiness checks passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
