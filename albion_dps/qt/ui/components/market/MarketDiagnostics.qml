import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme, AppButton, TableSurface access

/**
 * MarketDiagnostics - Diagnostics panel for market operations
 *
 * Displays:
 * - Diagnostic messages from market operations
 * - Clear button to reset diagnostics
 */
TableSurface {
    id: root
    level: 1
    Layout.fillWidth: true
    Layout.preferredHeight: 110
    Layout.minimumHeight: 82
    Layout.maximumHeight: 140
    clip: true

    // Properties
    property string diagnosticsText: ""

    // Signals
    signal clearDiagnostics()

    // Access to theme
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 4

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "Market diagnostics"
                color: textColor
                font.pixelSize: 11
                font.bold: true
            }
            Item { Layout.fillWidth: true }
            AppButton {
                text: "Clear"
                implicitHeight: 20
                font.pixelSize: 10
                onClicked: root.clearDiagnostics()
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            TextArea {
                text: root.diagnosticsText
                readOnly: true
                wrapMode: Text.NoWrap
                color: mutedColor
                font.family: "Consolas"
                font.pixelSize: 10
                selectByMouse: true
                background: Rectangle { color: "transparent" }
            }
        }
    }
}
