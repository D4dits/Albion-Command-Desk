import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme access

/**
 * ProgressBar - Linear progress indicator
 *
 * Features:
 * - Horizontal progress bar with smooth animations
 * - Optional label with percentage
 * - Optional status text
 * - Customizable colors
 * - Determinate and indeterminate modes
 *
 * Usage:
 *   ProgressBar {
 *       value: 0.75  // 0-1
 *       showLabel: true
 *       labelText: "Loading..."
 *   }
 */
RowLayout {
    id: root
    spacing: 12

    // Public properties
    property real value: 0.0  // 0-1
    property bool indeterminate: false
    property bool showLabel: true
    property string labelText: ""
    property int barHeight: 6
    property int barWidth: 200
    property bool showPercentage: true

    // Access to theme
    property var theme: Theme {}
    property color color: theme.brandPrimary
    property color bgColor: theme.surfaceInset
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    // Computed width for the bar
    readonly property int computedBarWidth: showLabel ? -1 : barWidth

    // Optional label text
    Text {
        id: label
        visible: showLabel && labelText.length > 0
        text: labelText
        color: textColor
        font.pixelSize: 12
        elide: Text.ElideRight
        Layout.maximumWidth: 150
    }

    // Progress bar container
    Rectangle {
        id: barContainer
        Layout.preferredWidth: root.computedBarWidth >= 0 ? root.computedBarWidth : barWidth
        Layout.preferredHeight: barHeight
        Layout.fillWidth: root.computedBarWidth < 0
        radius: barHeight / 2
        color: bgColor

        // Progress fill
        Rectangle {
            id: barFill
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: root.indeterminate ? parent.width / 3 : (parent.width * Math.max(0, Math.min(1, value)))
            radius: parent.radius
            color: root.color

            // Smooth animation for value changes
            Behavior on width {
                NumberAnimation {
                    duration: 200
                    easing.type: Easing.OutCubic
                }
            }

            // Indeterminate animation
            NumberAnimation on x {
                from: -barContainer.width
                to: barContainer.width
                duration: 1000
                loops: Animation.Infinite
                running: root.indeterminate
                easing.type: Easing.Linear
            }

            // Shimmer effect for indeterminate
            ShaderEffect {
                anchors.fill: parent
                visible: root.indeterminate
                opacity: 0.3

                fragmentShader: "
                    #version 440
                    layout(location = 0) in vec2 qt_TexCoord0;
                    layout(location = 0) out vec4 fragColor;
                    uniform float time;
                    void main() {
                        vec2 pos = qt_TexCoord0;
                        float shimmer = sin(pos.x * 3.14159 * 2.0 + time) * 0.5 + 0.5;
                        fragColor = vec4(1.0, 1.0, 1.0, shimmer);
                    }
                "

                property real time: 0
                NumberAnimation on time {
                    from: 0
                    to: 6.28318  // 2 * PI
                    duration: 1000
                    loops: Animation.Infinite
                    running: root.indeterminate
                }
            }
        }
    }

    // Percentage text
    Text {
        id: percentage
        visible: showPercentage && !root.indeterminate
        text: Math.round(root.value * 100) + "%"
        color: mutedColor
        font.pixelSize: 12
        Layout.preferredWidth: 40
    }

    // Indeterminate indicator
    Text {
        id: indeterminateText
        visible: root.indeterminate
        text: "..."
        color: mutedColor
        font.pixelSize: 12
    }
}
