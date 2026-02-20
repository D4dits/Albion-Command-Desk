import QtQuick 2.15
import QtQuick.Controls 2.15
import "." // for Theme access

SpinBox {
    id: root

    property int sideButtonWidth: 24

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
        leftPadding: (root.down && root.down.indicator) ? (root.down.indicator.width + 6) : 8
        rightPadding: (root.up && root.up.indicator) ? (root.up.indicator.width + 6) : 8
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
        z: 2
        width: root.sideButtonWidth
        height: Math.max(18, root.availableHeight)
        radius: Theme.radiusSm
        color: root.up.pressed ? Theme.controlPressedBackground : (root.up.hovered ? Theme.controlHoverBackground : Theme.surfaceInteractive)
        border.width: 1
        border.color: Theme.borderStrong
        Text {
            anchors.fill: parent
            text: "\u002B"
            color: Theme.textPrimary
            font.pixelSize: 13
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    down.indicator: Rectangle {
        z: 2
        width: root.sideButtonWidth
        height: Math.max(18, root.availableHeight)
        radius: Theme.radiusSm
        color: root.down.pressed ? Theme.controlPressedBackground : (root.down.hovered ? Theme.controlHoverBackground : Theme.surfaceInteractive)
        border.width: 1
        border.color: Theme.borderStrong
        Text {
            anchors.fill: parent
            text: "\u2212"
            color: Theme.textPrimary
            font.pixelSize: 13
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    background: Rectangle {
        radius: Theme.radiusMd
        color: root.enabled ? Theme.inputBackground : Theme.inputBackgroundDisabled
        border.width: root.activeFocus ? Theme.focusRingWidth : 1
        border.color: root.activeFocus ? Theme.inputBorderFocus : (root.enabled ? Theme.inputBorder : Theme.controlDisabledBorder)
    }
}
