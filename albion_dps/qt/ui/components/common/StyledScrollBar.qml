import QtQuick 2.15
import QtQuick.Controls 2.15
import "../../." // for Theme access

/**
 * StyledScrollBar - Custom styled scrollbar that matches the application theme
 *
 * Features:
 * - Thin, modern scrollbar design
 * - Appears on hover with smooth fade-in
 * - Customizable colors through theme
 * - Smooth scroll behavior
 * - Minimal visual footprint
 *
 * Usage:
 *   ScrollView {
 *       ScrollBar.vertical: StyledScrollBar {
 *           policy: ScrollBar.AsNeeded
 *       }
 *       // content...
 *   }
 *
 * Or as a standalone:
 *   StyledScrollBar {
 *       id: vbar
 *       orientation: Qt.Vertical
 *       size: 0.3
 *       position: 0.2
 *   }
 */
ScrollBar {
    id: root

    // Access to theme
    property var theme: Theme {}

    // Scrollbar appearance
    contentItem: Rectangle {
        id: thumb
        implicitWidth: root.interactive ? 10 : 6
        implicitHeight: root.interactive ? 10 : 6
        radius: width / 2

        // Color based on interaction state
        color: {
            if (!root.interactive) return "transparent"
            if (root.pressed) return root.theme.scrollbarThumbPressed
            if (root.hovered) return root.theme.scrollbarThumbHover
            return root.theme.scrollbarThumb
        }

        // Smooth opacity transitions
        opacity: {
            if (!root.interactive) return 0
            if (root.active) return 1.0
            return root.hovered ? 0.8 : 0.3
        }

        Behavior on opacity {
            NumberAnimation {
                duration: 150
                easing.type: Easing.OutCubic
            }
        }

        Behavior on color {
            ColorAnimation {
                duration: 100
                easing.type: Easing.OutCubic
            }
        }

        Behavior on implicitWidth {
            NumberAnimation {
                duration: 150
                easing.type: Easing.OutCubic
            }
        }

        Behavior on implicitHeight {
            NumberAnimation {
                duration: 150
                easing.type: Easing.OutCubic
            }
        }
    }

    // Background (track) - minimal
    background: Rectangle {
        implicitWidth: root.interactive ? 12 : 0
        implicitHeight: root.interactive ? 12 : 0
        color: root.interactive ? root.theme.scrollbarTrack : "transparent"
        opacity: root.hovered || root.active ? 0.5 : 0.3

        Behavior on opacity {
            NumberAnimation {
                duration: 150
                easing.type: Easing.OutCubic
            }
        }

        Behavior on implicitWidth {
            NumberAnimation {
                duration: 150
                easing.type: Easing.OutCubic
            }
        }

        Behavior on implicitHeight {
            NumberAnimation {
                duration: 150
                easing.type: Easing.OutCubic
            }
        }
    }
}
