import QtQuick 2.15
import QtQuick.Controls 2.15

TextField {
    id: root

    Theme {
        id: theme
    }

    implicitHeight: theme.controlHeightRegular
    padding: theme.spacingSm
    color: enabled ? theme.textPrimary : theme.textDisabled
    placeholderTextColor: theme.textMuted
    selectByMouse: true
    selectionColor: theme.brandPrimary
    selectedTextColor: theme.textOnAccent

    background: Rectangle {
        radius: theme.radiusMd
        color: root.enabled ? theme.inputBackground : theme.inputBackgroundDisabled
        border.width: root.activeFocus ? 2 : 1
        border.color: root.activeFocus ? theme.inputBorderFocus : (root.enabled ? theme.inputBorder : theme.controlDisabledBorder)

        Behavior on color {
            ColorAnimation { duration: 120 }
        }
        Behavior on border.color {
            ColorAnimation { duration: 120 }
        }
    }
}
