import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme and AppButton access

/**
 * MeterControls - Control bar for mode and sort selection
 *
 * Provides buttons for:
 * - Mode selection: Battle, Zone, Manual
 * - Sort key selection: DPS, DMG, HPS, HEAL
 */
TableSurface {
    id: root
    level: 1
    implicitHeight: 62

    // Properties to bind to parent state
    property string currentMode: "battle"
    property string currentSortKey: "dps"

    // Signals to notify parent of changes
    signal modeChanged(string mode)
    signal sortKeyChanged(string sortKey)

    // Access to theme (injected by parent)
    property var theme: Theme {}

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 6
        spacing: 6

        RowLayout {
            spacing: 8
            Layout.fillWidth: true

            Text {
                text: "Mode:"
                color: root.theme.textMuted
                font.pixelSize: 11
            }
            AppButton {
                id: battleButton
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
                id: zoneButton
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
                id: manualButton
                text: "Manual"
                compact: true
                implicitHeight: 24
                implicitWidth: 64
                variant: checked ? "primary" : "secondary"
                checkable: true
                checked: root.currentMode === "manual"
                onClicked: root.modeChanged("manual")
            }
            Item { Layout.fillWidth: true }
            Text {
                text: "Sort:"
                color: root.theme.textMuted
                font.pixelSize: 11
            }
            AppButton {
                id: sortDpsButton
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
                id: sortDmgButton
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
                id: sortHpsButton
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
                id: sortHealButton
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
