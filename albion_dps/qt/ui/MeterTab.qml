import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Item {
    id: root
    anchors.fill: parent

    property string mode: "battle"
    property bool manualActive: false
    property int contributorCount: 0
    property int rosterCount: 0
    property string zone: ""
    property string sortKey: "dps"
    property int selectedHistoryIndex: -1
    property string timeText: ""
    property string durationText: ""
    property string fameText: ""
    property string famePerHourText: ""
    property string silverText: ""
    property string silverPerHourText: ""
    property string captureRuntimeState: "unknown"
    property string captureRuntimeDetail: ""
    property string captureRuntimeActionLabel: ""
    property bool sessionCompareAvailable: false
    property string sessionCompareTitle: ""
    property string sessionCompareText: ""

    property var playersModel: null
    property var historyModel: null
    property var sessionActivityModel: null

    property bool compactLayout: false
    property bool historyAvailable: historyModel && historyModel.count > 0
    property bool activityAvailable: sessionActivityModel && sessionActivityModel.count > 0
    property bool showCompactHistory: false

    signal setMode(string mode)
    signal setSortKey(string sortKey)
    signal clearHistorySelection()
    signal selectHistory(int index)
    signal copyHistory(int index)
    signal copyHistoryShort(int index)
    signal copyHistoryFull(int index)
    signal copyCurrent(bool full)
    signal toggleManual()
    signal deleteSelectedHistory()
    signal clearCurrentHistory()
    signal copySessionCompare()
    signal refreshCaptureRuntimeStatus()
    signal openCaptureRuntimeAction()

    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary
    property int panelSpacing: 12
    property int rightPanelWidth: compactLayout ? width : 372
    property int leftPanelWidth: compactLayout ? width : Math.max(0, width - rightPanelWidth - panelSpacing)

    property var tableRowColor: function(index) {
        return index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
    }

    function runtimeHintText() {
        if (root.captureRuntimeState === "available") {
            return ""
        }
        if (Qt.platform.os === "windows") {
            if (root.captureRuntimeState === "missing") {
                return "Live mode is unavailable. Install Npcap Runtime (Npcap installer). Npcap SDK is not required for normal users."
            }
            if (root.captureRuntimeState === "blocked") {
                return "Live mode is unavailable. Runtime is installed, but this build does not include the Windows live capture component."
            }
        }
        return root.captureRuntimeDetail
    }

    function runtimeHintColor() {
        if (root.captureRuntimeState === "missing") return theme.stateWarning
        if (root.captureRuntimeState === "blocked") return theme.stateDanger
        return mutedColor
    }

    CardPanel {
        id: leftPanel
        level: 1
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.leftPanelWidth
        visible: !root.compactLayout || !root.showCompactHistory

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: "Meter"
                    color: root.textColor
                    font.pixelSize: 14
                    font.bold: true
                }

                ToolButton {
                    text: "?"
                    hoverEnabled: true
                    implicitWidth: 24
                    implicitHeight: 24
                    font.pixelSize: 13
                    background: Rectangle {
                        radius: 12
                        color: root.accentColor
                        border.color: "#79c0ff"
                    }
                    contentItem: Text {
                        text: "?"
                        color: "#081018"
                        font.pixelSize: 13
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    ToolTip.visible: hovered
                    ToolTip.text: "Live combat meter. Tracks DMG/HEAL/DPS/HPS and opens fight snapshots from History."
                }

                Item { Layout.fillWidth: true }

                AppButton {
                    visible: root.compactLayout
                    text: "History"
                    compact: true
                    onClicked: root.showCompactHistory = true
                }
            }

            Text {
                Layout.fillWidth: true
                text: root.selectedHistoryIndex >= 0
                    ? "Scoreboard (history #" + (root.selectedHistoryIndex + 1) + ", " + root.durationText + ", sorted by " + root.sortKey + ")"
                    : "Scoreboard (live " + root.durationText + ", sorted by " + root.sortKey + ")"
                color: root.textColor
                font.pixelSize: 14
                font.bold: true
                wrapMode: Text.WordWrap
            }

            Text {
                Layout.fillWidth: true
                text: "Contributors " + root.contributorCount + " / party " + root.rosterCount
                color: root.mutedColor
                font.pixelSize: 11
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                visible: runtimeHintText().length > 0

                Text {
                    Layout.fillWidth: true
                    text: runtimeHintText()
                    color: runtimeHintColor()
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                AppButton { text: "Refresh"; compact: true; onClicked: root.refreshCaptureRuntimeStatus() }
                AppButton { visible: root.captureRuntimeActionLabel.length > 0; text: root.captureRuntimeActionLabel; compact: true; onClicked: root.openCaptureRuntimeAction() }
            }

            MeterControls {
                id: meterControls
                Layout.fillWidth: true
                theme: root.theme
                currentMode: root.mode
                currentSortKey: root.sortKey
                manualActive: root.manualActive
                onModeChanged: function(mode) { root.setMode(mode) }
                onSortKeyChanged: function(sortKey) { root.setSortKey(sortKey) }
                onToggleManual: root.toggleManual()
                onCopyCurrent: function(full) { root.copyCurrent(full) }
            }

            MeterScoreboard {
                id: meterScoreboard
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                textColor: root.textColor
                mutedColor: root.mutedColor
                playersModel: root.playersModel
                showHistory: root.selectedHistoryIndex >= 0
                selectedHistoryIndex: root.selectedHistoryIndex
                sortKey: root.sortKey
                tableRowColor: root.tableRowColor
            }
        }
    }

    CardPanel {
        id: rightPanel
        level: 1
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.rightPanelWidth
        visible: !root.compactLayout || root.showCompactHistory

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            AppButton {
                visible: root.compactLayout
                text: "Back to meter"
                compact: true
                onClicked: root.showCompactHistory = false
            }

            MeterHistoryPanel {
                id: meterHistoryPanel
                Layout.fillWidth: true
                Layout.fillHeight: true
                theme: root.theme
                textColor: root.textColor
                mutedColor: root.mutedColor
                historyModel: root.historyModel
                selectedHistoryIndex: root.selectedHistoryIndex
                sessionCompareAvailable: root.sessionCompareAvailable
                sessionCompareTitle: root.sessionCompareTitle
                sessionCompareText: root.sessionCompareText
                sortKey: root.sortKey
                tableRowColor: root.tableRowColor
                onClearHistorySelection: root.clearHistorySelection()
                onSelectHistory: function(index) { root.selectHistory(index) }
                onCopyHistory: function(index) { root.copyHistory(index) }
                onCopyHistoryShort: function(index) { root.copyHistoryShort(index) }
                onCopyHistoryFull: function(index) { root.copyHistoryFull(index) }
                onDeleteSelectedHistory: root.deleteSelectedHistory()
                onClearCurrentHistory: root.clearCurrentHistory()
                onCopySessionCompare: root.copySessionCompare()
            }

            MeterSessionStatsPanel {
                Layout.fillWidth: true
                theme: root.theme
                textColor: root.textColor
                mutedColor: root.mutedColor
                fameText: root.fameText
                famePerHourText: root.famePerHourText
                silverText: root.silverText
                silverPerHourText: root.silverPerHourText
            }

            MeterSessionActivityPanel {
                visible: root.activityAvailable
                Layout.fillWidth: true
                Layout.preferredHeight: 140
                Layout.minimumHeight: 120
                theme: root.theme
                activityModel: root.sessionActivityModel
            }
        }
    }
}
