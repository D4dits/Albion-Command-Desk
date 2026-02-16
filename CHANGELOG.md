# Changelog

All notable changes to this project are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses semantic versioning.

## [Unreleased]

### Added
- Phase 0 execution tickets for UX/minimal-release work in `docs/UX_MINIMAL_RELEASE_PLAN.md`.
- Active Phase 0 milestone queue in `docs/DELIVERY_BACKLOG.md`.
- `core` GUI runtime command in `albion_dps/cli.py` for non-capture startup.
- Install profile contract in `pyproject.toml` (`core` default, `capture` optional).
- QML design token source in `albion_dps/qt/ui/Theme.qml`.
- Shared tab styling component in `albion_dps/qt/ui/ShellTabButton.qml`.
- Shared card container component in `albion_dps/qt/ui/CardPanel.qml`.
- Shared inset/table container component in `albion_dps/qt/ui/TableSurface.qml`.
- Grouped regression runner for Phase 3 QA in `tools/qa/run_regression_suite.py`.
- QA regression runbook in `docs/qa/QA_REGRESSION_PASS.md`.
- Clean-machine CI matrix verifier in `tools/qa/verify_clean_machine_matrix.py`.
- QA clean-machine runbook in `docs/qa/QA_CLEAN_MACHINE.md`.
- Release/update flow verifier in `tools/qa/verify_release_update_flow.py`.
- Release/update QA runbook in `docs/qa/QA_RELEASE_UPDATE.md`.
- Manifest contract regression test in `tests/test_release_manifest_contract.py`.
- Qt update-banner state tests in `tests/test_qt_update_banner.py`.

### Changed
- Progress log in `docs/DELIVERY_BACKLOG.md` now tracks Phase 0 kickoff state.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` marks `UXR-001` as completed and documents delivery notes.
- `docs/ARCHITECTURE.md` now defines the frozen Phase 0 Qt shell layout contract.
- `albion_dps/qt/ui/Main.qml` now uses explicit shell zone IDs and fixed ordering for header actions.
- `albion_dps/qt/runner.py` now supports `core` mode startup without capture backend.
- Windows/Linux/macOS bootstrap installers now share `core|capture` profile selection.
- Installer docs and root README now document profile-based install flow.
- `docs/TROUBLESHOOTING.md` now includes profile-based recovery commands.
- `docs/release/RELEASE_CHECKLIST.md` now locks Phase 0 packaging targets and blocker/warning release gates.
- `.github/workflows/bootstrap-smoke.yml` now maps mandatory core checks and advisory capture checks per OS.
- `.github/workflows/release-manifest.yml` now validates manifest assets against Phase 0 release strategy.
- `docs/release/RELEASE_MANIFEST_SPEC.md` now documents manifest blocker/warning policy.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` and `docs/DELIVERY_BACKLOG.md` now mark `REL-002` as completed.
- `albion_dps/qt/ui/Main.qml` now consumes shared theme tokens for app shell and baseline styles.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` and `docs/DELIVERY_BACKLOG.md` now start Phase 1 with `UXR-010` completed.
- `docs/ARCHITECTURE.md` now documents centralized QML theme tokens.
- `albion_dps/qt/ui/Main.qml` now centers top navigation in a width-clamped shell nav zone.
- `albion_dps/qt/ui/Main.qml` now reuses `ShellTabButton` for shell and market tab bars.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` and `docs/DELIVERY_BACKLOG.md` now mark `UXR-011` as completed.
- `albion_dps/qt/ui/Main.qml` now applies shared card/table primitives with unified table row/header token usage across Meter/Scanner/Market.
- `albion_dps/qt/ui/Theme.qml` now includes explicit table/header/control surface tokens for the unified Phase 1 visual system.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` and `docs/DELIVERY_BACKLOG.md` now mark `UXR-012` as completed.
- `docs/ARCHITECTURE.md` now documents `CardPanel`/`TableSurface` shared UI primitives.
- `albion_dps/qt/ui/Main.qml` now applies compact/narrow breakpoints for shell/header/nav and market panel widths to reduce overflow on small windows.
- `albion_dps/qt/ui/Theme.qml` now exposes shared breakpoint tokens for responsive layout behavior.
- `docs/TROUBLESHOOTING.md` now includes compact-layout guidance for small-window table workflows.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` and `docs/DELIVERY_BACKLOG.md` now mark `UXR-013` as completed.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` and `docs/DELIVERY_BACKLOG.md` now mark `QA-001` as completed.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` and `docs/DELIVERY_BACKLOG.md` now mark `QA-002` as completed.
- `docs/release/RELEASE_CHECKLIST.md` now includes the clean-machine matrix verification command.
- `docs/UX_MINIMAL_RELEASE_PLAN.md` and `docs/DELIVERY_BACKLOG.md` now mark `QA-003` as completed.
- `docs/release/RELEASE_CHECKLIST.md` now includes release-manifest/update-banner validation commands.

## [0.1.14] - 2026-02-13

### Added
- `docs/DELIVERY_BACKLOG.md` as the canonical ticket queue with execution order.
- Changelog policy: each completed ticket must update this file.
- Release update contract spec: `docs/release/RELEASE_MANIFEST_SPEC.md`.
- Example release manifest payload: `tools/release/manifest/manifest.example.json`.
- Windows bootstrap installer script: `tools/install/windows/install.ps1`.
- Windows installer script documentation: `tools/install/windows/README.md`.
- Linux bootstrap installer script: `tools/install/linux/install.sh`.
- Linux installer script documentation: `tools/install/linux/README.md`.
- macOS bootstrap installer script: `tools/install/macos/install.sh`.
- macOS installer script documentation: `tools/install/macos/README.md`.
- Shared install smoke check runner: `tools/install/common/smoke_check.py`.
- Manifest-based update checker module: `albion_dps/update/checker.py`.
- Persistent app settings store: `albion_dps/settings.py`.
- Release manifest builder script: `tools/release/manifest/build_manifest.py`.
- Release manifest CI workflow: `.github/workflows/release-manifest.yml`.
- Release process checklist: `docs/release/RELEASE_CHECKLIST.md`.
- Manifest publish helper script (Windows): `tools/release/manifest/publish_manifest.ps1`.
- Clean-machine bootstrap validation workflow: `.github/workflows/bootstrap-smoke.yml`.
- Windows Npcap runtime detection module: `albion_dps/capture/npcap_runtime.py`.
- Branding generation script from source art: `tools/branding/render_brand_from_logo.ps1`.
- Tests for Npcap runtime detection: `tests/test_npcap_runtime.py`.

### Changed
- `README.md` docs section now links to the delivery backlog and changelog.
- `README.md` now includes a Release Metadata section for update/install integration.
- `README.md` now includes recommended Windows bootstrap install command.
- `README.md` now includes recommended Linux bootstrap install command.
- `README.md` now includes recommended macOS bootstrap install command.
- Windows/Linux/macOS bootstrap scripts now run a common post-install smoke check.
- Qt UI now shows a non-blocking update banner when a newer release is detected.
- Qt header now includes `Auto update` toggle and `Check now` manual trigger.
- Update-check preference is persisted between runs.
- `docs/TROUBLESHOOTING.md` now includes update-settings and config path details.
- `docs/release/RELEASE_MANIFEST_SPEC.md` now includes publication workflow and build command.
- `README.md` now includes an install support matrix for Windows/Linux/macOS bootstrap scripts.
- `docs/TROUBLESHOOTING.md` now includes a dedicated installer/update error map.
- `docs/ARCHITECTURE.md` now includes install/update delivery components.
- `README.md` docs section now links `docs/release/RELEASE_CHECKLIST.md`.
- `README.md` release-metadata section now references manifest publish helper and bootstrap smoke CI.
- `publish_manifest.ps1` now omits `--min-supported-version` when not provided (no manual workaround needed).
- `bootstrap-smoke.yml` now runs `install.ps1` directly on Windows, uses a workspace-local venv path, and installs full Qt runtime libs on Linux.
- `tools/install/windows/install.ps1` now resolves alternative `python*.exe` names in venvs and retries creation with `--copies` when needed.
- `tools/install/windows/install.ps1` now validates `VenvPath` defensively and logs the resolved venv path for CI diagnostics.
- `tools/install/windows/install.ps1` now handles missing venv Python without calling `Test-Path` on `$null`.
- `tools/install/windows/install.ps1` now falls back to `virtualenv` when `python -m venv` produces no usable interpreter on Windows CI.
- `tools/install/windows/install.ps1` now treats launcher commands as string arrays (not character arrays), fixing broken interpreter invocation in CI.
- `tools/install/windows/install.ps1` now prints launcher commands and exit codes to simplify bootstrap CI diagnostics.
- `tools/install/windows/install.ps1` now passes launcher command arguments correctly (`-m venv`, `-m pip`, etc.) after renaming the internal args parameter.
- `tools/install/windows/install.ps1` now supports `-SkipCaptureExtras` for environments without Npcap headers.
- `bootstrap-smoke.yml` now uses `-SkipCaptureExtras` on Windows to validate installer flow without external SDK downloads.
- `run_qt` now validates Windows Npcap runtime before `live` start, logs detected install location, and shows download link when missing.
- Brand assets and app icon now derive from source logo art using the current Albion Command Desk branding set.
- README hero graphic now uses `assets/Logo.png`.
- `tools/branding/render_brand_from_logo.ps1` now requires explicit `-Source` input path.
- Update checker default endpoint now points to release asset `releases/latest/download/manifest.json`.
- Qt runner now prioritizes `command_desk_icon.ico` on Windows and logs icon source path at startup.

## [0.1.0] - 2026-02-11

### Added
- Initial public release of Albion Command Desk (Qt UI).
- DPS/HPS meter with live capture and replay support.
- Party-aware combat filtering and battle history.
- Scanner helper integration and market workspace.
