import QtQuick 2.15
import QtQuick.Controls 2.15

TabButton {
    id: root

    property color activeColor: "#4aa3ff"
    property color inactiveColor: "#0f1620"
    property color activeTextColor: "#0b0f14"
    property color inactiveTextColor: "#e6edf3"
    property color borderColor: "#1f2a37"
    property int cornerRadius: 5
    property int labelPixelSize: 12
    property bool labelBold: true

    height: parent ? parent.height : implicitHeight

    background: Rectangle {
        radius: root.cornerRadius
        color: root.checked ? root.activeColor : root.inactiveColor
        border.color: root.checked ? root.activeColor : root.borderColor
    }

    contentItem: Text {
        text: root.text
        color: root.checked ? root.activeTextColor : root.inactiveTextColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: root.labelPixelSize
        font.bold: root.labelBold
        elide: Text.ElideRight
    }
}
