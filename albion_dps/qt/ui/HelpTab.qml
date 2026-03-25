import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for AppButton, CardPanel, TableSurface

CardPanel {
    id: root
    level: 1
    anchors.fill: parent

    property string appVersion: "local-dev"
    property string updateCheckStatus: ""
    property string configDir: ""
    property string captureRuntimeState: "unknown"
    property string gitDetail: ""
    property string gameDataDetail: ""
    property bool compactLayout: false
    property int contentPadding: compactLayout ? 8 : 12
    property int contentSpacing: compactLayout ? 8 : 10
    property bool showBrandTile: width >= 1080
    property bool dashboardTwoColumn: width >= 940

    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    signal exportDiagnosticsBundle()

    readonly property string websiteUrl: "https://d4dits.github.io/Albion-Command-Desk/"
    readonly property string releaseUrl: "https://github.com/D4dits/Albion-Command-Desk/releases/latest"
    readonly property string changelogUrl: "https://github.com/D4dits/Albion-Command-Desk/blob/main/CHANGELOG.md"
    readonly property string troubleshootingUrl: "https://github.com/D4dits/Albion-Command-Desk/blob/main/docs/TROUBLESHOOTING.md"
    readonly property string scannerRepoUrl: "https://github.com/ao-data/albiondata-client"
    readonly property string npcapUrl: "https://npcap.com/#download"
    readonly property string gitUrl: "https://git-scm.com/downloads"

    ScrollView {
        id: helpScroll
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: Math.max(helpScroll.availableWidth - (root.contentPadding * 2), 360)
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
                        text: "Help"
                        color: textColor
                        font.pixelSize: 14
                        font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: "Release links, dependency guidance, troubleshooting, and diagnostics export."
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
                                text: "Operator handbook"
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

                        Text { text: "Release center"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Version: " + root.appVersion; color: textColor; font.pixelSize: 11; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: root.updateCheckStatus.length > 0 ? ("Update status: " + root.updateCheckStatus) : "Update status: not checked"
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Config directory: " + root.configDir
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { text: "Website"; compact: true; onClicked: Qt.openUrlExternally(root.websiteUrl) }
                            AppButton { text: "Release"; compact: true; onClicked: Qt.openUrlExternally(root.releaseUrl) }
                            AppButton { text: "Changelog"; compact: true; onClicked: Qt.openUrlExternally(root.changelogUrl) }
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

                        Text { text: "Dependencies"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: "Capture runtime: " + root.captureRuntimeState
                            color: textColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: root.gitDetail.length > 0 ? root.gitDetail : "Git status not checked."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: root.gameDataDetail.length > 0 ? root.gameDataDetail : "Game data status not checked."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { text: "Npcap"; compact: true; onClicked: Qt.openUrlExternally(root.npcapUrl) }
                            AppButton { text: "Git"; compact: true; onClicked: Qt.openUrlExternally(root.gitUrl) }
                            AppButton { text: "Scanner repo"; compact: true; onClicked: Qt.openUrlExternally(root.scannerRepoUrl) }
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

                        Text { text: "Troubleshooting"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: "\u2022 Missing Npcap: install Npcap Runtime, then restart the app.\n\u2022 Missing Git: install Git, restart, then use Scanner sync/update.\n\u2022 Missing game data: run Game data setup from Settings.\n\u2022 Capture problems: try the correct interface and confirm live mode prerequisites."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { text: "Troubleshooting"; variant: "primary"; compact: true; onClicked: Qt.openUrlExternally(root.troubleshootingUrl) }
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

                        Text { text: "Diagnostics"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: "Export diagnostics before reporting problems with capture, market, or scanner workflows."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "Include version, update status, scanner log excerpt, and market diagnostics when relevant."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Flow {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton {
                                text: "Export diagnostics"
                                variant: "primary"
                                compact: true
                                onClicked: root.exportDiagnosticsBundle()
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
