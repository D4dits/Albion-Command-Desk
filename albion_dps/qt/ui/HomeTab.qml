import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

CardPanel {
    id: root
    level: 1
    anchors.fill: parent

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

    property bool compactLayout: false
    property int contentPadding: compactLayout ? 8 : 12
    property int cardSpacing: compactLayout ? 8 : 10
    property int brandTileWidth: 194
    property int bodyWidth: Math.max(920, contentScroll.availableWidth - (contentPadding * 2))
    property int gridColumnWidth: Math.floor((bodyWidth - cardSpacing) / 2)

    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

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
        if (captureRuntimeState === "available") return theme.stateSuccess
        if (captureRuntimeState === "missing") return theme.stateWarning
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
        contentWidth: bodyWidth + (root.contentPadding * 2)
        contentHeight: contentColumn.height + (root.contentPadding * 2)
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        Column {
            id: contentColumn
            x: root.contentPadding
            y: root.contentPadding
            width: root.bodyWidth
            spacing: root.cardSpacing

            Item {
                width: parent.width
                height: 84

                Column {
                    anchors.left: parent.left
                    anchors.right: brandTile.left
                    anchors.rightMargin: 12
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 4

                    Text {
                        text: "Start"
                        color: root.textColor
                        font.pixelSize: 14
                        font.bold: true
                    }
                    Text {
                        width: parent.width
                        text: "Startup checklist: verify dependencies here, then move to Scanner or Market. Settings holds paths and runtime controls."
                        color: root.mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }

                TableSurface {
                    id: brandTile
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

                            Text {
                                text: "Command Desk"
                                color: root.textColor
                                font.pixelSize: 12
                                font.bold: true
                            }
                            Text {
                                text: "Startup center"
                                color: root.mutedColor
                                font.pixelSize: 10
                            }
                        }
                    }
                }
            }

            Row {
                width: parent.width
                spacing: root.cardSpacing

                TableSurface {
                    width: root.gridColumnWidth
                    height: 150
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Capture runtime"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: root.runtimeStateLabel(); color: root.runtimeStateColor(); font.pixelSize: 11; font.bold: true }
                        Text {
                            width: parent.width
                            text: root.captureRuntimeInstallHint.length > 0 ? root.captureRuntimeInstallHint : root.captureRuntimeDetail
                            color: root.mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            width: parent.width
                            spacing: 6
                            AppButton { visible: root.captureRuntimeActionLabel.length > 0; text: root.captureRuntimeActionLabel; variant: "primary"; compact: true; onClicked: root.openCaptureRuntimeAction() }
                            AppButton { visible: root.captureRuntimeInstallCommand.length > 0; text: "Copy"; compact: true; onClicked: root.copyCommand(root.captureRuntimeInstallCommand) }
                            AppButton { text: "Refresh"; compact: true; onClicked: root.refreshCaptureRuntimeStatus() }
                        }
                    }
                }

                TableSurface {
                    width: root.gridColumnWidth
                    height: 150
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Git dependency"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: root.gitStateLabel(); color: root.gitStateColor(); font.pixelSize: 11; font.bold: true }
                        Text {
                            width: parent.width
                            text: root.gitInstallHint.length > 0 ? root.gitInstallHint : root.gitDetail
                            color: root.mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            width: parent.width
                            spacing: 6
                            AppButton { visible: root.gitActionLabel.length > 0; text: root.gitActionLabel; variant: "primary"; compact: true; onClicked: root.openGitInstallAction() }
                            AppButton { visible: root.gitInstallCommand.length > 0; text: "Copy"; compact: true; onClicked: root.copyCommand(root.gitInstallCommand) }
                            AppButton { text: "Refresh"; compact: true; onClicked: root.refreshGitStatus() }
                        }
                    }
                }
            }

            Row {
                width: parent.width
                spacing: root.cardSpacing

                TableSurface {
                    width: root.gridColumnWidth
                    height: 150
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Game data"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: root.gameDataStateLabel(); color: root.gameDataStateColor(); font.pixelSize: 11; font.bold: true }
                        Text {
                            width: parent.width
                            text: root.gameDataHint.length > 0 ? root.gameDataHint : root.gameDataDetail
                            color: root.mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            width: parent.width
                            spacing: 6
                            AppButton { text: root.gameDataActionLabel; variant: "primary"; compact: true; onClicked: root.setupGameData() }
                            AppButton { text: "Refresh"; compact: true; onClicked: root.refreshGameDataStatus() }
                        }
                    }
                }

                TableSurface {
                    width: root.gridColumnWidth
                    height: 150
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Update center"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text {
                            width: parent.width
                            text: root.updateCheckStatus.length > 0 ? root.updateCheckStatus : "Not checked"
                            color: root.textColor
                            font.pixelSize: 12
                            font.bold: true
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            width: parent.width
                            text: "App updates only. Scanner repo sync and build stay in Scanner."
                            color: root.mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Row {
                            width: parent.width
                            spacing: 8
                            AppCheckBox { text: "Auto"; checked: root.updateAutoCheck; onToggled: root.setUpdateAutoCheck(checked) }
                            Item { width: Math.max(0, parent.width - 160) }
                            AppButton { text: "Check updates"; compact: true; onClicked: root.requestManualUpdateCheck() }
                        }
                    }
                }
            }

            TableSurface {
                width: parent.width
                height: 110
                level: 1

                Column {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 8

                    Text { text: "Startup checklist"; color: root.textColor; font.pixelSize: 12; font.bold: true }

                    Row {
                        width: parent.width
                        spacing: 18

                        Column {
                            width: Math.floor((parent.width - 18) / 2)
                            spacing: 6
                            Text { width: parent.width; text: "1) Capture runtime: " + root.runtimeStateLabel(); color: root.runtimeStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                            Text { width: parent.width; text: "3) Game data: " + root.gameDataStateLabel(); color: root.gameDataStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                        }

                        Column {
                            width: Math.floor((parent.width - 18) / 2)
                            spacing: 6
                            Text { width: parent.width; text: "2) Git dependency: " + root.gitStateLabel(); color: root.gitStateColor(); font.pixelSize: 11; font.bold: true; wrapMode: Text.WordWrap }
                            Text { width: parent.width; text: "4) Scanner status: " + root.scannerStatusText; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        }
                    }

                    Text {
                        width: parent.width
                        text: "Next step: when the first three checks are ready, move to Scanner for repo/build tasks or Market for planning."
                        color: root.mutedColor
                        font.pixelSize: 10
                        wrapMode: Text.WordWrap
                    }
                }
            }
        }
    }
}
