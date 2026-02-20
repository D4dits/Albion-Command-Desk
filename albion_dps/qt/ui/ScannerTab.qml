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
    property bool captureRuntimeNeedsAction: false
    property string captureRuntimeInstallHint: ""
    property bool gitAvailable: false
    property string gitDetail: ""
    property string gitActionLabel: ""
    property string gitActionUrl: ""
    property bool gitNeedsInstall: false
    property string gitInstallHint: ""

    // Signals to notify parent of actions
    signal checkForUpdates()
    signal syncClientRepo()
    signal startScanner()
    signal startScannerSudo()
    signal stopScanner()
    signal clearLog()
    signal refreshCaptureRuntimeStatus()
    signal openCaptureRuntimeAction()
    signal refreshGitStatus()
    signal openGitInstallAction()

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

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: runtimeColumn.implicitHeight + 12
                radius: 6
                color: root.captureRuntimeState === "available"
                    ? (theme ? theme.stateSuccessBg : "#11261b")
                    : (theme ? theme.stateWarningBg : "#2a220f")
                border.width: 1
                border.color: root.captureRuntimeState === "available"
                    ? (theme ? theme.stateSuccess : "#2ecc71")
                    : (theme ? theme.stateWarning : "#f39c12")

                ColumnLayout {
                    id: runtimeColumn
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 4

                    Text {
                        text: root.captureRuntimeState === "available" ? "Capture runtime: ready" : "Capture runtime: action required"
                        color: root.captureRuntimeState === "available"
                            ? (theme ? theme.stateSuccess : "#2ecc71")
                            : (theme ? theme.stateWarning : "#f39c12")
                        font.pixelSize: 11
                        font.bold: true
                    }
                    Text {
                        text: root.captureRuntimeDetail
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: root.captureRuntimeInstallHint.length > 0
                        text: root.captureRuntimeInstallHint
                        color: textColor
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        AppButton {
                            visible: root.captureRuntimeActionLabel.length > 0
                            text: root.captureRuntimeActionLabel
                            variant: root.captureRuntimeNeedsAction ? "primary" : "secondary"
                            compact: true
                            onClicked: root.openCaptureRuntimeAction()
                        }
                        AppButton {
                            text: "Refresh runtime"
                            compact: true
                            onClicked: root.refreshCaptureRuntimeStatus()
                        }
                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: gitColumn.implicitHeight + 12
                radius: 6
                color: root.gitAvailable
                    ? (theme ? theme.stateSuccessBg : "#11261b")
                    : (theme ? theme.stateWarningBg : "#2a220f")
                border.width: 1
                border.color: root.gitAvailable
                    ? (theme ? theme.stateSuccess : "#2ecc71")
                    : (theme ? theme.stateWarning : "#f39c12")

                ColumnLayout {
                    id: gitColumn
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 4

                    Text {
                        text: root.gitAvailable ? "Git: ready" : "Git: missing"
                        color: root.gitAvailable
                            ? (theme ? theme.stateSuccess : "#2ecc71")
                            : (theme ? theme.stateWarning : "#f39c12")
                        font.pixelSize: 11
                        font.bold: true
                    }
                    Text {
                        text: root.gitDetail
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: root.gitInstallHint.length > 0
                        text: root.gitInstallHint
                        color: textColor
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        Layout.fillWidth: true
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        AppButton {
                            visible: root.gitActionLabel.length > 0
                            text: root.gitActionLabel
                            variant: root.gitNeedsInstall ? "primary" : "secondary"
                            compact: true
                            onClicked: root.openGitInstallAction()
                        }
                        AppButton {
                            text: "Refresh Git"
                            compact: true
                            onClicked: root.refreshGitStatus()
                        }
                        Item { Layout.fillWidth: true }
                    }
                }
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
            gitAvailable: root.gitAvailable

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
