import QtQuick 2.15

Rectangle {
    id: root

    property int level: 0 // 0=base,1=raised,2=highlight
    property color fillColor: level === 2 ? theme.cardLevel2 : (level === 1 ? theme.cardLevel1 : theme.cardLevel0)
    property color strokeColor: level > 0 ? theme.borderStrong : theme.borderSubtle
    property int cornerRadius: theme.radiusLg
    property bool emphasizeBorder: false
    property real shadowOpacity: level === 0 ? theme.elevationLowOpacity : theme.elevationMediumOpacity

    Theme {
        id: theme
    }

    color: fillColor
    radius: cornerRadius
    border.color: emphasizeBorder ? theme.borderFocus : strokeColor
    border.width: 1

    Behavior on color {
        ColorAnimation {
            duration: theme.motionSlowMs
        }
    }

    Behavior on border.color {
        ColorAnimation {
            duration: theme.motionNormalMs
        }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 1
        radius: Math.max(0, root.cornerRadius - 1)
        color: "transparent"
        border.color: Qt.rgba(1, 1, 1, root.shadowOpacity * 0.08)
        border.width: 1
    }
}
