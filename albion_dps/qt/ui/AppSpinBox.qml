import QtQuick 2.15
import QtQuick.Controls 2.15

SpinBox {
    id: root

    Theme {
        id: theme
    }

    implicitHeight: theme.controlHeightRegular
    editable: true
    stepSize: 1
    focusPolicy: Qt.StrongFocus

    contentItem: TextInput {
        text: root.textFromValue(root.value, root.locale)
        font: root.font
        color: root.enabled ? theme.textPrimary : theme.textDisabled
        selectionColor: theme.brandPrimary
        selectedTextColor: theme.textOnAccent
        horizontalAlignment: Qt.AlignHCenter
        verticalAlignment: Qt.AlignVCenter
        readOnly: !root.editable
        validator: root.validator
        inputMethodHints: Qt.ImhFormattedNumbersOnly
        onEditingFinished: {
            if (!root.editable) {
                return
            }
            var parsed = root.valueFromText(text, root.locale)
            if (!isNaN(parsed)) {
                root.value = parsed
            }
        }
    }

    up.indicator: Rectangle {
        implicitWidth: 20
        implicitHeight: parent ? parent.height / 2 : 12
        radius: theme.radiusSm
        color: root.up.pressed ? theme.controlPressedBackground : (root.up.hovered ? theme.controlHoverBackground : theme.surfaceInteractive)
        border.color: theme.borderSubtle
        Text {
            anchors.centerIn: parent
            text: "+"
            color: theme.textPrimary
            font.pixelSize: 12
            font.bold: true
        }
    }

    down.indicator: Rectangle {
        implicitWidth: 20
        implicitHeight: parent ? parent.height / 2 : 12
        radius: theme.radiusSm
        color: root.down.pressed ? theme.controlPressedBackground : (root.down.hovered ? theme.controlHoverBackground : theme.surfaceInteractive)
        border.color: theme.borderSubtle
        Text {
            anchors.centerIn: parent
            text: "-"
            color: theme.textPrimary
            font.pixelSize: 12
            font.bold: true
        }
    }

    background: Rectangle {
        radius: theme.radiusMd
        color: root.enabled ? theme.inputBackground : theme.inputBackgroundDisabled
        border.width: root.activeFocus ? theme.focusRingWidth : 1
        border.color: root.activeFocus ? theme.inputBorderFocus : (root.enabled ? theme.inputBorder : theme.controlDisabledBorder)
    }
}
