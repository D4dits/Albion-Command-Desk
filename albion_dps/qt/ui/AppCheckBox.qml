import QtQuick 2.15
import QtQuick.Controls 2.15

CheckBox {
    id: root

    Theme {
        id: theme
    }

    spacing: theme.spacingSm

    indicator: Rectangle {
        implicitWidth: 18
        implicitHeight: 18
        radius: 4
        x: root.leftPadding
        y: (root.height - height) / 2
        color: !root.enabled
            ? theme.controlDisabledBackground
            : (root.checked ? theme.buttonPrimaryBackground : theme.surfaceInteractive)
        border.width: root.activeFocus ? 2 : 1
        border.color: root.activeFocus
            ? theme.borderFocus
            : (!root.enabled ? theme.controlDisabledBorder : (root.checked ? theme.buttonPrimaryPressed : theme.borderSubtle))

        Rectangle {
            anchors.centerIn: parent
            visible: root.checkState !== Qt.Unchecked
            width: 9
            height: 9
            radius: 2
            color: root.checkState === Qt.PartiallyChecked ? theme.textOnAccent : "#ffffff"
            opacity: root.enabled ? 1.0 : 0.55
        }
    }

    contentItem: Text {
        text: root.text
        color: root.enabled ? theme.textSecondary : theme.textDisabled
        verticalAlignment: Text.AlignVCenter
        leftPadding: root.indicator.width + root.spacing
        elide: Text.ElideRight
        font.pixelSize: 12
    }
}
