import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Item {
    id: root

    property var theme
    property bool compactLayout: false
    property int eventCount: 0
    property string latestLootSummary: ""
    property string logPath: ""
    property var eventsModel: null

    Rectangle {
        anchors.fill: parent
        radius: theme.cornerRadiusPanel
        color: theme.surfacePanel
        border.color: theme.borderSubtle

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: theme.spacingSection
            spacing: theme.spacingSection

            RowLayout {
                Layout.fillWidth: true
                spacing: theme.spacingSection

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Text {
                        text: "Loot"
                        color: theme.textPrimary
                        font.pixelSize: 24
                        font.bold: true
                    }

                    Text {
                        Layout.fillWidth: true
                        text: latestLootSummary.length > 0 ? latestLootSummary : "No loot events recorded yet."
                        color: latestLootSummary.length > 0 ? theme.textMuted : theme.textFaint
                        wrapMode: Text.Wrap
                    }
                }

                Rectangle {
                    Layout.alignment: Qt.AlignTop
                    Layout.preferredWidth: compactLayout ? 120 : 160
                    radius: theme.cornerRadiusCard
                    color: theme.surfaceRaised
                    border.color: theme.borderSubtle
                    implicitHeight: 72

                    Column {
                        anchors.centerIn: parent
                        spacing: 4

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: String(eventCount)
                            color: theme.textPrimary
                            font.pixelSize: 22
                            font.bold: true
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "events"
                            color: theme.textMuted
                            font.pixelSize: 11
                            font.letterSpacing: 0.6
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: compactLayout ? 84 : 72
                radius: theme.cornerRadiusCard
                color: theme.surfaceRaised
                border.color: theme.borderSubtle

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 4

                    Text {
                        text: "Session Log"
                        color: theme.textPrimary
                        font.pixelSize: 13
                        font.bold: true
                    }

                    Text {
                        Layout.fillWidth: true
                        text: logPath.length > 0 ? logPath : "Writer not initialized"
                        color: theme.textMuted
                        font.pixelSize: 11
                        elide: Text.ElideMiddle
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: theme.cornerRadiusCard
                color: theme.cardLevel1
                border.color: theme.borderSubtle

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        Text { text: "Time"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 72 }
                        Text { text: "Looter"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 160 }
                        Text { text: "Item"; color: theme.textMuted; font.pixelSize: 11; Layout.fillWidth: true }
                        Text { text: "Qty"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 48 }
                        Text { text: "Source"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 180 }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: theme.borderSubtle
                    }

                    ListView {
                        id: lootList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 6
                        model: eventsModel

                        delegate: Rectangle {
                            required property string timestampText
                            required property string lootedByName
                            required property string lootedByGuild
                            required property string itemName
                            required property int quantity
                            required property string sourceName
                            required property string sourceKind
                            required property string summary

                            width: lootList.width
                            radius: theme.cornerRadiusCard
                            color: index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
                            border.color: theme.borderSubtle
                            implicitHeight: detailText.implicitHeight + 30

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 6

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 12

                                    Text {
                                        text: timestampText
                                        color: theme.textPrimary
                                        font.pixelSize: 12
                                        Layout.preferredWidth: 72
                                    }
                                    Text {
                                        text: lootedByGuild.length > 0 ? (lootedByName + " [" + lootedByGuild + "]") : lootedByName
                                        color: theme.textPrimary
                                        font.pixelSize: 12
                                        Layout.preferredWidth: 160
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        text: itemName
                                        color: theme.textPrimary
                                        font.pixelSize: 12
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    Text {
                                        text: String(quantity)
                                        color: theme.textPrimary
                                        font.pixelSize: 12
                                        horizontalAlignment: Text.AlignRight
                                        Layout.preferredWidth: 48
                                    }
                                    Rectangle {
                                        Layout.preferredWidth: 180
                                        radius: 10
                                        color: sourceKind === "mob" ? theme.stateWarning : (sourceKind === "player" ? theme.stateInfo : theme.surfaceRaised)
                                        implicitHeight: 22

                                        Text {
                                            anchors.centerIn: parent
                                            text: sourceName
                                            color: sourceKind === "mob" ? theme.surfaceApp : theme.textPrimary
                                            font.pixelSize: 11
                                            elide: Text.ElideRight
                                            width: parent.width - 12
                                            horizontalAlignment: Text.AlignHCenter
                                        }
                                    }
                                }

                                Text {
                                    id: detailText
                                    Layout.fillWidth: true
                                    text: summary
                                    color: theme.textMuted
                                    font.pixelSize: 11
                                    wrapMode: Text.Wrap
                                }
                            }
                        }

                        ScrollBar.vertical: ScrollBar {}
                    }
                }
            }
        }
    }
}
