import QtQuick 2.15
import QtQuick.Controls 2.15
import "." // for Theme access

ComboBox {
    id: root


    implicitHeight: Theme.controlHeightRegular
    focusPolicy: Qt.StrongFocus
    leftPadding: Theme.spacingSm
    rightPadding: 24
    font.pixelSize: 12

    contentItem: Text {
        leftPadding: root.leftPadding
        rightPadding: root.rightPadding
        text: root.displayText
        font: root.font
        color: root.enabled ? Theme.textPrimary : Theme.textDisabled
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
            context.fillStyle = root.enabled ? Theme.textMuted : Theme.textDisabled
            context.fill()
        }
    }

    background: Rectangle {
        radius: Theme.radiusMd
        color: root.enabled ? Theme.inputBackground : Theme.inputBackgroundDisabled
        border.width: root.visualFocus ? Theme.focusRingWidth : 1
        border.color: root.visualFocus ? Theme.inputBorderFocus : (root.enabled ? Theme.inputBorder : Theme.controlDisabledBorder)
    }

    delegate: ItemDelegate {
        implicitHeight: Theme.controlHeightRegular
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
            color: parent.highlighted ? Theme.tableSelectedBackground : Theme.surfaceInteractive
        }
        contentItem: Text {
            text: parent.text
            color: Theme.textPrimary
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            font.pixelSize: 12
        }
    }

    popup: Popup {
        parent: Overlay.overlay
        x: {
            var p = root.mapToItem(Overlay.overlay, 0, 0)
            return p ? p.x : 0
        }
        y: {
            var p = root.mapToItem(Overlay.overlay, 0, root.height + 2)
            return p ? p.y : root.height + 2
        }
        width: root.width
        z: 2000
        padding: 1
        modal: false
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent
        background: Rectangle {
            radius: Theme.radiusMd
            color: Theme.surfaceRaised
            border.color: Theme.borderStrong
        }
        contentItem: ListView {
            clip: true
            implicitHeight: Math.min(contentHeight, 260)
            model: root.delegateModel
            currentIndex: root.highlightedIndex
        }
    }
}
