# UX + Minimal Release Plan

Goal: modernize the UI (clean/minimal look) and reduce end-user installation friction to near one-click on each OS.

## 1) Product targets

- UI target:
  - consistent visual system across Meter/Scanner/Market
  - cleaner hierarchy, less visual noise, better spacing/readability
  - fixed global action placement (updates/support/settings)
- Release target:
  - end user should not install Python/toolchains manually
  - avoid requiring build-time SDKs on user machines
  - clear fallback behavior when live capture dependency is missing

## 2) Current pain points (baseline)

- Header/action placement is inconsistent and shifts by view.
- Legacy styles and mixed component patterns in `Main.qml`.
- End-user setup is too long (manual dependencies + environment steps).
- Windows capture path is fragile (Npcap + capture backend dependency chain).

## 3) Work streams

### Stream A - UI system and visual redesign

Files:
- `albion_dps/qt/ui/Main.qml`
- `albion_dps/qt/models.py` (only if data formatting/state updates are needed)
- optionally split reusable QML components under `albion_dps/qt/ui/components/`

Tasks:
1. Define design tokens (spacing, typography, color, border radii, elevation).
2. Standardize shell layout:
   - left: context/title
   - center: tab navigation
   - right: update controls, support buttons, settings
3. Simplify sections/cards:
   - reduce border noise
   - increase content density without crowding
   - align tables and controls to one rhythm grid
4. Improve responsive behavior (small/medium/large widths).
5. Apply one visual language to Meter, Scanner, Market.

Acceptance:
- No major layout shift when switching tabs.
- Header controls remain anchored and predictable.
- Core views usable at common laptop resolutions.

### Stream B - Dependency and runtime simplification

Files:
- `pyproject.toml`
- `albion_dps/capture/*`
- `tools/install/windows/install.ps1`
- `tools/install/linux/install.sh`
- `tools/install/macos/install.sh`
- `README.md`, `docs/TROUBLESHOOTING.md`

Tasks:
1. Split runtime modes clearly:
   - replay/market/scanner should run without capture extras
   - live capture remains optional
2. Keep unknown/raw dumps opt-in (`--debug`) to avoid artifact explosion.
3. Minimize hard dependencies:
   - remove any user-side SDK requirement from normal install path
   - keep only runtime dependencies for live capture
4. Add deterministic capability checks at startup:
   - show exact missing dependency + direct fix path
5. Harden bootstrap scripts with explicit "install profile":
   - default profile: full app
   - safe fallback profile when capture cannot be installed

Acceptance:
- Fresh machine can run app core features with one command/script.
- Missing capture backend does not block non-capture features.

### Stream C - Cross-platform release pipeline

Files:
- `.github/workflows/*`
- `tools/release/*`
- `docs/release/RELEASE_CHECKLIST.md`
- `tools/release/manifest/*`

Tasks:
1. Build release artifacts per OS with bundled runtime.
2. Ensure release outputs are directly runnable by users.
3. Keep manifest publication automatic for each release.
4. Add smoke checks on produced artifacts (launch + basic UI load).
5. Define rollback/hotfix path in checklist (already present, validate in practice).

Acceptance:
- Windows/Linux/macOS release assets exist and are tested.
- "Latest" release can be installed without developer tooling.

## 4) Proposed execution order (tickets)

### Phase 0 - Architecture lock (1-2 days)
- [x] UXR-001: freeze target shell layout and component map
- [ ] REL-001: freeze dependency profiles (core vs live capture)
- [ ] REL-002: decide release packaging strategy per OS

#### Phase 0 concrete tickets (execution-ready)

##### UXR-001 - Shell layout freeze and component map
- Status: DONE
- Goal: lock one consistent app shell used by Meter/Scanner/Market before visual polish starts.
- Files to modify:
  1. `docs/UX_MINIMAL_RELEASE_PLAN.md`
  2. `docs/ARCHITECTURE.md`
  3. `albion_dps/qt/ui/Main.qml`
- Tasks:
  - define final header zones and strict ordering (left context, center tabs, right utilities/support)
  - inventory duplicated/legacy QML sections and mark candidates for extraction into reusable components
  - set hard constraints for table/card spacing, minimum widths, and overflow behavior
- Done when:
  - shell layout rules are documented and no longer "to decide"
  - `Main.qml` has an identified target map (what stays inline vs what will be extracted)
  - no header/action drift between top-level tabs in the current baseline
- Delivery notes:
  - shell contract documented in `docs/ARCHITECTURE.md`
  - shell zone IDs and extraction map markers added in `albion_dps/qt/ui/Main.qml`

##### REL-001 - Dependency profile freeze (core vs live capture)
- Status: TODO
- Goal: define mandatory runtime dependencies for "core app" and optional dependencies for "live capture".
- Files to modify:
  1. `pyproject.toml`
  2. `tools/install/windows/install.ps1`
  3. `tools/install/linux/install.sh`
  4. `tools/install/macos/install.sh`
  5. `docs/TROUBLESHOOTING.md`
- Tasks:
  - freeze two install profiles:
    - `core`: UI + scanner/market/replay (no capture extras)
    - `capture`: adds live capture backend requirements
  - enforce capability checks on startup with direct install guidance when capture is unavailable
  - align bootstrap scripts to the same profile naming and behavior
- Done when:
  - one profile matrix is documented and reflected by install scripts
  - clean install can run core features without capture dependencies
  - missing capture backend produces actionable message, not hard crash

##### REL-002 - Release packaging strategy lock (Win/Linux/macOS)
- Status: TODO
- Goal: finalize packaging approach per OS so release work is deterministic.
- Files to modify:
  1. `docs/release/RELEASE_CHECKLIST.md`
  2. `docs/release/RELEASE_MANIFEST_SPEC.md`
  3. `.github/workflows/release-manifest.yml`
  4. `.github/workflows/bootstrap-smoke.yml`
- Tasks:
  - freeze packaging targets per OS (artifact type, install flow, fallback mode)
  - map required CI checks to each target artifact
  - define release gates (what blocks publish vs what is warning-only)
- Done when:
  - each OS has one chosen artifact strategy documented in release checklist
  - CI checks explicitly map to those artifacts
  - release decision is no longer ad-hoc per version

### Phase 1 - UI refactor foundation (2-4 days)
- [ ] UXR-010: extract/declare QML design tokens
- [ ] UXR-011: normalize header/nav/action zones
- [ ] UXR-012: card/table visual unification
- [ ] UXR-013: responsive breakpoints and overflow handling

### Phase 2 - Install/release simplification (3-5 days)
- [ ] REL-010: bootstrap scripts profile support + clearer diagnostics
- [ ] REL-011: ensure no SDK requirement in end-user path
- [ ] REL-012: release artifact smoke checks per OS
- [ ] REL-013: docs rewrite for one-click install paths

### Phase 3 - Stabilization and ship (2-3 days)
- [ ] QA-001: regression pass (meter/scanner/market/live/replay)
- [ ] QA-002: clean machine install tests (Win/Linux/macOS)
- [ ] QA-003: release + manifest + update banner validation

## 5) Non-goals (for this cycle)

- No full feature redesign of combat/market logic.
- No protocol overhaul unless blocking release stability.
- No broad plugin architecture changes.

## 6) Definition of done

- UI is visually consistent and clearly more modern/minimal.
- End-user install path is short, documented, and reproducible.
- Release artifacts are validated on all target OSes.
- Update manifest flow works from released artifacts.
