# Release Runbook

This runbook defines the release, hotfix, and rollback path for Albion Command Desk.

## 1) Standard release flow

1. Prepare code and changelog on `main`.
2. Run local gates:
   - `.\venv\Scripts\python -m pytest -q --ignore=tests/test_qt_smoke.py`
   - `.\venv\Scripts\python -m pytest -q tests/test_update_checker.py tests/test_settings.py tests/test_release_manifest_contract.py tests/test_qt_update_banner.py tests/test_verify_clean_machine_matrix.py`
   - `.\venv\Scripts\python tools\qa\verify_release_update_flow.py`
3. Create and push tag:
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`
4. Build and publish GitHub release assets using canonical names from `docs/release/RELEASE_CHECKLIST.md`.
   - Windows bootstrap installer:
     - `powershell -ExecutionPolicy Bypass -File .\tools\release\windows\build_bootstrap_setup.ps1 -ReleaseTag vX.Y.Z`
   - Upload generated EXE from `dist\installer\`.
5. Run `release-manifest.yml` and confirm `manifest.json` is attached.
6. Run `bootstrap-smoke.yml` and confirm:
   - required jobs pass: `windows-core`, `linux-core`, `macos-core`
   - required evidence artifacts exist: `bootstrap-smoke-windows-core`, `bootstrap-smoke-linux-core`, `bootstrap-smoke-macos-core`
   - `python .\tools\qa\verify_clean_machine_matrix.py` exits `0`.

## 2) Mark last-known-good pointer

After release verification passes, update the rollback pointer:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\release\manifest\set_last_known_good.ps1 -Tag vX.Y.Z
```

Commit and push `tools/release/manifest/last_known_good.json`.

## 3) Hotfix flow

1. Branch from `main`, implement minimal fix.
2. Run same local and CI gates as standard release.
3. Tag hotfix (`vX.Y.Z+1`) and publish release.
4. Update LKG pointer to hotfix tag with `set_last_known_good.ps1`.

## 4) Manifest rollback (target under 10 minutes)

If latest manifest is broken, restore from LKG pointer with one command:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\release\manifest\rollback_manifest.ps1
```

What it does:
- reads `tools/release/manifest/last_known_good.json`,
- downloads the referenced `manifest.json` asset from the good tag,
- uploads it to the current latest release as `manifest.json` (`--clobber`).

Optional explicit target:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\release\manifest\rollback_manifest.ps1 -TargetTag vX.Y.Z
```

## 5) Post-rollback checks

1. Verify endpoint:
   - `https://github.com/D4dits/Albion-Command-Desk/releases/latest/download/manifest.json`
2. Validate update flow:
   - `.\venv\Scripts\python tools\qa\verify_release_update_flow.py`
3. Log incident in `CHANGELOG.md` and open follow-up issue.
