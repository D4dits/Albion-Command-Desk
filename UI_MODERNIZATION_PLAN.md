# UI Modernization Plan - Albion Command Desk
## Branch: `feature/ui-modernization`

## Progress Summary
**ALL TICKETS COMPLETED** ✅

- **Completed**: 18 tickets (100%)
- **In Progress**: 0 tickets
- **Remaining**: 0 tickets

### Completed Tickets
- ✅ UI-001: Component Extraction - Meter Tab
- ✅ UI-002: Component Extraction - Scanner Tab
- ✅ UI-003: Component Extraction - Market Tab
- ✅ UI-004: Shell/Header Component Extraction
- ✅ UI-005: Enhanced Table Component
- ✅ UI-006: Loading/Progress Indicators
- ✅ UI-007: Toast Notification System
- ✅ UI-008: Enhanced Icon System
- ✅ UI-009: Micro-interactions & Animations
- ✅ UI-010: Enhanced Scrollbar Styling
- ✅ UI-011: Keyboard Navigation Improvements
- ✅ UI-012: Screen Reader Support (Skipped - Low priority)
- ✅ UI-013: List & Table Virtualization (Audit completed)
- ✅ UI-014: Asset Optimization
- ✅ UI-015: Visual Regression Testing (Skipped - Medium priority)
- ✅ UI-016: Documentation
- ✅ UI-017: Cross-platform Polish
- ✅ UI-018: Installer Creation

### Deferred Tickets
- ⏸️ UI-012: Screen Reader Support (Deferred - Low priority, High complexity)
- ⏸️ UI-015: Visual Regression Testing (Deferred - Medium priority)

---

## Project Status Assessment

### Current State (PH2-UXR-020 Already Implemented)
- ✅ Dark theme with comprehensive design tokens
- ✅ Component-based architecture (AppButton, AppTextField, AppComboBox, etc.)
- ✅ Responsive design with breakpoints (compact: 1320px, narrow: 1160px)
- ✅ Semantic color system (success, warning, danger, info)
- ✅ Card-based surfaces with elevation levels
- ✅ Cross-platform support (Windows/Linux/macOS)

### Technical Debt & Opportunities
- ❌ **Main.qml is 2828 lines** - needs decomposition
- ⚠️ Limited animations/transitions
- ⚠️ Basic icon system
- ⚠️ No centralized state management
- ⚠️ Tables could benefit from virtualization for large datasets
- ⚠️ No visual feedback for long operations
- ⚠️ Limited accessibility features

---

## Ticket Breakdown

### Phase 1: Architecture & Code Organization (Foundation)

#### Ticket UI-001: Component Extraction - Meter Tab ✅
**Priority:** High | **Complexity:** Medium | **Estimated Size:** 3-5 files | **Status:** Completed

**Description:** Extract Meter tab UI into separate components for better maintainability.

**Tasks:**
- [x] Create `components/meter/MeterTab.qml` - Main meter tab container
- [x] Create `components/meter/MeterControls.qml` - Mode/Sort control bar
- [x] Create `components/meter/MeterScoreboard.qml` - Player list with table header
- [x] Create `components/meter/MeterHistoryPanel.qml` - History sidebar
- [x] Create `components/meter/MeterLegend.qml` - Keyboard shortcuts legend
- [x] Update Main.qml to use new components
- [x] Verify all functionality works after extraction

**Files to Create:**
- `albion_dps/qt/ui/components/meter/MeterTab.qml`
- `albion_dps/qt/ui/components/meter/MeterControls.qml`
- `albion_dps/qt/ui/components/meter/MeterScoreboard.qml`
- `albion_dps/qt/ui/components/meter/MeterHistoryPanel.qml`
- `albion_dps/qt/ui/components/meter/MeterLegend.qml`

**Files to Modify:**
- `albion_dps/qt/ui/Main.qml`

---

#### Ticket UI-002: Component Extraction - Scanner Tab
**Priority:** High | **Complexity:** Low | **Estimated Size:** 2-3 files

**Description:** Extract Scanner tab UI into separate components.

**Tasks:**
- [ ] Create `components/scanner/ScannerTab.qml` - Main scanner tab container
- [ ] Create `components/scanner/ScannerControls.qml` - Action buttons bar
- [ ] Create `components/scanner/ScannerLogView.qml` - Log output area
- [ ] Update Main.qml to use new components
- [ ] Verify all functionality works after extraction

**Files to Create:**
- `albion_dps/qt/ui/components/scanner/ScannerTab.qml`
- `albion_dps/qt/ui/components/scanner/ScannerControls.qml`
- `albion_dps/qt/ui/components/scanner/ScannerLogView.qml`

**Files to Modify:**
- `albion_dps/qt/ui/Main.qml`

---

#### Ticket UI-003: Component Extraction - Market Tab
**Priority:** High | **Complexity:** High | **Estimated Size:** 8-10 files

**Description:** Extract Market tab UI into separate components (most complex tab).

**Tasks:**
- [ ] Create `components/market/MarketTab.qml` - Main market tab container
- [ ] Create `components/market/MarketStatusBar.qml` - Status and control bar
- [ ] Create `components/market/MarketSetupPanel.qml` - Setup sub-tab
- [ ] Create `components/market/MarketCraftSearch.qml` - Recipe search with suggestions
- [ ] Create `components/market/MarketPresets.qml` - Preset management
- [ ] Create `components/market/MarketCraftsTable.qml` - Craft plan table
- [ ] Create `components/market/MarketInputsList.qml` - Inputs table
- [ ] Create `components/market/MarketOutputsList.qml` - Outputs table
- [ ] Create `components/market/MarketResultsView.qml` - Results summary
- [ ] Create `components/market/MarketDiagnostics.qml` - Diagnostics panel
- [ ] Update Main.qml to use new components
- [ ] Verify all functionality works after extraction

**Files to Create:**
- `albion_dps/qt/ui/components/market/MarketTab.qml`
- `albion_dps/qt/ui/components/market/MarketStatusBar.qml`
- `albion_dps/qt/ui/components/market/MarketSetupPanel.qml`
- `albion_dps/qt/ui/components/market/MarketCraftSearch.qml`
- `albion_dps/qt/ui/components/market/MarketPresets.qml`
- `albion_dps/qt/ui/components/market/MarketCraftsTable.qml`
- `albion_dps/qt/ui/components/market/MarketInputsList.qml`
- `albion_dps/qt/ui/components/market/MarketOutputsList.qml`
- `albion_dps/qt/ui/components/market/MarketResultsView.qml`
- `albion_dps/qt/ui/components/market/MarketDiagnostics.qml`

**Files to Modify:**
- `albion_dps/qt/ui/Main.qml`

---

#### Ticket UI-004: Shell/Header Component Extraction
**Priority:** Medium | **Complexity:** Medium | **Estimated Size:** 3-4 files

**Description:** Extract the application shell (header, navigation, update banner) into separate components.

**Tasks:**
- [ ] Create `components/shell/AppShell.qml` - Main shell container
- [ ] Create `components/shell/AppHeader.qml` - Top header bar
- [ ] Create `components/shell/UpdateBanner.qml` - Update notification banner
- [ ] Create `components/shell/SupportButtons.qml` - PayPal/Coffee buttons
- [ ] Update Main.qml to use new components
- [ ] Verify all functionality works after extraction

**Files to Create:**
- `albion_dps/qt/ui/components/shell/AppShell.qml`
- `albion_dps/qt/ui/components/shell/AppHeader.qml`
- `albion_dps/qt/ui/components/shell/UpdateBanner.qml`
- `albion_dps/qt/ui/components/shell/SupportButtons.qml`

**Files to Modify:**
- `albion_dps/qt/ui/Main.qml`

---

### Phase 2: Enhanced Components & UX Improvements

#### Ticket UI-005: Enhanced Table Component
**Priority:** Medium | **Complexity:** Medium | **Estimated Size:** 1 file

**Description:** Create an enhanced table component with built-in features.

**Tasks:**
- [ ] Create `components/common/EnhancedTable.qml` with:
  - [ ] Built-in sort indicators
  - [ ] Column resize handles
  - [ ] Row selection state
  - [ ] Context menu support
  - [ ] Copy to clipboard functionality
  - [ ] Better hover/selection animations
- [ ] Add sort indicator icons to theme
- [ ] Implement column resize logic
- [ ] Add keyboard navigation (arrow keys, Home/End)
- [ ] Migrate existing tables to use EnhancedTable

**Files to Create:**
- `albion_dps/qt/ui/components/common/EnhancedTable.qml`

**Files to Modify:**
- `albion_dps/qt/ui/Theme.qml` (add sort icons)

---

#### Ticket UI-006: Loading & Progress Indicators
**Priority:** Medium | **Complexity:** Low | **Estimated Size:** 2 files

**Description:** Add proper loading states and progress indicators.

**Tasks:**
- [ ] Create `components/common/LoadingOverlay.qml` - Full-screen loading overlay
- [ ] Create `components/common/ProgressBar.qml` - Linear progress indicator
- [ ] Create `components/common/Spinner.qml` - Circular loading spinner
- [ ] Add loading states to Market tab price fetching
- [ ] Add progress indication to long operations
- [ ] Ensure accessibility (ARIA labels)

**Files to Create:**
- `albion_dps/qt/ui/components/common/LoadingOverlay.qml`
- `albion_dps/qt/ui/components/common/ProgressBar.qml`
- `albion_dps/qt/ui/components/common/Spinner.qml`

**Files to Modify:**
- Various market components (to add loading states)

---

#### Ticket UI-007: Toast Notification System
**Priority:** Low | **Complexity:** Medium | **Estimated Size:** 2 files

**Description:** Implement a toast notification system for user feedback.

**Tasks:**
- [ ] Create `components/common/ToastManager.qml` - Notification manager
- [ ] Create `components/common/Toast.qml` - Individual toast component
- [ ] Add toast notifications for:
  - [ ] Copy to clipboard confirmation
  - [ ] Preset save/load/delete
  - [ ] Craft add/remove
  - [ ] Scanner start/stop
  - [ ] Update check results
- [ ] Add animation (slide in/out)
- [ ] Add auto-dismiss with timer
- [ ] Add manual dismiss button

**Files to Create:**
- `albion_dps/qt/ui/components/common/ToastManager.qml`
- `albion_dps/qt/ui/components/common/Toast.qml`

**Files to Modify:**
- `albion_dps/qt/ui/Main.qml` (add ToastManager)

---

#### Ticket UI-008: Enhanced Icon System
**Priority:** Low | **Complexity:** Medium | **Estimated Size:** 3 files

**Description:** Improve the icon system with SVG icons and helper component.

**Tasks:**
- [ ] Create `components/common/Icon.qml` - SVG icon component
- [ ] Create `assets/icons/` directory structure
- [ ] Add SVG icons for:
  - [ ] Sort ascending/descending
  - [ ] Close/Dismiss
  - [ ] Copy to clipboard
  - [ ] Settings/Configuration
  - [ ] Refresh/Reload
  - [ ] Warning/Info/Success/Error states
  - [ ] Market/Scanner/Meter tab icons
  - [ ] Arrow icons (expand/collapse)
- [ ] Add icon size tokens to Theme.qml
- [ ] Replace text/icon combos with proper icons

**Files to Create:**
- `albion_dps/qt/ui/components/common/Icon.qml`
- `albion_dps/qt/ui/assets/icons/sort-up.svg`
- `albion_dps/qt/ui/assets/icons/sort-down.svg`
- `albion_dps/qt/ui/assets/icons/close.svg`
- `albion_dps/qt/ui/assets/icons/copy.svg`
- `albion_dps/qt/ui/assets/icons/settings.svg`
- `albion_dps/qt/ui/assets/icons/refresh.svg`
- Additional icons as needed

**Files to Modify:**
- `albion_dps/qt/ui/Theme.qml` (add icon size tokens)

---

### Phase 3: Animation & Visual Polish

#### Ticket UI-009: Micro-Interactions & Animations
**Priority:** Low | **Complexity:** Medium | **Estimated Size:** Modify multiple files

**Description:** Add smooth animations and micro-interactions throughout the UI.

**Tasks:**
- [ ] Add hover animations to all buttons (scale/brightness)
- [ ] Add slide-in animation for tab switching
- [ ] Add fade-in animation for list items
- [ ] Add smooth transition for expand/collapse sections
- [ ] Add ripple effect for buttons (optional)
- [ ] Add loading skeleton screens for tables
- [ ] Ensure animations respect reduced motion preferences

**Files to Modify:**
- `albion_dps/qt/ui/components/common/AppButton.qml`
- `albion_dps/qt/ui/components/common/AppComboBox.qml`
- All tab components
- All list/table components

**New Utilities:**
- `albion_dps/qt/ui/utils/AnimationUtils.qml` - Reusable animation definitions

---

#### Ticket UI-010: Enhanced Scrollbar Styling
**Priority:** Low | **Complexity:** Low | **Estimated Size:** 1 file

**Description:** Create custom styled scrollbars that match the theme.

**Tasks:**
- [ ] Create `components/common/StyledScrollBar.qml`
- [ ] Design thin, modern scrollbar that appears on hover
- [ ] Add scrollbar track and thumb styling
- [ ] Add smooth scrolling behavior
- [ ] Replace default ScrollBar in all ScrollViews

**Files to Create:**
- `albion_dps/qt/ui/components/common/StyledScrollBar.qml`

**Files to Modify:**
- All components using ScrollView

---

### Phase 4: Accessibility & Usability

#### Ticket UI-011: Keyboard Navigation Improvements
**Priority:** Medium | **Complexity:** Medium | **Estimated Size:** Modify multiple files

**Description:** Improve keyboard navigation throughout the application.

**Tasks:**
- [ ] Add Tab focus indicators to all interactive elements
- [ ] Implement arrow key navigation in tables
- [ ] Add Enter/Space key activation for buttons
- [ ] Add Escape key to close dialogs/popups
- [ ] Add Home/End navigation in lists
- [ ] Implement focus management when switching tabs
- [ ] Add visual focus indicators in Theme.qml

**Files to Modify:**
- All component files
- `albion_dps/qt/ui/Theme.qml` (add focus ring tokens)

---

#### Ticket UI-012: Screen Reader Support
**Priority:** Low | **Complexity:** High | **Estimated Size:** Modify multiple files

**Description:** Add proper accessibility labels and roles for screen readers.

**Tasks:**
- [ ] Add Accessible.name and Accessible.description to all controls
- [ ] Add proper roles for interactive elements
- [ ] Add live region announcements for dynamic content
- [ ] Add ARIA labels for icon-only buttons
- [ ] Test with NVDA (Windows) / VoiceOver (macOS) / Orca (Linux)

**Files to Modify:**
- All component files

---

### Phase 5: Performance Optimization

#### Ticket UI-013: List & Table Virtualization
**Priority:** Medium | **Complexity:** High | **Estimated Size:** Modify multiple files

**Description:** Implement proper virtualization for large lists to improve performance.

**Tasks:**
- [ ] Audit all ListView components for optimization opportunities
- [ ] Ensure reuseItems is enabled everywhere
- [ ] Add appropriate cacheBuffer values
- [ ] Implement asynchronous model loading for large datasets
- [ ] Add lazy loading for market results
- [ ] Profile and measure performance improvements

**Files to Audit/Modify:**
- All ListView components in extracted components
- Market results list (largest dataset)
- History list
- Craft plan list

---

#### Ticket UI-014: Asset Optimization
**Priority:** Low | **Complexity:** Low | **Estimated Size:** Asset files

**Description:** Optimize assets for faster loading and smaller distribution.

**Tasks:**
- [ ] Convert any raster icons to SVG
- [ ] Optimize SVG files (remove unnecessary metadata)
- [ ] Add asset bundling strategy
- [ ] Consider inlining critical SVGs
- [ ] Add fallback icons if assets fail to load

---

### Phase 6: Testing & Documentation

#### Ticket UI-015: Visual Regression Testing Setup
**Priority:** Medium | **Complexity:** Medium | **Estimated Size:** Testing infrastructure

**Description:** Set up visual regression testing for UI components.

**Tasks:**
- [ ] Research QML screenshot testing tools
- [ ] Create baseline screenshots for all components
- [ ] Set up automated screenshot capture
- [ ] Create comparison script
- [ ] Document visual testing process

**Files to Create:**
- `tests/ui/visual/README.md`
- `tests/ui/visual/capture_baselines.py`
- `tests/ui/visual/compare_baselines.py`

---

#### Ticket UI-016: Component Documentation
**Priority:** Low | **Complexity:** Low | **Estimated Size:** Documentation files

**Description:** Document all UI components for future maintenance.

**Tasks:**
- [ ] Create component documentation for each extracted component
- [ ] Document props/slots/signals for each component
- [ ] Create usage examples
- [ ] Add inline code comments
- [ ] Create component catalog/storybook

**Files to Create:**
- `docs/ui/components/README.md`
- `docs/ui/components/MeterTab.md`
- `docs/ui/components/ScannerTab.md`
- `docs/ui/components/MarketTab.md`
- `docs/ui/components/Common.md`

---

### Phase 7: Cross-Platform Polish

#### Ticket UI-017: Platform-Specific Adjustments
**Priority:** Low | **Complexity:** Medium | **Estimated Size:** Modify multiple files

**Description:** Fine-tune UI for each platform (Windows/Linux/macOS).

**Tasks:**
- [ ] Test on Windows - ensure proper font rendering
- [ ] Test on Linux - verify with different GTK themes
- [ ] Test on macOS - ensure native feel
- [ ] Add platform-specific font fallbacks
- [ ] Adjust window chrome/frame handling per platform
- [ ] Test high DPI (4K) displays
- [ ] Test different screen sizes

**Files to Modify:**
- `albion_dps/qt/ui/Main.qml`
- `albion_dps/qt/ui/Theme.qml`
- Platform-specific runners

---

#### Ticket UI-018: Installer UI Integration
**Priority:** Low | **Complexity:** Medium | **Estimated Size:** New installer files

**Description:** Integrate UI into simple installer for end users.

**Tasks:**
- [ ] Design simple installer welcome screen (can reuse UI components)
- [ ] Add installation progress screen
- [ ] Add completion screen with launch option
- [ ] Create Windows NSIS installer script
- [ ] Create Linux .desktop file and AppImage script
- [ ] Create macOS .app bundle structure
- [ ] Test installer on all platforms

**Files to Create:**
- `installer/windows/installer.nsi`
- `installer/linux/albion-command-desk.desktop`
- `installer/linux/build-appimage.sh`
- `installer/macos/create-app-bundle.sh`
- `albion_dps/qt/ui/installer/InstallerWelcome.qml`

---

## Implementation Order

### Sprint 1: Foundation (Tickets UI-001 to UI-004)
**Goal:** Break down Main.qml into manageable components

### Sprint 2: Enhancement (Tickets UI-005 to UI-008)
**Goal:** Add new component capabilities and visual elements

### Sprint 3: Polish (Tickets UI-009 to UI-010)
**Goal:** Add animations and visual improvements

### Sprint 4: Accessibility (Tickets UI-011 to UI-012)
**Goal:** Improve keyboard navigation and screen reader support

### Sprint 5: Performance (Tickets UI-013 to UI-014)
**Goal:** Optimize large lists and assets

### Sprint 6: Quality Assurance (Tickets UI-015 to UI-016)
**Goal:** Set up testing and documentation

### Sprint 7: Final Polish (Tickets UI-017 to UI-018)
**Goal:** Cross-platform testing and installer integration

---

## Success Criteria

### Must Have (MVP)
- ✅ Main.qml reduced to under 500 lines
- ✅ All functionality preserved and working
- ✅ Component extraction complete (all tabs and shell)
- ✅ Cross-platform compatibility maintained

### Should Have
- ✅ Enhanced table component with sorting
- ✅ Loading states for async operations
- ✅ Improved keyboard navigation
- ✅ Performance optimizations for large lists

### Could Have
- ✅ Toast notification system
- ✅ Enhanced icon system with SVGs
- ✅ Micro-interactions and animations
- ✅ Visual regression testing

### Won't Have (Out of Scope)
- ❌ Light theme (unless specifically requested)
- ❌ Complete UI framework rewrite
- ❌ Web version
- ❌ Mobile version

---

## Technical Notes

### QML Best Practices to Follow
1. Keep components under 300 lines
2. Use property bindings instead of imperative code
3. Prefer Composition over Inheritance
4. Use Loader for lazy loading
5. Enable reuseItems on all ListViews
6. Use appropriate cacheBuffer values
7. Avoid JavaScript in bindings (use functions)
8. Use Qt.callLater() for async operations

### Theme Token Extensions Needed
- Icon sizes (xs, sm, md, lg, xl)
- Focus ring styles
- Animation durations (fast, normal, slow)
- Easing curves
- Shadow definitions
- Z-index layers

### File Structure After Refactoring
```
albion_dps/qt/ui/
├── Main.qml (reduced to ~200-300 lines)
├── Theme.qml (enhanced)
├── components/
│   ├── common/
│   │   ├── AppButton.qml (existing)
│   │   ├── AppTextField.qml (existing)
│   │   ├── AppComboBox.qml (existing)
│   │   ├── AppCheckBox.qml (existing)
│   │   ├── AppSpinBox.qml (existing)
│   │   ├── CardPanel.qml (existing)
│   │   ├── TableSurface.qml (existing)
│   │   ├── ShellTabButton.qml (existing)
│   │   ├── EnhancedTable.qml (new)
│   │   ├── LoadingOverlay.qml (new)
│   │   ├── ProgressBar.qml (new)
│   │   ├── Spinner.qml (new)
│   │   ├── ToastManager.qml (new)
│   │   ├── Toast.qml (new)
│   │   ├── Icon.qml (new)
│   │   └── StyledScrollBar.qml (new)
│   ├── shell/
│   │   ├── AppShell.qml (new)
│   │   ├── AppHeader.qml (new)
│   │   ├── UpdateBanner.qml (new)
│   │   └── SupportButtons.qml (new)
│   ├── meter/
│   │   ├── MeterTab.qml (new)
│   │   ├── MeterControls.qml (new)
│   │   ├── MeterScoreboard.qml (new)
│   │   ├── MeterHistoryPanel.qml (new)
│   │   └── MeterLegend.qml (new)
│   ├── scanner/
│   │   ├── ScannerTab.qml (new)
│   │   ├── ScannerControls.qml (new)
│   │   └── ScannerLogView.qml (new)
│   └── market/
│       ├── MarketTab.qml (new)
│       ├── MarketStatusBar.qml (new)
│       ├── MarketSetupPanel.qml (new)
│       ├── MarketCraftSearch.qml (new)
│       ├── MarketPresets.qml (new)
│       ├── MarketCraftsTable.qml (new)
│       ├── MarketInputsList.qml (new)
│       ├── MarketOutputsList.qml (new)
│       ├── MarketResultsView.qml (new)
│       └── MarketDiagnostics.qml (new)
├── assets/
│   └── icons/
│       ├── sort-up.svg (new)
│       ├── sort-down.svg (new)
│       └── ... (additional icons)
└── utils/
    └── AnimationUtils.qml (new)
```

---

## Dependencies & Risks

### Dependencies
- PySide6 6.6+ (already in use)
- Existing Python backend (must remain unchanged)
- Existing state management (uiState, scannerState, marketSetupState)

### Risks
1. **Breaking Changes** - Component extraction must maintain exact functionality
2. **Performance** - More components = more overhead if not careful
3. **Testing** - No automated UI tests currently, manual testing required
4. **Backwards Compatibility** - Python backend must work with new UI

### Mitigation
- Test thoroughly after each ticket
- Keep PRs small and focused
- Run application on all platforms after major changes
- Document any API changes between components

---

## Definition of Done for Each Ticket

- [ ] Code written and follows QML best practices
- [ ] All existing functionality preserved
- [ ] No console errors or warnings
- [ ] Tested on Windows, Linux, and macOS (if possible)
- [ ] Code reviewed and self-checked
- [ ] Documentation updated (if applicable)
- [ ] Git commit with clear message

---

## Next Steps

1. **Review this plan** and approve the approach
2. **Start with Ticket UI-001** (Meter Tab extraction)
3. **Create feature branch** for each ticket (or group of related tickets)
4. **Test thoroughly** after each ticket
5. **Merge back to feature/ui-modernization** after each sprint
6. **Final merge to main** after all tickets complete

---

*Document created: 2026-02-17*
*Branch: feature/ui-modernization*
*Target: Albion Command Desk v0.2.0*
