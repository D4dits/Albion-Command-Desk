import QtQuick 2.15
import QtQuick.Controls 2.15

SpinBox {
    id: root


    implicitHeight: Theme.controlHeightRegular
    editable: true
    stepSize: 1
    focusPolicy: Qt.StrongFocus

    contentItem: TextInput {
        text: root.textFromValue(root.value, root.locale)
        font: root.font
        color: root.enabled ? Theme.textPrimary : Theme.textDisabled
        selectionColor: Theme.brandPrimary
        selectedTextColor: Theme.textOnAccent
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
        radius: Theme.radiusSm
        color: root.up.pressed ? Theme.controlPressedBackground : (root.up.hovered ? Theme.controlHoverBackground : Theme.surfaceInteractive)
        border.color: Theme.borderSubtle
        Text {
            anchors.centerIn: parent
            text: "+"
            color: Theme.textPrimary
            font.pixelSize: 12
            font.bold: true
        }
    }

    down.indicator: Rectangle {
        implicitWidth: 20
        implicitHeight: parent ? parent.height / 2 : 12
        radius: Theme.radiusSm
        color: root.down.pressed ? Theme.controlPressedBackground : (root.down.hovered ? Theme.controlHoverBackground : Theme.surfaceInteractive)
        border.color: Theme.borderSubtle
        Text {
            anchors.centerIn: parent
            text: "-"
            color: Theme.textPrimary
            font.pixelSize: 12
            font.bold: true
        }
    }

    background: Rectangle {
        radius: Theme.radiusMd
        color: root.enabled ? Theme.inputBackground : Theme.inputBackgroundDisabled
        border.width: root.activeFocus ? Theme.focusRingWidth : 1
        border.color: root.activeFocus ? Theme.inputBorderFocus : (root.enabled ? Theme.inputBorder : Theme.controlDisabledBorder)
    }
}
