# Release Checklist

Use this checklist before publishing a new release.

## 1) Version and changelog

- [ ] Update version in `pyproject.toml`.
- [ ] Add release notes to `CHANGELOG.md` (move items from `[Unreleased]`).
- [ ] Verify changelog links and release date format.

## 2) Local validation

- [ ] Run core tests:
  - `python -m pytest -q --ignore=tests/test_qt_smoke.py`
- [ ] Run update/settings tests:
  - `python -m pytest -q tests/test_update_checker.py tests/test_settings.py`
- [ ] Validate install scripts syntax:
  - Windows parser check (`install.ps1`)
  - Linux/macOS shell syntax on native shell

## 3) Build and packaging

- [ ] Build target artifacts for intended platforms.
- [ ] Verify each artifact launches and can open the Qt UI.
- [ ] Verify capture mode works on target platform (live/replay).

## 4) Release publication

- [ ] Create Git tag `vX.Y.Z`.
- [ ] Publish GitHub Release with artifacts attached.
- [ ] Run/confirm `.github/workflows/release-manifest.yml`.
- [ ] Verify `manifest.json` includes:
  - version,
  - release URL,
  - changelog URL,
  - checksums (`sha256`) for assets.

## 5) Post-release verification

- [ ] Fresh install test (Windows/Linux/macOS script path).
- [ ] Existing install update-check test (header banner + manual check).
- [ ] Validate docs are aligned (`README.md`, `docs/TROUBLESHOOTING.md`).

## 6) Rollback plan

- [ ] Keep previous stable release asset links available.
- [ ] If critical issue found, publish hotfix tag and update manifest quickly.
- [ ] Record incident notes in `CHANGELOG.md` and issue tracker.
