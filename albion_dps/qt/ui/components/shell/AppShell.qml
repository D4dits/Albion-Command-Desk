import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../." // for all component access

/**
 * AppShell - Main application shell container
 *
 * Contains:
 * - Application header
 * - Tab navigation
 * - Content area (StackLayout with tabs)
 */
ColumnLayout {
    id: root
    anchors.fill: parent
    spacing: theme.spacingSection

    // View state
    property int currentTabIndex: 0
    property bool compactLayout: width < theme.breakpointCompact
    property bool narrowLayout: width < theme.breakpointNarrow

    // Navigation properties
    property int shellNavHeight: 34
    property int shellNavWidthMax: 920
    property int shellNavWidthMin: 520
    property int shellNavWidthMinActive: narrowLayout ? 320 : shellNavWidthMin
    property int shellNavAvailableWidth: Math.max(300, root.width - (theme.spacingPage * 2))

    // Header state
    property bool meterView: currentTabIndex === 0
    property bool scannerView: currentTabIndex === 1
    property bool marketView: currentTabIndex === 2

    property string meterMode: ""
    property string meterZone: ""
    property string meterTimeText: ""
    property string meterFameText: ""
    property string meterFamePerHourText: ""

    property string scannerStatusText: ""
    property string scannerUpdateText: ""

    property string marketRegion: ""
    property int marketCraftPlanEnabledCount: 0
    property int marketCraftPlanCount: 0
    property int marketInputsTotalCost: 0
    property int marketNetProfitValue: 0

    property bool updateBannerVisible: false
    property string updateBannerText: ""
    property string updateBannerUrl: ""
    property bool updateAutoCheck: false
    property string updateCheckStatus: ""

    // Signals
    signal setUpdateAutoCheck(bool checked)
    signal requestManualUpdateCheck()
    signal dismissUpdateBanner()
    signal tabChanged(int index)

    // Access to theme
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary
    property color borderColor: theme.borderSubtle
    property color shellTabIdleBackground: theme.shellTabIdleBackground
    property color shellTabActiveText: theme.shellTabActiveText
    property int shellTabRadius: theme.shellTabRadius
    property string payPalLabel: narrowLayout ? "Pay" : "PayPal"
    property string coffeeLabel: narrowLayout ? "Coffee" : "Buy me a coffee"
    property string autoUpdateLabel: narrowLayout ? "Auto" : "Auto update"

    // Helper function
    property var formatInt: function(value) {
        var n = Number(value)
        if (!isFinite(n)) return "0"
        var whole = Math.round(n)
        var sign = whole < 0 ? "-" : ""
        var raw = Math.abs(whole).toString()
        return sign + raw.replace(/\B(?=(\d{3})+(?!\d))/g, " ")
    }

    // Application Header
    AppHeader {
        id: shellHeader
        Layout.fillWidth: true
        headerHeight: theme.shellHeaderHeight
        headerMargin: narrowLayout ? 8 : 12
        zoneSpacing: narrowLayout ? 10 : 20
        meterView: root.meterView
        scannerView: root.scannerView
        marketView: root.marketView
        compactLayout: root.compactLayout
        narrowLayout: root.narrowLayout
        meterMetaWidth: theme.shellMeterMetaWidth
        rightZoneSpacing: theme.shellRightZoneSpacing
        meterMode: root.meterMode
        meterZone: root.meterZone
        meterTimeText: root.meterTimeText
        meterFameText: root.meterFameText
        meterFamePerHourText: root.meterFamePerHourText
        scannerStatusText: root.scannerStatusText
        scannerUpdateText: root.scannerUpdateText
        marketRegion: root.marketRegion
        marketCraftPlanEnabledCount: root.marketCraftPlanEnabledCount
        marketCraftPlanCount: root.marketCraftPlanCount
        marketInputsTotalCost: root.marketInputsTotalCost
        marketNetProfitValue: root.marketNetProfitValue
        updateBannerVisible: root.updateBannerVisible
        updateBannerText: root.updateBannerText
        updateBannerUrl: root.updateBannerUrl
        updateAutoCheck: root.updateAutoCheck
        updateCheckStatus: root.updateCheckStatus
        autoUpdateLabel: root.autoUpdateLabel
        payPalLabel: root.payPalLabel
        coffeeLabel: root.coffeeLabel
        theme: root.theme
        textColor: root.textColor
        mutedColor: root.mutedColor
        formatInt: root.formatInt
        onSetUpdateAutoCheck: function(checked) { root.setUpdateAutoCheck(checked) }
        onRequestManualUpdateCheck: root.requestManualUpdateCheck()
        onDismissUpdateBanner: root.dismissUpdateBanner()
    }

    // Tab Navigation
    RowLayout {
        Layout.fillWidth: true
        spacing: theme.spacingCompact

        Item { Layout.fillWidth: true }

        TabBar {
            id: viewTabs
            Layout.preferredWidth: Math.min(shellNavWidthMax, Math.max(shellNavWidthMinActive, shellNavAvailableWidth))
            Layout.maximumWidth: Math.min(shellNavWidthMax, shellNavAvailableWidth)
            Layout.minimumWidth: Math.min(shellNavWidthMinActive, shellNavAvailableWidth)
            implicitHeight: shellNavHeight
            padding: 0
            spacing: theme.spacingCompact
            background: Rectangle {
                color: "transparent"
                border.width: 0
            }

            ShellTabButton {
                id: meterTab
                text: "Meter"
                activeColor: accentColor
                inactiveColor: shellTabIdleBackground
                activeTextColor: shellTabActiveText
                inactiveTextColor: textColor
                borderColor: borderColor
                cornerRadius: shellTabRadius
                labelPixelSize: 13
            }
            ShellTabButton {
                id: scannerTab
                text: "Scanner"
                activeColor: accentColor
                inactiveColor: shellTabIdleBackground
                activeTextColor: shellTabActiveText
                inactiveTextColor: textColor
                borderColor: borderColor
                cornerRadius: shellTabRadius
                labelPixelSize: 13
            }
            ShellTabButton {
                id: marketTab
                text: "Market"
                activeColor: accentColor
                inactiveColor: shellTabIdleBackground
                activeTextColor: shellTabActiveText
                inactiveTextColor: textColor
                borderColor: borderColor
                cornerRadius: shellTabRadius
                labelPixelSize: 13
            }

            onCurrentIndexChanged: {
                root.tabChanged(currentIndex)
            }
        }
    }

    // Content Area (StackLayout - to be filled by parent)
    Item {
        id: contentArea
        Layout.fillWidth: true
        Layout.fillHeight: true

        // Default content placeholder
        // Parent should add actual content here
    }

    // Expose currentIndex for parent binding
    property alias tabBarCurrentIndex: viewTabs.currentIndex
}
