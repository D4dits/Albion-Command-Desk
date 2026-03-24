import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for CardPanel

CardPanel {
    id: root

    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property string fameText: "0"
    property string famePerHourText: "0.0"
    property string silverText: "0"
    property string silverPerHourText: "0.0"
    property bool singleColumnLayout: width < 260

    implicitHeight: Math.max(132, statsContent.implicitHeight + 24)

    function _formatInt(text) {
        var value = Number(text)
        if (!isFinite(value)) {
            return "0"
        }
        var whole = Math.round(value)
        var sign = whole < 0 ? "-" : ""
        var raw = Math.abs(whole).toString()
        return sign + raw.replace(/\B(?=(\d{3})+(?!\d))/g, " ")
    }

    ColumnLayout {
        id: statsContent
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        Text {
            text: "Session gains"
            color: root.textColor
            font.pixelSize: 13
            font.bold: true
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.singleColumnLayout ? 1 : 2
            columnSpacing: 12
            rowSpacing: 8

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: "Fame"
                    color: root.mutedColor
                    font.pixelSize: 11
                }
                Text {
                    Layout.fillWidth: true
                    text: root._formatInt(root.fameText)
                    color: root.textColor
                    font.bold: true
                    font.pixelSize: 18
                    minimumPixelSize: 11
                    fontSizeMode: Text.Fit
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignLeft
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: "Fame / h"
                    color: root.mutedColor
                    font.pixelSize: 11
                }
                Text {
                    Layout.fillWidth: true
                    text: root._formatInt(root.famePerHourText)
                    color: root.textColor
                    font.bold: true
                    font.pixelSize: 18
                    minimumPixelSize: 11
                    fontSizeMode: Text.Fit
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignLeft
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: "Silver"
                    color: root.mutedColor
                    font.pixelSize: 11
                }
                Text {
                    Layout.fillWidth: true
                    text: root._formatInt(root.silverText)
                    color: root.textColor
                    font.bold: true
                    font.pixelSize: 18
                    minimumPixelSize: 11
                    fontSizeMode: Text.Fit
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignLeft
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    text: "Silver / h"
                    color: root.mutedColor
                    font.pixelSize: 11
                }
                Text {
                    Layout.fillWidth: true
                    text: root._formatInt(root.silverPerHourText)
                    color: root.textColor
                    font.bold: true
                    font.pixelSize: 18
                    minimumPixelSize: 11
                    fontSizeMode: Text.Fit
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignLeft
                }
            }
        }
    }
}
