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
- [x] Status: DONE
- Goal: reduce border noise and enforce cleaner panel depth hierarchy.
- Files:
  1. `albion_dps/qt/ui/CardPanel.qml`
  2. `albion_dps/qt/ui/TableSurface.qml`
  3. `albion_dps/qt/ui/Main.qml`

### PH2-UXR-024 - Table redesign
- [x] Status: DONE
- Goal: improve table readability and consistency across Meter/Market/History.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-025 - Header + action bar polish
- [x] Status: DONE
- Goal: stabilize action placement and visual priority at all breakpoints.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-026 - Color semantics for data
- [x] Status: DONE
- Goal: enforce semantic color mapping for KPI status and warnings.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-027 - Empty/loading/error states
- [x] Status: DONE
- Goal: add intentional placeholders and recovery actions.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `docs/TROUBLESHOOTING.md`

### PH2-UXR-028 - Subtle micro-interactions
- [x] Status: DONE
- Goal: add lightweight transitions to improve perceived quality.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`

### PH2-UXR-029 - Accessibility + contrast pass
- [x] Status: DONE
- Goal: ensure focus visibility and readable contrast in all themes/states.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/Theme.qml`
  3. `docs/TROUBLESHOOTING.md`

### PH2-UXR-030 - Visual regression baseline
- [x] Status: DONE
- Goal: capture reference screenshots/checklist to prevent UI regressions.
- Files:
  1. `assets/`
  2. `README.md`
  3. `docs/release/RELEASE_CHECKLIST.md`

## Active Milestone - Phase 4 (Zero-friction release execution)

### PH4-REL-040 - Freeze final artifact matrix
- [x] Status: DONE
- Goal: lock deterministic artifact naming + priority per OS for release + manifest consumers.
- Files:
  1. `docs/release/RELEASE_CHECKLIST.md`
  2. `docs/release/RELEASE_MANIFEST_SPEC.md`
  3. `docs/release/ZERO_FRICTION_RELEASE_PLAN.md`

### PH4-REL-041 - Bootstrap parity with packaged installers
- [x] Status: DONE
- Goal: align `tools/install/*` scripts with canonical artifact names and profile flags.
- Files:
  1. `tools/install/windows/install.ps1`
  2. `tools/install/linux/install.sh`
  3. `tools/install/macos/install.sh`
  4. `tools/install/common/smoke_check.py`

### PH4-REL-042 - Capture runtime detector hardening
- [x] Status: DONE
- Goal: explicit runtime states (`available`, `missing`, `blocked`, `unknown`) and guided UI actions.
- Files:
  1. `albion_dps/capture/npcap_runtime.py`
  2. `albion_dps/qt/runner.py`
  3. `albion_dps/qt/ui/Main.qml`

### PH4-REL-043 - Core fallback guarantee
- [x] Status: DONE
- Goal: ensure startup degrades to `core` without crashes when capture prerequisites are absent.
- Files:
  1. `albion_dps/qt/runner.py`
  2. `albion_dps/capture/startup_policy.py`
  3. `tests/test_capture_startup_policy.py`

### PH4-REL-044 - Installer-first manifest policy
- [x] Status: DONE
- Goal: enforce preferred asset ordering + checksum validation in release metadata.
- Files:
  1. `.github/workflows/release-manifest.yml`
  2. `tools/release/manifest/build_manifest.py`
  3. `tests/test_release_manifest_contract.py`

### PH4-REL-045 - In-app update CTA polish
- [x] Status: DONE
- Goal: one-click update CTA resolves OS-correct primary installer/archive and suppresses noisy repeats.
- Files:
  1. `albion_dps/update/checker.py`
  2. `albion_dps/qt/models.py`
  3. `albion_dps/qt/runner.py`
  4. `albion_dps/qt/ui/Main.qml`
  5. `albion_dps/qt/ui/AppHeader.qml`
  6. `albion_dps/qt/ui/UpdateBanner.qml`
  7. `tests/test_update_checker.py`
  8. `tests/test_qt_update_banner.py`
  9. `tools/qa/verify_release_update_flow.py`

### PH4-QA-040 - Clean-machine end-to-end install verification
- [x] Status: DONE
- Goal: enforce clean-machine matrix checks with CI evidence payloads for each required OS job.
- Files:
  1. `.github/workflows/bootstrap-smoke.yml`
  2. `tools/install/common/smoke_check.py`
  3. `tools/qa/verify_clean_machine_matrix.py`
  4. `tests/test_verify_clean_machine_matrix.py`
  5. `docs/qa/QA_CLEAN_MACHINE.md`
  6. `docs/release/RELEASE_CHECKLIST.md`

### PH4-OPS-040 - Release runbook and rollback
- [x] Status: DONE
- Goal: define a deterministic release/hotfix/rollback path with one-command manifest restore.
- Files:
  1. `docs/release/RELEASE_RUNBOOK.md`
  2. `docs/release/RELEASE_CHECKLIST.md`
  3. `docs/release/RELEASE_MANIFEST_SPEC.md`
  4. `tools/release/manifest/last_known_good.json`
  5. `tools/release/manifest/set_last_known_good.ps1`
  6. `tools/release/manifest/rollback_manifest.ps1`

## Active Milestone - Phase 5 (Meter reliability + operator UX)

### PH5-MTR-050 - Tight local-context party filtering
- [x] Status: DONE
- Goal: only show self + relevant local party members in meter snapshots and history.
- Files:
  1. `albion_dps/domain/party_registry.py`
  2. `albion_dps/domain/name_registry.py`
  3. `albion_dps/pipeline.py`
  4. `albion_dps/qt/runner.py`
  5. `tests/test_party_registry.py`
  6. `tests/test_party_pcap*.py`
- Done when:
  - Party members from other maps / stale contexts no longer appear in meter.
  - Self remains visible even during roster/bootstrap transitions.
  - Zone/cluster transitions do not permanently break party filtering.

### PH5-MTR-051 - Battle continuity hardening
- [x] Status: DONE
- Goal: stop mid-fight resets/freezes and keep active battle state coherent.
- Files:
  1. `albion_dps/meter/session_meter.py`
  2. `albion_dps/meter/aggregate.py`
  3. `albion_dps/pipeline.py`
  4. `tests/test_party_pcap49*.py`
  5. `tests/test_party_pcap50*.py`
  6. `tests/test_party_pcap52*.py`
- Done when:
  - Active fights do not reset while combat events continue.
  - Frozen/stale live snapshots are detected and recovered.
  - Portal/map changes end or split battles deterministically.

### PH5-MTR-052 - History panel correctness
- [x] Status: DONE
- Goal: make meter history stable, readable, and copyable at all window sizes.
- Files:
  1. `albion_dps/qt/ui/MeterHistoryPanel.qml`
  2. `albion_dps/qt/ui/MeterTab.qml`
  3. `albion_dps/qt/models.py`
  4. `tests/test_qt_meter_history.py`
- Done when:
  - `Copy` action is consistently visible and clickable.
  - History text never overflows card bounds.
  - Scrolling history never snaps back to top after model refresh.

### PH5-MTR-053 - Meter responsive layout pass
- [x] Status: DONE
- Goal: make the meter readable across supported window sizes without broken tables.
- Files:
  1. `albion_dps/qt/ui/MeterTab.qml`
  2. `albion_dps/qt/ui/MeterScoreboard.qml`
  3. `albion_dps/qt/ui/Main.qml`
  4. `docs/TROUBLESHOOTING.md`
- Done when:
  - Meter remains usable at the minimum supported width.
  - History/session gains do not crush the scoreboard.
  - Update CTA/header actions do not hide critical meter content.

### PH5-MTR-054 - Session gains validation
- [x] Status: DONE
- Goal: validate fame/silver/session-rate calculations against controlled PCAP samples.
- Files:
  1. `albion_dps/domain/fame_tracker.py`
  2. `albion_dps/qt/models.py`
  3. `tests/test_fame_tracker_pcap53.py`
  4. `docs/qa/QA_REGRESSION_PASS.md`
- Done when:
  - Fame and silver totals match reference captures.
  - Fame/h and silver/h are numerically stable and formatted cleanly.
  - Session gains layout does not overflow with large values.

## Active Milestone - Phase 6 (Market correctness + planning workflow)

### PH6-MKT-060 - Resource requirement correctness
- [x] Status: DONE
- Goal: ensure market planner computes required materials, artifacts, journals, and no-return items correctly.
- Files:
  1. `albion_dps/market/`
  2. `albion_dps/qt/market/state.py`
  3. `tests/test_market_*.py`
  4. `mail.txt`
- Done when:
  - Enchant-aware ingredients use correct item IDs and prices.
  - Royal sigils and similar no-return items ignore RRR.
  - Journal quantities match expected craft outputs with consistent precision.

### PH6-MKT-061 - Profit math audit
- [x] Status: DONE
- Goal: make investment/revenue/fee/tax/profit/margin calculations defensible and internally consistent.
- Files:
  1. `albion_dps/qt/market/state.py`
  2. `albion_dps/qt/ui/MarketTab.qml`
  3. `tests/test_market_profit_math.py`
  4. `docs/ARCHITECTURE.md`
- Done when:
  - Result rows and top KPIs use the same formulas.
  - Margin is calculated from the intended base and documented.
  - Journal P/L is decoupled from unrelated output price edits where appropriate.

### PH6-MKT-062 - AO Data rate-limit strategy
- [x] Status: DONE
- Goal: remove user-visible hangs and make large refreshes predictable under AO Data 429 limits.
- Files:
  1. `albion_dps/market/aod_client.py`
  2. `albion_dps/qt/market/state.py`
  3. `albion_dps/qt/ui/MarketTab.qml`
  4. `tests/test_market_aod_client.py`
- Done when:
  - Large batches degrade gracefully under 429.
  - UI shows visible loading/progress for long refreshes.
  - Cache/live/stale fallback states are explicit and understandable.

### PH6-MKT-063 - Saved plans, import/export, and presets
- [x] Status: DONE
- Goal: turn the market tab into a reusable planning workspace.
- Files:
  1. `albion_dps/settings.py`
  2. `albion_dps/qt/market/state.py`
  3. `albion_dps/qt/ui/MarketTab.qml`
  4. `README.md`
- Done when:
  - User can save/load craft plans and presets.
  - Shopping/selling/results exports are available via clipboard and file.
  - Default city/filter presets persist between runs.

### PH6-MKT-064 - Market table UX hardening
- [x] Status: DONE
- Goal: finish interaction polish for setup/inputs/outputs/results tables.
- Files:
  1. `albion_dps/qt/ui/MarketTab.qml`
  2. `albion_dps/qt/ui/MarketCraftsTable.qml`
  3. `albion_dps/qt/ui/MarketSetupPanel.qml`
  4. `tests/test_market_qt_state.py`
- Done when:
  - Checkbox hit areas are stable.
  - Search/filter/sort controls are visually and functionally consistent.
  - Narrow-width behavior is usable without hidden columns becoming inaccessible.

- Progress:
  - 2026-03-25: PH6-MKT-064 completed (market table toolbars now use consistent wrapped controls, setup/inputs/outputs/results tables expose horizontal scrolling instead of clipping columns, and market tab QML is regression-covered at the enforced minimum window width).

## Active Milestone - Phase 7 (Product surface + supportability)

### PH7-PRD-070 - Settings tab
- [x] Status: DONE
- Goal: centralize runtime, update, logging, and path controls in one place.
- Files:
  1. `albion_dps/settings.py`
  2. `albion_dps/qt/ui/Main.qml`
  3. `albion_dps/qt/ui/SettingsTab.qml`
  4. `tests/test_settings.py`
- Done when:
  - User can manage update, capture, scanner, and logging settings from one tab.
  - Critical paths (runtime/game data/scanner repo) are visible and editable.
  - Start tab no longer acts as a pseudo-settings screen.

- Progress:
  - 2026-03-24: PH7-PRD-070 completed (shared app settings now merge safely, scanner repo/logging settings persist, CLI picks up saved default log level, and a dedicated Settings tab centralizes update, scanner, game-data, runtime, and Git controls).

### PH7-PRD-071 - Help/About tab
- [x] Status: DONE
- Goal: provide in-app troubleshooting, versioning, and release-note visibility.
- Files:
  1. `albion_dps/qt/ui/HelpTab.qml`
  2. `albion_dps/qt/ui/Main.qml`
  3. `README.md`
  4. `docs/TROUBLESHOOTING.md`
- Done when:
  - App version, release notes, support links, and setup help are easy to find.
  - Common dependency errors (Npcap, Git, game data) have direct guidance.

- Progress:
  - 2026-03-24: PH7-PRD-071 completed (new Help tab exposes app version, website/release/changelog links, troubleshooting entry points, and direct dependency guidance for Npcap, Git, scanner repo, and game data).

### PH7-PRD-072 - Diagnostics bundle export
- [x] Status: DONE
- Goal: make support/debugging reproducible with one exported bundle.
- Files:
  1. `albion_dps/qt/runner.py`
  2. `albion_dps/qt/ui/ScannerTab.qml`
  3. `albion_dps/qt/ui/HelpTab.qml`
  4. `tools/qa/`
- Done when:
  - User can export logs, version info, runtime state, and selected diagnostics in one zip/txt bundle.
  - Support requests can be handled without manual log hunting.

- Progress:
  - 2026-03-24: PH7-PRD-072 completed (Scanner and Help tabs can now export a diagnostics zip with summary metadata, scanner log, market diagnostics, and current settings, plus a QA helper verifies the bundle structure).

### PH7-PRD-073 - Session export and compare
- [x] Status: DONE
- Goal: let users archive and compare combat sessions outside the live UI.
- Files:
  1. `albion_dps/meter/session_meter.py`
  2. `albion_dps/qt/models.py`
  3. `albion_dps/qt/ui/MeterTab.qml`
  4. `tests/test_session_export.py`
- Done when:
  - History entries can be exported as txt/csv/json.
  - Two sessions can be compared on core KPIs.

- Progress:
  - 2026-03-24: PH7-PRD-073 completed (Meter history now exports TXT/CSV/JSON archives, persists a dedicated meter export directory, and shows an in-app selected-session KPI compare panel with copy/export actions).

### PH7-PRD-074 - Loot/session map history
- [x] Status: DONE
- Goal: add safe post-analysis features inspired by reference projects without moving into overlay/radar territory.
- Files:
  1. `albion_dps/domain/`
  2. `albion_dps/qt/ui/`
  3. `docs/ARCHITECTURE.md`
- Done when:
  - Session map trail and passive loot/session history are available.
  - No live overlay, radar, or auto-alert behavior is introduced.

- Progress:
  - 2026-03-24: PH7-PRD-074 completed as a safe session-activity trail (map transitions plus passive fame/silver reward history) surfaced in the Meter sidebar, with no overlay/radar/auto-alert behavior added.

## Active Milestone - Phase 8 (Responsive shell + layout modernization)

### PH8-UXR-080 - Supported window contract
- [x] Status: DONE
- Goal: stop unsupported window sizes from producing broken layouts and give every tab the same shell constraints.
- Files:
  1. `albion_dps/qt/ui/Theme.qml`
  2. `albion_dps/qt/ui/Main.qml`
  3. `docs/UX_RESPONSIVE_LAYOUT_PLAN.md`
- Done when:
  - Default and minimum window sizes are tokenized in `Theme.qml`.
  - `Main.qml` consumes those tokens instead of hardcoded geometry.
  - Responsive breakpoints are documented as the contract for subsequent UI tickets.

### PH8-UXR-081 - Start tab compact redesign
- [ ] Status: IN PROGRESS
- Goal: remove wasted space and give Start a dense, readable system dashboard.
- Files:
  1. `albion_dps/qt/ui/HomeTab.qml`
  2. `albion_dps/qt/ui/components/`
  3. `tests/test_qml_home_tab.py`
- Done when:
  - Start uses space efficiently at the supported minimum size.
  - Health cards, update checks, and shortcuts read as one coherent dashboard.
  - No clipped or uneven sections remain.

### PH8-UXR-082 - Meter adaptive layout redesign
- [ ] Status: IN PROGRESS
- Goal: make Meter readable and stable at the supported minimum size without layout collapse.
- Files:
  1. `albion_dps/qt/ui/MeterTab.qml`
  2. `albion_dps/qt/ui/MeterScoreboard.qml`
  3. `albion_dps/qt/ui/MeterHistoryPanel.qml`
  4. `tests/test_qml_meter_tab.py`
- Done when:
  - Scoreboard, history, and session panels stay readable at minimum size.
  - Update banner/header actions never obscure meter controls.
  - Horizontal overflow is controlled, not accidental.

### PH8-UXR-083 - Market layout containment pass
- [ ] Status: TODO
- Goal: keep setup/table/results readable without accidental clipping or dead space.
- Files:
  1. `albion_dps/qt/ui/MarketTab.qml`
  2. `albion_dps/qt/ui/MarketSetupPanel.qml`
  3. `albion_dps/qt/ui/MarketCraftsTable.qml`
  4. `tests/test_qml_market_tab.py`
- Done when:
  - Setup panel width and scroll behavior remain stable.
  - Table toolbars and content stay accessible at supported sizes.
  - Results/header stats do not drift or collapse awkwardly.

### PH8-UXR-084 - Scanner/Settings/Help consistency pass
- [ ] Status: TODO
- Goal: align non-meter tabs to the same card density, spacing, and responsive behavior.
- Files:
  1. `albion_dps/qt/ui/ScannerTab.qml`
  2. `albion_dps/qt/ui/SettingsTab.qml`
  3. `albion_dps/qt/ui/HelpTab.qml`
  4. `tests/test_qt_smoke.py`
- Done when:
  - Utility tabs share the same visual density and breakpoint behavior.
  - Primary actions remain visible without overlap or orphan gaps.

### PH8-UXR-085 - Header and update CTA redesign
- [ ] Status: TODO
- Goal: modernize the header so updates/support actions remain compact, readable, and intentional.
- Files:
  1. `albion_dps/qt/ui/AppHeader.qml`
  2. `albion_dps/qt/ui/UpdateBanner.qml`
  3. `albion_dps/qt/ui/Main.qml`
  4. `tests/test_qt_update_banner.py`
- Done when:
  - Update CTA never looks truncated or visually broken.
  - Support actions scale gracefully across supported widths.
  - Header metadata and actions feel balanced rather than crowded.

- Progress:
  - 2026-03-25: PH8-UXR-080 completed by moving the window/default breakpoint contract into `Theme.qml`, wiring `Main.qml` to those tokens, and documenting the supported geometry in `docs/UX_RESPONSIVE_LAYOUT_PLAN.md`.
  - 2026-03-25: PH8-UXR-081/082 started with a denser Start dashboard, shorter update CTA copy, and a stacked Meter layout that scrolls instead of clipping at smaller supported sizes.

## Next Milestone - Phase 9 (Reliability lock for meter, market, and release)

### PH9-MTR-090 - Meter replay regression pack
- [x] Status: DONE
- Goal: lock replay correctness on the latest high-value pcaps before adding more meter features.
- Files:
  1. `tests/test_meter_pcap49_party_flow.py` (new)
  2. `tests/test_meter_pcap50_rows_visible.py`
  3. `tests/test_meter_pcap51_self_visible.py`
  4. `tests/test_party_pcap52_history_keeps_player_labels.py`
  5. `tests/test_fame_tracker_pcap53.py`
- Done when:
  - Replay regressions cover party bootstrap, portal/map changes, history label stability, and fame/silver totals.
  - Known bad outputs (`@MOB_*` relabels, empty live rows, missing self row) are blocked by tests.

- Progress:
  - 2026-03-31: Added `tests/test_meter_pcap49_party_flow.py` and refreshed the 50/51/52/53 replay pack to lock portal/map-change bootstrap, live row visibility, self-row visibility, stable history labels, and fame/silver totals.

### PH9-MTR-091 - Live meter sanity hardening
- [ ] Status: IN PROGRESS
- Goal: make live meter behavior deterministic when party state, local context, or snapshots are noisy.
- Files:
  1. `albion_dps/pipeline.py`
  2. `albion_dps/domain/party_registry.py`
  3. `albion_dps/meter/session_meter.py`
  4. `albion_dps/qt/models.py`
  5. `tests/test_pipeline_party_seed.py`
  6. `tests/test_party_registry.py`
- Done when:
  - Live rows do not disappear during bootstrap or local-context transitions.
  - Party filtering remains local enough to exclude stale/off-map ghosts.
  - Battle history and active snapshots stay stable through party changes.

- Progress:
  - 2026-03-31: Tightened `_allowed_display_names_for_snapshot()` so once a local non-self party member exists, non-local active party IDs stop leaking into the live meter view.

### PH9-MKT-092 - Market correctness lock
- [ ] Status: IN PROGRESS
- Goal: freeze the current market math into deterministic regressions and close remaining quantity/profit gaps.
- Files:
  1. `albion_dps/market/engine.py`
  2. `albion_dps/qt/market/state.py`
  3. `tests/test_market_engine.py`
  4. `tests/test_market_qt_state.py`
  5. `tests/test_market_profit_math.py`
- Done when:
  - Inputs show upfront purchase requirements that are sufficient to complete planned crafts.
  - Journals, non-returnable components, and profit math stay consistent across inputs/outputs/results.
  - Known regressions (boltcasters, royal/sigil handling, journal coupling) are blocked by tests.

- Progress:
  - 2026-03-31: Locked a regression where selected material cost could still inherit shopping-style safety rounding; top KPI material cost now uses exact expected economic quantities while Inputs keeps full upfront purchase counts.
  - 2026-03-31: Added explicit regression coverage for multi-component weapon crafts so Inputs keeps full upfront counts for mixed returnable/non-returnable recipes (Boltcasters-style case).

### PH9-UXR-093 - Market containment and desktop UX pass
- [ ] Status: IN PROGRESS
- Goal: keep supported desktop layouts stable while removing clipping, overlap, and dead space.
- Files:
  1. `albion_dps/qt/ui/Main.qml`
  2. `albion_dps/qt/ui/MarketTab.qml`
  3. `albion_dps/qt/ui/HomeTab.qml`
  4. `albion_dps/qt/ui/MeterTab.qml`
  5. `albion_dps/qt/ui/SettingsTab.qml`
  6. `albion_dps/qt/ui/HelpTab.qml`
- Done when:
  - Supported desktop sizes do not trigger clipped controls or overlapping cards.
  - Inputs/Outputs/Results remain usable without losing key actions.
  - Start, Meter, Settings, and Help share the same desktop layout contract.
- Progress:
  - 2026-03-31: Market setup now stays in a fixed desktop two-pane layout (setup panel + crafts table) and is regression-checked at the enforced minimum width.
  - 2026-03-31: Crafts/Inputs/Outputs/Results toolbars now use a stable desktop row layout instead of wrapping Flow controls, keeping primary actions visible at supported widths.

### PH9-REL-094 - Installer and release smoke lock
- [x] Status: DONE
- Goal: make the release flow boring by validating the installer/update path every time.
- Files:
  1. `tools/qa/run_release_readiness.py`
  2. `tools/qa/verify_release_update_flow.py`
  3. `tools/qa/verify_release_artifact_matrix.py`
  4. `docs/release/RELEASE_CHECKLIST.md`
- Done when:
  - Release readiness catches missing assets, broken update flow, and installer regressions before tagging.
  - Windows bootstrap/install/update smoke remains green on the current release contract.

### PH9-REL-095 - Version and reporting consistency
- [x] Status: DONE
- Goal: ensure every user-facing version, diagnostic, and update surface reports the same release state.
- Files:
  1. `albion_dps/__init__.py`
  2. `albion_dps/qt/runner.py`
  3. `albion_dps/update/checker.py`
  4. `tools/release/manifest/build_manifest.py`
  5. `tests/test_update_checker.py`
- Done when:
  - App version, manifest version, update banner, and diagnostics bundle agree on the active release.
  - No view falls back to stale hardcoded version strings.
- Progress:
  - CLI, Qt runner, and scanner diagnostics now resolve app version from the shared helper.
  - Local release gate validates version surfaces explicitly before tagging.
  - Local release gate now validates the artifact matrix for Windows/Linux/macOS against the checked-in manifest contract without needing remote release probes.

- Progress:
  - 2026-03-31: centralized version resolution in `albion_dps.versioning`, rewired CLI and Qt runner to the shared helper, and added regression tests so package-metadata fallback stays consistent across CLI/app/update surfaces.

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

- 2026-03-24: PH6-MKT-061 completed (market result-row formulas now use a shared helper aligned with top-level `ProfitBreakdown`, profit/margin regressions were added, and market math is documented in `docs/ARCHITECTURE.md`).
- 2026-03-24: PH6-MKT-062 completed (AO Data price requests now default to smaller batches, large 429-limited batches split into predictable chunks, market UI exposes queued/loading/cooldown states more clearly, and regressions cover both client chunking and state cooldown messaging).
- 2026-03-24: PH6-MKT-063 completed (selected market presets now persist between runs, shopping/selling/results CSV exports are available from the UI and file dialog flows, and export directory preferences are stored in app settings).
- 2026-03-24: PH6-MKT-060 completed (journal mapping now falls back correctly for royal plate items, royal sigils/tokens stay non-returnable in planner regressions, and journal quantity expectations are locked for real dataset cases).
- 2026-03-24: PH5-MTR-051 completed (battle sessions now ignore stale combat-stop markers while fresh combat events continue, short-gap merged summaries preserve `totals_by_id`, and continuity regressions are locked in `tests/test_session_meter.py`).
- 2026-03-24: PH5-MTR-054 completed (pcap53 fame/silver totals are now regression-locked, session rate strings stay stable, and the session-gains panel falls back to a single-column grid at narrow widths).
- 2026-03-24: PH5-MTR-053 completed (meter now switches to stacked layout earlier, compact control groups adapt to narrow widths, and scoreboard content uses controlled horizontal overflow instead of clipping columns).
- 2026-03-24: PH5-MTR-052 completed (history rows now preserve scroll position across unchanged model refreshes, long summaries wrap inside card bounds, and `Copy` remains consistently visible).
- 2026-03-25: PH5-MTR-050 completed (pipeline event/combat-state filtering now gates resolved party IDs by recent local observations with bootstrap fallback before first local party sighting, and session labels preserve player names instead of relabeling old rows as later mobs).
- 2026-02-18: PH4-OPS-040 completed (added release runbook with hotfix path, introduced `last_known_good.json` pointer maintenance command, and shipped one-command manifest rollback script).
- 2026-02-18: PH4-QA-040 completed (bootstrap-smoke now uploads per-job evidence bundles with logs/smoke JSON/update-flow traces + UX baselines; clean-machine verifier now blocks on missing/expired required evidence artifacts).
- 2026-02-18: PH4-REL-045 completed (update checker now resolves per-OS installer/bootstrap URL + notes URL, update banner exposes Install/Notes actions, and repeated alerts are suppressed once a version is dismissed).
- 2026-02-18: PH4-REL-044 completed (manifest builder now enforces deterministic preferred-asset ordering, validates HTTPS URLs and SHA256 checksums, and workflow strategy checks use the shared policy validator).
- 2026-02-18: PH4-REL-043 completed (live startup policy now degrades to core on missing/blocked capture prerequisites and no-interface scenarios; regression tests added for fallback transitions/messages).
- 2026-02-18: PH4-REL-042 completed (runtime detector states hardened to available/missing/blocked/unknown, scanner UI now exposes runtime action CTA, live startup handles missing runtime without crash).
- 2026-02-18: PH4-REL-041 completed (bootstrap scripts now support non-interactive CI mode and emit canonical per-OS artifact diagnostics; shared smoke check consumes profile/artifact context).
- 2026-02-18: PH4-REL-040 completed (deterministic artifact matrix/naming contract documented in release checklist and manifest spec).
- 2026-02-17: REL-010 completed (installer diagnostics/preflight summary for Windows/Linux/macOS with capture-specific hints).
- 2026-02-17: REL-011 completed (capture profile fallback to core by default; strict capture mode added for advanced users).
- 2026-02-17: REL-012 completed (release asset smoke workflow + manifest asset verifier script + QA runbook).
- 2026-02-17: REL-013 completed (README + troubleshooting rewritten for one-click bootstrap install and short recovery path).
- 2026-02-17: PH2-UXR-030 completed (PH2 baseline screenshot set + README screenshot refresh + release checklist baseline gate).
- 2026-02-17: PH2-UXR-029 completed (stronger text contrast + tokenized focus ring + keyboard focus guidance in docs).
- 2026-02-17: PH2-UXR-028 completed (tokenized motion timings + subtle hover/press/fade transitions for controls and rows).
- 2026-02-17: PH2-UXR-027 completed (empty/loading/error placeholders added for Meter/History/Scanner/Market views).
- 2026-02-17: PH2-UXR-026 completed (semantic data-color helpers + replacement of hardcoded profit/status colors).
- 2026-02-17: PH2-UXR-025 completed (header action tokens + aligned compact controls + stable update-banner slot behavior).
- 2026-02-17: PH2-UXR-024 completed (table header/text token refresh + row hover/selection polish in Meter/Market/History).
- 2026-02-17: PH2-UXR-023 completed (level-based panel/table primitives + Main.qml hierarchy cleanup and style deduplication).
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
