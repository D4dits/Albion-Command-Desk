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

- [ ] Build target artifacts for intended platforms (frozen strategy):
  - Windows x86_64: installer asset (`kind=installer`) - **BLOCKER**
  - Linux x86_64: archive/bootstrap asset (`kind=archive` or `kind=bootstrap-script`) - warning only in Phase 0
  - macOS (x86_64/arm64): archive/bootstrap asset (`kind=archive` or `kind=bootstrap-script`) - warning only in Phase 0
- [ ] Verify each produced artifact launches and opens Qt UI.
- [ ] Verify replay mode works on each OS target.
- [ ] Verify live capture mode on at least one environment per OS family (advisory for CI; blocker for manual release sign-off).

## 4) CI gate mapping (Phase 0 lock)

- [ ] `bootstrap-smoke.yml`:
  - `windows-core`, `linux-core`, `macos-core` jobs must pass (**BLOCKER**).
  - `linux-capture-advisory`, `macos-capture-advisory` are warning-only.
- [ ] `release-manifest.yml`:
  - Manifest build must pass (**BLOCKER**).
  - Manifest strategy validation requires Windows installer asset (**BLOCKER**).
  - Missing Linux/macOS assets is warning-only in workflow logs.

## 5) Release publication

- [ ] Create Git tag `vX.Y.Z`.
- [ ] Publish GitHub Release with artifacts attached.
- [ ] Run/confirm `.github/workflows/release-manifest.yml`.
- [ ] Verify `manifest.json` includes:
  - version,
  - release URL,
  - changelog URL,
  - checksums (`sha256`) for assets.

## 6) Post-release verification

- [ ] Fresh install test (Windows/Linux/macOS script path).
- [ ] Existing install update-check test (header banner + manual check).
- [ ] Validate docs are aligned (`README.md`, `docs/TROUBLESHOOTING.md`).

## 7) Rollback plan

- [ ] Keep previous stable release asset links available.
- [ ] If critical issue found, publish hotfix tag and update manifest quickly.
- [ ] Record incident notes in `CHANGELOG.md` and issue tracker.
