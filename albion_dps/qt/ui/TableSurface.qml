import QtQuick 2.15

Rectangle {
    id: root

    property int level: 0
    property color fillColor: level > 0 ? theme.surfaceInteractive : theme.surfaceInset
    property color strokeColor: level > 0 ? theme.borderStrong : theme.borderSubtle
    property int cornerRadius: theme.radiusMd
    property bool showTopRule: true

    Theme {
        id: theme
    }

    color: fillColor
    radius: cornerRadius
    border.color: strokeColor
    border.width: 1

    Behavior on color {
        ColorAnimation {
            duration: theme.motionNormalMs
        }
    }

    Behavior on border.color {
        ColorAnimation {
            duration: theme.motionNormalMs
        }
    }

    Rectangle {
        visible: showTopRule
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        height: 1
        color: Qt.rgba(1, 1, 1, 0.08)
    }
}
