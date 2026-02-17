import QtQuick 2.15
import QtQuick.Controls 2.15

ComboBox {
    id: root

    Theme {
        id: theme
    }

    implicitHeight: theme.controlHeightRegular
    focusPolicy: Qt.StrongFocus
    leftPadding: theme.spacingSm
    rightPadding: 24
    font.pixelSize: 12

    contentItem: Text {
        leftPadding: root.leftPadding
        rightPadding: root.rightPadding
        text: root.displayText
        font: root.font
        color: root.enabled ? theme.textPrimary : theme.textDisabled
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Canvas {
        x: root.width - width - 8
        y: (root.height - height) / 2
        width: 10
        height: 6
        contextType: "2d"
        onPaint: {
            context.reset()
            context.moveTo(0, 0)
            context.lineTo(width, 0)
            context.lineTo(width / 2, height)
            context.closePath()
            context.fillStyle = root.enabled ? theme.textMuted : theme.textDisabled
            context.fill()
        }
    }

    background: Rectangle {
        radius: theme.radiusMd
        color: root.enabled ? theme.inputBackground : theme.inputBackgroundDisabled
        border.width: root.visualFocus ? theme.focusRingWidth : 1
        border.color: root.visualFocus ? theme.inputBorderFocus : (root.enabled ? theme.inputBorder : theme.controlDisabledBorder)
    }

    delegate: ItemDelegate {
        readonly property string delegateText: {
            if (typeof modelData === "string" || typeof modelData === "number") {
                return String(modelData)
            }
            if (typeof modelData === "object" && modelData !== null) {
                if (root.textRole && modelData[root.textRole] !== undefined) {
                    return String(modelData[root.textRole])
                }
                if (modelData.text !== undefined) {
                    return String(modelData.text)
                }
            }
            return String(modelData)
        }
        width: ListView.view ? ListView.view.width : root.width
        text: delegateText
        highlighted: root.highlightedIndex === index
        background: Rectangle {
            color: parent.highlighted ? theme.tableSelectedBackground : theme.surfaceInteractive
        }
        contentItem: Text {
            text: parent.text
            color: theme.textPrimary
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            font.pixelSize: 12
        }
    }

    popup: Popup {
        parent: Overlay.overlay
        y: root.height + 2
        width: root.width
        z: 2000
        padding: 1
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        background: Rectangle {
            radius: theme.radiusMd
            color: theme.surfaceRaised
            border.color: theme.borderStrong
        }
        contentItem: ListView {
            clip: true
            model: root.delegateModel
            currentIndex: root.highlightedIndex
        }
    }
}
