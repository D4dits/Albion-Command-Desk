import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for CardPanel access

/**
 * ScannerTab - Main scanner tab container
 *
 * Contains the complete scanner view with:
 * - Header with title and help button
 * - Status information
 * - Control buttons
 * - Log output area
 *
 * Signals:
 * - checkForUpdates(): Fired when user clicks Check updates
 * - syncClientRepo(): Fired when user clicks Sync repo
 * - startScanner(): Fired when user clicks Start scanner
 * - startScannerSudo(): Fired when user clicks Start scanner (sudo)
 * - stopScanner(): Fired when user clicks Stop scanner
 * - clearLog(): Fired when user clicks Clear log
 * - refreshCaptureRuntimeStatus(): Fired when user refreshes runtime diagnostics
 * - openCaptureRuntimeAction(): Fired when user clicks runtime action button
 */
CardPanel {
    id: root
    level: 1
    anchors.fill: parent

    // Scanner state properties (bound to parent's scannerState)
    property string statusText: ""
    property string updateText: ""
    property string clientDir: ""
    property bool scannerRunning: false
    property string logText: ""
    property string captureRuntimeState: "unknown"
    property string captureRuntimeDetail: ""
    property string captureRuntimeActionLabel: ""
    property string captureRuntimeActionUrl: ""

    // Signals to notify parent of actions
    signal checkForUpdates()
    signal syncClientRepo()
    signal startScanner()
    signal startScannerSudo()
    signal stopScanner()
    signal clearLog()
    signal refreshCaptureRuntimeStatus()
    signal openCaptureRuntimeAction()

    // Access to theme (injected by parent)
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        // Header with title and help button
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Text {
                text: "AlbionData Scanner"
                color: textColor
                font.pixelSize: 14
                font.bold: true
            }
            ToolButton {
                text: "?"
                hoverEnabled: true
                implicitWidth: 24
                implicitHeight: 24
                font.pixelSize: 13
                background: Rectangle {
                    radius: 12
                    color: accentColor
                    border.color: "#79c0ff"
                }
                contentItem: Text {
                    text: "?"
                    color: "#081018"
                    font.pixelSize: 13
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                ToolTip.visible: hovered
                ToolTip.text: "Albion Data uploader control.\nUse it to check/sync client repo, start or stop scanner,\nand monitor detailed runtime logs."
            }
            Item { Layout.fillWidth: true }
        }

        // Status information
        Text {
            text: "Status: " + root.statusText + "  |  Updates: " + root.updateText
            color: mutedColor
            font.pixelSize: 11
        }
        Text {
            text: "Local repo: " + root.clientDir
            color: mutedColor
            font.pixelSize: 11
            elide: Text.ElideRight
            Layout.fillWidth: true
        }

        Text {
            text: "Scanner uses fixed runtime defaults (upload enabled, official public ingest endpoint)."
            color: mutedColor
            font.pixelSize: 11
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                Layout.fillWidth: true
                text: "Capture runtime: " + root.captureRuntimeState + " | " + root.captureRuntimeDetail
                color: root.captureRuntimeState === "available"
                    ? (theme ? theme.stateSuccess : "#2ecc71")
                    : (root.captureRuntimeState === "missing"
                        ? (theme ? theme.stateWarning : "#f39c12")
                        : (theme ? theme.stateDanger : "#e74c3c"))
                font.pixelSize: 11
                wrapMode: Text.Wrap
            }

            AppButton {
                visible: root.captureRuntimeActionLabel.length > 0
                text: root.captureRuntimeActionLabel
                compact: true
                onClicked: root.openCaptureRuntimeAction()
            }

            AppButton {
                text: "Refresh runtime"
                compact: true
                onClicked: root.refreshCaptureRuntimeStatus()
            }
        }

        Text {
            visible: Qt.platform.os === "windows"
            text: "Live mode requires Npcap Runtime (Npcap installer). Npcap SDK is only needed for optional capture-profile builds."
            color: mutedColor
            font.pixelSize: 11
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }

        // Control buttons
        ScannerControls {
            id: scannerControls
            Layout.fillWidth: true
            scannerRunning: root.scannerRunning

            onCheckForUpdates: root.checkForUpdates()
            onSyncClientRepo: root.syncClientRepo()
            onStartScanner: root.startScanner()
            onStartScannerSudo: root.startScannerSudo()
            onStopScanner: root.stopScanner()
            onClearLog: root.clearLog()
        }

        // Log output area
        ScannerLogView {
            id: scannerLogView
            Layout.fillWidth: true
            Layout.fillHeight: true
            theme: root.theme
            textColor: root.textColor
            logText: root.logText
        }
    }
}
