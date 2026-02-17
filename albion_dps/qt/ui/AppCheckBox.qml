import QtQuick 2.15
import QtQuick.Controls 2.15

CheckBox {
    id: root


    spacing: Theme.spacingSm
    focusPolicy: Qt.StrongFocus

    indicator: Rectangle {
        implicitWidth: 18
        implicitHeight: 18
        radius: 4
        x: root.leftPadding
        y: (root.height - height) / 2
        color: !root.enabled
            ? Theme.controlDisabledBackground
            : (root.checked ? Theme.buttonPrimaryBackground : Theme.surfaceInteractive)
        border.width: root.activeFocus ? Theme.focusRingWidth : 1
        border.color: root.activeFocus
            ? Theme.borderFocus
            : (!root.enabled ? Theme.controlDisabledBorder : (root.checked ? Theme.buttonPrimaryPressed : Theme.borderSubtle))

        Rectangle {
            anchors.centerIn: parent
            visible: root.checkState !== Qt.Unchecked
            width: 9
            height: 9
            radius: 2
            color: root.checkState === Qt.PartiallyChecked ? Theme.textOnAccent : "#ffffff"
            opacity: root.enabled ? 1.0 : 0.55
        }
    }

    contentItem: Text {
        text: root.text
        color: root.enabled ? Theme.textSecondary : Theme.textDisabled
        verticalAlignment: Text.AlignVCenter
        leftPadding: root.indicator.width + root.spacing
        elide: Text.ElideRight
        font.pixelSize: 12
    }
}
