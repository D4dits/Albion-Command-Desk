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
    signal exportHistoryTxt()
    signal exportHistoryCsv()
    signal exportHistoryJson()
    signal copySessionCompare()
    signal exportSessionCompare()
    property bool sessionCompareAvailable: false
    property string sessionCompareTitle: ""
    property string sessionCompareText: ""

    // Access to theme and helpers (injected by parent)
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property real preservedContentY: 0

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

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            AppButton {
                text: "TXT"
                compact: true
                implicitHeight: 28
                onClicked: root.exportHistoryTxt()
            }

            AppButton {
                text: "CSV"
                compact: true
                implicitHeight: 28
                onClicked: root.exportHistoryCsv()
            }

            AppButton {
                text: "JSON"
                compact: true
                implicitHeight: 28
                onClicked: root.exportHistoryJson()
            }

            Item { Layout.fillWidth: true }
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
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Rectangle {
                id: historyRow
                width: Math.max(0, ListView.view.width - 6)
                height: Math.max(98, historyRowContent.implicitHeight + 16)
                radius: 6
                clip: true
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
                    id: historyRowContent
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: label
                            Layout.fillWidth: true
                            color: textColor
                            font.pixelSize: 12
                            font.bold: true
                            elide: Text.ElideRight
                        }
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
                        Layout.fillWidth: true
                        color: root.theme.tableTextSecondary
                        font.pixelSize: 11
                        elide: Text.ElideRight
                    }
                    Text {
                        text: players
                        Layout.fillWidth: true
                        color: root.theme.tableTextPrimary
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                        maximumLineCount: 3
                        clip: true
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

        Rectangle {
            visible: root.sessionCompareAvailable
            Layout.fillWidth: true
            radius: 6
            color: root.theme.surfaceElevated
            border.color: root.theme.tableDivider
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: root.sessionCompareTitle
                        Layout.fillWidth: true
                        color: textColor
                        font.pixelSize: 12
                        font.bold: true
                        elide: Text.ElideRight
                    }

                    AppButton {
                        text: "Copy"
                        compact: true
                        implicitHeight: 26
                        onClicked: root.copySessionCompare()
                    }

                    AppButton {
                        text: "Export"
                        compact: true
                        implicitHeight: 26
                        onClicked: root.exportSessionCompare()
                    }
                }

                Text {
                    text: root.sessionCompareText
                    Layout.fillWidth: true
                    color: root.theme.tableTextPrimary
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }
        }
    }

    Connections {
        target: root.historyModel

        function onModelAboutToBeReset() {
            root.preservedContentY = historyList.contentY
        }

        function onModelReset() {
            Qt.callLater(function() {
                var maxContentY = Math.max(0, historyList.contentHeight - historyList.height)
                historyList.contentY = Math.min(root.preservedContentY, maxContentY)
            })
        }
    }
}
