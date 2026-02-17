import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme, AppButton, AppComboBox, AppCheckBox access
import "../common" as CommonComponents

/**
 * MarketStatusBar - Status and control bar for market operations
 *
 * Displays:
 * - Status line with validation and pricing info
 * - Region selection
 * - Premium toggle
 * - Refresh prices button
 * - Show/hide details buttons
 */
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 6

    // State properties
    property bool priceFetchInProgress: false
    property string validationText: ""
    property string pricesSource: ""
    property string listActionText: ""
    property string region: "europe"
    property bool premium: false
    property string refreshPricesButtonText: "Refresh prices"
    property bool canRefreshPrices: true
    property bool statusExpanded: false
    property bool diagnosticsVisible: false
    property string pricesStatusText: ""

    // Helper functions (injected by parent)
    property var priceSourceColor: function(source) { return root.theme.stateSuccess }
    property var validationColor: function(isValid) { return root.theme.stateSuccess }

    // Signals
    signal setRegion(string region)
    signal setPremium(bool premium)
    signal refreshPrices()
    signal toggleStatusExpanded()
    signal toggleDiagnosticsVisible()

    // Access to theme
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    // Main status line
    Text {
        Layout.fillWidth: true
        text: (root.priceFetchInProgress ? "[loading] " : "")
            + "Status: "
            + (root.validationText.length === 0 ? "ok" : "invalid")
            + "  |  Prices: " + root.pricesSource
            + (root.listActionText.length > 0 ? "  |  " + root.listActionText : "")
        color: root.validationText.length === 0
            ? root.priceSourceColor(root.pricesSource)
            : root.validationColor(false)
        font.pixelSize: 11
        elide: Text.ElideRight
    }

    // Control row
    Flow {
        Layout.fillWidth: true
        spacing: 8

        Text {
            text: "Region"
            color: mutedColor
            font.pixelSize: 11
        }
        AppComboBox {
            implicitWidth: 110
            implicitHeight: 24
            font.pixelSize: 11
            model: ["europe", "west", "east"]
            currentIndex: Math.max(0, model.indexOf(root.region))
            onActivated: root.setRegion(currentText)
        }

        AppCheckBox {
            id: premiumCheck
            implicitHeight: 24
            checked: root.premium
            text: "Premium"
            palette.windowText: textColor
            palette.text: textColor
            onToggled: root.setPremium(checked)
        }

        AppButton {
            text: root.refreshPricesButtonText
            compact: true
            implicitHeight: 24
            enabled: root.canRefreshPrices && !root.priceFetchInProgress
            onClicked: root.refreshPrices()
        }

        // Loading spinner for price fetch
        CommonComponents.Spinner {
            size: "xs"
            active: root.priceFetchInProgress
            Layout.alignment: Qt.AlignVCenter
        }
        AppButton {
            text: root.statusExpanded ? "Hide details" : "Show details"
            compact: true
            implicitHeight: 24
            onClicked: root.toggleStatusExpanded()
        }
        AppButton {
            text: root.diagnosticsVisible ? "Hide diagnostics" : "Show diagnostics"
            compact: true
            implicitHeight: 24
            onClicked: root.toggleDiagnosticsVisible()
        }
    }

    // Expanded details (conditionally visible)
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4
        visible: root.statusExpanded

        Text {
            Layout.fillWidth: true
            text: root.validationText.length === 0
                ? "Configuration valid."
                : "Validation: " + root.validationText
            color: root.validationColor(root.validationText.length === 0)
            font.pixelSize: 11
            elide: Text.ElideRight
        }

        Text {
            Layout.fillWidth: true
            text: "Prices details: " + root.pricesStatusText
            color: root.priceSourceColor(root.pricesSource)
            font.pixelSize: 11
            elide: Text.ElideRight
        }
    }
}
