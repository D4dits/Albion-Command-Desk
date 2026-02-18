from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass


REQUIRED_JOBS = ("windows-core", "linux-core", "macos-core")
ADVISORY_JOBS = ("linux-capture-advisory", "macos-capture-advisory")
REQUIRED_EVIDENCE_ARTIFACTS = (
    "bootstrap-smoke-windows-core",
    "bootstrap-smoke-linux-core",
    "bootstrap-smoke-macos-core",
)


@dataclass
class JobState:
    name: str
    conclusion: str


@dataclass
class ArtifactState:
    name: str
    expired: bool


def _run_gh(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        details = stderr or stdout or "unknown gh error"
        raise RuntimeError(f"{' '.join(command)} failed: {details}")
    return completed.stdout


def _latest_bootstrap_run_id() -> int:
    raw = _run_gh(
        [
            "gh",
            "run",
            "list",
            "--workflow",
            "bootstrap-smoke.yml",
            "--branch",
            "main",
            "--limit",
            "20",
            "--json",
            "databaseId,status,conclusion",
        ]
    )
    runs = json.loads(raw)
    for run in runs:
        if str(run.get("status", "")).lower() == "completed":
            return int(run["databaseId"])
    raise RuntimeError("no completed bootstrap-smoke run found on main")


def _repo_name_with_owner() -> str:
    raw = _run_gh(["gh", "repo", "view", "--json", "nameWithOwner"])
    payload = json.loads(raw)
    value = str(payload.get("nameWithOwner", "")).strip()
    if not value:
        raise RuntimeError("unable to resolve repository from gh")
    return value


def _load_job_states(run_id: int) -> dict[str, JobState]:
    raw = _run_gh(["gh", "run", "view", str(run_id), "--json", "jobs"])
    payload = json.loads(raw)
    jobs = payload.get("jobs", [])
    result: dict[str, JobState] = {}
    for job in jobs:
        name = str(job.get("name", "")).strip()
        conclusion = str(job.get("conclusion", "")).strip().lower()
        if name:
            result[name] = JobState(name=name, conclusion=conclusion)
    return result


def _load_artifacts(run_id: int) -> dict[str, ArtifactState]:
    repo = _repo_name_with_owner()
    raw = _run_gh(["gh", "api", f"repos/{repo}/actions/runs/{run_id}/artifacts"])
    payload = json.loads(raw)
    artifacts = payload.get("artifacts", [])
    result: dict[str, ArtifactState] = {}
    for artifact in artifacts:
        name = str(artifact.get("name", "")).strip()
        if not name:
            continue
        expired = bool(artifact.get("expired", False))
        result[name] = ArtifactState(name=name, expired=expired)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify clean-machine bootstrap matrix from bootstrap-smoke workflow."
    )
    parser.add_argument(
        "--run-id",
        type=int,
        default=0,
        help="Optional explicit GitHub Actions run ID. Defaults to latest completed run on main.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        run_id = int(args.run_id) if int(args.run_id) > 0 else _latest_bootstrap_run_id()
        jobs = _load_job_states(run_id)
        artifacts = _load_artifacts(run_id)
    except Exception as exc:
        print(f"[qa] unable to verify bootstrap matrix: {exc}", file=sys.stderr)
        return 2

    failures: list[str] = []
    print(f"[qa] bootstrap-smoke run id: {run_id}")
    print("[qa] required jobs:")
    for name in REQUIRED_JOBS:
        state = jobs.get(name)
        conclusion = state.conclusion if state else "missing"
        print(f"- {name}: {conclusion}")
        if conclusion != "success":
            failures.append(name)

    print("[qa] advisory jobs:")
    for name in ADVISORY_JOBS:
        state = jobs.get(name)
        conclusion = state.conclusion if state else "missing"
        print(f"- {name}: {conclusion}")

    print("[qa] required evidence artifacts:")
    for name in REQUIRED_EVIDENCE_ARTIFACTS:
        state = artifacts.get(name)
        if state is None:
            print(f"- {name}: missing")
            failures.append(f"artifact:{name}")
            continue
        if state.expired:
            print(f"- {name}: expired")
            failures.append(f"artifact:{name}")
            continue
        print(f"- {name}: ok")

    if failures:
        print(f"[qa] clean-machine matrix FAILED: {', '.join(failures)}")
        return 1
    print("[qa] clean-machine matrix PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
