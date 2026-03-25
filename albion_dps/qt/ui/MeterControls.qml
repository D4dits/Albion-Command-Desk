import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for Theme and AppButton access

TableSurface {
    id: root
    level: 1

    property string currentMode: "battle"
    property string currentSortKey: "dps"
    property var theme: null
    property bool veryCompact: width < 520

    signal modeChanged(string mode)
    signal sortKeyChanged(string sortKey)

    implicitHeight: controlsColumn.implicitHeight + 16

    ColumnLayout {
        id: controlsColumn
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        Flow {
            Layout.fillWidth: true
            spacing: 8

            Text {
                height: 24
                text: "Mode:"
                color: root.theme.textMuted
                font.pixelSize: 11
                verticalAlignment: Text.AlignVCenter
            }

            AppButton {
                text: "Battle"
                compact: true
                implicitHeight: 24
                implicitWidth: 62
                variant: checked ? "primary" : "secondary"
                checkable: true
                checked: root.currentMode === "battle"
                onClicked: root.modeChanged("battle")
            }
            AppButton {
                text: "Zone"
                compact: true
                implicitHeight: 24
                implicitWidth: 56
                variant: checked ? "primary" : "secondary"
                checkable: true
                checked: root.currentMode === "zone"
                onClicked: root.modeChanged("zone")
            }
            AppButton {
                text: "Manual"
                compact: true
                implicitHeight: 24
                implicitWidth: 64
                variant: checked ? "primary" : "secondary"
                checkable: true
                checked: root.currentMode === "manual"
                onClicked: root.modeChanged("manual")
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: 8

            Text {
                height: 24
                text: "Sort:"
                color: root.theme.textMuted
                font.pixelSize: 11
                verticalAlignment: Text.AlignVCenter
            }

            AppButton {
                text: "DPS"
                compact: true
                implicitHeight: 24
                implicitWidth: 56
                variant: checked ? "primary" : "secondary"
                checkable: true
                checked: root.currentSortKey === "dps"
                onClicked: root.sortKeyChanged("dps")
            }
            AppButton {
                text: "DMG"
                compact: true
                implicitHeight: 24
                implicitWidth: 56
                variant: checked ? "primary" : "secondary"
                checkable: true
                checked: root.currentSortKey === "dmg"
                onClicked: root.sortKeyChanged("dmg")
            }
            AppButton {
                text: "HPS"
                compact: true
                implicitHeight: 24
                implicitWidth: 56
                variant: checked ? "primary" : "secondary"
                checkable: true
                checked: root.currentSortKey === "hps"
                onClicked: root.sortKeyChanged("hps")
            }
            AppButton {
                text: "HEAL"
                compact: true
                implicitHeight: 24
                implicitWidth: 60
                variant: checked ? "primary" : "secondary"
                checkable: true
                checked: root.currentSortKey === "heal"
                onClicked: root.sortKeyChanged("heal")
            }
        }
    }
}
