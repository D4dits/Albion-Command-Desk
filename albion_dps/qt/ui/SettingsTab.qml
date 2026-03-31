import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

CardPanel {
    id: root
    level: 1
    anchors.fill: parent

    property string updateCheckStatus: ""
    property bool updateAutoCheck: false
    property string scannerRepoDir: ""
    property string scannerRepoUrl: ""
    property string appLogLevel: "INFO"
    property string configDir: ""

    property string captureRuntimeState: "unknown"
    property string captureRuntimeDetail: ""
    property string captureRuntimeActionLabel: ""
    property string captureRuntimeInstallHint: ""

    property bool gitAvailable: false
    property string gitDetail: ""
    property string gitActionLabel: ""
    property string gitInstallHint: ""

    property bool gameDataReady: false
    property string gameDataDetail: ""
    property string gameDataHint: ""
    property string gameDataRoot: ""
    property string gameDataActionLabel: "Select game folder"

    property bool compactLayout: false
    property int contentPadding: compactLayout ? 8 : 12
    property int cardSpacing: compactLayout ? 8 : 10
    property int brandTileWidth: 194
    property int bodyWidth: Math.max(920, settingsScroll.availableWidth - (contentPadding * 2))
    property int gridColumnWidth: Math.floor((bodyWidth - cardSpacing) / 2)
    property bool showBrandTile: true

    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    signal setUpdateAutoCheck(bool checked)
    signal requestManualUpdateCheck()
    signal setScannerRepoDir(string pathText)
    signal resetScannerRepoDir()
    signal setScannerRepoUrl(string urlText)
    signal setAppLogLevel(string value)
    signal refreshCaptureRuntimeStatus()
    signal openCaptureRuntimeAction()
    signal refreshGitStatus()
    signal openGitInstallAction()
    signal refreshGameDataStatus()
    signal setupGameData()
    signal copyCommand(string commandText)

    function gameDataStateColor() {
        return gameDataReady ? theme.stateSuccess : theme.stateWarning
    }

    function gameDataStateLabel() {
        return gameDataReady ? "ready" : "missing"
    }

    ScrollView {
        id: settingsScroll
        anchors.fill: parent
        clip: true
        contentWidth: bodyWidth + (root.contentPadding * 2)
        contentHeight: settingsColumn.height + (root.contentPadding * 2)
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        Column {
            id: settingsColumn
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

                    Text { text: "Settings"; color: root.textColor; font.pixelSize: 14; font.bold: true }
                    Text {
                        width: parent.width
                        text: "Update behavior, logging, scanner repository, and game data paths. Status checks stay on Start."
                        color: root.mutedColor
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }

                TableSurface {
                    id: brandTile
                    visible: root.showBrandTile
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
                            Text { text: "Runtime config"; color: root.mutedColor; font.pixelSize: 10 }
                        }
                    }
                }
            }

            Row {
                width: parent.width
                spacing: root.cardSpacing

                TableSurface {
                    width: root.gridColumnWidth
                    height: 154
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Updates"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text {
                            width: parent.width
                            text: root.updateCheckStatus.length > 0 ? root.updateCheckStatus : "Not checked"
                            color: root.textColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Row {
                            width: parent.width
                            spacing: 8
                            AppCheckBox { text: "Auto"; checked: root.updateAutoCheck; onToggled: root.setUpdateAutoCheck(checked) }
                            AppButton { text: "Check now"; compact: true; onClicked: root.requestManualUpdateCheck() }
                        }
                        Text {
                            width: parent.width
                            text: "Automatic checks run on startup when enabled."
                            color: root.mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                TableSurface {
                    width: root.gridColumnWidth
                    height: 154
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Logging"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { width: parent.width; text: "Default log level for the next app start."; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        Row {
                            width: parent.width
                            spacing: 8
                            Text { text: "Level"; color: root.mutedColor; font.pixelSize: 11; anchors.verticalCenter: parent.verticalCenter }
                            AppComboBox {
                                id: logLevelCombo
                                width: 140
                                model: ["DEBUG", "INFO", "WARNING", "ERROR"]
                                currentIndex: Math.max(0, model.indexOf(root.appLogLevel))
                                onActivated: root.setAppLogLevel(String(currentText))
                            }
                        }
                        Text {
                            width: parent.width
                            text: "Use DEBUG only for packet/runtime troubleshooting. Normal use should stay on INFO."
                            color: root.mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }

            Row {
                width: parent.width
                spacing: root.cardSpacing

                TableSurface {
                    width: root.gridColumnWidth
                    height: 216
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Scanner repository"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Local repo path"; color: root.mutedColor; font.pixelSize: 11 }
                        AppTextField {
                            id: repoDirField
                            width: parent.width
                            text: root.scannerRepoDir
                            placeholderText: "artifacts/albiondata-client"
                        }
                        Text { text: "Upstream URL"; color: root.mutedColor; font.pixelSize: 11 }
                        AppTextField {
                            id: repoUrlField
                            width: parent.width
                            text: root.scannerRepoUrl
                            placeholderText: "https://github.com/ao-data/albiondata-client.git"
                        }
                        Flow {
                            width: parent.width
                            spacing: 6
                            AppButton { text: "Save path"; variant: "primary"; compact: true; onClicked: root.setScannerRepoDir(repoDirField.text) }
                            AppButton { text: "Reset path"; compact: true; onClicked: { root.resetScannerRepoDir(); repoDirField.text = root.scannerRepoDir } }
                            AppButton { text: "Save URL"; compact: true; onClicked: root.setScannerRepoUrl(repoUrlField.text) }
                        }
                    }
                }

                TableSurface {
                    width: root.gridColumnWidth
                    height: 216
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Game data"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Status: " + root.gameDataStateLabel(); color: root.gameDataStateColor(); font.pixelSize: 11; font.bold: true }
                        Text { width: parent.width; text: root.gameDataDetail; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        Text {
                            width: parent.width
                            text: root.gameDataRoot.length > 0 ? ("Game folder: " + root.gameDataRoot) : "Game folder not configured."
                            color: root.textColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            visible: root.gameDataHint.length > 0
                            width: parent.width
                            text: root.gameDataHint
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
            }

            TableSurface {
                width: parent.width
                height: 86
                level: 1

                Column {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 6

                    Text { text: "Notes"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                    Text { width: parent.width; text: "Start is the status dashboard. Settings is only for values you want to change."; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                    Text { width: parent.width; text: "Config directory: " + root.configDir; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                }
            }
        }
    }
}
