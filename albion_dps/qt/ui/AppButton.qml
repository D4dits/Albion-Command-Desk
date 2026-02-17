import QtQuick 2.15
import QtQuick.Controls 2.15
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

    Theme {
        id: theme
    }

    implicitHeight: compact ? theme.buttonHeightCompact : theme.buttonHeightRegular
    implicitWidth: Math.max(64, contentItem.implicitWidth + 20)
    padding: compact ? theme.spacingSm : theme.spacingMd
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
            return theme.controlDisabledBackground
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
            return theme.buttonPrimaryBackground
        }
        if (variant === "danger") {
            return theme.buttonDangerBackground
        }
        if (variant === "ghost") {
            return theme.buttonGhostBackground
        }
        if (variant === "warm") {
            return theme.brandWarmAccent
        }
        return theme.buttonSecondaryBackground
    }

    function hoverBackground() {
        if (isCustomColor(customHover)) {
            return customHover
        }
        if (variant === "primary") {
            return theme.buttonPrimaryHover
        }
        if (variant === "danger") {
            return theme.buttonDangerHover
        }
        if (variant === "ghost") {
            return theme.buttonGhostHover
        }
        if (variant === "warm") {
            return "#ffd980"
        }
        return theme.buttonSecondaryHover
    }

    function pressedBackground() {
        if (isCustomColor(customPressed)) {
            return customPressed
        }
        if (variant === "primary") {
            return theme.buttonPrimaryPressed
        }
        if (variant === "danger") {
            return theme.buttonDangerPressed
        }
        if (variant === "ghost") {
            return theme.buttonGhostPressed
        }
        if (variant === "warm") {
            return "#e0a93c"
        }
        return theme.buttonSecondaryPressed
    }

    function resolvedBorderColor() {
        if (isCustomColor(customBorderColor)) {
            return customBorderColor
        }
        if (!enabled) {
            return theme.controlDisabledBorder
        }
        if (checkable && checked) {
            if (variant === "primary") {
                return theme.buttonPrimaryPressed
            }
            if (variant === "danger") {
                return theme.buttonDangerPressed
            }
            if (variant === "warm") {
                return "#d89f35"
            }
            return theme.borderFocus
        }
        if (variant === "ghost") {
            return hovered ? theme.borderStrong : theme.borderSubtle
        }
        if (variant === "primary") {
            return theme.buttonPrimaryBackground
        }
        if (variant === "danger") {
            return theme.buttonDangerBackground
        }
        if (variant === "warm") {
            return "#f0bf57"
        }
        return theme.borderStrong
    }

    function resolvedTextColor() {
        if (isCustomColor(customTextColor)) {
            return customTextColor
        }
        if (!enabled) {
            return theme.textDisabled
        }
        if (variant === "primary") {
            return theme.buttonPrimaryText
        }
        if (variant === "danger") {
            return theme.buttonDangerText
        }
        if (variant === "warm") {
            return "#1f1400"
        }
        if (variant === "ghost") {
            return theme.buttonGhostText
        }
        return theme.buttonSecondaryText
    }

    background: Rectangle {
        id: backgroundRect
        readonly property color activeBg: root.colorForState(root.baseBackground(), root.hoverBackground(), root.pressedBackground())
        radius: compact ? theme.buttonRadiusCompact : theme.buttonRadiusRegular
        color: "transparent"
        border.width: root.visualFocus ? theme.focusRingWidth : 1
        border.color: root.visualFocus ? theme.borderFocus : root.resolvedBorderColor()

        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: Qt.lighter(backgroundRect.activeBg, root.variant === "ghost" ? 1.0 : 1.08)
            }
            GradientStop {
                position: 1.0
                color: Qt.darker(backgroundRect.activeBg, root.variant === "ghost" ? 1.0 : 1.08)
            }
        }

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
