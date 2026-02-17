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
   - default profile: `core` (no live capture backend)
   - optional profile: `capture` (enables live mode backend)

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
- [x] REL-001: freeze dependency profiles (core vs live capture)
- [x] REL-002: decide release packaging strategy per OS

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
- Status: DONE
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
- Delivery notes:
  - profile matrix defined in `pyproject.toml` under `tool.albion_command_desk.install_profiles`
  - unified profile switches added to Windows/Linux/macOS installers (`core` default, `capture` optional)
  - CLI includes `core` mode to run GUI without live capture backend

##### REL-002 - Release packaging strategy lock (Win/Linux/macOS)
- Status: DONE
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
- Delivery notes:
  - release checklist now defines blocker vs warning assets per OS
  - bootstrap and manifest workflows now enforce/report Phase 0 gate mapping

### Phase 1 - UI refactor foundation (2-4 days)
- [x] UXR-010: extract/declare QML design tokens
- [x] UXR-011: normalize header/nav/action zones
- [x] UXR-012: card/table visual unification
- [x] UXR-013: responsive breakpoints and overflow handling

#### Phase 1 concrete tickets

##### UXR-010 - Extract/declare QML design tokens
- Status: DONE
- Goal: move core style constants into a reusable token source before visual restyling.
- Files modified:
  1. `albion_dps/qt/ui/Theme.qml` (new)
  2. `albion_dps/qt/ui/Main.qml`
- Delivery notes:
  - color, spacing, shell, and market baseline tokens were extracted to `Theme.qml`
  - `Main.qml` now consumes theme tokens for global shell and baseline visual state

##### UXR-011 - Normalize header/nav/action zones
- Status: DONE
- Goal: normalize top-level navigation and action placement using shared primitives.
- Files modified:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/ShellTabButton.qml` (new)
  3. `albion_dps/qt/ui/Theme.qml`
- Delivery notes:
  - main tab navigation is centered and width-clamped in a dedicated nav zone
  - shared `ShellTabButton` component now styles top and market tab controls
  - header/nav/action zones now use one tokenized style path

##### UXR-012 - Card/table visual unification
- Status: DONE
- Goal: align card and table primitives to one visual language across Meter/Scanner/Market.
- Files modified:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`
  3. `albion_dps/qt/ui/CardPanel.qml` (new)
  4. `albion_dps/qt/ui/TableSurface.qml` (new)
  5. `docs/ARCHITECTURE.md`
- Delivery notes:
  - introduced reusable `CardPanel` and `TableSurface` QML primitives for panel/inset containers
  - standardized alternating table row helpers (`tableRowColor`, `tableRowStrongColor`) in `Main.qml`
  - moved remaining table/header row colors to shared tokens in `Theme.qml`
  - migrated key Meter/Scanner/Market container sections to shared primitives to remove ad-hoc border/background styling

##### UXR-013 - Responsive breakpoints and overflow handling
- Status: DONE
- Goal: enforce stable behavior for small/medium/large app widths and reduce header/content overflow.
- Files modified:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`
  3. `docs/TROUBLESHOOTING.md`
- Delivery notes:
  - added shared shell breakpoints (`compact`, `narrow`) and responsive sizing tokens in `Theme.qml`
  - updated shell header/nav controls to adapt widths/labels and hide non-critical banner on narrow windows
  - reduced market setup panel width on compact/narrow layouts and adjusted key table column widths
  - documented responsive behavior and recovery steps in troubleshooting docs

### Phase 2 - Install/release simplification (3-5 days)
- [ ] REL-010: bootstrap scripts profile support + clearer diagnostics
- [ ] REL-011: ensure no SDK requirement in end-user path
- [ ] REL-012: release artifact smoke checks per OS
- [ ] REL-013: docs rewrite for one-click install paths

### Phase 3 - Stabilization and ship (2-3 days)
- [x] QA-001: regression pass (meter/scanner/market/live/replay)
- [x] QA-002: clean machine install tests (Win/Linux/macOS)
- [x] QA-003: release + manifest + update banner validation

#### Phase 3 concrete tickets

##### QA-001 - Regression pass (meter/scanner/market/live/replay)
- Status: DONE
- Goal: run a repeatable grouped regression pass for core product areas before release.
- Files modified:
  1. `tools/qa/run_regression_suite.py` (new)
  2. `docs/qa/QA_REGRESSION_PASS.md` (new)
  3. `docs/DELIVERY_BACKLOG.md`
- Delivery notes:
  - added grouped regression runner covering meter/scanner/market/live/replay
  - added QA runbook with scope, commands, and exit criteria

##### QA-002 - Clean machine install tests (Win/Linux/macOS)
- Status: DONE
- Goal: validate bootstrap install matrix through CI and a deterministic maintainer verification command.
- Files modified:
  1. `tools/qa/verify_clean_machine_matrix.py` (new)
  2. `docs/qa/QA_CLEAN_MACHINE.md` (new)
  3. `docs/release/RELEASE_CHECKLIST.md`
  4. `docs/DELIVERY_BACKLOG.md`
- Delivery notes:
  - added `gh`-based verifier for required clean-machine jobs from `bootstrap-smoke.yml`
  - documented runbook and explicit pass/fail semantics for clean-machine matrix checks

##### QA-003 - Release + manifest + update banner validation
- Status: DONE
- Goal: validate that release metadata contract maps correctly to user-visible update banner behavior.
- Files modified:
  1. `tests/test_release_manifest_contract.py` (new)
  2. `tests/test_qt_update_banner.py` (new)
  3. `tools/qa/verify_release_update_flow.py` (new)
  4. `docs/qa/QA_RELEASE_UPDATE.md` (new)
  5. `docs/release/RELEASE_CHECKLIST.md`
  6. `docs/DELIVERY_BACKLOG.md`
- Delivery notes:
  - added explicit manifest contract test and UI update banner state tests
  - added end-to-end local smoke verifier from manifest payload to Qt update banner state
  - updated release checklist with mandatory QA-003 validation commands

### Phase 4 - Visual modernization pass (ticket namespace: PH2-UXR)
- [x] PH2-UXR-020: visual direction + token expansion
- [x] PH2-UXR-021: button system (primary/secondary/ghost/danger + states)
- [x] PH2-UXR-022: input/select/spinbox refresh
- [x] PH2-UXR-023: card layout hierarchy cleanup
- [ ] PH2-UXR-024: table redesign (meter/market/history)
- [ ] PH2-UXR-025: header + action bar polish
- [ ] PH2-UXR-026: color semantics for data states (profit/age/status)
- [ ] PH2-UXR-027: empty/loading/error states
- [ ] PH2-UXR-028: subtle micro-interactions
- [ ] PH2-UXR-029: accessibility + contrast pass
- [ ] PH2-UXR-030: visual regression baseline (screenshots/checklist)

#### Phase 4 concrete tickets

##### PH2-UXR-020 - Visual direction + token expansion
- Status: DONE
- Goal: define a modern/minimal visual system with complete semantic tokens.
- Files modified:
  1. `albion_dps/qt/ui/Theme.qml`
  2. `docs/ARCHITECTURE.md`
  3. `docs/UX_MINIMAL_RELEASE_PLAN.md`
- Delivery notes:
  - expanded `Theme.qml` to include semantic token families for brand/surface/border/text/state/control/button/table/layout/elevation
  - preserved compatibility path for existing token consumers (`accentPrimary`, `surface*`, `control*`, shell/market tokens)
  - documented PH2 visual direction and token taxonomy in architecture doc for follow-up tickets (`PH2-UXR-021+`)

##### PH2-UXR-021 - Button system
- Status: DONE
- Goal: replace ad-hoc gray buttons with a consistent variant/state system.
- Files modified:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/AppButton.qml`
  3. `albion_dps/qt/ui/Theme.qml`
- Delivery notes:
  - added reusable `AppButton.qml` with variants (`primary`, `secondary`, `ghost`, `danger`, `warm`) and hover/pressed/focus states
  - migrated `Main.qml` `Button` usages to `AppButton` and applied variant usage to global update/support actions
  - preserved local overrides where context-specific button visuals are still intentionally custom

##### PH2-UXR-022 - Input/select/spinbox refresh
- Status: DONE
- Goal: unify text fields, combos, spinboxes, and checkbox readability/states.
- Files modified:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`
- Delivery notes:
  - added shared control primitives: `AppTextField.qml`, `AppComboBox.qml`, `AppSpinBox.qml`, `AppCheckBox.qml`
  - migrated `Main.qml` form controls from base Qt widgets to shared components
  - introduced dedicated input tokens in `Theme.qml` to keep field backgrounds/borders consistent

##### PH2-UXR-023 - Card layout hierarchy cleanup
- Status: DONE
- Goal: simplify panel depth and improve section hierarchy with less border noise.
- Files modified:
  1. `albion_dps/qt/ui/CardPanel.qml`
  2. `albion_dps/qt/ui/TableSurface.qml`
  3. `albion_dps/qt/ui/Main.qml`
- Delivery notes:
  - extended `CardPanel`/`TableSurface` with semantic level-based surfaces and calmer border rules
  - removed repetitive per-instance panel color/border overrides from `Main.qml`
  - migrated panel/table containers in `Main.qml` to shared level-driven hierarchy tokens

##### PH2-UXR-024 - Table redesign
- Status: TODO
- Goal: improve readability and consistency of meter/market/history tables.
- Files to modify:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

##### PH2-UXR-025 - Header + action bar polish
- Status: TODO
- Goal: keep global actions stable and visually intentional across all widths.
- Files to modify:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

##### PH2-UXR-026 - Color semantics for data
- Status: TODO
- Goal: enforce semantic color meaning for profit, freshness, warnings, and errors.
- Files to modify:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

##### PH2-UXR-027 - Empty/loading/error states
- Status: TODO
- Goal: provide intentional placeholders and recovery actions instead of blank areas.
- Files to modify:
  1. `albion_dps/qt/ui/Main.qml`
  2. `docs/TROUBLESHOOTING.md`

##### PH2-UXR-028 - Subtle micro-interactions
- Status: TODO
- Goal: add lightweight motion for state transitions without UI clutter.
- Files to modify:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

##### PH2-UXR-029 - Accessibility + contrast pass
- Status: TODO
- Goal: ensure minimal look still passes readability and focus visibility.
- Files to modify:
  1. `albion_dps/qt/ui/Theme.qml`
  2. `albion_dps/qt/ui/Main.qml`
  3. `docs/TROUBLESHOOTING.md`

##### PH2-UXR-030 - Visual regression baseline
- Status: TODO
- Goal: establish screenshot-based baseline to avoid style regressions.
- Files to modify:
  1. `assets/`
  2. `README.md`
  3. `docs/release/RELEASE_CHECKLIST.md`

## 5) Non-goals (for this cycle)

- No full feature redesign of combat/market logic.
- No protocol overhaul unless blocking release stability.
- No broad plugin architecture changes.

## 6) Definition of done

- UI is visually consistent and clearly more modern/minimal.
- End-user install path is short, documented, and reproducible.
- Release artifacts are validated on all target OSes.
- Update manifest flow works from released artifacts.
