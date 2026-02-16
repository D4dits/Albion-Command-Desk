# Changelog

All notable changes to this project are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses semantic versioning.

## [Unreleased]

### Added
- Phase 0 execution tickets for UX/minimal-release work in `docs/UX_MINIMAL_RELEASE_PLAN.md`.
- Active Phase 0 milestone queue in `docs/DELIVERY_BACKLOG.md`.

### Changed
- Progress log in `docs/DELIVERY_BACKLOG.md` now tracks Phase 0 kickoff state.

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
