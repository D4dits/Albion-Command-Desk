import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Rectangle {
    id: root
    objectName: "meterHistoryChart"

    property var theme: null
    property var playersModel: null
    property string sortKey: "dps"

    implicitHeight: 142
    radius: 6
    color: theme.cardLevel2
    border.color: theme.borderStrong
    border.width: 1
    clip: true

    function metricLabel() {
        if (sortKey === "dmg") return "DMG"
        if (sortKey === "heal") return "HEAL"
        if (sortKey === "hps") return "HPS"
        return "DPS"
    }

    function metricValue(damageValue, healValue, dpsValue, hpsValue) {
        if (sortKey === "dmg") return Number(damageValue)
        if (sortKey === "heal") return Number(healValue)
        if (sortKey === "hps") return Number(hpsValue)
        return Number(dpsValue)
    }

    function compactNumber(value) {
        var amount = Number(value)
        if (!isFinite(amount)) return "0"
        if (Math.abs(amount) >= 1000000) return (amount / 1000000).toFixed(1) + "m"
        if (Math.abs(amount) >= 1000) return (amount / 1000).toFixed(1) + "k"
        return amount.toFixed(sortKey === "dps" || sortKey === "hps" ? 1 : 0)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 5

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "Selected fight"
                Layout.fillWidth: true
                color: root.theme.textPrimary
                font.pixelSize: 12
                font.bold: true
            }
            Text {
                text: root.metricLabel()
                color: root.theme.brandPrimary
                font.pixelSize: 10
                font.bold: true
            }
        }

        ListView {
            id: chartRows
            objectName: "meterHistoryChartRows"
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: root.playersModel
            clip: true
            spacing: 3
            boundsBehavior: Flickable.StopAtBounds

            delegate: Item {
                id: chartRow
                width: ListView.view.width
                height: 20

                readonly property real metricAmount: root.metricValue(damage, heal, dps, hps)

                RowLayout {
                    anchors.fill: parent
                    spacing: 6

                    Text {
                        Layout.preferredWidth: 84
                        Layout.maximumWidth: 84
                        text: name
                        color: root.theme.tableTextPrimary
                        font.pixelSize: 10
                        elide: Text.ElideRight
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 9
                        radius: 3
                        color: root.theme.cardLevel0

                        Rectangle {
                            height: parent.height
                            width: parent.width * Math.max(0, Math.min(1, Number(barRatio)))
                            radius: parent.radius
                            color: barColor
                        }
                    }

                    Text {
                        Layout.preferredWidth: 48
                        horizontalAlignment: Text.AlignRight
                        text: root.compactNumber(chartRow.metricAmount)
                        color: root.theme.textSecondary
                        font.pixelSize: 9
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: chartRows.count === 0
                text: "No player data"
                color: root.theme.textMuted
                font.pixelSize: 10
            }
        }
    }
}
