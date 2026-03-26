import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for AppButton, AppCheckBox, AppComboBox, AppTextField, CardPanel, TableSurface

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
    property bool twoColumn: true
    property int contentPadding: compactLayout ? 8 : 12
    property int contentSpacing: compactLayout ? 8 : 10
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
        id: settingsScroll
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        contentHeight: settingsContent.implicitHeight + (root.contentPadding * 2)
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            id: settingsContent
            width: Math.max(settingsScroll.availableWidth - (root.contentPadding * 2), 360)
            height: implicitHeight
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
                        text: "Settings"
                        color: textColor
                        font.pixelSize: 14
                        font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Update behavior, logging, scanner repository, and game data paths."
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
                                text: "Runtime config"
                                color: mutedColor
                                font.pixelSize: 10
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    TableSurface {
                        Layout.fillWidth: true
                        level: 1
                        implicitHeight: 146

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Text { text: "Updates"; color: textColor; font.pixelSize: 12; font.bold: true }
                            Text {
                                Layout.fillWidth: true
                                text: root.updateCheckStatus.length > 0 ? root.updateCheckStatus : "Not checked"
                                color: textColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                AppCheckBox {
                                    text: "Auto check updates"
                                    checked: root.updateAutoCheck
                                    onToggled: root.setUpdateAutoCheck(checked)
                                }
                                AppButton {
                                    text: "Check now"
                                    compact: true
                                    onClicked: root.requestManualUpdateCheck()
                                }
                                Item { Layout.fillWidth: true }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: "Automatic checks run on startup when enabled."
                                color: mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                    }

                    TableSurface {
                        Layout.fillWidth: true
                        level: 1
                        implicitHeight: 146

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Text { text: "Logging"; color: textColor; font.pixelSize: 12; font.bold: true }
                            Text {
                                Layout.fillWidth: true
                                text: "Default log level for the next app start."
                                color: mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Text { text: "Level"; color: mutedColor; font.pixelSize: 11 }
                                AppComboBox {
                                    id: logLevelCombo
                                    Layout.preferredWidth: 140
                                    model: ["DEBUG", "INFO", "WARNING", "ERROR"]
                                    currentIndex: Math.max(0, model.indexOf(root.appLogLevel))
                                    onActivated: root.setAppLogLevel(String(currentText))
                                }
                                Item { Layout.fillWidth: true }
                            }
                            Text {
                                Layout.fillWidth: true
                                text: "Use DEBUG when you need packet/runtime troubleshooting. Normal use should stay on INFO."
                                color: mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }

                TableSurface {
                    Layout.fillWidth: true
                    level: 1
                    implicitHeight: 198

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "Scanner repository"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Local repo path"; color: mutedColor; font.pixelSize: 11 }
                        AppTextField {
                            id: repoDirField
                            Layout.fillWidth: true
                            text: root.scannerRepoDir
                            placeholderText: "artifacts/albiondata-client"
                        }
                        Text { text: "Upstream URL"; color: mutedColor; font.pixelSize: 11 }
                        AppTextField {
                            id: repoUrlField
                            Layout.fillWidth: true
                            text: root.scannerRepoUrl
                            placeholderText: "https://github.com/ao-data/albiondata-client.git"
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { text: "Save path"; variant: "primary"; compact: true; onClicked: root.setScannerRepoDir(repoDirField.text) }
                            AppButton {
                                text: "Reset path"
                                compact: true
                                onClicked: {
                                    root.resetScannerRepoDir()
                                    repoDirField.text = root.scannerRepoDir
                                }
                            }
                            AppButton { text: "Save URL"; compact: true; onClicked: root.setScannerRepoUrl(repoUrlField.text) }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Config directory: " + root.configDir
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    TableSurface {
                        Layout.fillWidth: true
                        level: 1
                        implicitHeight: 166

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Text { text: "Game data"; color: textColor; font.pixelSize: 12; font.bold: true }
                            Text { text: "Status: " + root.gameDataStateLabel(); color: root.gameDataStateColor(); font.pixelSize: 11; font.bold: true }
                            Text { Layout.fillWidth: true; text: root.gameDataDetail; color: mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                            Text {
                                Layout.fillWidth: true
                                text: root.gameDataRoot.length > 0 ? ("Game folder: " + root.gameDataRoot) : "Game folder not configured."
                                color: textColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                            Text {
                                visible: root.gameDataHint.length > 0
                                Layout.fillWidth: true
                                text: root.gameDataHint
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
                        implicitHeight: 166

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 8

                            Text { text: "Notes"; color: textColor; font.pixelSize: 12; font.bold: true }
                            Text {
                                Layout.fillWidth: true
                                text: "Start is the status dashboard. Settings is only for values you want to change."
                                color: mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                            Text {
                                Layout.fillWidth: true
                                text: root.captureRuntimeState === "available"
                                    ? "Capture runtime is available."
                                    : "Capture runtime requires attention. Use Start or Help for the exact action."
                                color: textColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                            Text {
                                Layout.fillWidth: true
                                text: root.gitAvailable
                                    ? "Git is available for Scanner workflows."
                                    : "Git is missing. Install it if you want Scanner sync/update/build."
                                color: mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 2
            }
        }
    }
}
