import QtQuick 2.15
import "." // for Theme access
import "utils" 1.0 as Utils

/**
 * AppButton - Custom button component with full style control
 *
 * Variants:
 * - primary: Blue (#4aa3ff)
 * - secondary: Gray (#1b2a3c)
 * - ghost: Transparent with border
 * - danger: Red (#b93c47)
 * - warm: Amber (#f2c14e)
 */
Rectangle {
    id: root

    // Public properties
    property string variant: "secondary"
    property bool compact: false
    property bool checked: false
    property bool checkable: false
    property bool down: false
    property bool hovered: false
    property bool enabled: true
    property bool visualFocus: false
    property string text: ""
    property int implicitHeight: compact ? Theme.buttonHeightCompact : Theme.buttonHeightRegular
    property int implicitWidth: Math.max(64, buttonText.implicitWidth + 20)
    property int padding: compact ? Theme.spacingSm : Theme.spacingMd
    property int fontPixelSize: 12
    property bool fontBold: variant === "primary" || variant === "danger" || variant === "warm"

    // Click handling
    signal clicked()
    signal toggled(bool checked)

    // Custom colors
    property color customBackground: "transparent"
    property color customHover: "transparent"
    property color customPressed: "transparent"
    property color customTextColor: "transparent"
    property color customBorderColor: "transparent"

    readonly property color activeBg: root.colorForState(root.baseBackground(), root.hoverBackground(), root.pressedBackground())
    readonly property color activeBorder: root.colorForState(root.baseBorderColor(), root.hoverBorderColor(), root.pressedBorderColor())
    readonly property color activeText: root.resolvedTextColor()

    width: implicitWidth
    height: implicitHeight
    // Appearance
    color: activeBg
    radius: compact ? Theme.buttonRadiusCompact : Theme.buttonRadiusRegular
    border.width: root.visualFocus ? Theme.focusRingWidth : 1
    border.color: root.visualFocus ? Theme.borderFocus : activeBorder

    // Helper functions
    function isCustomColor(colorValue) {
        return colorValue.a > 0 || colorValue.r > 0 || colorValue.g > 0 || colorValue.b > 0
    }

    function colorForState(baseColor, hoverColor, pressedColor) {
        if (!root.enabled) {
            return Theme.controlDisabledBackground
        }
        if (root.checkable && root.checked) {
            return pressedColor
        }
        if (root.down) {
            return pressedColor
        }
        if (root.hovered) {
            return hoverColor
        }
        return baseColor
    }

    function baseBackground() {
        if (isCustomColor(customBackground)) {
            return customBackground
        }
        if (variant === "primary") {
            return Theme.buttonPrimaryBackground
        }
        if (variant === "danger") {
            return Theme.buttonDangerBackground
        }
        if (variant === "ghost") {
            return Theme.buttonGhostBackground
        }
        if (variant === "warm") {
            return Theme.brandWarmAccent
        }
        return Theme.buttonSecondaryBackground
    }

    function hoverBackground() {
        if (isCustomColor(customHover)) {
            return customHover
        }
        if (variant === "primary") {
            return Theme.buttonPrimaryHover
        }
        if (variant === "danger") {
            return Theme.buttonDangerHover
        }
        if (variant === "ghost") {
            return Theme.buttonGhostHover
        }
        if (variant === "warm") {
            return "#ffd980"
        }
        return Theme.buttonSecondaryHover
    }

    function pressedBackground() {
        if (isCustomColor(customPressed)) {
            return customPressed
        }
        if (variant === "primary") {
            return Theme.buttonPrimaryPressed
        }
        if (variant === "danger") {
            return Theme.buttonDangerPressed
        }
        if (variant === "ghost") {
            return Theme.buttonGhostPressed
        }
        if (variant === "warm") {
            return "#e0a93c"
        }
        return Theme.buttonSecondaryPressed
    }

    function baseBorderColor() {
        if (isCustomColor(customBorderColor)) {
            return customBorderColor
        }
        if (!root.enabled) {
            return Theme.controlDisabledBorder
        }
        if (variant === "ghost") {
            return root.hovered ? Theme.borderStrong : Theme.borderSubtle
        }
        if (variant === "primary") {
            return Theme.buttonPrimaryBackground
        }
        if (variant === "danger") {
            return Theme.buttonDangerBackground
        }
        if (variant === "warm") {
            return "#f0bf57"
        }
        return Theme.borderStrong
    }

    function hoverBorderColor() {
        return baseBorderColor()
    }

    function pressedBorderColor() {
        if (root.checkable && root.checked) {
            if (variant === "primary") {
                return Theme.buttonPrimaryPressed
            }
            if (variant === "danger") {
                return Theme.buttonDangerPressed
            }
            if (variant === "warm") {
                return "#d89f35"
            }
            return Theme.borderFocus
        }
        return baseBorderColor()
    }

    function resolvedTextColor() {
        if (isCustomColor(customTextColor)) {
            return customTextColor
        }
        if (!root.enabled) {
            return Theme.textDisabled
        }
        if (variant === "primary") {
            return Theme.buttonPrimaryText
        }
        if (variant === "danger") {
            return Theme.buttonDangerText
        }
        if (variant === "warm") {
            return "#1f1400"
        }
        if (variant === "ghost") {
            return Theme.buttonGhostText
        }
        return Theme.buttonSecondaryText
    }

    // Scale animation
    scale: {
        if (root.down) return 0.97
        if (root.hovered && root.enabled && variant !== "ghost") return 1.02
        return 1.0
    }
    opacity: root.enabled ? 1.0 : 0.5

    Behavior on color {
        ColorAnimation {
            duration: Utils.AnimationUtils.durationNormal
            easing.type: Utils.AnimationUtils.easingOut
        }
    }

    Behavior on border.color {
        ColorAnimation {
            duration: Utils.AnimationUtils.durationFast
            easing.type: Utils.AnimationUtils.easingOut
        }
    }

    Behavior on scale {
        NumberAnimation {
            duration: Utils.AnimationUtils.durationNormal
            easing.type: Utils.AnimationUtils.easingOut
        }
    }

    Behavior on opacity {
        NumberAnimation {
            duration: Utils.AnimationUtils.durationNormal
            easing.type: Utils.AnimationUtils.easingOut
        }
    }

    // Mouse area for click handling
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: root.enabled
        cursorShape: Qt.PointingHandCursor

        onPressed: mouse => {
            root.down = true
        }

        onReleased: mouse => {
            root.down = false
            if (root.checkable) {
                root.checked = !root.checked
                root.toggled(root.checked)
            }
            root.clicked()
        }

        onCanceled: {
            root.down = false
        }

        onEntered: {
            root.hovered = true
        }

        onExited: {
            root.hovered = false
        }
    }

    // Button text
    Text {
        id: buttonText
        anchors.centerIn: parent
        anchors.leftMargin: root.padding
        anchors.rightMargin: root.padding
        text: root.text
        color: activeText
        font.pixelSize: root.fontPixelSize
        font.bold: root.fontBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        wrapMode: Text.NoWrap
    }
}
