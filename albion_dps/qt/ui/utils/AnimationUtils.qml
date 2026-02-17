import QtQuick 2.15

/**
 * AnimationUtils - Reusable animation definitions and utilities
 *
 * Provides common animation behaviors that can be used across components.
 * All animations are designed to be smooth and respect performance.
 *
 * Usage:
 *   Behavior on opacity { AnimationUtils.fadeBehavior }
 *   Behavior on scale { AnimationUtils.scaleBehavior }
 *   AnimationUtils.fadeIn(target)
 *   AnimationUtils.slideIn(target, "left")
 */

pragma Singleton

QtObject {
    // Animation durations (in ms)
    readonly property int durationInstant: 0
    readonly property int durationFast: 100
    readonly property int durationNormal: 150
    readonly property int durationSlow: 200
    readonly property int durationSlower: 300

    // Easing functions
    readonly property var easingOut: Easing.OutCubic
    readonly property var easingIn: Easing.InCubic
    readonly property var easingInOut: Easing.InOutCubic
    readonly property var easingOutBack: Easing.OutBack
    readonly property var easingOutQuad: Easing.OutQuad
    readonly property var easingLinear: Easing.Linear

    // Fade behaviors
    readonly property var fadeBehavior: Behavior {
        NumberAnimation {
            duration: AnimationUtils.durationNormal
            easing.type: AnimationUtils.easingOut
        }
    }

    readonly property var fadeBehaviorFast: Behavior {
        NumberAnimation {
            duration: AnimationUtils.durationFast
            easing.type: AnimationUtils.easingOut
        }
    }

    // Scale behaviors
    readonly property var scaleBehavior: Behavior {
        NumberAnimation {
            duration: AnimationUtils.durationNormal
            easing.type: AnimationUtils.easingOut
        }
    }

    readonly property var scaleBehaviorSpring: Behavior {
        NumberAnimation {
            duration: AnimationUtils.durationSlow
            easing.type: AnimationUtils.easingOutBack
            easing.overshoot: 1.2
        }
    }

    // Color behaviors
    readonly property var colorBehavior: Behavior {
        ColorAnimation {
            duration: AnimationUtils.durationNormal
            easing.type: AnimationUtils.easingOut
        }
    }

    // Rotation behaviors
    readonly property var rotationBehavior: Behavior {
        NumberAnimation {
            duration: AnimationUtils.durationSlow
            easing.type: AnimationUtils.easingOut
        }
    }

    // Position/translation behaviors
    readonly property var positionBehavior: Behavior {
        NumberAnimation {
            duration: AnimationUtils.durationNormal
            easing.type: AnimationUtils.easingOut
        }
    }

    // Hover scale effect for buttons
    readonly property real hoverScale: 1.03
    readonly property real pressScale: 0.97

    // Opacity values for different states
    readonly property real opacityHover: 1.0
    readonly property real opacityNormal: 0.85
    readonly property real opacityDisabled: 0.4
    readonly property real opacityHidden: 0.0
}
