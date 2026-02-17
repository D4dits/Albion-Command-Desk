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
    scale: root.pressed ? 0.99 : 1.0
    hoverEnabled: true

    Behavior on scale {
        NumberAnimation {
            duration: Theme.motionFastMs
            easing.type: Easing.OutCubic
        }
    }

    background: Rectangle {
        id: tabBg
        radius: root.cornerRadius
        color: "transparent"
        border.width: root.checked || root.hovered ? 1 : 1
        border.color: root.checked ? Qt.darker(root.activeColor, 1.15) : (root.hovered ? "#35516f" : root.borderColor)

        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: root.checked
                    ? Qt.lighter(root.activeColor, 1.08)
                    : (root.hovered ? "#18263a" : "#111b2a")
            }
            GradientStop {
                position: 1.0
                color: root.checked
                    ? Qt.darker(root.activeColor, 1.06)
                    : (root.hovered ? "#132235" : root.inactiveColor)
            }
        }

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
    }

    contentItem: Text {
        id: tabLabel
        text: root.text
        color: root.checked ? "#07121f" : (root.hovered ? "#f0f6ff" : root.inactiveTextColor)
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: root.labelPixelSize
        font.bold: root.labelBold
        elide: Text.ElideRight

        Behavior on color {
            ColorAnimation {
                duration: Theme.motionNormalMs
            }
        }
    }
}
