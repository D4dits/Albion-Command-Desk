# QA-004 Release Asset Smoke Checks

Goal: verify that release manifest assets are reachable per OS target.

## Source of truth

- Workflow: `.github/workflows/release-asset-smoke.yml`
- Script: `tools/qa/verify_release_artifact_matrix.py`

## Gate policy (current)

- **Blocker**: Windows release asset must be reachable.
- **Advisory**: Linux/macOS asset checks are warning-only until native package outputs are fully locked.

## Local validation commands

Run from repository root:

```
python .\tools\qa\verify_release_artifact_matrix.py --target-os windows
python .\tools\qa\verify_release_artifact_matrix.py --target-os linux
python .\tools\qa\verify_release_artifact_matrix.py --target-os macos
```

Optional custom manifest source:

```
python .\tools\qa\verify_release_artifact_matrix.py --target-os windows --manifest-url "file:///.../manifest.json"
```

## Exit codes

- `0` -> target OS has at least one reachable asset with valid kind.
- `1` -> asset mapping or URL checks failed.
- `2` -> manifest fetch/parsing failed.
