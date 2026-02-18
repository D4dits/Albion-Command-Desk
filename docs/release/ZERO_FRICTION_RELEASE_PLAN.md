# Zero-Friction Release Plan

Goal: make ACD install/run/update with one command or one installer click on Windows, Linux, and macOS, with no manual dependency hunting for core usage.

## Out of Scope

- Any in-game overlay, client injection, memory editing, or gameplay automation.
- Releasing nonessential package formats before primary per-OS artifact is stable.
- Bundling third-party capture runtimes when license/distribution terms are unclear.

## Success Criteria

- New user can install and launch `core` mode without reading troubleshooting docs.
- Live capture remains optional; missing capture runtime is handled with clear UI guidance, not a crash.
- Release artifacts are consistent and discoverable from the manifest (`releases/latest/download/manifest.json`).
- CI validates artifact availability and clean-machine bootstrap path per OS before marking release as healthy.
- Median clean install + first launch time is under 5 minutes on CI baseline machines.
- Crash-free startup rate in `core` mode is 100% on release-candidate smoke runs.

## Product Contract

- `core` profile: always supported, no packet-capture prerequisite.
- `capture` profile: best-effort auto-detect, explicit guidance for missing runtime.
- In-app update check points to a stable installer/bootstrap asset per platform.
- Any blocked dependency must degrade to `core` with a visible reason.

## Ticket Governance

- Every ticket must have: `owner`, `status` (`todo`, `in_progress`, `blocked`, `done`), and `target_release`.
- Default owner is `@maintainer` until reassigned.
- Status updates are required in the same commit that changes implementation scope.

## Critical Path (Do First)

1. `PH4-REL-040` - freeze artifact matrix and naming.
2. `PH4-REL-041` - align bootstrap scripts with artifact contract.
3. `PH4-REL-043` - enforce guaranteed core fallback.
4. Then continue with update UX (`PH4-REL-044`, `PH4-REL-045`) and full QA/ops tickets.

## Target Distribution Shape

### Windows
- Primary artifact: signed installer (`.exe`) with bundled app runtime.
- Optional capture setup: detect Npcap runtime; show guided install action if missing.
- No mandatory manual installation for `core`.

### Linux
- Primary artifact: AppImage (plus optional `.deb` for convenience).
- Capture dependency check: detect `libpcap`; continue in `core` when missing.

### macOS
- Primary artifact: signed `.app` in `.dmg`.
- Capture dependency check: detect runtime capability; continue in `core` when missing.

## Delivery Phases

## Phase 4A - Packaging Baseline

### PH4-REL-040 - Freeze final artifact matrix
- Owner: `@maintainer`
- Status: `done`
- Target release: `v0.2.0`
- Define one "recommended" artifact per OS and optional secondary artifacts.
- Document exact naming conventions consumed by manifest/update checker.
- Done when release checklist includes a deterministic artifact table.

### PH4-REL-041 - Bootstrap parity with packaged installers
- Owner: `@maintainer`
- Status: `done`
- Target release: `v0.2.0`
- Align `tools/install/*` scripts with shipped artifact names and profile flags.
- Ensure bootstrap can run fully non-interactive for CI.
- Done when all bootstrap scripts pass smoke checks with `core`.

## Phase 4B - Runtime Dependency UX

### PH4-REL-042 - Capture runtime detector hardening
- Owner: `@maintainer`
- Status: `done`
- Target release: `v0.2.0`
- Add explicit detector status states: `available`, `missing`, `blocked`, `unknown`.
- Provide "Install runtime" or "Open official download page" actions in UI.
- Done when scanner startup never crashes on missing capture runtime.

### PH4-REL-043 - Core fallback guarantee
- Owner: `@maintainer`
- Status: `done`
- Target release: `v0.2.0`
- Enforce fallback to `core` in bootstrap and runtime startup paths.
- Add regression tests for fallback transitions and messaging.
- Done when missing capture prereqs still produce successful app launch.

## Phase 4C - Update and Release Ops

### PH4-REL-044 - Installer-first manifest policy
- Owner: `@maintainer`
- Status: `done`
- Target release: `v0.2.0`
- Manifest must include platform-preferred asset first and checksum metadata.
- Validate URLs and checksums during release pipeline.
- Done when update checker always resolves a valid per-OS recommended asset.

### PH4-REL-045 - In-app update CTA polish
- Owner: `@maintainer`
- Status: `done`
- Target release: `v0.2.0`
- Update banner should open the correct installer/bootstrap asset by OS.
- Show release notes + version delta; suppress noisy repeats.
- Done when update path from app to installer is one click.

## Phase 4D - Verification and Rollout

### PH4-QA-040 - Clean-machine end-to-end install verification
- Owner: `@maintainer`
- Status: `done`
- Target release: `v0.2.0`
- Add matrix tests for first install + first launch + update check on all OS.
- Capture screenshots/log artifacts from CI for every release candidate.
- Done when CI gates fail on missing/invalid artifacts or broken bootstrap.

### PH4-OPS-040 - Release runbook and rollback
- Owner: `@maintainer`
- Status: `todo`
- Target release: `v0.2.0`
- Document exact release steps, hotfix flow, and manifest rollback procedure.
- Define `last-known-good` manifest pointer and one-command rollback that restores it in under 10 minutes.
- Done when maintainer can recover from broken release metadata in one command.

## Risks

- OS signing/notarization steps can delay release cadence.
- Capture runtime installers may change URLs/policies.
- Mixed artifact strategy (installer + bootstrap + archive) can drift without strict CI checks.

## Mitigation

- Keep one recommended artifact per OS in manifest.
- Treat Linux/macOS optional artifacts as warning-only until stable.
- Automate checksum + URL validation in release workflows.

## Capture Runtime Licensing Policy

- Do not bundle Npcap/libpcap binaries into release artifacts without explicit license review.
- If bundling is disallowed or unclear, provide official download links and guided setup steps.
- Keep `core` install path fully functional regardless of capture runtime availability.
