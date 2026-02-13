# Changelog

All notable changes to this project are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses semantic versioning.

## [Unreleased]

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

### Changed
- `README.md` docs section now links to the delivery backlog and changelog.
- `README.md` now includes a Release Metadata section for update/install integration.
- `README.md` now includes recommended Windows bootstrap install command.
- `README.md` now includes recommended Linux bootstrap install command.
- `README.md` now includes recommended macOS bootstrap install command.
- Windows/Linux/macOS bootstrap scripts now run a common post-install smoke check.
- Qt UI now shows a non-blocking update banner when a newer release is detected.

## [0.1.0] - 2026-02-11

### Added
- Initial public release of Albion Command Desk (Qt UI).
- DPS/HPS meter with live capture and replay support.
- Party-aware combat filtering and battle history.
- Scanner helper integration and market workspace.
