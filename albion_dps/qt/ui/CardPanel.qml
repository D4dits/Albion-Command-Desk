import QtQuick 2.15

Rectangle {
    id: root

    property color fillColor: "#131a22"
    property color strokeColor: "#1f2a37"
    property int cornerRadius: 8

    color: fillColor
    radius: cornerRadius
    border.color: strokeColor
    border.width: 1
}
