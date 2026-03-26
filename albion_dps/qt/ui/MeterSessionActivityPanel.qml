import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

CardPanel {
    id: root

    property var theme: null
    property var activityModel: null
    implicitHeight: Math.max(124, activityContent.implicitHeight + 24)

    ColumnLayout {
        id: activityContent
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        Text {
            text: "Session activity"
            color: root.theme.textPrimary
            font.pixelSize: 13
            font.bold: true
        }

        ListView {
            id: activityList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: root.activityModel

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Rectangle {
                width: ListView.view.width
                height: Math.max(44, content.implicitHeight + 10)
                radius: 6
                color: index % 2 === 0 ? root.theme.tableRowEven : root.theme.tableRowOdd
                border.color: root.theme.tableDivider
                border.width: 1

                ColumnLayout {
                    id: content
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 2

                    Text {
                        Layout.fillWidth: true
                        text: model.title
                        color: root.theme.textPrimary
                        font.pixelSize: 12
                        font.bold: true
                        elide: Text.ElideRight
                    }

                    Text {
                        Layout.fillWidth: true
                        text: model.meta
                        color: root.theme.textSecondary
                        font.pixelSize: 11
                        elide: Text.ElideRight
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: activityList.count === 0
                text: "No session activity yet."
                color: root.theme.textSecondary
                font.pixelSize: 12
            }
        }
    }
}
