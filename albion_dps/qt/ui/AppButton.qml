import QtQuick 2.15
import QtQuick.Controls 2.15
import "." // for Theme access
import "utils" 1.0 as Utils

Button {
    id: root

    property string variant: "secondary" // primary | secondary | ghost | danger | warm
    property bool compact: false
    property color customBackground: "transparent"
    property color customHover: "transparent"
    property color customPressed: "transparent"
    property color customTextColor: "transparent"
    property color customBorderColor: "transparent"


    implicitHeight: compact ? Theme.buttonHeightCompact : Theme.buttonHeightRegular
    implicitWidth: Math.max(64, contentItem.implicitWidth + 20)
    padding: compact ? Theme.spacingSm : Theme.spacingMd
    hoverEnabled: enabled
    focusPolicy: Qt.StrongFocus
    font.pixelSize: 12
    font.bold: variant === "primary" || variant === "danger" || variant === "warm"
    scale: {
        if (down) return 0.97
        if (hovered && enabled && variant !== "ghost") return 1.02
        return 1.0
    }
    opacity: enabled ? 1.0 : 0.5

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

    function isCustomColor(colorValue) {
        return colorValue.a > 0 || colorValue.r > 0 || colorValue.g > 0 || colorValue.b > 0
    }

    function colorForState(baseColor, hoverColor, pressedColor) {
        if (!enabled) {
            return Theme.controlDisabledBackground
        }
        if (checkable && checked) {
            return pressedColor
        }
        if (down) {
            return pressedColor
        }
        if (hovered) {
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

    function resolvedBorderColor() {
        if (isCustomColor(customBorderColor)) {
            return customBorderColor
        }
        if (!enabled) {
            return Theme.controlDisabledBorder
        }
        if (checkable && checked) {
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
        if (variant === "ghost") {
            return hovered ? Theme.borderStrong : Theme.borderSubtle
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

    function resolvedTextColor() {
        if (isCustomColor(customTextColor)) {
            return customTextColor
        }
        if (!enabled) {
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

    background: Rectangle {
        id: backgroundRect
        readonly property color activeBg: root.colorForState(root.baseBackground(), root.hoverBackground(), root.pressedBackground())
        radius: compact ? Theme.buttonRadiusCompact : Theme.buttonRadiusRegular
        color: activeBg
        border.width: root.visualFocus ? Theme.focusRingWidth : 1
        border.color: root.visualFocus ? Theme.borderFocus : root.resolvedBorderColor()

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
    }

    contentItem: Text {
        text: root.text
        anchors.fill: parent
        anchors.leftMargin: root.padding
        anchors.rightMargin: root.padding
        color: root.resolvedTextColor()
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        wrapMode: Text.NoWrap
        font: root.font
    }
}
