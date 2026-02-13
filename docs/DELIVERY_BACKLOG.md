# Delivery Backlog

This file is the single source of truth for planned work and execution order.
Update status checkboxes and notes after each implemented ticket.

## Rules

- Keep ticket order unless dependencies force a swap.
- Every ticket completion must also update `CHANGELOG.md` (`[Unreleased]`).
- If ticket scope changes, update this file in the same commit.

## Ticket Queue (Execution Order)

### ACD-REL-001 - Release metadata contract
- [x] Status: DONE
- Goal: define a stable app update metadata format used by installers and in-app checks.
- Files to modify:
  1. `docs/release/RELEASE_MANIFEST_SPEC.md` (new)
  2. `tools/release/manifest/manifest.example.json` (new)
  3. `README.md`
- Done when:
  - Manifest schema and sample are documented.
  - Fields for version, channel, changelog URL, and assets are defined.

### ACD-REL-002 - Windows bootstrap installer script
- [x] Status: DONE
- Goal: one command/script that installs prerequisites and starts the app on Windows.
- Files to modify:
  1. `tools/install/windows/install.ps1` (new)
  2. `tools/install/windows/README.md` (new)
  3. `README.md`
- Done when:
  - Script checks Python, creates venv, installs package with capture extras, and runs app.
  - Script exits with clear errors.

### ACD-REL-003 - Linux bootstrap installer script
- [x] Status: DONE
- Goal: one command/script for Linux setup and first run.
- Files to modify:
  1. `tools/install/linux/install.sh` (new)
  2. `tools/install/linux/README.md` (new)
  3. `README.md`
- Done when:
  - Script installs/validates dependencies, creates venv, installs package, starts app.
  - Non-root mode and distro caveats are documented.

### ACD-REL-004 - macOS bootstrap installer script
- [x] Status: DONE
- Goal: one command/script for macOS setup and first run.
- Files to modify:
  1. `tools/install/macos/install.sh` (new)
  2. `tools/install/macos/README.md` (new)
  3. `README.md`
- Done when:
  - Script validates Python + build deps, creates venv, installs package, starts app.
  - Apple Silicon/Intel notes are documented.

### ACD-REL-005 - Shared install smoke checks
- [x] Status: DONE
- Goal: add post-install validation for all platforms.
- Files to modify:
  1. `tools/install/common/smoke_check.py` (new)
  2. `tools/install/windows/install.ps1`
  3. `tools/install/linux/install.sh`
  4. `tools/install/macos/install.sh`
- Done when:
  - Script verifies CLI entrypoint and Qt startup probe.
  - Failures give actionable hints.

### ACD-REL-006 - In-app update check (read-only)
- [x] Status: DONE
- Goal: app can notify user that a newer version exists.
- Files to modify:
  1. `albion_dps/update/checker.py` (new)
  2. `albion_dps/qt/runner.py`
  3. `albion_dps/qt/ui/Main.qml`
- Done when:
  - App checks release metadata endpoint.
  - Non-blocking banner shows current/latest version and download link.

### ACD-REL-007 - Update settings and opt-out
- [ ] Status: TODO
- Goal: let users control update-check behavior.
- Files to modify:
  1. `albion_dps/settings.py`
  2. `albion_dps/qt/ui/Main.qml`
  3. `docs/TROUBLESHOOTING.md`
- Done when:
  - User can disable auto-check and trigger manual check.
  - Setting is persisted.

### ACD-REL-008 - CI publish helper for manifests
- [ ] Status: TODO
- Goal: automate generation and publication of release metadata.
- Files to modify:
  1. `.github/workflows/release-manifest.yml` (new)
  2. `tools/release/manifest/build_manifest.py` (new)
  3. `docs/release/RELEASE_MANIFEST_SPEC.md`
- Done when:
  - Workflow publishes manifest tied to release/tag artifacts.
  - Manifest includes checksum and release notes URL.

### ACD-REL-009 - Installer docs and support matrix
- [ ] Status: TODO
- Goal: keep install paths clear and consistent across platforms.
- Files to modify:
  1. `README.md`
  2. `docs/TROUBLESHOOTING.md`
  3. `docs/ARCHITECTURE.md`
- Done when:
  - README has one "Quick install" per platform.
  - Troubleshooting includes common setup and update errors.

### ACD-REL-010 - Stabilization and release checklist
- [ ] Status: TODO
- Goal: lock down repeatable release process.
- Files to modify:
  1. `docs/release/RELEASE_CHECKLIST.md` (new)
  2. `CHANGELOG.md`
  3. `README.md`
- Done when:
  - Checklist covers test, package, verify, publish, rollback.
  - Changelog entries are required in release prep.

## Progress Log

- 2026-02-13: backlog initialized.
- 2026-02-13: ACD-REL-001 completed (`RELEASE_MANIFEST_SPEC.md`, manifest example, README links).
- 2026-02-13: ACD-REL-002 completed (Windows installer script + docs + README quick bootstrap).
- 2026-02-13: ACD-REL-003 completed (Linux installer script + docs + README quick bootstrap).
- 2026-02-13: ACD-REL-004 completed (macOS installer script + docs + README quick bootstrap).
- 2026-02-13: ACD-REL-005 completed (shared smoke checks wired into Windows/Linux/macOS install scripts).
- 2026-02-13: ACD-REL-006 completed (manifest-based update checker + non-blocking UI banner).
