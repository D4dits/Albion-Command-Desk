import QtQuick 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, AppButton, AppComboBox, AppCheckBox access

/**
 * AppHeader - Top application header bar
 *
 * Contains:
 * - Left zone: Title and contextual status
 * - Right zone: Meter meta, Update banner, Support buttons
 */
Rectangle {
    id: root
    Layout.fillWidth: true
    height: headerHeight
    color: theme.cardLevel1
    radius: theme.cornerRadiusPanel
    border.color: theme.borderStrong

    // Layout properties
    property int headerHeight: 72
    property int headerMargin: 12
    property int zoneSpacing: 20

    // View state
    property bool homeView: false
    property bool meterView: false
    property bool scannerView: false
    property bool marketView: false
    property bool flipperView: false
    property bool lootView: false
    property bool settingsView: false
    property bool helpView: false
    property bool compactLayout: false
    property bool narrowLayout: false
    property bool veryNarrowLayout: width < 1040
    property bool compactActionsLayout: width < 1320

    // Right zone widths
    property int meterMetaWidth: 180
    property int rightZoneSpacing: 8

    // Contextual status
    property string meterMode: ""
    property string meterZone: ""
    property string meterTimeText: ""
    property string meterFameText: ""
    property string meterFamePerHourText: ""
    property string scannerStatusText: ""
    property string scannerUpdateText: ""
    property string captureRuntimeState: ""
    property bool gitAvailable: false
    property string marketRegion: ""
    property int marketCraftPlanEnabledCount: 0
    property int marketCraftPlanCount: 0
    property int marketInputsTotalCost: 0
    property int marketNetProfitValue: 0
    property int flipperValidCount: 0
    property int flipperSelectedProfit: 0
    property string flipperSourceCity: ""
    property int lootEventCount: 0
    property string lootLatestSummary: ""

    // Update banner state
    property bool updateBannerVisible: false
    property string updateBannerText: ""
    property string updateBannerUrl: ""
    property string updateBannerNotesUrl: ""

    // Update controls state
    property bool updateAutoCheck: false
    property string updateCheckStatus: ""
    property string autoUpdateLabel: "Auto update"

    // Support buttons state
    property string payPalLabel: "PayPal"
    property string coffeeLabel: "Buy me a coffee"
    property int supportPayPalWidth: 118
    property int supportCoffeeWidth: 166

    // Signals
    signal setUpdateAutoCheck(bool checked)
    signal requestManualUpdateCheck()
    signal dismissUpdateBanner()

    // Helper functions
    property var formatInt: function(value) {
        var n = Number(value)
        if (!isFinite(n)) return "0"
        var whole = Math.round(n)
        var sign = whole < 0 ? "-" : ""
        var raw = Math.abs(whole).toString()
        return sign + raw.replace(/\B(?=(\d{3})+(?!\d))/g, " ")
    }

    function contextStatusText() {
        var base = ""
        if (root.meterView) {
            base = "Mode: " + root.meterMode + "  |  Zone: " + root.meterZone
        } else if (root.homeView) {
            base = "Start  |  Capture runtime: " + root.captureRuntimeState + "  |  Git: "
                + (root.gitAvailable ? "ready" : "missing")
        } else if (root.scannerView) {
            base = "Scanner status: " + root.scannerStatusText + "  |  Updates: " + root.scannerUpdateText
        } else if (root.flipperView) {
            base = "Market Flipper  |  Buy: " + root.flipperSourceCity
                + "  |  Flips: " + root.flipperValidCount
                + "  |  Checked profit: " + formatInt(root.flipperSelectedProfit)
        } else if (root.lootView) {
            base = "Loot log  |  Events: " + root.lootEventCount + "  |  Latest: "
                + (root.lootLatestSummary.length > 0 ? root.lootLatestSummary : "waiting for loot")
        } else if (root.settingsView) {
            base = "Settings  |  Runtime: " + root.captureRuntimeState + "  |  Git: "
                + (root.gitAvailable ? "ready" : "missing")
        } else if (root.helpView) {
            base = "Help  |  Releases, troubleshooting, and diagnostics"
        } else {
            base = "Market setup  |  Region: " + root.marketRegion
                + "  |  Crafts: " + root.marketCraftPlanEnabledCount + "/" + root.marketCraftPlanCount
                + "  |  Inputs: " + formatInt(root.marketInputsTotalCost)
                + "  |  Net: " + formatInt(root.marketNetProfitValue)
        }
        if (root.updateBannerVisible && root.narrowLayout && root.updateBannerText.length > 0) {
            return base + "  |  " + root.updateBannerText
        }
        return base
    }

    // Access to theme
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    RowLayout {
        id: shellHeaderLayout
        anchors.fill: parent
        anchors.margins: root.headerMargin
        spacing: root.zoneSpacing

        // Left zone: Title + Contextual Status
        ColumnLayout {
            id: shellLeftZone
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 4

            Text {
                text: "Albion Command Desk"
                color: textColor
                font.pixelSize: 20
                font.bold: true
            }
            Text {
                Layout.fillWidth: true
                text: root.contextStatusText()
                color: mutedColor
                font.pixelSize: 12
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
            }
        }

        // Right zone: Meter Meta + Update Banner + Update Controls + Support Buttons
        RowLayout {
            id: shellRightZone
            Layout.fillWidth: false
            Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
            Layout.minimumWidth: implicitWidth
            spacing: root.narrowLayout ? 6 : root.rightZoneSpacing

            // Meter Meta Zone (time and fame)
            ColumnLayout {
                id: shellMeterZone
                Layout.preferredWidth: (root.meterView && !root.compactLayout) ? root.meterMetaWidth : 0
                Layout.minimumWidth: Layout.preferredWidth
                Layout.maximumWidth: Layout.preferredWidth
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                visible: Layout.preferredWidth > 0
                opacity: visible ? 1.0 : 0.0
                enabled: visible
                spacing: 4

                Text {
                    text: root.meterTimeText
                    color: textColor
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignRight
                }
                Text {
                    text: "Fame: " + root.meterFameText + "  |  Fame/h: " + root.meterFamePerHourText
                    color: mutedColor
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignRight
                }
            }

            // Update Banner
            UpdateBanner {
                id: shellUpdateBanner
                visible: root.updateBannerVisible && !root.veryNarrowLayout
                bannerVisible: root.updateBannerVisible
                bannerText: root.updateBannerText
                bannerUrl: root.updateBannerUrl
                bannerNotesUrl: root.updateBannerNotesUrl
                minWidth: root.compactActionsLayout ? 220 : 270
                maxWidth: root.compactActionsLayout ? 340 : 420
                bannerHeight: theme.shellActionHeight + 4
                availableWidth: Math.max(240, root.width - 740)
                theme: root.theme
                onDismissBanner: root.dismissUpdateBanner()
            }

            AppButton {
                visible: root.updateBannerVisible && root.veryNarrowLayout
                text: "Check update"
                compact: true
                onClicked: root.requestManualUpdateCheck()
            }

            // Support Buttons Zone
            SupportButtons {
                id: shellSupportZone
                spacingOverride: root.narrowLayout ? 6 : 8
                payPalLabel: root.payPalLabel
                coffeeLabel: root.compactActionsLayout ? "Buy Coffee" : root.coffeeLabel
                payPalWidth: root.supportPayPalWidth
                coffeeWidth: root.compactActionsLayout ? 124 : root.supportCoffeeWidth
                buttonHeight: theme.shellActionHeight
                theme: root.theme
            }
        }
    }
}
