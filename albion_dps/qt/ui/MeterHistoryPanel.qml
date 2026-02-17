import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, AppButton, TableSurface access

/**
 * MeterHistoryPanel - History sidebar with battle list
 *
 * Displays:
 * - "Back to live" button when viewing history
 * - Scrollable list of archived battles
 * - Keyboard shortcuts legend
 */
Item {
    id: root
    Layout.preferredWidth: 360
    Layout.fillHeight: true

    // Properties to bind to parent state
    property var historyModel: null
    property int selectedHistoryIndex: -1
    property string sortKey: "dps"

    // Signals to notify parent of actions
    signal clearHistorySelection()
    signal selectHistory(int index)
    signal copyHistory(int index)

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
        anchors.margins: 12
        spacing: 8

        Text {
            text: "History"
            color: textColor
            font.pixelSize: 14
            font.bold: true
        }

        AppButton {
            visible: root.selectedHistoryIndex >= 0
            text: "Back to live"
            implicitHeight: 30
            implicitWidth: 104
            onClicked: root.clearHistorySelection()
        }

        ListView {
            id: historyList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            rightMargin: 6
            model: root.historyModel
            reuseItems: true
            cacheBuffer: 300

            delegate: Rectangle {
                id: historyRow
                width: Math.max(0, ListView.view.width - 6)
                height: 98
                radius: 6
                property bool hovered: historyHover.containsMouse
                color: selected
                    ? root.theme.tableSelectedBackground
                    : (hovered ? root.theme.tableRowHover : tableRowColor(index))
                border.color: selected ? root.theme.tableSelectedBorder : root.theme.tableDivider
                border.width: 1
                Behavior on color {
                    ColorAnimation { duration: 120 }
                }
                TapHandler {
                    onTapped: root.selectHistory(index)
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: label
                            color: textColor
                            font.pixelSize: 12
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                        AppButton {
                            text: "Copy"
                            variant: "ghost"
                            compact: true
                            implicitWidth: 64
                            implicitHeight: 24
                            onClicked: root.copyHistory(index)
                        }
                    }
                    Text {
                        text: meta
                        color: root.theme.tableTextSecondary
                        font.pixelSize: 11
                    }
                    Text {
                        text: players
                        color: root.theme.tableTextPrimary
                        font.pixelSize: 11
                        wrapMode: Text.NoWrap
                        elide: Text.ElideRight
                    }
                }

                MouseArea {
                    id: historyHover
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton
                }
            }

            // Empty state
            Text {
                anchors.centerIn: parent
                visible: historyList.count === 0
                text: "No archived battles yet."
                color: root.theme.textSecondary
                font.pixelSize: 12
            }
        }
    }
}
