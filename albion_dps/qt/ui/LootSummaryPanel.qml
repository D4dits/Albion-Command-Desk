import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root

    property var theme
    property string title: ""
    property string emptyText: ""
    property string accentMode: "neutral"
    property var model: null
    property string valueSuffix: "x"

    function panelBorderColor() {
        if (accentMode === "items") {
            return theme.stateSuccess
        }
        if (accentMode === "silver") {
            return theme.stateWarning
        }
        return theme.borderStrong
    }

    function rowBackground() {
        if (accentMode === "items") {
            return "#102016"
        }
        if (accentMode === "silver") {
            return "#221c0e"
        }
        return theme.surfaceInteractive
    }

    function rowBorderColor() {
        if (accentMode === "items") {
            return "#264c31"
        }
        if (accentMode === "silver") {
            return "#6b5420"
        }
        return theme.borderSubtle
    }

    function valueColor() {
        if (accentMode === "items") {
            return theme.stateSuccess
        }
        if (accentMode === "silver") {
            return theme.brandWarmAccent
        }
        return theme.textPrimary
    }

    radius: theme.radiusLg
    color: theme.surfacePanel
    border.color: panelBorderColor()
    clip: true
    implicitHeight: 206

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        Text {
            text: root.title
            color: theme.textPrimary
            font.pixelSize: 14
            font.bold: true
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: summaryList
                anchors.fill: parent
                clip: true
                spacing: 6
                model: root.model

                delegate: Rectangle {
                    required property string label
                    required property string sublabel
                    required property int quantity
                    required property int eventCount

                    width: summaryList.width
                    height: 52
                    radius: theme.radiusLg
                    color: root.rowBackground()
                    border.color: root.rowBorderColor()

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                text: label
                                color: theme.textPrimary
                                font.pixelSize: 12
                                elide: Text.ElideRight
                            }

                            Text {
                                text: sublabel
                                visible: sublabel.length > 0
                                color: theme.textMuted
                                font.pixelSize: 10
                                elide: Text.ElideRight
                            }
                        }

                        ColumnLayout {
                            spacing: 1

                            Text {
                                text: valueSuffix.length > 0 ? (quantity + valueSuffix) : String(quantity)
                                color: root.valueColor()
                                font.pixelSize: 12
                                font.bold: true
                            }

                            Text {
                                text: eventCount + " ev"
                                color: theme.textMuted
                                font.pixelSize: 10
                            }
                        }
                    }
                }

                ScrollBar.vertical: ScrollBar {}
            }

            Item {
                anchors.fill: parent
                visible: summaryList.count === 0

                Text {
                    anchors.centerIn: parent
                    text: root.emptyText
                    color: theme.textSecondary
                    font.pixelSize: 12
                }
            }
        }
    }
}
