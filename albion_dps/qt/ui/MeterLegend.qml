import QtQuick 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, TableSurface access

/**
 * MeterLegend - Keyboard shortcuts legend
 *
 * Displays all available keyboard shortcuts for the meter:
 * - q: quit
 * - b/z/m: mode switching
 * - 1-4: sort key selection
 * - space: manual start/stop
 * - n: archive current battle
 * - r: fame reset
 * - 1-9: copy history entry
 */
TableSurface {
    id: root
    level: 1
    Layout.fillWidth: true
    implicitHeight: 120

    // Access to theme (injected by parent)
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 4

        Text {
            text: "Legend"
            color: textColor
            font.pixelSize: 12
            font.bold: true
        }
        Text {
            text: "q: quit  |  b/z/m: mode  |  1-4: sort"
            color: mutedColor
            font.pixelSize: 11
        }
        Text {
            text: "space: manual start/stop  |  n: archive  |  r: fame reset"
            color: mutedColor
            font.pixelSize: 11
        }
        Text {
            text: "1-9: copy history entry"
            color: mutedColor
            font.pixelSize: 11
        }
    }
}
