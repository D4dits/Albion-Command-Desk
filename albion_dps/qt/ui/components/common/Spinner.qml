import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme access

/**
 * Spinner - Circular loading spinner
 *
 * Features:
 * - Rotating circular spinner
 * - Multiple size options (xs, sm, md, lg, xl)
 * - Customizable color
 * - Optional label
 * - Smooth animations
 *
 * Usage:
 *   Spinner {
 *       size: "md"  // xs, sm, md, lg, xl
 *       active: true
 *       label: "Loading..."
 *   }
 */
RowLayout {
    id: root
    spacing: 12

    // Public properties
    property bool active: true
    property string size: "md"  // xs, sm, md, lg, xl
    property color spinnerColor: theme.brandPrimary
    property string label: ""

    // Access to theme
    property var theme: null

    // Size mappings
    readonly property int sizeXs: 16
    readonly property int sizeSm: 24
    readonly property int sizeMd: 32
    readonly property int sizeLg: 48
    readonly property int sizeXl: 64

    readonly property int currentSize: {
        switch (size.toLowerCase()) {
            case "xs": return sizeXs
            case "sm": return sizeSm
            case "md": return sizeMd
            case "lg": return sizeLg
            case "xl": return sizeXl
            default: return sizeMd
        }
    }

    readonly property int lineThickness: Math.max(2, currentSize / 8)

    // Spinner container
    Item {
        id: spinnerContainer
        Layout.alignment: Qt.AlignCenter
        width: root.currentSize
        height: root.currentSize
        visible: root.active
        opacity: root.active ? 1.0 : 0.0

        Behavior on opacity {
            NumberAnimation {
                duration: 150
                easing.type: Easing.OutCubic
            }
        }

        // Circular spinner using rotating dashes
        Repeater {
            model: 8

            Rectangle {
                id: dash
                width: root.lineThickness
                height: root.currentSize / 4
                radius: root.lineThickness / 2
                color: root.spinnerColor
                opacity: {
                    var baseOpacity = 0.2 + 0.8 * (index / 8)
                    return baseOpacity
                }
                x: spinnerContainer.width / 2
                y: spinnerContainer.height / 2 - height / 2 - root.currentSize / 3
                transformOrigin: Item.Center


                transform: Rotation {
                    angle: index * 45
                }

                // Fade animation
                SequentialAnimation on opacity {
                    loops: Animation.Infinite
                    running: root.active
                    NumberAnimation { to: 0.2; duration: 400; easing.type: Easing.InOutQuad }
                    NumberAnimation { to: 1.0; duration: 400; easing.type: Easing.InOutQuad }
                }

                // Scale animation for "breathing" effect
                SequentialAnimation on scale {
                    loops: Animation.Infinite
                    running: root.active
                    NumberAnimation { to: 0.8; duration: 400; easing.type: Easing.InOutQuad }
                    NumberAnimation { to: 1.2; duration: 400; easing.type: Easing.InOutQuad }
                }
            }
        }

        // Continuous rotation
        RotationAnimation on rotation {
            from: 0
            to: 360
            duration: 1000
            loops: Animation.Infinite
            running: root.active
            easing.type: Easing.Linear
        }
    }

    // Optional label
    Text {
        id: spinnerLabel
        visible: root.label.length > 0
        text: root.label
        color: theme.textPrimary
        font.pixelSize: 12
        Layout.alignment: Qt.AlignVCenter
    }
}
