import QtQuick 2.15

Rectangle {
    id: root

    property int level: 0
    property color fillColor: level > 0 ? Theme.surfaceInteractive : Theme.surfaceInset
    property color strokeColor: level > 0 ? Theme.borderStrong : Theme.borderSubtle
    property int cornerRadius: Theme.radiusMd
    property bool showTopRule: true


    color: fillColor
    radius: cornerRadius
    border.color: strokeColor
    border.width: 1

    Behavior on color {
        ColorAnimation {
            duration: Theme.motionNormalMs
        }
    }

    Behavior on border.color {
        ColorAnimation {
            duration: Theme.motionNormalMs
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
