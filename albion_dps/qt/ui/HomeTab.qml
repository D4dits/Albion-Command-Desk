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
    property bool showBrandTile: width >= 1060
    property bool statusTwoColumn: width >= 860
    property bool bottomTwoColumn: width >= 980

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
                spacing: 10

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
                        text: "Startup checklist: verify dependencies, then use Scanner or Market actions."
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }

                TableSurface {
                    visible: root.showBrandTile
                    level: 1
                    Layout.preferredWidth: 210
                    Layout.minimumWidth: 210
                    Layout.preferredHeight: 84
                    Layout.minimumHeight: 84

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 8

                        Image {
                            source: "command_desk_icon.png"
                            sourceSize.width: 48
                            sourceSize.height: 48
                            fillMode: Image.PreserveAspectFit
                            Layout.preferredWidth: 48
                            Layout.preferredHeight: 48
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

            TableSurface {
                id: systemHealthCard
                Layout.fillWidth: true
                level: 1

                ColumnLayout {
                    id: systemHealthContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    anchors.topMargin: 10
                    spacing: 8

                    Text {
                        text: "System health"
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                    }

                    GridLayout {
                        Layout.fillWidth: true
                        columns: root.statusTwoColumn ? 2 : 1
                        rowSpacing: 8
                        columnSpacing: 10

                        TableSurface {
                            Layout.fillWidth: true
                            level: 0
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 6
                                Text { text: "Capture runtime"; color: textColor; font.pixelSize: 12; font.bold: true }
                                Text { text: "Status: " + root.runtimeStateLabel(); color: root.runtimeStateColor(); font.pixelSize: 11; font.bold: true }
                                Text { text: root.captureRuntimeDetail; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                                Text {
                                    visible: root.captureRuntimeInstallHint.length > 0
                                    text: root.captureRuntimeInstallHint
                                    color: textColor
                                    font.pixelSize: 11
                                    Layout.fillWidth: true
                                    wrapMode: Text.WordWrap
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
                                    AppButton { text: "Refresh"; compact: true; onClicked: root.refreshCaptureRuntimeStatus() }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                        }

                        TableSurface {
                            Layout.fillWidth: true
                            level: 0
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 6
                                Text { text: "Git dependency"; color: textColor; font.pixelSize: 12; font.bold: true }
                                Text { text: "Status: " + root.gitStateLabel(); color: root.gitStateColor(); font.pixelSize: 11; font.bold: true }
                                Text { text: root.gitDetail; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                                Text {
                                    visible: root.gitInstallHint.length > 0
                                    text: root.gitInstallHint
                                    color: textColor
                                    font.pixelSize: 11
                                    Layout.fillWidth: true
                                    wrapMode: Text.WordWrap
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
                                    AppButton { text: "Refresh"; compact: true; onClicked: root.refreshGitStatus() }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                        }

                        TableSurface {
                            Layout.fillWidth: true
                            Layout.columnSpan: root.statusTwoColumn ? 2 : 1
                            level: 0
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 6
                                Text { text: "Game data"; color: textColor; font.pixelSize: 12; font.bold: true }
                                Text { text: "Status: " + root.gameDataStateLabel(); color: root.gameDataStateColor(); font.pixelSize: 11; font.bold: true }
                                Text { text: root.gameDataDetail; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                                Text {
                                    visible: root.gameDataHint.length > 0
                                    text: root.gameDataHint
                                    color: textColor
                                    font.pixelSize: 11
                                    Layout.fillWidth: true
                                    wrapMode: Text.WordWrap
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6
                                    AppButton { text: root.gameDataActionLabel; variant: "primary"; compact: true; onClicked: root.setupGameData() }
                                    AppButton { text: "Refresh"; compact: true; onClicked: root.refreshGameDataStatus() }
                                    Item { Layout.fillWidth: true }
                                }
                            }
                        }
                    }
                }

                implicitHeight: systemHealthContent.implicitHeight + 20
            }

            GridLayout {
                Layout.fillWidth: true
                columns: root.bottomTwoColumn ? 2 : 1
                columnSpacing: 10
                rowSpacing: 10

                TableSurface {
                    id: checklistCard
                    Layout.fillWidth: true
                    level: 1

                    ColumnLayout {
                        id: checklistContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        anchors.topMargin: 10
                        spacing: 6

                        Text { text: "Startup checklist"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text { Layout.fillWidth: true; text: "1) Capture runtime: " + root.runtimeStateLabel(); color: root.runtimeStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                        Text { Layout.fillWidth: true; text: "2) Git dependency: " + root.gitStateLabel(); color: root.gitStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                        Text { Layout.fillWidth: true; text: "3) Game data: " + root.gameDataStateLabel(); color: root.gameDataStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                        Text { Layout.fillWidth: true; text: "4) Scanner status: " + root.scannerStatusText; color: mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                    }

                    implicitHeight: checklistContent.implicitHeight + 20
                }

                TableSurface {
                    id: updatesCard
                    Layout.fillWidth: true
                    level: 1

                    ColumnLayout {
                        id: updatesCardContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        anchors.topMargin: 10
                        spacing: 8

                        Text { text: "Update checks"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Status"; color: mutedColor; font.pixelSize: 11 }
                        Text {
                            text: root.updateCheckStatus.length > 0 ? root.updateCheckStatus : "Not checked"
                            color: textColor
                            font.pixelSize: 11
                            font.bold: true
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
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
                            Item { Layout.fillWidth: true }
                        }
                    }

                    implicitHeight: updatesCardContent.implicitHeight + 20
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 2
            }
        }
    }
}
