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
    property bool twoColumn: width >= 940

    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    readonly property string websiteUrl: "https://d4dits.github.io/Albion-Command-Desk/"
    readonly property string releaseUrl: "https://github.com/D4dits/Albion-Command-Desk/releases/latest"
    readonly property string changelogUrl: "https://github.com/D4dits/Albion-Command-Desk/blob/main/CHANGELOG.md"
    readonly property string troubleshootingUrl: "https://github.com/D4dits/Albion-Command-Desk/blob/main/docs/TROUBLESHOOTING.md"
    readonly property string scannerRepoUrl: "https://github.com/ao-data/albiondata-client"
    readonly property string npcapUrl: "https://npcap.com/#download"
    readonly property string gitUrl: "https://git-scm.com/downloads"

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: Math.max(parent.availableWidth - 24, 360)
            x: 12
            y: 12
            spacing: compactLayout ? 8 : 10

            Text {
                text: "Help"
                color: textColor
                font.pixelSize: 14
                font.bold: true
            }
            Text {
                Layout.fillWidth: true
                text: "Version, release notes, dependency guidance, and support entry points."
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
                    level: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text { text: "About Albion Command Desk"; color: textColor; font.pixelSize: 12; font.bold: true }
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
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { text: "Website"; compact: true; onClicked: Qt.openUrlExternally(root.websiteUrl) }
                            AppButton { text: "Latest release"; compact: true; onClicked: Qt.openUrlExternally(root.releaseUrl) }
                            AppButton { text: "Changelog"; compact: true; onClicked: Qt.openUrlExternally(root.changelogUrl) }
                            Item { Layout.fillWidth: true }
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
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { text: "Npcap"; compact: true; onClicked: Qt.openUrlExternally(root.npcapUrl) }
                            AppButton { text: "Git"; compact: true; onClicked: Qt.openUrlExternally(root.gitUrl) }
                            AppButton { text: "Scanner repo"; compact: true; onClicked: Qt.openUrlExternally(root.scannerRepoUrl) }
                            Item { Layout.fillWidth: true }
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

                        Text { text: "Common fixes"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: "\u2022 Missing Npcap: install Npcap Runtime, then restart the app.\n\u2022 Missing Git: install Git, restart, then use Scanner sync/update.\n\u2022 Missing game data: run Game data setup from Settings.\n\u2022 Capture problems: try the correct interface and confirm live mode prerequisites."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            AppButton { text: "Troubleshooting"; variant: "primary"; compact: true; onClicked: Qt.openUrlExternally(root.troubleshootingUrl) }
                            Item { Layout.fillWidth: true }
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

                        Text { text: "Support"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Text {
                            Layout.fillWidth: true
                            text: "Use this tab as the operator handbook: website, releases, changelog, troubleshooting, and dependency download pages are one click away."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "For bug reports, include version, current update status, scanner log excerpt, and market diagnostics when relevant."
                            color: mutedColor
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
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
