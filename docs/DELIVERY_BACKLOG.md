# Delivery Backlog

This file is the single source of truth for planned work and execution order.
Update status checkboxes and notes after each implemented ticket.

## Rules

- Keep ticket order unless dependencies force a swap.
- Every ticket completion must also update `CHANGELOG.md` (`[Unreleased]`).
- If ticket scope changes, update this file in the same commit.

## Active Milestone - Phase 0 (UX + Minimal Release)

### PH0-UXR-001 - Shell layout freeze and component map
- [x] Status: DONE
- Goal: lock one global shell structure and remove layout drift before visual redesign.
- Files:
  1. `docs/UX_MINIMAL_RELEASE_PLAN.md`
  2. `docs/ARCHITECTURE.md`
  3. `albion_dps/qt/ui/Main.qml`
- Done when:
  - Header zones/order are fully documented and frozen.
  - Reusable component extraction map is defined for `Main.qml`.
  - Top-level tabs keep stable action placement.

### PH0-REL-001 - Dependency profile freeze (core vs capture)
- [x] Status: DONE
- Goal: separate required core dependencies from optional live-capture dependencies.
- Files:
  1. `pyproject.toml`
  2. `tools/install/windows/install.ps1`
  3. `tools/install/linux/install.sh`
  4. `tools/install/macos/install.sh`
  5. `docs/TROUBLESHOOTING.md`
- Done when:
  - Install profiles are consistent across all bootstrap scripts.
  - Core profile runs without capture extras.
  - Capture-missing path is handled with clear diagnostics.

### PH0-REL-002 - Release packaging strategy lock per OS
- [x] Status: DONE
- Goal: freeze artifact strategy and release gates for Windows/Linux/macOS.
- Files:
  1. `docs/release/RELEASE_CHECKLIST.md`
  2. `docs/release/RELEASE_MANIFEST_SPEC.md`
  3. `.github/workflows/bootstrap-smoke.yml`
  4. `.github/workflows/release-manifest.yml`
- Done when:
  - Packaging target per OS is documented and approved.
  - CI checks are mapped to every artifact.
  - Publish blockers vs warnings are explicitly defined.

## Active Milestone - Phase 1 (UI Refactor Foundation)

### PH1-UXR-010 - Extract/declare QML design tokens
- [x] Status: DONE
- Goal: centralize visual constants before deeper component refactor.
- Files:
  1. `albion_dps/qt/ui/Theme.qml`
  2. `albion_dps/qt/ui/Main.qml`
  3. `docs/UX_MINIMAL_RELEASE_PLAN.md`
- Done when:
  - core design tokens exist in a dedicated QML file
  - main shell consumes shared theme tokens instead of ad-hoc literals

### PH1-UXR-011 - Normalize header/nav/action zones
- [x] Status: DONE
- Goal: finish normalizing all header and navigation interactions around frozen shell map.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/ShellTabButton.qml`
  3. `docs/ARCHITECTURE.md`

### PH1-UXR-012 - Card/table visual unification
- [x] Status: DONE
- Goal: align card and table primitives to one visual language.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`
  3. `albion_dps/qt/ui/CardPanel.qml`
  4. `albion_dps/qt/ui/TableSurface.qml`

### PH1-UXR-013 - Responsive breakpoints and overflow handling
- [x] Status: DONE
- Goal: enforce stable behavior for small/medium/large app widths.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`
  3. `docs/TROUBLESHOOTING.md`

## Active Milestone - Phase 3 (Stabilization and ship)

### QA-001 - Regression pass (meter/scanner/market/live/replay)
- [x] Status: DONE
- Goal: run deterministic grouped regression checks across core app domains.
- Files:
  1. `tools/qa/run_regression_suite.py`
  2. `docs/qa/QA_REGRESSION_PASS.md`

### QA-002 - Clean machine install tests (Win/Linux/macOS)
- [x] Status: DONE
- Goal: validate bootstrap/install path on clean OS runners and local clean profile.
- Files:
  1. `tools/qa/verify_clean_machine_matrix.py`
  2. `docs/qa/QA_CLEAN_MACHINE.md`
  3. `docs/release/RELEASE_CHECKLIST.md`

### QA-003 - Release + manifest + update banner validation
- [x] Status: DONE
- Goal: verify release metadata publication and in-app update signaling end-to-end.
- Files:
  1. `tests/test_release_manifest_contract.py`
  2. `tests/test_qt_update_banner.py`
  3. `tools/qa/verify_release_update_flow.py`
  4. `docs/qa/QA_RELEASE_UPDATE.md`
  5. `docs/release/RELEASE_CHECKLIST.md`

## Active Milestone - Phase PH2-UXR (Visual modernization)

### PH2-UXR-020 - Visual direction + token expansion
- [x] Status: DONE
- Goal: define full semantic token set for modern/minimal UI styling.
- Files:
  1. `albion_dps/qt/ui/Theme.qml`
  2. `docs/ARCHITECTURE.md`
  3. `docs/UX_MINIMAL_RELEASE_PLAN.md`

### PH2-UXR-021 - Button system
- [x] Status: DONE
- Goal: standardize button variants/states and remove legacy gray controls.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/AppButton.qml`
  3. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-022 - Input/select/spinbox refresh
- [x] Status: DONE
- Goal: unify form control appearance and interaction states.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-023 - Card layout hierarchy cleanup
- [ ] Status: TODO
- Goal: reduce border noise and enforce cleaner panel depth hierarchy.
- Files:
  1. `albion_dps/qt/ui/CardPanel.qml`
  2. `albion_dps/qt/ui/TableSurface.qml`
  3. `albion_dps/qt/ui/Main.qml`

### PH2-UXR-024 - Table redesign
- [ ] Status: TODO
- Goal: improve table readability and consistency across Meter/Market/History.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-025 - Header + action bar polish
- [ ] Status: TODO
- Goal: stabilize action placement and visual priority at all breakpoints.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-026 - Color semantics for data
- [ ] Status: TODO
- Goal: enforce semantic color mapping for KPI status and warnings.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-027 - Empty/loading/error states
- [ ] Status: TODO
- Goal: add intentional placeholders and recovery actions.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `docs/TROUBLESHOOTING.md`

### PH2-UXR-028 - Subtle micro-interactions
- [ ] Status: TODO
- Goal: add lightweight transitions to improve perceived quality.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-029 - Accessibility + contrast pass
- [ ] Status: TODO
- Goal: ensure focus visibility and readable contrast in all themes/states.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`
  3. `docs/TROUBLESHOOTING.md`

### PH2-UXR-030 - Visual regression baseline
- [ ] Status: TODO
- Goal: capture reference screenshots/checklist to prevent UI regressions.
- Files:
  1. `assets/`
  2. `README.md`
  3. `docs/release/RELEASE_CHECKLIST.md`

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
- [x] Status: DONE
- Goal: let users control update-check behavior.
- Files to modify:
  1. `albion_dps/settings.py`
  2. `albion_dps/qt/ui/Main.qml`
  3. `docs/TROUBLESHOOTING.md`
- Done when:
  - User can disable auto-check and trigger manual check.
  - Setting is persisted.

### ACD-REL-008 - CI publish helper for manifests
- [x] Status: DONE
- Goal: automate generation and publication of release metadata.
- Files to modify:
  1. `.github/workflows/release-manifest.yml` (new)
  2. `tools/release/manifest/build_manifest.py` (new)
  3. `docs/release/RELEASE_MANIFEST_SPEC.md`
- Done when:
  - Workflow publishes manifest tied to release/tag artifacts.
  - Manifest includes checksum and release notes URL.

### ACD-REL-009 - Installer docs and support matrix
- [x] Status: DONE
- Goal: keep install paths clear and consistent across platforms.
- Files to modify:
  1. `README.md`
  2. `docs/TROUBLESHOOTING.md`
  3. `docs/ARCHITECTURE.md`
- Done when:
  - README has one "Quick install" per platform.
  - Troubleshooting includes common setup and update errors.

### ACD-REL-010 - Stabilization and release checklist
- [x] Status: DONE
- Goal: lock down repeatable release process.
- Files to modify:
  1. `docs/release/RELEASE_CHECKLIST.md` (new)
  2. `CHANGELOG.md`
  3. `README.md`
- Done when:
  - Checklist covers test, package, verify, publish, rollback.
  - Changelog entries are required in release prep.

## Post-Backlog Operational Items

### OPS-001 - First manifest publish runbook
- [x] Status: DONE
- Scope:
  - Add helper script for publishing first manifest to an existing GitHub release.
- Files:
  - `tools/release/manifest/publish_manifest.ps1`
  - `docs/release/RELEASE_MANIFEST_SPEC.md`

### OPS-002 - Clean-machine bootstrap validation
- [x] Status: DONE
- Scope:
  - Add CI workflow executing bootstrap scripts on clean Windows/Linux/macOS runners.
- Files:
  - `.github/workflows/bootstrap-smoke.yml`
  - `README.md`

## Progress Log

- 2026-02-17: PH2-UXR-022 completed (shared form control components + input tokenization + Main.qml migration).
- 2026-02-17: PH2-UXR-021 completed (new `AppButton` variant system + migration of `Main.qml` button usage to shared control).
- 2026-02-17: PH2-UXR-020 completed (semantic token expansion in `Theme.qml` + architecture-level visual direction/taxonomy notes).
- 2026-02-17: Added PH2-UXR visual modernization phase (020-030) and locked execution order for commit-per-ticket flow.
- 2026-02-16: QA-003 completed (manifest contract test + update banner test + release/update validation runbook).
- 2026-02-16: QA-002 completed (clean-machine matrix verifier + QA runbook + release checklist gate command).
- 2026-02-16: QA-001 completed (grouped regression runner + QA runbook for meter/scanner/market/live/replay).
- 2026-02-16: PH1-UXR-013 completed (responsive shell breakpoints + narrow/compact overflow handling in header/nav/market panels).
- 2026-02-16: PH1-UXR-012 completed (shared `CardPanel`/`TableSurface` primitives + tokenized table row/header colors wired across Meter/Scanner/Market).
- 2026-02-16: PH1-UXR-011 completed (centered shell nav zone + shared tab button component for shell/market tabs).
- 2026-02-16: PH1-UXR-010 completed (new `Theme.qml` tokens and `Main.qml` token wiring baseline).
- 2026-02-16: PH0-REL-002 completed (packaging strategy + CI gate map locked in release docs/workflows).
- 2026-02-16: PH0-REL-001 completed (install profiles frozen: `core` default, `capture` optional; bootstrap scripts + docs aligned).
- 2026-02-16: PH0-UXR-001 completed (shell layout contract frozen in docs + `Main.qml` zone map IDs).
- 2026-02-16: Phase 0 kickoff started (PH0-UXR-001 IN PROGRESS, PH0-REL-001/002 queued).
- 2026-02-13: backlog initialized.
- 2026-02-13: ACD-REL-001 completed (`RELEASE_MANIFEST_SPEC.md`, manifest example, README links).
- 2026-02-13: ACD-REL-002 completed (Windows installer script + docs + README quick bootstrap).
- 2026-02-13: ACD-REL-003 completed (Linux installer script + docs + README quick bootstrap).
- 2026-02-13: ACD-REL-004 completed (macOS installer script + docs + README quick bootstrap).
- 2026-02-13: ACD-REL-005 completed (shared smoke checks wired into Windows/Linux/macOS install scripts).
- 2026-02-13: ACD-REL-006 completed (manifest-based update checker + non-blocking UI banner).
- 2026-02-13: ACD-REL-007 completed (persistent auto-check preference + manual check trigger + troubleshooting docs).
- 2026-02-13: ACD-REL-008 completed (manifest builder + release-manifest workflow + publishing docs).
- 2026-02-13: ACD-REL-009 completed (README support matrix + installer/update troubleshooting + architecture delivery notes).
- 2026-02-13: ACD-REL-010 completed (release checklist and changelog gate added to docs).
- 2026-02-13: OPS-001 completed (Windows manifest publish helper script).
- 2026-02-13: OPS-002 completed (bootstrap smoke workflow on clean CI runners).
