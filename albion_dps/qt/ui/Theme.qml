import QtQuick 2.15

QtObject {
    // Color tokens
    readonly property color surfaceApp: "#0b0f14"
    readonly property color surfacePanel: "#131a22"
    readonly property color borderSubtle: "#1f2a37"
    readonly property color textPrimary: "#e6edf3"
    readonly property color textMuted: "#9aa4af"
    readonly property color accentPrimary: "#4aa3ff"
    readonly property color stateSuccess: "#2ea043"
    readonly property color stateWarning: "#e3b341"
    readonly property color stateDanger: "#ff7b72"
    readonly property color stateInfo: "#79c0ff"
    readonly property color surfaceInset: "#0f1620"
    readonly property color controlIdleBackground: "#101923"
    readonly property color tableHeaderBackground: "#111b28"
    readonly property color tableRowEven: "#0f1620"
    readonly property color tableRowOdd: "#101924"
    readonly property color tableSelectedBackground: "#162231"

    // Layout tokens
    readonly property int spacingPage: 16
    readonly property int spacingSection: 12
    readonly property int spacingCompact: 8
    readonly property int cornerRadiusPanel: 8
    readonly property int controlHeightCompact: 24
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

    // Market tokens
    readonly property int marketColumnSpacing: 6
    readonly property int marketSetupPanelWidth: 360
}
