import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme, AppButton access

/**
 * Toast - Individual toast notification component
 *
 * Features:
 * - Slide in/out animations
 * - Auto-dismiss with timer
 * - Manual dismiss button
 * - Icon based on type (success, warning, error, info)
 * - Progress bar for auto-dismiss
 *
 * Usage:
 *   Toast {
 *       type: "success"  // success, warning, error, info
 *       title: "Copied to clipboard"
 *       message: "Text copied successfully"
 *       duration: 3000  // ms, 0 = no auto-dismiss
 *       onDismissed: toast.dismiss()
 *   }
 */
Rectangle {
    id: root
    height: contentColumn.height + topPadding + bottomPadding
    radius: 6
    color: root.backgroundColor

    // Public properties
    property string type: "info"  // success, warning, error, info
    property string title: ""
    property string message: ""
    property int duration: 3000  // 0 = no auto-dismiss
    property bool showProgress: true

    // Computed colors based on type
    readonly property color backgroundColor: {
        switch (root.type) {
            case "success": return theme.stateSuccessBg
            case "warning": return theme.stateWarningBg
            case "error": return theme.stateDangerBg
            case "info": return theme.stateInfoBg
            default: return theme.stateInfoBg
        }
    }
    readonly property color borderColor: {
        switch (root.type) {
            case "success": return theme.stateSuccess
            case "warning": return theme.stateWarning
            case "error": return theme.stateDanger
            case "info": return theme.stateInfo
            default: return theme.stateInfo
        }
    }
    readonly property color iconColor: {
        switch (root.type) {
            case "success": return theme.stateSuccess
            case "warning": return theme.stateWarning
            case "error": return theme.stateDanger
            case "info": return theme.stateInfo
            default: return theme.stateInfo
        }
    }
    readonly property string iconName: {
        switch (root.type) {
            case "success": return "check"
            case "warning": return "warning"
            case "error": return "error"
            case "info": return "info"
            default: return "info"
        }
    }

    // Signals
    signal dismissed()

    // Access to theme
    property var theme: null
    property color textColor: theme.textPrimary

    // Spacing
    readonly property int topPadding: 12
    readonly property int bottomPadding: 12
    readonly property int leftPadding: 12
    readonly property int rightPadding: 12
    readonly property int spacing: 8

    border.color: borderColor
    border.width: 1

    // Slide in/out animations
    states: [
        State {
            name: "visible"
            when: true
            PropertyChanges {
                target: root
                opacity: 1.0
                scale: 1.0
            }
        },
        State {
            name: "hidden"
            when: false
            PropertyChanges {
                target: root
                opacity: 0.0
                scale: 0.95
            }
        }
    ]

    transitions: [
        Transition {
            from: "hidden"
            to: "visible"
            ParallelAnimation {
                NumberAnimation { property: "opacity"; from: 0; to: 1.0; duration: 200; easing.type: Easing.OutCubic }
                NumberAnimation { property: "scale"; from: 0.95; to: 1.0; duration: 200; easing.type: Easing.OutCubic }
            }
        },
        Transition {
            from: "visible"
            to: "hidden"
            ParallelAnimation {
                NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; duration: 150; easing.type: Easing.InCubic }
                NumberAnimation { property: "scale"; from: 1.0; to: 0.95; duration: 150; easing.type: Easing.InCubic }
            }
        }
    ]

    // Auto-dismiss timer
    Timer {
        id: autoDismissTimer
        interval: root.duration
        running: root.duration > 0 && root.visible
        onTriggered: root.dismissed()
    }

    // Progress bar for auto-dismiss
    Rectangle {
        id: progressBar
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        height: 2
        color: root.iconColor
        opacity: 0.6

        states: [
            State {
                name: "progress"
                when: root.showProgress && root.duration > 0
                PropertyChanges { target: progressBar; width: parent.width * 0 }
                PropertyChanges { target: progressBar; opacity: 0.6 }
            },
            State {
                name: "noProgress"
                when: !root.showProgress || root.duration <= 0
                PropertyChanges { target: progressBar; width: 0 }
                PropertyChanges { target: progressBar; opacity: 0 }
            }
        ]

        transitions: [
            Transition {
                to: "progress"
                NumberAnimation { property: "width"; from: parent.width; to: 0; duration: root.duration }
            }
        ]
    }

    ColumnLayout {
        id: contentColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: root.spacing
        spacing: root.spacing

        // Top row: Icon + Title + Dismiss button
        RowLayout {
            Layout.fillWidth: true
            spacing: root.spacing

            // Icon
            Icon {
                id: icon
                name: root.iconName
                size: 16
                color: root.iconColor
                Layout.alignment: Qt.AlignTop
            }

            // Title
            Text {
                id: titleText
                text: root.title
                color: root.textColor
                font.pixelSize: 12
                font.bold: true
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            // Dismiss button
            AppButton {
                text: "×"
                variant: "ghost"
                compact: true
                implicitWidth: 24
                implicitHeight: 20
                fontPixelSize: 14
                onClicked: root.dismissed()
            }
        }

        // Message
        Text {
            id: messageText
            visible: root.message.length > 0
            text: root.message
            color: root.textColor
            font.pixelSize: 11
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            elide: Text.ElideRight
            maximumLineCount: 3
        }
    }
}
