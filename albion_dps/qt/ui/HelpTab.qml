import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

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
    property int cardSpacing: compactLayout ? 8 : 10
    property int brandTileWidth: 194
    property int bodyWidth: Math.max(920, width - (contentPadding * 2))
    property int gridColumnWidth: Math.floor((bodyWidth - cardSpacing) / 2)
    property bool showBrandTile: true

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
        contentWidth: root.width
        contentHeight: helpColumn.height + (root.contentPadding * 2)
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        Column {
            id: helpColumn
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

                    Text { text: "Help"; color: root.textColor; font.pixelSize: 14; font.bold: true }
                    Text {
                        width: parent.width
                        text: "Release links, dependency guidance, troubleshooting, and diagnostics export."
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
                            Text { text: "Operator handbook"; color: root.mutedColor; font.pixelSize: 10 }
                        }
                    }
                }
            }

            GridLayout {
                width: parent.width
                columns: 2
                columnSpacing: root.cardSpacing
                rowSpacing: root.cardSpacing

                TableSurface {
                    Layout.fillWidth: true
                    height: 154
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8
                        Text { text: "Release center"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { text: "Version: " + root.appVersion; color: root.textColor; font.pixelSize: 11; font.bold: true }
                        Text { width: parent.width; text: root.updateCheckStatus.length > 0 ? ("Update status: " + root.updateCheckStatus) : "Update status: not checked"; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        Flow {
                            width: parent.width
                            spacing: 6
                            AppButton { text: "Website"; compact: true; onClicked: Qt.openUrlExternally(root.websiteUrl) }
                            AppButton { text: "Release"; compact: true; onClicked: Qt.openUrlExternally(root.releaseUrl) }
                            AppButton { text: "Changelog"; compact: true; onClicked: Qt.openUrlExternally(root.changelogUrl) }
                        }
                    }
                }

                TableSurface {
                    Layout.fillWidth: true
                    height: 154
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8
                        Text { text: "Diagnostics"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { width: parent.width; text: "Export diagnostics before reporting problems with capture, market, or scanner workflows."; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        Text { width: parent.width; text: "Include version, update status, scanner log excerpt, and market diagnostics when relevant."; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        Flow {
                            width: parent.width
                            spacing: 6
                            AppButton { text: "Export diagnostics"; variant: "primary"; compact: true; onClicked: root.exportDiagnosticsBundle() }
                        }
                    }
                }
            
                TableSurface {
                    Layout.fillWidth: true
                    height: 154
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8
                        Text { text: "Dependencies"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Text { width: parent.width; text: "Capture runtime: " + root.captureRuntimeState; color: root.textColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        Text { width: parent.width; text: "Git status, game data status, and runtime actions stay on Start and Settings."; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                        Flow {
                            width: parent.width
                            spacing: 6
                            AppButton { text: "Npcap"; compact: true; onClicked: Qt.openUrlExternally(root.npcapUrl) }
                            AppButton { text: "Git"; compact: true; onClicked: Qt.openUrlExternally(root.gitUrl) }
                            AppButton { text: "Scanner repo"; compact: true; onClicked: Qt.openUrlExternally(root.scannerRepoUrl) }
                        }
                    }
                }

                TableSurface {
                    Layout.fillWidth: true
                    height: 182
                    level: 1

                    Column {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8
                        Text { text: "Troubleshooting"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                        Column {
                            width: parent.width
                            spacing: 4
                            Text {
                                width: parent.width
                                text: "- Missing Npcap: install Npcap Runtime, then restart the app."
                                color: root.mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                            Text {
                                width: parent.width
                                text: "- Missing Git: install Git, restart, then use Scanner sync/update."
                                color: root.mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                            Text {
                                width: parent.width
                                text: "- Missing game data: run Game data setup from Settings."
                                color: root.mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                            Text {
                                width: parent.width
                                text: "- Capture problems: verify the correct interface and live mode prerequisites."
                                color: root.mutedColor
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }
                        }
                        Flow {
                            width: parent.width
                            spacing: 6
                            AppButton { text: "Troubleshooting"; variant: "primary"; compact: true; onClicked: Qt.openUrlExternally(root.troubleshootingUrl) }
                        }
                    }
                }
            }

            TableSurface {
                width: parent.width
                height: 72
                level: 1

                Column {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 6
                    Text { text: "Reference"; color: root.textColor; font.pixelSize: 12; font.bold: true }
                    Text { width: parent.width; text: "Config directory: " + root.configDir; color: root.mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                }
            }
        }
    }
}
