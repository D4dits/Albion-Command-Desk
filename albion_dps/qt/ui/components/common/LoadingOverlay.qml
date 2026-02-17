import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme access

/**
 * LoadingOverlay - Full-screen loading overlay with spinner and message
 *
 * Features:
 * - Semi-transparent dark overlay
 * - Centered content with spinner
 * - Optional message text
 * - Optional progress percentage
 * - Smooth fade in/out animations
 *
 * Usage:
 *   LoadingOverlay {
 *       id: loadingOverlay
 *       visible: loading
 *       message: "Loading data..."
 *       progress: 0.75  // Optional: 0-1 for percentage
 *   }
 */
Rectangle {
    id: root
    anchors.fill: parent
    visible: false
    color: theme.surfaceOverlay
    opacity: active ? 0.9 : 0.0

    // Public properties
    property bool active: false
    property string message: ""
    property real progress: -1  // -1 = indeterminate, 0-1 = determinate

    // Access to theme
    property var theme: Theme {}

    // Signals
    signal cancelled()

    Behavior on opacity {
        NumberAnimation {
            duration: 180
            easing.type: Easing.OutCubic
        }
    }

    // Only enable interaction when active
    enabled: active

    // Mouse blocker to prevent interaction with underlying content
    MouseArea {
        anchors.fill: parent
        enabled: root.active
        onClicked: {
            // Optional: click outside to cancel
            // root.cancelled()
        }
    }

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 16

        // Loading spinner
        Item {
            id: spinnerContainer
            Layout.alignment: Qt.AlignCenter
            width: 48
            height: 48

            // Circular spinner using rotating rectangles
            Repeater {
                model: 8

                Rectangle {
                    width: 4
                    height: 12
                    radius: 2
                    x: spinnerContainer.width / 2 - width / 2
                    y: 4
                    color: theme.brandPrimary
                    opacity: 0.3 + 0.7 * (index / 8)
                    transform: Rotation {
                        angle: index * 45
                        origin.x: 2
                        origin.y: 20
                    }

                    // Rotation animation
                    SequentialAnimation on opacity {
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.2; duration: 400; easing.type: Easing.InOutQuad }
                        NumberAnimation { to: 1.0; duration: 400; easing.type: Easing.InOutQuad }
                    }

                    // Scale animation for pulsing effect
                    SequentialAnimation on scale {
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.8; duration: 400; easing.type: Easing.InOutQuad }
                        NumberAnimation { to: 1.2; duration: 400; easing.type: Easing.InOutQuad }
                    }
                }

                // Continuous rotation
                NumberAnimation on rotation {
                    from: 0
                    to: 360
                    duration: 1000
                    loops: Animation.Infinite
                    running: root.active
                }
            }
        }

        // Message text
        Text {
            id: messageText
            Layout.alignment: Qt.AlignCenter
            visible: root.message.length > 0
            text: root.message
            color: theme.textPrimary
            font.pixelSize: 14
            horizontalAlignment: Text.AlignHCenter
        }

        // Progress percentage (if determinate)
        Text {
            id: progressText
            Layout.alignment: Qt.AlignCenter
            visible: root.progress >= 0 && root.progress <= 1
            text: Math.round(root.progress * 100) + "%"
            color: theme.textSecondary
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
        }

        // Progress bar (if determinate)
        Rectangle {
            id: progressBarBg
            Layout.alignment: Qt.AlignCenter
            Layout.preferredWidth: 200
            Layout.preferredHeight: 4
            visible: root.progress >= 0 && root.progress <= 1
            radius: 2
            color: theme.surfaceInset

            Rectangle {
                id: progressBarFill
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: parent.width * root.progress
                radius: 2
                color: theme.brandPrimary

                Behavior on width {
                    NumberAnimation {
                        duration: 150
                        easing.type: Easing.OutCubic
                    }
                }
            }
        }

        // Cancel button (optional)
        AppButton {
            id: cancelButton
            Layout.alignment: Qt.AlignCenter
            visible: false  // Set to true to enable cancel
            text: "Cancel"
            variant: "secondary"
            compact: true
            onClicked: root.cancelled()
        }
    }

    // Keyboard shortcut to cancel (ESC)
    Keys.onEscapePressed: root.cancelled()
}
