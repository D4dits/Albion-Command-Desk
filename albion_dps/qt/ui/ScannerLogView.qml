import QtQuick 2.15
import QtQuick.Controls 2.15
import "." // for TableSurface access

/**
 * ScannerLogView - Log output area for scanner diagnostics
 *
 * Displays:
 * - Scrollable text area with scanner logs
 * - Auto-scroll to latest log entry
 * - Empty state message when no logs
 */
TableSurface {
    id: root
    level: 1
    Layout.fillWidth: true
    Layout.fillHeight: true
    clip: true

    // Properties to bind to parent state
    property string logText: ""

    // Access to theme (injected by parent)
    property var theme: Theme {}
    property color textColor: theme.textPrimary

    ScrollView {
        id: scannerLogView
        anchors.fill: parent
        anchors.margins: 8
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        TextArea {
            id: scannerLogArea
            text: root.logText
            readOnly: true
            wrapMode: Text.NoWrap
            color: root.textColor
            font.family: "Consolas"
            font.pixelSize: 11
            selectByMouse: true

            function followTail() {
                cursorPosition = length
                if (scannerLogView.contentItem
                        && scannerLogView.contentItem.contentHeight !== undefined
                        && scannerLogView.contentItem.height !== undefined) {
                    scannerLogView.contentItem.contentY = Math.max(
                        0,
                        scannerLogView.contentItem.contentHeight - scannerLogView.contentItem.height
                    )
                }
            }

            onTextChanged: Qt.callLater(followTail)
            Component.onCompleted: Qt.callLater(followTail)
        }
    }

    // Empty state message
    Text {
        anchors.centerIn: parent
        visible: root.logText.length === 0
        text: "Scanner log is empty. Run a scanner action to see diagnostics."
        color: root.theme.textSecondary
        font.pixelSize: 11
    }
}
