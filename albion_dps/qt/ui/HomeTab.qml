import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for AppButton, AppCheckBox, CardPanel, TableSurface

/**
 * HomeTab - Start tab with quick status and actions
 */
CardPanel {
    id: root
    level: 1
    anchors.fill: parent

    // App state
    property string scannerStatusText: ""
    property string scannerUpdateText: ""
    property string updateCheckStatus: ""
    property bool updateAutoCheck: false

    property string captureRuntimeState: "unknown"
    property string captureRuntimeDetail: ""
    property string captureRuntimeActionLabel: ""
    property string captureRuntimeInstallHint: ""
    property string captureRuntimeInstallCommand: ""

    property bool gitAvailable: false
    property string gitDetail: ""
    property string gitActionLabel: ""
    property string gitInstallHint: ""
    property string gitInstallCommand: ""

    property bool compactLayout: false
    property bool twoColumn: width >= 900

    // Theme
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    // Signals
    signal goToMeter()
    signal goToScanner()
    signal goToMarket()
    signal refreshCaptureRuntimeStatus()
    signal openCaptureRuntimeAction()
    signal refreshGitStatus()
    signal openGitInstallAction()
    signal copyCommand(string commandText)
    signal requestManualUpdateCheck()
    signal setUpdateAutoCheck(bool checked)

    function runtimeStateColor() {
        if (captureRuntimeState === "available") {
            return theme.stateSuccess
        }
        if (captureRuntimeState === "missing") {
            return theme.stateWarning
        }
        return theme.stateDanger
    }

    function runtimeStateLabel() {
        return captureRuntimeState === "available" ? "ready" : "action required"
    }

    function gitStateColor() {
        return gitAvailable ? theme.stateSuccess : theme.stateWarning
    }

    function gitStateLabel() {
        return gitAvailable ? "ready" : "missing"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Text {
            text: "Start"
            color: textColor
            font.pixelSize: 14
            font.bold: true
        }
        Text {
            Layout.fillWidth: true
            text: "Quick setup and health checks. Use this tab first before running live scanner actions."
            color: mutedColor
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.twoColumn ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10

            TableSurface {
                Layout.fillWidth: true
                Layout.fillHeight: true
                level: 1
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    Text {
                        text: "Capture runtime"
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Text {
                        text: "Status: " + root.runtimeStateLabel()
                        color: root.runtimeStateColor()
                        font.pixelSize: 11
                        font.bold: true
                    }
                    Text {
                        text: root.captureRuntimeDetail
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: root.captureRuntimeInstallHint.length > 0
                        text: root.captureRuntimeInstallHint
                        color: textColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        AppButton {
                            visible: root.captureRuntimeActionLabel.length > 0
                            text: root.captureRuntimeActionLabel
                            variant: "primary"
                            compact: true
                            onClicked: root.openCaptureRuntimeAction()
                        }
                        AppButton {
                            visible: root.captureRuntimeInstallCommand.length > 0
                            text: "Copy command"
                            compact: true
                            onClicked: root.copyCommand(root.captureRuntimeInstallCommand)
                        }
                        AppButton {
                            text: "Refresh"
                            compact: true
                            onClicked: root.refreshCaptureRuntimeStatus()
                        }
                        Item { Layout.fillWidth: true }
                    }
                }
            }

            TableSurface {
                Layout.fillWidth: true
                Layout.fillHeight: true
                level: 1
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    Text {
                        text: "Git dependency"
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Text {
                        text: "Status: " + root.gitStateLabel()
                        color: root.gitStateColor()
                        font.pixelSize: 11
                        font.bold: true
                    }
                    Text {
                        text: root.gitDetail
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: root.gitInstallHint.length > 0
                        text: root.gitInstallHint
                        color: textColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        AppButton {
                            visible: root.gitActionLabel.length > 0
                            text: root.gitActionLabel
                            variant: "primary"
                            compact: true
                            onClicked: root.openGitInstallAction()
                        }
                        AppButton {
                            visible: root.gitInstallCommand.length > 0
                            text: "Copy command"
                            compact: true
                            onClicked: root.copyCommand(root.gitInstallCommand)
                        }
                        AppButton {
                            text: "Refresh"
                            compact: true
                            onClicked: root.refreshGitStatus()
                        }
                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }

        TableSurface {
            Layout.fillWidth: true
            level: 1
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: "Quick actions"
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                    AppCheckBox {
                        text: compactLayout ? "Auto" : "Auto update"
                        checked: root.updateAutoCheck
                        onToggled: root.setUpdateAutoCheck(checked)
                    }
                    AppButton {
                        text: "Check updates"
                        compact: true
                        onClicked: root.requestManualUpdateCheck()
                    }
                }

                Text {
                    text: "Scanner: " + root.scannerStatusText + "  |  Repo updates: " + root.scannerUpdateText
                    color: mutedColor
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
                Text {
                    visible: root.updateCheckStatus.length > 0
                    text: "App update: " + root.updateCheckStatus
                    color: mutedColor
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    AppButton {
                        text: "Open Meter"
                        variant: "primary"
                        compact: true
                        onClicked: root.goToMeter()
                    }
                    AppButton {
                        text: "Open Scanner"
                        compact: true
                        onClicked: root.goToScanner()
                    }
                    AppButton {
                        text: "Open Market"
                        compact: true
                        onClicked: root.goToMarket()
                    }
                    Item { Layout.fillWidth: true }
                }
            }
        }
    }
}
