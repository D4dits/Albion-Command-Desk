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

    property bool gameDataReady: false
    property string gameDataDetail: ""
    property string gameDataHint: ""
    property string gameDataActionLabel: "Select game folder"

    property bool compactLayout: false
    property bool twoColumn: width >= 900
    property bool wideLayout: width >= 1040

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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

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
                    text: "Use this tab as your startup checklist: verify dependencies first, then move to Scanner or Market actions."
                    color: mutedColor
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }

            TableSurface {
                visible: root.wideLayout
                level: 1
                Layout.preferredWidth: 230
                Layout.minimumWidth: 230
                Layout.preferredHeight: 96
                Layout.minimumHeight: 96

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 8

                    Image {
                        source: "command_desk_icon.png"
                        sourceSize.width: 60
                        sourceSize.height: 60
                        fillMode: Image.PreserveAspectFit
                        Layout.preferredWidth: 60
                        Layout.preferredHeight: 60
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: "Command Desk"
                            color: textColor
                            font.pixelSize: 11
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
            columns: root.twoColumn ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10

            TableSurface {
                id: captureCard
                Layout.fillWidth: true
                level: 1
                ColumnLayout {
                    id: captureCardContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    anchors.topMargin: 10
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

                implicitHeight: captureCardContent.implicitHeight + 20
            }

            TableSurface {
                id: gitCard
                Layout.fillWidth: true
                level: 1
                ColumnLayout {
                    id: gitCardContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    anchors.topMargin: 10
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

                implicitHeight: gitCardContent.implicitHeight + 20
            }

            TableSurface {
                id: gameDataCard
                Layout.fillWidth: true
                Layout.columnSpan: root.twoColumn ? 2 : 1
                level: 1
                ColumnLayout {
                    id: gameDataCardContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    anchors.topMargin: 10
                    spacing: 8

                    Text {
                        text: "Game data"
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Text {
                        text: "Status: " + root.gameDataStateLabel()
                        color: root.gameDataStateColor()
                        font.pixelSize: 11
                        font.bold: true
                    }
                    Text {
                        text: root.gameDataDetail
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: root.gameDataHint.length > 0
                        text: root.gameDataHint
                        color: textColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        AppButton {
                            text: root.gameDataActionLabel
                            variant: "primary"
                            compact: true
                            onClicked: root.setupGameData()
                        }
                        AppButton {
                            text: "Refresh"
                            compact: true
                            onClicked: root.refreshGameDataStatus()
                        }
                        Item { Layout.fillWidth: true }
                    }
                }

                implicitHeight: gameDataCardContent.implicitHeight + 20
            }
        }

        GridLayout {
            id: infoGrid
            Layout.fillWidth: true
            columns: root.twoColumn ? 2 : 1
            columnSpacing: 10
            rowSpacing: 10
            property int infoRowHeight: Math.max(checklistContent.implicitHeight, modulesContent.implicitHeight) + 20

            TableSurface {
                id: checklistCard
                Layout.fillWidth: true
                Layout.preferredHeight: infoGrid.infoRowHeight
                level: 1

                ColumnLayout {
                    id: checklistContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    anchors.topMargin: 10
                    spacing: 8

                    Text {
                        text: "Startup checklist"
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "1) Capture runtime: " + root.runtimeStateLabel()
                        color: root.runtimeStateColor()
                        font.pixelSize: 11
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "2) Git dependency: " + root.gitStateLabel()
                        color: root.gitStateColor()
                        font.pixelSize: 11
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "3) Game data: " + root.gameDataStateLabel()
                        color: root.gameDataStateColor()
                        font.pixelSize: 11
                        font.bold: true
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "4) Scanner status: " + root.scannerStatusText
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "When all checks are ready, go to Scanner to sync/build client and start live mode."
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }

                implicitHeight: checklistContent.implicitHeight + 20
            }

            TableSurface {
                id: modulesCard
                Layout.fillWidth: true
                Layout.preferredHeight: infoGrid.infoRowHeight
                level: 1

                ColumnLayout {
                    id: modulesContent
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    anchors.topMargin: 10
                    spacing: 8

                    Text {
                        text: "Modules overview"
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Meter: combat stats and history from live capture or replay data."
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Scanner: sync/build/start Albion Data Client integration."
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Market: crafting and profitability planning using market data."
                        color: mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }

                implicitHeight: modulesContent.implicitHeight + 20
            }
        }

        TableSurface {
            id: quickActionsCard
            Layout.fillWidth: true
            level: 1
            ColumnLayout {
                id: quickActionsContent
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                anchors.topMargin: 10
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: "Update checks"
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: "Use this section to check for new Albion Command Desk releases."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }
                    }

                    ColumnLayout {
                        Layout.alignment: Qt.AlignRight | Qt.AlignTop
                        spacing: 4
                        RowLayout {
                            spacing: 6
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
                            visible: root.updateCheckStatus.length > 0
                            text: root.updateCheckStatus
                            color: mutedColor
                            font.pixelSize: 11
                            horizontalAlignment: Text.AlignRight
                        }
                    }
                }

            }

            implicitHeight: quickActionsContent.implicitHeight + 20
        }
    }
}
