import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, AppButton, CardPanel, TableSurface access

/**
 * MeterTab - Main meter tab container
 *
 * Contains the complete meter view with:
 * - Left panel: Title, status text, controls, and scoreboard
 * - Right panel: History list and legend
 *
 * Signals:
 * - modeChanged(string): Fired when meter mode changes
 * - sortKeyChanged(string): Fired when sort key changes
 * - clearHistorySelection(): Fired when user returns to live view
 * - selectHistory(int): Fired when user selects a history entry
 * - copyHistory(int): Fired when user copies a history entry
 */
Item {
    id: root

    // State properties (bound to parent's uiState)
    property string mode: "battle"
    property string zone: ""
    property string sortKey: "dps"
    property int selectedHistoryIndex: -1
    property string timeText: ""
    property string fameText: ""
    property string famePerHourText: ""
    property string captureRuntimeState: "unknown"
    property string captureRuntimeDetail: ""
    property string captureRuntimeActionLabel: ""

    // Models
    property var playersModel: null
    property var historyModel: null

    // UI flags
    property bool compactLayout: false

    // Signals to notify parent of actions
    signal setMode(string mode)
    signal setSortKey(string sortKey)
    signal clearHistorySelection()
    signal selectHistory(int index)
    signal copyHistory(int index)
    signal refreshCaptureRuntimeStatus()
    signal openCaptureRuntimeAction()

    // Access to theme (injected by parent)
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary

    // Helper functions (injected by parent or defined here)
    property var tableRowColor: function(index) {
        return index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
    }

    function tableRowStrongColor(index) {
        return index % 2 === 0 ? theme.surfaceInteractive : theme.tableRowEven
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
                return "Live mode is unavailable. Runtime is installed, but capture backend is missing. Reinstall with capture profile (SDK + C++ tools only for this build step)."
            }
        }
        return root.captureRuntimeDetail
    }

    function runtimeHintColor() {
        if (root.captureRuntimeState === "missing") {
            return theme.stateWarning
        }
        if (root.captureRuntimeState === "blocked") {
            return theme.stateDanger
        }
        return mutedColor
    }

    RowLayout {
        anchors.fill: parent
        spacing: 12

        // Left Panel - Scoreboard
        CardPanel {
            level: 1
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                // Header with title and help button
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    Text {
                        text: "Meter"
                        color: textColor
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
                            color: accentColor
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
                        ToolTip.text: "Live combat meter.\nTracks DMG/HEAL/DPS/HPS, supports Battle/Zone/Manual mode,\nand lets you open fight snapshots from History."
                    }

                    Item { Layout.fillWidth: true }
                }

                // Status text showing current mode/sort
                Text {
                    text: root.selectedHistoryIndex >= 0
                        ? "Scoreboard (history #" + (root.selectedHistoryIndex + 1) + ", sorted by " + root.sortKey + ")"
                        : "Scoreboard (live, sorted by " + root.sortKey + ")"
                    color: textColor
                    font.pixelSize: 14
                    font.bold: true
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
                        wrapMode: Text.Wrap
                    }

                    AppButton {
                        text: "Refresh"
                        compact: true
                        onClicked: root.refreshCaptureRuntimeStatus()
                    }

                    AppButton {
                        visible: root.captureRuntimeActionLabel.length > 0
                        text: root.captureRuntimeActionLabel
                        compact: true
                        onClicked: root.openCaptureRuntimeAction()
                    }
                }

                // Mode and Sort controls
                MeterControls {
                    id: meterControls
                    Layout.fillWidth: true
                    theme: root.theme
                    currentMode: root.mode
                    currentSortKey: root.sortKey

                    onModeChanged: function(mode) {
                        root.setMode(mode)
                    }

                    onSortKeyChanged: function(sortKey) {
                        root.setSortKey(sortKey)
                    }
                }

                // Player scoreboard
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

        // Right Panel - History
        CardPanel {
            level: 1
            Layout.preferredWidth: 360
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                // History panel
                MeterHistoryPanel {
                    id: meterHistoryPanel
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    theme: root.theme
                    textColor: root.textColor
                    mutedColor: root.mutedColor
                    historyModel: root.historyModel
                    selectedHistoryIndex: root.selectedHistoryIndex
                    sortKey: root.sortKey
                    tableRowColor: root.tableRowColor

                    onClearHistorySelection: root.clearHistorySelection()
                    onSelectHistory: function(index) { root.selectHistory(index) }
                    onCopyHistory: function(index) { root.copyHistory(index) }
                }

                // Legend
                MeterLegend {
                    id: meterLegend
                    Layout.fillWidth: true
                    theme: root.theme
                    textColor: root.textColor
                    mutedColor: root.mutedColor
                }
            }
        }
    }
}
