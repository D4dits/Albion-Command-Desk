import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for Theme and AppButton access

TableSurface {
    id: root
    level: 1

    property string currentMode: "battle"
    property string currentSortKey: "dps"
    property bool manualActive: false
    property var theme: null
    signal modeChanged(string mode)
    signal sortKeyChanged(string sortKey)
    signal toggleManual()
    signal copyCurrent(bool full)

    implicitHeight: controlsColumn.implicitHeight + 16

    ColumnLayout {
        id: controlsColumn
        anchors.fill: parent
        anchors.margins: 8
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                Layout.preferredWidth: 38
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

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                Layout.preferredWidth: 38
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

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                Layout.preferredWidth: 38
                text: "Actions:"
                color: root.theme.textMuted
                font.pixelSize: 11
            }

            AppButton {
                visible: root.currentMode === "manual"
                text: root.manualActive ? "Stop" : "Start"
                compact: true
                variant: root.manualActive ? "danger" : "primary"
                onClicked: root.toggleManual()
            }
            AppButton {
                text: "Copy short"
                compact: true
                onClicked: root.copyCurrent(false)
            }
            AppButton {
                text: "Copy full"
                compact: true
                onClicked: root.copyCurrent(true)
            }
        }
    }
}
