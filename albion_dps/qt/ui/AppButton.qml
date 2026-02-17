import QtQuick 2.15
import QtQuick.Controls 2.15

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
    font.pixelSize: 12
    font.bold: variant === "primary" || variant === "danger" || variant === "warm"
    scale: down ? 0.985 : 1.0
    opacity: enabled ? 1.0 : 0.62

    Behavior on scale {
        NumberAnimation {
            duration: theme.motionFastMs
            easing.type: Easing.OutCubic
        }
    }

    Behavior on opacity {
        NumberAnimation {
            duration: theme.motionNormalMs
        }
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
        if (customBackground !== "transparent") {
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
        if (customHover !== "transparent") {
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
        if (customPressed !== "transparent") {
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
        if (customBorderColor !== "transparent") {
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
        if (customTextColor !== "transparent") {
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
        radius: compact ? theme.buttonRadiusCompact : theme.buttonRadiusRegular
        color: root.colorForState(root.baseBackground(), root.hoverBackground(), root.pressedBackground())
        border.width: root.visualFocus ? 2 : 1
        border.color: root.visualFocus ? theme.borderFocus : root.resolvedBorderColor()

        Behavior on color {
            ColorAnimation {
                duration: theme.motionNormalMs
            }
        }
        Behavior on border.color {
            ColorAnimation {
                duration: theme.motionFastMs
            }
        }
    }

    contentItem: Text {
        text: root.text
        color: root.resolvedTextColor()
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        font: root.font
    }
}
