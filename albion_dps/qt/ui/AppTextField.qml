import QtQuick 2.15
import QtQuick.Controls 2.15
import "." // for Theme access

TextField {
    id: root


    implicitHeight: Theme.controlHeightRegular
    focusPolicy: Qt.StrongFocus
    padding: Theme.spacingSm
    color: enabled ? Theme.textPrimary : Theme.textDisabled
    placeholderTextColor: Theme.textMuted
    selectByMouse: true
    selectionColor: Theme.brandPrimary
    selectedTextColor: Theme.textOnAccent

    background: Rectangle {
        radius: Theme.radiusMd
        color: root.enabled ? Theme.inputBackground : Theme.inputBackgroundDisabled
        border.width: root.activeFocus ? Theme.focusRingWidth : 1
        border.color: root.activeFocus ? Theme.inputBorderFocus : (root.enabled ? Theme.inputBorder : Theme.controlDisabledBorder)

        Behavior on color {
            ColorAnimation { duration: 120 }
        }
        Behavior on border.color {
            ColorAnimation { duration: 120 }
        }
    }
}
