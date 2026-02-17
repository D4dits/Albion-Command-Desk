import QtQuick 2.15

QtObject {
    // Visual direction (PH2-UXR-020):
    // - dark neutral surfaces
    // - cool blue primary actions
    // - warm amber highlights for premium/support accents

    // Brand tokens
    readonly property color brandPrimary: "#4aa3ff"
    readonly property color brandPrimaryHover: "#66b4ff"
    readonly property color brandPrimaryPressed: "#2e8df0"
    readonly property color brandSecondary: "#2ea8a1"
    readonly property color brandWarmAccent: "#f2c14e"

    // Surface tokens
    readonly property color surfaceApp: "#0b0f14"
    readonly property color surfacePanel: "#131a22"
    readonly property color surfaceRaised: "#182231"
    readonly property color surfaceOverlay: "#0d1826"
    readonly property color surfaceInteractive: "#111e2d"
    readonly property color surfaceInset: "#0f1620"
    readonly property color cardLevel0: "#121922"
    readonly property color cardLevel1: "#16202d"
    readonly property color cardLevel2: "#1a2634"

    // Border tokens
    readonly property color borderSubtle: "#1f2a37"
    readonly property color borderStrong: "#2a3a4f"
    readonly property color borderFocus: "#4aa3ff"
    readonly property color borderDanger: "#ff7b72"
    readonly property color dividerMuted: "#1a2533"

    // Text tokens
    readonly property color textPrimary: "#e6edf3"
    readonly property color textSecondary: "#cbd8e6"
    readonly property color textMuted: "#b1bfce"
    readonly property color textDisabled: "#6e7d8f"
    readonly property color textOnAccent: "#081018"

    // Semantic state tokens
    readonly property color accentPrimary: brandPrimary
    readonly property color stateSuccess: "#2ea043"
    readonly property color stateWarning: "#e3b341"
    readonly property color stateDanger: "#ff7b72"
    readonly property color stateInfo: "#79c0ff"

    readonly property color stateSuccessBg: "#11261b"
    readonly property color stateWarningBg: "#2a220f"
    readonly property color stateDangerBg: "#2f1416"
    readonly property color stateInfoBg: "#112433"

    // Control tokens
    readonly property color controlIdleBackground: "#101923"
    readonly property color controlHoverBackground: "#142437"
    readonly property color controlPressedBackground: "#1a2c40"
    readonly property color controlDisabledBackground: "#0e141d"
    readonly property color controlDisabledBorder: "#223040"
    readonly property color inputBackground: "#111d2b"
    readonly property color inputBackgroundDisabled: "#0d141e"
    readonly property color inputBorder: "#253449"
    readonly property color inputBorderFocus: "#4aa3ff"

    // Button tokens
    readonly property color buttonPrimaryBackground: brandPrimary
    readonly property color buttonPrimaryHover: brandPrimaryHover
    readonly property color buttonPrimaryPressed: brandPrimaryPressed
    readonly property color buttonPrimaryText: textOnAccent
    readonly property color buttonSecondaryBackground: "#1b2a3c"
    readonly property color buttonSecondaryHover: "#24354a"
    readonly property color buttonSecondaryPressed: "#1a293a"
    readonly property color buttonSecondaryText: textPrimary
    readonly property color buttonGhostBackground: "transparent"
    readonly property color buttonGhostHover: "#182636"
    readonly property color buttonGhostPressed: "#1f3145"
    readonly property color buttonGhostText: textSecondary
    readonly property color buttonDangerBackground: "#b93c47"
    readonly property color buttonDangerHover: "#d14957"
    readonly property color buttonDangerPressed: "#a5323d"
    readonly property color buttonDangerText: "#ffffff"
    readonly property int buttonHeightCompact: 24
    readonly property int buttonHeightRegular: 30
    readonly property int buttonRadiusCompact: 4
    readonly property int buttonRadiusRegular: 6

    // Table tokens
    readonly property color tableHeaderBackground: "#111b28"
    readonly property color tableHeaderText: "#c8d6e5"
    readonly property color tableRowEven: "#0f1620"
    readonly property color tableRowOdd: "#101924"
    readonly property color tableRowHover: "#142437"
    readonly property color tableSelectedBackground: "#162231"
    readonly property color tableSelectedBorder: "#4aa3ff"
    readonly property color tableTextPrimary: "#e6edf3"
    readonly property color tableTextSecondary: "#aebbc9"
    readonly property color tableDivider: "#1e2a39"
    readonly property color tableSortIndicator: brandPrimary
    readonly property color tableSortIndicatorInactive: "#5f6b7a"
    readonly property int focusRingWidth: 2

    // Layout tokens
    readonly property int spacingXs: 4
    readonly property int spacingSm: 8
    readonly property int spacingMd: 12
    readonly property int spacingLg: 16
    readonly property int spacingXl: 24
    readonly property int spacingPage: 16
    readonly property int spacingSection: 12
    readonly property int spacingCompact: 8
    readonly property int radiusSm: 4
    readonly property int radiusMd: 6
    readonly property int radiusLg: 8
    readonly property int cornerRadiusPanel: 8
    readonly property int controlHeightCompact: 24
    readonly property int controlHeightRegular: 30

    // Icon tokens
    readonly property int iconSizeXs: 12
    readonly property int iconSizeSm: 16
    readonly property int iconSizeMd: 20
    readonly property int iconSizeLg: 24
    readonly property int iconSizeXl: 32

    // Elevation tokens (for shadow/overlay usage when needed)
    readonly property real elevationLowOpacity: 0.12
    readonly property real elevationMediumOpacity: 0.20
    readonly property real elevationHighOpacity: 0.28
    readonly property int motionFastMs: 100
    readonly property int motionNormalMs: 140
    readonly property int motionSlowMs: 180
    readonly property int breakpointCompact: 1320
    readonly property int breakpointNarrow: 1160

    // Shell tokens
    readonly property int shellHeaderHeight: 72
    readonly property int shellRightZoneSpacing: 8
    readonly property int shellMeterMetaWidth: 180
    readonly property int shellUpdateControlWidth: 215
    readonly property int shellUpdateBannerMinWidth: 270
    readonly property int shellUpdateBannerMaxWidth: 420
    readonly property int shellNavHeight: 34
    readonly property int shellNavWidthMax: 920
    readonly property int shellNavWidthMin: 520
    readonly property int shellTabRadius: 5
    readonly property color shellTabIdleBackground: "#0f1620"
    readonly property color shellTabActiveText: "#0b0f14"
    readonly property int shellPillRadius: 16
    readonly property int shellActionHeight: 28
    readonly property color shellBannerBackground: "#1a2d20"
    readonly property color shellBannerBorder: "#2ea043"
    readonly property color shellBannerText: "#7ee787"

    // Market tokens
    readonly property int marketColumnSpacing: 6
    readonly property int marketSetupPanelWidth: 330
}
