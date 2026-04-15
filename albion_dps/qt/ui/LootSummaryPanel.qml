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

    function formatValue(value) {
        var number = Number(value)
        if (!isFinite(number)) {
            return "0"
        }
        var absValue = Math.abs(number)
        if (absValue >= 1000000000) {
            return (number / 1000000000).toFixed(1) + "B"
        }
        if (absValue >= 1000000) {
            return (number / 1000000).toFixed(1) + "M"
        }
        if (absValue >= 1000) {
            return (number / 1000).toFixed(1) + "k"
        }
        return String(Math.round(number))
    }

    function panelBorderColor() {
        if (accentMode === "items") {
            return theme.stateSuccess
        }
        if (accentMode === "silver") {
            return theme.stateWarning
        }
        if (accentMode === "danger") {
            return theme.stateDanger
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
        if (accentMode === "danger") {
            return theme.stateDangerBg
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
        if (accentMode === "danger") {
            return theme.stateDanger
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
        if (accentMode === "danger") {
            return theme.stateDanger
        }
        return theme.textPrimary
    }

    radius: theme.radiusLg
    color: theme.surfacePanel
    border.color: panelBorderColor()
    clip: true
    implicitHeight: 172

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 5

        Text {
            text: root.title
            color: theme.textPrimary
            font.pixelSize: 13
            font.bold: true
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: summaryList
                anchors.fill: parent
                clip: true
                spacing: 4
                model: root.model
                reuseItems: true
                cacheBuffer: 360

                delegate: Rectangle {
                    required property string label
                    required property string sublabel
                    required property string iconUrl
                    required property int quantity
                    required property int eventCount

                    width: summaryList.width
                    height: 44
                    radius: theme.radiusLg
                    color: root.rowBackground()
                    border.color: root.rowBorderColor()
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 7
                        spacing: 6

                        Item {
                            width: iconUrl.length > 0 ? 28 : 0
                            height: 28
                            visible: iconUrl.length > 0

                            Rectangle {
                                anchors.fill: parent
                                radius: 6
                                color: theme.surfaceRaised
                                border.color: theme.borderSubtle

                                Image {
                                    anchors.fill: parent
                                    anchors.margins: 2
                                    source: iconUrl
                                    fillMode: Image.PreserveAspectFit
                                    asynchronous: true
                                    cache: true
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1

                            Text {
                                text: label
                                color: theme.textPrimary
                                font.pixelSize: 10
                                elide: Text.ElideRight
                            }

                            Text {
                                text: sublabel
                                visible: sublabel.length > 0
                                color: theme.textMuted
                                font.pixelSize: 8
                                elide: Text.ElideRight
                            }
                        }

                        ColumnLayout {
                            Layout.preferredWidth: 64
                            Layout.alignment: Qt.AlignRight
                            spacing: 1

                            Text {
                                text: valueSuffix.length > 0 ? (root.formatValue(quantity) + valueSuffix) : root.formatValue(quantity)
                                color: root.valueColor()
                                font.pixelSize: 10
                                font.bold: true
                                horizontalAlignment: Text.AlignRight
                                width: parent.width
                            }

                            Text {
                                text: eventCount + " ev"
                                color: theme.textMuted
                                font.pixelSize: 8
                                horizontalAlignment: Text.AlignRight
                                width: parent.width
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
