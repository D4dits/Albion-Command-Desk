from __future__ import annotations

from types import SimpleNamespace

from tools.qa import verify_clean_machine_matrix as matrix


def _job_states_ok() -> dict[str, matrix.JobState]:
    return {
        "windows-core": matrix.JobState(name="windows-core", conclusion="success"),
        "linux-core": matrix.JobState(name="linux-core", conclusion="success"),
        "macos-core": matrix.JobState(name="macos-core", conclusion="success"),
    }


def _artifacts_ok() -> dict[str, matrix.ArtifactState]:
    return {
        "bootstrap-smoke-windows-core": matrix.ArtifactState(
            name="bootstrap-smoke-windows-core",
            expired=False,
        ),
        "bootstrap-smoke-linux-core": matrix.ArtifactState(
            name="bootstrap-smoke-linux-core",
            expired=False,
        ),
        "bootstrap-smoke-macos-core": matrix.ArtifactState(
            name="bootstrap-smoke-macos-core",
            expired=False,
        ),
    }


def test_main_passes_when_required_jobs_and_artifacts_exist(monkeypatch) -> None:
    monkeypatch.setattr(matrix, "_parse_args", lambda: SimpleNamespace(run_id=123))
    monkeypatch.setattr(matrix, "_load_job_states", lambda run_id: _job_states_ok())
    monkeypatch.setattr(matrix, "_load_artifacts", lambda run_id: _artifacts_ok())

    assert matrix.main() == 0


def test_main_fails_when_required_artifact_missing(monkeypatch) -> None:
    artifacts = _artifacts_ok()
    artifacts.pop("bootstrap-smoke-linux-core")
    monkeypatch.setattr(matrix, "_parse_args", lambda: SimpleNamespace(run_id=123))
    monkeypatch.setattr(matrix, "_load_job_states", lambda run_id: _job_states_ok())
    monkeypatch.setattr(matrix, "_load_artifacts", lambda run_id: artifacts)

    assert matrix.main() == 1
