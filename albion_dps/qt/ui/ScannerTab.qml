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
 * - exportDiagnosticsBundle(): Fired when user exports support bundle
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
    property string captureRuntimeInstallCommand: ""
    property bool gitAvailable: false
    property string gitDetail: ""
    property string gitActionLabel: ""
    property string gitActionUrl: ""
    property bool gitNeedsInstall: false
    property string gitInstallHint: ""
    property string gitInstallCommand: ""

    // Signals to notify parent of actions
    signal checkForUpdates()
    signal syncClientRepo()
    signal startScanner()
    signal startScannerSudo()
    signal stopScanner()
    signal clearLog()
    signal exportDiagnosticsBundle()
    signal refreshCaptureRuntimeStatus()
    signal openCaptureRuntimeAction()
    signal refreshGitStatus()
    signal openGitInstallAction()
    signal copyCommand(string commandText)
    signal openStartTab()

    // Access to theme (injected by parent)
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary
    property int brandTileWidth: 194

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 84

            Column {
                anchors.left: parent.left
                anchors.right: scannerBrandTile.left
                anchors.rightMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                spacing: 4

                Row {
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
                }

                Text {
                    width: parent.width
                    text: "Repo sync, update checks, and scanner runtime controls. Dependency setup stays on Start and Settings."
                    color: mutedColor
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }

            TableSurface {
                id: scannerBrandTile
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: root.brandTileWidth
                height: 84
                level: 1

                Row {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    Image {
                        source: "command_desk_icon.png"
                        sourceSize.width: 40
                        sourceSize.height: 40
                        fillMode: Image.PreserveAspectFit
                        width: 40
                        height: 40
                    }

                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.width - 60
                        spacing: 2

                        Text { text: "Command Desk"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Scanner control"; color: root.mutedColor; font.pixelSize: 10 }
                    }
                }
            }
        }

        TableSurface {
            Layout.fillWidth: true
            Layout.preferredHeight: 104
            level: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 6

                Text {
                    Layout.fillWidth: true
                    text: "Status: " + root.statusText + "  |  Updates: " + root.updateText
                    color: textColor
                    font.pixelSize: 11
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
                Text {
                    Layout.fillWidth: true
                    text: "Local repo: " + root.clientDir
                    color: mutedColor
                    font.pixelSize: 11
                    elide: Text.ElideMiddle
                }
                Text {
                    Layout.fillWidth: true
                    text: "Runtime: " + root.captureRuntimeState + "  |  Git: " + (root.gitAvailable ? "available" : "missing") + "  |  Scanner uses the official public ingest endpoint."
                    color: mutedColor
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    Item { Layout.fillWidth: true }
                    AppButton {
                        text: "Open Start"
                        compact: true
                        variant: "primary"
                        onClicked: root.openStartTab()
                    }
                }
            }
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

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                Layout.fillWidth: true
                text: "Need support data? Export one diagnostics bundle with scanner log, app status, and market diagnostics."
                color: mutedColor
                font.pixelSize: 11
                wrapMode: Text.Wrap
            }
            AppButton {
                text: "Export diagnostics"
                compact: true
                onClicked: root.exportDiagnosticsBundle()
            }
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
