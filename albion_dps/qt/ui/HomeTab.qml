import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for AppButton, AppCheckBox, CardPanel, TableSurface

/**
 * HomeTab - startup center with dependency checks and update controls
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

    property bool gameDataReady: false
    property string gameDataDetail: ""
    property string gameDataHint: ""
    property string gameDataActionLabel: "Select game folder"

    // Layout
    property bool compactLayout: false
    property int contentPadding: compactLayout ? 8 : 12
    property int contentSpacing: compactLayout ? 8 : 10
    property bool showBrandTile: width >= 1080
    property bool statusTwoColumn: width >= 900
    property bool dashboardTwoColumn: width >= 1040

    // Theme
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    // Signals
    signal refreshCaptureRuntimeStatus()
    signal openCaptureRuntimeAction()
    signal refreshGitStatus()
    signal openGitInstallAction()
    signal refreshGameDataStatus()
    signal setupGameData()
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

    function gameDataStateColor() {
        return gameDataReady ? theme.stateSuccess : theme.stateWarning
    }

    function gameDataStateLabel() {
        return gameDataReady ? "ready" : "missing"
    }

    ScrollView {
        id: contentScroll
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            id: contentLayout
            width: Math.max(contentScroll.availableWidth - (root.contentPadding * 2), 320)
            x: root.contentPadding
            y: root.contentPadding
            spacing: root.contentSpacing

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Text {
                        text: "Start"
                        color: textColor
                        font.pixelSize: 14
                        font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Startup checklist: verify dependencies here, then move to Scanner or Market. Settings holds paths and runtime controls."
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }

                TableSurface {
                    visible: root.showBrandTile
                    level: 1
                    Layout.preferredWidth: 194
                    Layout.minimumWidth: 194
                    Layout.preferredHeight: 84
                    Layout.minimumHeight: 84

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 10

                        Image {
                            source: "command_desk_icon.png"
                            sourceSize.width: 40
                            sourceSize.height: 40
                            fillMode: Image.PreserveAspectFit
                            Layout.preferredWidth: 40
                            Layout.preferredHeight: 40
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                text: "Command Desk"
                                color: textColor
                                font.pixelSize: 12
                                font.bold: true
                            }
                            Text {
                                text: "Startup center"
                                color: mutedColor
                                font.pixelSize: 10
                            }
                        }
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                columns: root.dashboardTwoColumn ? 2 : 1
                columnSpacing: 10
                rowSpacing: 10

                TableSurface {
                    Layout.fillWidth: true
                    level: 1
                    implicitHeight: 154

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Capture runtime"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: root.runtimeStateLabel(); color: root.runtimeStateColor(); font.pixelSize: 11; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: root.captureRuntimeInstallHint.length > 0 ? root.captureRuntimeInstallHint : root.captureRuntimeDetail
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { visible: root.captureRuntimeActionLabel.length > 0; text: root.captureRuntimeActionLabel; variant: "primary"; compact: true; onClicked: root.openCaptureRuntimeAction() }
                            AppButton { visible: root.captureRuntimeInstallCommand.length > 0; text: "Copy"; compact: true; onClicked: root.copyCommand(root.captureRuntimeInstallCommand) }
                            AppButton { text: "Refresh"; compact: true; onClicked: root.refreshCaptureRuntimeStatus() }
                        }
                    }
                }

                TableSurface {
                    Layout.fillWidth: true
                    level: 1
                    implicitHeight: 154

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Git dependency"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: root.gitStateLabel(); color: root.gitStateColor(); font.pixelSize: 11; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: root.gitInstallHint.length > 0 ? root.gitInstallHint : root.gitDetail
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { visible: root.gitActionLabel.length > 0; text: root.gitActionLabel; variant: "primary"; compact: true; onClicked: root.openGitInstallAction() }
                            AppButton { visible: root.gitInstallCommand.length > 0; text: "Copy"; compact: true; onClicked: root.copyCommand(root.gitInstallCommand) }
                            AppButton { text: "Refresh"; compact: true; onClicked: root.refreshGitStatus() }
                        }
                    }
                }

                TableSurface {
                    Layout.fillWidth: true
                    level: 1
                    implicitHeight: 154

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Game data"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: root.gameDataStateLabel(); color: root.gameDataStateColor(); font.pixelSize: 11; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: root.gameDataHint.length > 0 ? root.gameDataHint : root.gameDataDetail
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { text: root.gameDataActionLabel; variant: "primary"; compact: true; onClicked: root.setupGameData() }
                            AppButton { text: "Refresh"; compact: true; onClicked: root.refreshGameDataStatus() }
                        }
                    }
                }

                TableSurface {
                    Layout.fillWidth: true
                    level: 1
                    implicitHeight: 154

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Update center"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: root.updateCheckStatus.length > 0 ? root.updateCheckStatus : "Not checked"
                            color: textColor
                            font.pixelSize: 12
                            font.bold: true
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Scanner: " + root.scannerStatusText + "  |  Repo: " + root.scannerUpdateText
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            AppCheckBox { text: "Auto"; checked: root.updateAutoCheck; onToggled: root.setUpdateAutoCheck(checked) }
                            Item { Layout.fillWidth: true }
                            AppButton { text: "Check updates"; compact: true; onClicked: root.requestManualUpdateCheck() }
                        }
                    }
                }

                TableSurface {
                    Layout.fillWidth: true
                    Layout.columnSpan: root.dashboardTwoColumn ? 2 : 1
                    level: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Startup checklist"; color: textColor; font.pixelSize: 12; font.bold: true }
                        GridLayout {
                            Layout.fillWidth: true
                            columns: root.statusTwoColumn ? 2 : 1
                            rowSpacing: 6
                            columnSpacing: 14
                            Text { Layout.fillWidth: true; text: "1) Capture runtime: " + root.runtimeStateLabel(); color: root.runtimeStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                            Text { Layout.fillWidth: true; text: "2) Git dependency: " + root.gitStateLabel(); color: root.gitStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                            Text { Layout.fillWidth: true; text: "3) Game data: " + root.gameDataStateLabel(); color: root.gameDataStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                            Text { Layout.fillWidth: true; text: "4) Scanner status: " + root.scannerStatusText; color: mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Next step: if the first three checks are ready, move to Scanner for repo/build tasks or Market for planning."
                            color: mutedColor
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
    }
}
