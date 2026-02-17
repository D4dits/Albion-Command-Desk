import QtQuick 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, AppButton, AppComboBox, AppCheckBox access

/**
 * AppHeader - Top application header bar
 *
 * Contains:
 * - Left zone: Title and contextual status
 * - Right zone: Meter meta, Update banner, Update controls, Support buttons
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
    property bool meterView: false
    property bool scannerView: false
    property bool marketView: false
    property bool compactLayout: false
    property bool narrowLayout: false

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
    property string marketRegion: ""
    property int marketCraftPlanEnabledCount: 0
    property int marketCraftPlanCount: 0
    property int marketInputsTotalCost: 0
    property int marketNetProfitValue: 0

    // Update banner state
    property bool updateBannerVisible: false
    property string updateBannerText: ""
    property string updateBannerUrl: ""

    // Update controls state
    property bool updateAutoCheck: false
    property string updateCheckStatus: ""
    property string autoUpdateLabel: "Auto update"

    // Support buttons state
    property string payPalLabel: "PayPal"
    property string coffeeLabel: "Buy me a coffee"

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
                text: root.meterView
                    ? "Mode: " + root.meterMode + "  |  Zone: " + root.meterZone
                    : (root.scannerView
                        ? "Scanner status: " + root.scannerStatusText + "  |  Updates: " + root.scannerUpdateText
                        : "Market setup  |  Region: " + root.marketRegion
                          + "  |  Crafts: " + root.marketCraftPlanEnabledCount + "/" + root.marketCraftPlanCount
                          + "  |  Inputs: " + formatInt(root.marketInputsTotalCost)
                          + "  |  Net: " + formatInt(root.marketNetProfitValue))
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
                visible: !root.narrowLayout
                bannerVisible: root.updateBannerVisible
                bannerText: root.updateBannerText
                bannerUrl: root.updateBannerUrl
                minWidth: root.narrowLayout ? 180 : 270
                maxWidth: root.narrowLayout ? 280 : 420
                bannerHeight: theme.shellActionHeight + 4
                availableWidth: root.width
                theme: root.theme
                onDismissBanner: root.dismissUpdateBanner()
            }

            // Update Controls Zone
            ColumnLayout {
                id: shellUpdateZone
                Layout.preferredWidth: implicitWidth
                Layout.minimumWidth: implicitWidth
                spacing: 2

                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    spacing: 6
                    AppCheckBox {
                        id: autoUpdateCheckBox
                        implicitHeight: theme.shellActionHeight
                        checked: root.updateAutoCheck
                        text: root.autoUpdateLabel
                        onToggled: root.setUpdateAutoCheck(checked)
                    }
                    AppButton {
                        id: checkUpdatesButton
                        text: "Check now"
                        variant: "primary"
                        compact: true
                        implicitHeight: theme.shellActionHeight
                        implicitWidth: root.narrowLayout ? 78 : 88
                        onClicked: root.requestManualUpdateCheck()
                    }
                }
                Text {
                    Layout.fillWidth: true
                    visible: root.updateCheckStatus.length > 0
                    text: root.updateCheckStatus
                    color: mutedColor
                    font.pixelSize: 10
                    horizontalAlignment: Text.AlignRight
                    elide: Text.ElideRight
                    wrapMode: Text.NoWrap
                }
            }

            // Support Buttons Zone
            SupportButtons {
                id: shellSupportZone
                spacingOverride: root.narrowLayout ? 6 : 8
                payPalLabel: root.payPalLabel
                coffeeLabel: root.coffeeLabel
                payPalWidth: root.narrowLayout ? 90 : 118
                coffeeWidth: root.narrowLayout ? 98 : 146
                buttonHeight: theme.shellActionHeight
                theme: root.theme
            }
        }
    }
}
