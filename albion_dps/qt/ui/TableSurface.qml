import QtQuick 2.15

Rectangle {
    id: root

    property color fillColor: "#0f1620"
    property color strokeColor: "#1f2a37"
    property int cornerRadius: 6

    color: fillColor
    radius: cornerRadius
    border.color: strokeColor
    border.width: 1
}
