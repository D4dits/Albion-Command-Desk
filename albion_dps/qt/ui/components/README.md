# UI Components Documentation

## Overview

The Albion Command Desk UI is built using QML/QtQuick 2.15 with a component-based architecture. All components are organized by feature area and share common design tokens from the Theme system.

## Component Structure

```
albion_dps/qt/ui/
├── Main.qml                 # Main application window
├── Theme.qml               # Design tokens and theme definitions
├── AppButton.qml           # Button component (primary, secondary, ghost, danger, warm)
├── AppComboBox.qml         # Dropdown selector
├── AppCheckBox.qml         # Checkbox input
├── AppTextField.qml        # Text input field
├── components/
│   ├── common/             # Shared/reusable components
│   │   ├── Icon.qml
│   │   ├── Toast.qml
│   │   ├── ToastManager.qml
│   │   ├── Spinner.qml
│   │   ├── ProgressBar.qml
│   │   ├── LoadingOverlay.qml
│   │   ├── StyledScrollBar.qml
│   │   └── EnhancedTable.qml
│   ├── meter/              # DPS Meter tab components
│   │   ├── MeterTab.qml
│   │   ├── MeterControls.qml
│   │   ├── MeterScoreboard.qml
│   │   ├── MeterHistoryPanel.qml
│   │   └── MeterLegend.qml
│   ├── scanner/            # Scanner tab components
│   │   ├── ScannerTab.qml
│   │   ├── ScannerControls.qml
│   │   └── ScannerLogView.qml
│   ├── market/             # Market tab components
│   │   ├── MarketTab.qml
│   │   ├── MarketStatusBar.qml
│   │   ├── MarketSetupPanel.qml
│   │   ├── MarketCraftSearch.qml
│   │   ├── MarketPresets.qml
│   │   ├── MarketCraftsTable.qml
│   │   └── MarketDiagnostics.qml
│   └── shell/              # Application shell components
│       ├── AppShell.qml
│       ├── AppHeader.qml
│       ├── UpdateBanner.qml
│       └── SupportButtons.qml
└── utils/
    ├── AnimationUtils.qml  # Animation singleton
    └── qmldir              # QML module definitions
```

## Common Components

### Icon
Text-based icon component with configurable size and color.

```qml
import "../common" as CommonComponents

CommonComponents.Icon {
    name: "close"  // close, check, warning, error, info, sortUp, sortDown, etc.
    size: 20
    color: theme.textPrimary
}
```

**Available icons**: close, check, warning, error, info, sortUp, sortDown, sort, plus, minus, arrowRight, arrowLeft, arrowDown, arrowUp, dots, copy, refresh, settings, menu, search, star, heart, bookmark.

### ToastManager
Notification system for displaying toast messages.

```qml
CommonComponents.ToastManager {
    id: toastManager
    theme: root.theme
}

// Show notifications
toastManager.showSuccess("Success", "Operation completed")
toastManager.showWarning("Warning", "Please check your input")
toastManager.showError("Error", "Something went wrong")
toastManager.showInfo("Info", "Processing...")
```

### Spinner
Loading indicator with configurable size.

```qml
CommonComponents.Spinner {
    size: "md"  // xs, sm, md, lg, xl
    active: true
    label: "Loading..."
}
```

### ProgressBar
Linear progress indicator with determinate/indeterminate modes.

```qml
CommonComponents.ProgressBar {
    value: 0.75  // 0-1
    indeterminate: false
    showLabel: true
    labelText: "Loading..."
}
```

### EnhancedTable
Advanced table component with sorting and keyboard navigation.

```qml
CommonComponents.EnhancedTable {
    columns: ListModel {
        ListElement { title: "Name"; role: "name"; width: 150; sortable: true }
        ListElement { title: "Value"; role: "value"; width: 100; sortable: true }
    }
    model: myModel
    sortColumn: 0
    sortDescending: false
    onSortChanged: function(column, descending) { ... }
    onRowSelected: function(index) { ... }
    onRowDoubleClicked: function(index, rowData) { ... }
}
```

**Keyboard shortcuts**:
- Arrow Up/Down: Navigate rows
- Home/End: First/Last row
- Page Up/Down: Navigate by page
- Enter: Trigger double-click action

## Form Controls

### AppButton
Button with multiple variants and hover/press animations.

```qml
AppButton {
    text: "Click me"
    variant: "primary"  // primary, secondary, ghost, danger, warm
    compact: false
    onClicked: { ... }
}
```

### AppComboBox
Dropdown selector.

```qml
AppComboBox {
    model: ["Option 1", "Option 2", "Option 3"]
    currentIndex: 0
    onActivated: function(index) { ... }
}
```

### AppCheckBox
Checkbox input.

```qml
AppCheckBox {
    text: "Enable feature"
    checked: false
    onToggled: function(checked) { ... }
}
```

### AppTextField
Text input field.

```qml
AppTextField {
    placeholderText: "Enter text..."
    text: ""
    onTextEdited: function(text) { ... }
    onAccepted: { ... }  // Enter key pressed
}
```

## Theme System

The theme is defined in `Theme.qml` and provides design tokens for:

**Colors**:
- Brand: `brandPrimary`, `brandSecondary`, `brandWarmAccent`
- Surfaces: `surfaceApp`, `surfacePanel`, `surfaceRaised`, etc.
- Borders: `borderSubtle`, `borderStrong`, `borderFocus`
- Text: `textPrimary`, `textSecondary`, `textMuted`, `textDisabled`
- States: `stateSuccess`, `stateWarning`, `stateDanger`, `stateInfo`
- Tables: `tableHeaderBackground`, `tableRowEven`, `tableRowOdd`, etc.
- Buttons: `buttonPrimaryBackground`, `buttonSecondaryHover`, etc.
- Scrollbars: `scrollbarTrack`, `scrollbarThumb`, etc.

**Spacing**:
- `spacingXs`: 4px
- `spacingSm`: 8px
- `spacingMd`: 12px
- `spacingLg`: 16px
- `spacingXl`: 24px

**Sizes**:
- Icon sizes: `iconSizeXs` (12) to `iconSizeXl` (32)
- Button heights: `buttonHeightCompact` (24), `buttonHeightRegular` (30)
- Control heights: `controlHeightCompact` (24), `controlHeightRegular` (30)

**Motion**:
- `motionFastMs`: 100ms
- `motionNormalMs`: 140ms
- `motionSlowMs`: 180ms

### Using Theme Tokens

```qml
property var theme: Theme {}

Rectangle {
    color: theme.surfacePanel
    border.color: theme.borderSubtle
    border.width: 1
    radius: theme.radiusMd
}

Text {
    color: theme.textPrimary
    font.pixelSize: 12
}
```

## Animation Utilities

The `AnimationUtils` singleton provides reusable animation definitions.

```qml
import "utils" 1.0 as Utils

Behavior on opacity {
    NumberAnimation {
        duration: Utils.AnimationUtils.durationNormal
        easing.type: Utils.AnimationUtils.easingOut
    }
}
```

**Durations**:
- `durationInstant`: 0ms
- `durationFast`: 100ms
- `durationNormal`: 150ms
- `durationSlow`: 200ms
- `durationSlower`: 300ms

**Easing**:
- `easingOut`: OutCubic
- `easingIn`: InCubic
- `easeInOut`: InOutCubic
- `easingOutBack`: OutBack (with overshoot)
- `easingOutQuad`: OutQuad
- `easingLinear`: Linear

## Performance Best Practices

1. **ListView Virtualization**: All ListViews have `reuseItems: true` and `cacheBuffer` set
2. **Lazy Loading**: Large datasets load asynchronously
3. **Property Bindings**: Minimize complex bindings in delegates
4. **Animations**: Use `Behavior` for smooth transitions
5. **Loading States**: Show indicators during long operations

## Cross-Platform Considerations

- **Windows**: Uses Npcap for packet capture
- **Linux**: Uses libpcap for packet capture
- **macOS**: Uses native packet capture (may require sudo)

Component layouts adapt to breakpoints:
- `breakpointCompact`: 1320px
- `breakpointNarrow`: 1160px

## Creating New Components

When creating new components:

1. Place in appropriate directory (`common/`, `meter/`, etc.)
2. Import Theme: `import "../../." // for Theme access`
3. Add comprehensive JSDoc-style documentation
4. Use theme tokens for all colors, spacing, sizes
5. Add appropriate animations via AnimationUtils
6. Include keyboard navigation where applicable
7. Test with different screen sizes and themes

Example template:

```qml
import QtQuick 2.15
import "../../." // for Theme access

/**
 * ComponentName - Brief description
 *
 * Features:
 * - Feature 1
 * - Feature 2
 *
 * Usage:
 *   ComponentName {
 *       property: value
 *   }
 */
Rectangle {
    id: root

    // Public properties
    property string text: ""

    // Access to theme
    property var theme: Theme {}

    // Implementation...
}
```
