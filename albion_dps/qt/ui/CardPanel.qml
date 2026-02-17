import QtQuick 2.15

Rectangle {
    id: root

    property int level: 0 // 0=base,1=raised,2=highlight
    property color fillColor: level === 2 ? Theme.cardLevel2 : (level === 1 ? Theme.cardLevel1 : Theme.cardLevel0)
    property color strokeColor: level > 0 ? Theme.borderStrong : Theme.borderSubtle
    property int cornerRadius: Theme.radiusLg
    property bool emphasizeBorder: false
    property real shadowOpacity: level === 0 ? Theme.elevationLowOpacity : Theme.elevationMediumOpacity


    color: fillColor
    radius: cornerRadius
    border.color: emphasizeBorder ? Theme.borderFocus : strokeColor
    border.width: 1

    Behavior on color {
        ColorAnimation {
            duration: Theme.motionSlowMs
        }
    }

    Behavior on border.color {
        ColorAnimation {
            duration: Theme.motionNormalMs
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
