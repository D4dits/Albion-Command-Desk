import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, AppButton, TableSurface access

/**
 * MeterScoreboard - Player list with table header
 *
 * Displays the combat meter scoreboard with:
 * - Table header (Name, Weapon, DMG, HEAL, DPS, HPS, BAR)
 * - Scrollable list of players
 * - Empty state message
 */
Item {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true

    // Properties to bind to parent state
    property var playersModel: null
    property bool showHistory: false
    property int selectedHistoryIndex: -1
    property string sortKey: "dps"

    // Access to theme and helpers (injected by parent)
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    // Helper functions (injected by parent)
    property var tableRowColor: function(index) {
        return index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Table Header
        TableSurface {
            level: 1
            Layout.fillWidth: true
            height: 26
            showTopRule: false

            RowLayout {
                anchors.fill: parent
                anchors.margins: 6
                spacing: 12

                Text {
                    text: "Name"
                    color: root.theme.tableHeaderText
                    font.pixelSize: 11
                    Layout.preferredWidth: 140
                }
                Text {
                    text: "Weapon"
                    color: root.theme.tableHeaderText
                    font.pixelSize: 11
                    Layout.preferredWidth: 90
                }
                Text {
                    text: "DMG"
                    color: root.theme.tableHeaderText
                    font.pixelSize: 11
                    Layout.preferredWidth: 60
                }
                Text {
                    text: "HEAL"
                    color: root.theme.tableHeaderText
                    font.pixelSize: 11
                    Layout.preferredWidth: 60
                }
                Text {
                    text: "DPS"
                    color: root.theme.tableHeaderText
                    font.pixelSize: 11
                    Layout.preferredWidth: 60
                }
                Text {
                    text: "HPS"
                    color: root.theme.tableHeaderText
                    font.pixelSize: 11
                    Layout.preferredWidth: 60
                }
                Text {
                    text: "BAR"
                    color: root.theme.tableHeaderText
                    font.pixelSize: 11
                    Layout.fillWidth: true
                }
            }
        }

        // Player List
        ListView {
            id: meterPlayersList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.playersModel
            spacing: 0
            reuseItems: true
            cacheBuffer: 300

            delegate: Rectangle {
                id: meterRow
                width: ListView.view.width
                height: 34
                property bool hovered: meterHoverArea.containsMouse
                color: hovered ? root.theme.tableRowHover : tableRowColor(index)
                radius: 4
                Behavior on color {
                    ColorAnimation { duration: 120 }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 4
                    spacing: 12

                    Text {
                        text: name
                        color: root.theme.tableTextPrimary
                        font.pixelSize: 12
                        elide: Text.ElideRight
                        Layout.preferredWidth: 140
                    }
                    Item {
                        Layout.preferredWidth: 90
                        height: 24
                        RowLayout {
                            anchors.fill: parent
                            spacing: 4
                            Image {
                                source: weaponIcon
                                width: 20
                                height: 20
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                                sourceSize.width: 20
                                sourceSize.height: 20
                                fillMode: Image.PreserveAspectFit
                                visible: weaponIcon && weaponIcon.length > 0
                            }
                            Text {
                                text: weaponTier && weaponTier.length > 0 ? weaponTier : "-"
                                color: root.theme.tableTextSecondary
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }
                        }
                        ToolTip.visible: weaponHover.containsMouse && weaponName && weaponName.length > 0
                        ToolTip.text: weaponName
                        MouseArea {
                            id: weaponHover
                            anchors.fill: parent
                            hoverEnabled: true
                        }
                    }
                    Text {
                        text: damage
                        color: root.theme.tableTextSecondary
                        font.pixelSize: 12
                        Layout.preferredWidth: 60
                    }
                    Text {
                        text: heal
                        color: root.theme.tableTextSecondary
                        font.pixelSize: 12
                        Layout.preferredWidth: 60
                    }
                    Text {
                        text: dps.toFixed(1)
                        color: root.theme.tableTextSecondary
                        font.pixelSize: 12
                        Layout.preferredWidth: 60
                    }
                    Text {
                        text: hps.toFixed(1)
                        color: root.theme.tableTextSecondary
                        font.pixelSize: 12
                        Layout.preferredWidth: 60
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 10
                        radius: 4
                        color: root.theme.surfaceInset
                        border.color: root.theme.borderSubtle
                        Rectangle {
                            height: parent.height
                            width: Math.max(4, parent.width * barRatio)
                            radius: 4
                            color: barColor
                        }
                    }
                }

                MouseArea {
                    id: meterHoverArea
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton
                }
            }

            // Empty state
            Text {
                anchors.centerIn: parent
                visible: meterPlayersList.count === 0
                text: root.selectedHistoryIndex >= 0
                    ? "No players in selected history entry."
                    : "No live combat data yet. Start fighting or switch replay."
                color: root.theme.textSecondary
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                width: parent.width - 24
            }
        }
    }
}
