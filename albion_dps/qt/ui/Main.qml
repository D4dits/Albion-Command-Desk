import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: root
    visible: true
    width: 1120
    height: 720
    title: "Albion DPS Meter"
    color: "#0b0f14"

    property color textColor: "#e6edf3"
    property color mutedColor: "#9aa4af"
    property color accentColor: "#4aa3ff"
    property color panelColor: "#131a22"
    property color borderColor: "#1f2a37"
    property bool meterView: viewTabs.currentIndex === 0

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Rectangle {
            Layout.fillWidth: true
            height: 72
            color: panelColor
            radius: 8
            border.color: borderColor

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 20

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Text {
                        text: "Albion DPS Meter"
                        color: textColor
                        font.pixelSize: 20
                        font.bold: true
                    }
                    Text {
                        text: meterView
                            ? "Mode: " + uiState.mode + "  |  Zone: " + uiState.zone
                            : "Scanner status: " + scannerState.statusText + "  |  Updates: " + scannerState.updateText
                        color: mutedColor
                        font.pixelSize: 12
                    }
                }

                ColumnLayout {
                    visible: meterView
                    spacing: 4
                    Text {
                        text: uiState.timeText
                        color: textColor
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignRight
                    }
                    Text {
                        text: "Fame: " + uiState.fameText + "  |  Fame/h: " + uiState.famePerHourText
                        color: mutedColor
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
        }

        TabBar {
            id: viewTabs
            Layout.fillWidth: true
            implicitHeight: 42
            background: Rectangle {
                color: panelColor
                radius: 6
                border.color: borderColor
            }
            TabButton {
                id: meterTab
                text: "Meter"
                background: Rectangle {
                    radius: 5
                    color: meterTab.checked ? accentColor : "#0f1620"
                    border.color: meterTab.checked ? accentColor : borderColor
                }
                contentItem: Text {
                    text: meterTab.text
                    color: meterTab.checked ? "#0b0f14" : textColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.bold: true
                }
            }
            TabButton {
                id: scannerTab
                text: "Scanner"
                background: Rectangle {
                    radius: 5
                    color: scannerTab.checked ? accentColor : "#0f1620"
                    border.color: scannerTab.checked ? accentColor : borderColor
                }
                contentItem: Text {
                    text: scannerTab.text
                    color: scannerTab.checked ? "#0b0f14" : textColor
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.bold: true
                }
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: viewTabs.currentIndex

            Item {
                RowLayout {
                    anchors.fill: parent
                    spacing: 12

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: panelColor
                        radius: 8
                        border.color: borderColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            Text {
                                text: uiState.selectedHistoryIndex >= 0
                                    ? "Scoreboard (history #" + (uiState.selectedHistoryIndex + 1) + ", sorted by " + uiState.sortKey + ")"
                                    : "Scoreboard (live, sorted by " + uiState.sortKey + ")"
                                color: textColor
                                font.pixelSize: 14
                                font.bold: true
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 62
                                color: "#0f1620"
                                radius: 6
                                border.color: "#1f2a37"

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    spacing: 6

                                    RowLayout {
                                        spacing: 8
                                        Text {
                                            text: "Mode:"
                                            color: mutedColor
                                            font.pixelSize: 11
                                        }
                                        Button {
                                            id: battleButton
                                            text: "Battle"
                                            checkable: true
                                            checked: uiState.mode === "battle"
                                            onClicked: uiState.setMode("battle")
                                            background: Rectangle {
                                                radius: 6
                                                color: battleButton.checked ? accentColor : "#101923"
                                                border.color: battleButton.checked ? accentColor : borderColor
                                            }
                                            contentItem: Text {
                                                text: battleButton.text
                                                color: battleButton.checked ? "#0b0f14" : textColor
                                                font.pixelSize: 11
                                            }
                                        }
                                        Button {
                                            id: zoneButton
                                            text: "Zone"
                                            checkable: true
                                            checked: uiState.mode === "zone"
                                            onClicked: uiState.setMode("zone")
                                            background: Rectangle {
                                                radius: 6
                                                color: zoneButton.checked ? accentColor : "#101923"
                                                border.color: zoneButton.checked ? accentColor : borderColor
                                            }
                                            contentItem: Text {
                                                text: zoneButton.text
                                                color: zoneButton.checked ? "#0b0f14" : textColor
                                                font.pixelSize: 11
                                            }
                                        }
                                        Button {
                                            id: manualButton
                                            text: "Manual"
                                            checkable: true
                                            checked: uiState.mode === "manual"
                                            onClicked: uiState.setMode("manual")
                                            background: Rectangle {
                                                radius: 6
                                                color: manualButton.checked ? accentColor : "#101923"
                                                border.color: manualButton.checked ? accentColor : borderColor
                                            }
                                            contentItem: Text {
                                                text: manualButton.text
                                                color: manualButton.checked ? "#0b0f14" : textColor
                                                font.pixelSize: 11
                                            }
                                        }
                                        Item { Layout.fillWidth: true }
                                        Text {
                                            text: "Sort:"
                                            color: mutedColor
                                            font.pixelSize: 11
                                        }
                                        Button {
                                            id: sortDpsButton
                                            text: "DPS"
                                            checkable: true
                                            checked: uiState.sortKey === "dps"
                                            onClicked: uiState.setSortKey("dps")
                                            background: Rectangle {
                                                radius: 6
                                                color: sortDpsButton.checked ? accentColor : "#101923"
                                                border.color: sortDpsButton.checked ? accentColor : borderColor
                                            }
                                            contentItem: Text {
                                                text: sortDpsButton.text
                                                color: sortDpsButton.checked ? "#0b0f14" : textColor
                                                font.pixelSize: 11
                                            }
                                        }
                                        Button {
                                            id: sortDmgButton
                                            text: "DMG"
                                            checkable: true
                                            checked: uiState.sortKey === "dmg"
                                            onClicked: uiState.setSortKey("dmg")
                                            background: Rectangle {
                                                radius: 6
                                                color: sortDmgButton.checked ? accentColor : "#101923"
                                                border.color: sortDmgButton.checked ? accentColor : borderColor
                                            }
                                            contentItem: Text {
                                                text: sortDmgButton.text
                                                color: sortDmgButton.checked ? "#0b0f14" : textColor
                                                font.pixelSize: 11
                                            }
                                        }
                                        Button {
                                            id: sortHpsButton
                                            text: "HPS"
                                            checkable: true
                                            checked: uiState.sortKey === "hps"
                                            onClicked: uiState.setSortKey("hps")
                                            background: Rectangle {
                                                radius: 6
                                                color: sortHpsButton.checked ? accentColor : "#101923"
                                                border.color: sortHpsButton.checked ? accentColor : borderColor
                                            }
                                            contentItem: Text {
                                                text: sortHpsButton.text
                                                color: sortHpsButton.checked ? "#0b0f14" : textColor
                                                font.pixelSize: 11
                                            }
                                        }
                                        Button {
                                            id: sortHealButton
                                            text: "HEAL"
                                            checkable: true
                                            checked: uiState.sortKey === "heal"
                                            onClicked: uiState.setSortKey("heal")
                                            background: Rectangle {
                                                radius: 6
                                                color: sortHealButton.checked ? accentColor : "#101923"
                                                border.color: sortHealButton.checked ? accentColor : borderColor
                                            }
                                            contentItem: Text {
                                                text: sortHealButton.text
                                                color: sortHealButton.checked ? "#0b0f14" : textColor
                                                font.pixelSize: 11
                                            }
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 26
                                color: "#0f1620"
                                radius: 4

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    spacing: 12

                                    Text { text: "Name"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 140 }
                                    Text { text: "Weapon"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90 }
                                    Text { text: "DMG"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                    Text { text: "HEAL"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                    Text { text: "DPS"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                    Text { text: "HPS"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                    Text { text: "BAR"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true }
                                }
                            }

                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: uiState.playersModel
                                delegate: Rectangle {
                                    width: ListView.view.width
                                    height: 34
                                    color: "transparent"

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: 12

                                        Text {
                                            text: name
                                            color: "#e6edf3"
                                            font.pixelSize: 12
                                            elide: Text.ElideRight
                                            Layout.preferredWidth: 140
                                        }
                                        Item {
                                            Layout.preferredWidth: 90
                                            height: 24
                                            RowLayout {
                                                anchors.fill: parent
                                                spacing: 4
                                                Image {
                                                    source: weaponIcon
                                                    width: 20
                                                    height: 20
                                                    Layout.preferredWidth: 20
                                                    Layout.preferredHeight: 20
                                                    sourceSize.width: 20
                                                    sourceSize.height: 20
                                                    fillMode: Image.PreserveAspectFit
                                                    visible: weaponIcon && weaponIcon.length > 0
                                                }
                                                Text {
                                                    text: weaponTier && weaponTier.length > 0 ? weaponTier : "-"
                                                    color: mutedColor
                                                    font.pixelSize: 11
                                                    elide: Text.ElideRight
                                                }
                                            }
                                            ToolTip.visible: weaponHover.containsMouse && weaponName && weaponName.length > 0
                                            ToolTip.text: weaponName
                                            MouseArea {
                                                id: weaponHover
                                                anchors.fill: parent
                                                hoverEnabled: true
                                            }
                                        }
                                        Text { text: damage; color: mutedColor; font.pixelSize: 12; Layout.preferredWidth: 60 }
                                        Text { text: heal; color: mutedColor; font.pixelSize: 12; Layout.preferredWidth: 60 }
                                        Text { text: dps.toFixed(1); color: mutedColor; font.pixelSize: 12; Layout.preferredWidth: 60 }
                                        Text { text: hps.toFixed(1); color: mutedColor; font.pixelSize: 12; Layout.preferredWidth: 60 }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 10
                                            radius: 4
                                            color: "#0f1620"
                                            border.color: "#1f2a37"
                                            Rectangle {
                                                height: parent.height
                                                width: Math.max(4, parent.width * barRatio)
                                                radius: 4
                                                color: barColor
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 360
                        Layout.fillHeight: true
                        color: panelColor
                        radius: 8
                        border.color: borderColor

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            Text {
                                text: "History"
                                color: textColor
                                font.pixelSize: 14
                                font.bold: true
                            }

                            Button {
                                visible: uiState.selectedHistoryIndex >= 0
                                text: "Back to live"
                                onClicked: uiState.clearHistorySelection()
                            }

                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: uiState.historyModel
                                delegate: Rectangle {
                                    width: ListView.view.width
                                    height: 92
                                    radius: 6
                                    color: selected ? "#162231" : "#0f1620"
                                    border.color: selected ? "#4aa3ff" : "#1f2a37"
                                    border.width: 1
                                    TapHandler {
                                        onTapped: uiState.selectHistory(index)
                                    }

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 4

                                        RowLayout {
                                            Layout.fillWidth: true
                                            Text { text: label; color: textColor; font.pixelSize: 12; font.bold: true }
                                            Item { Layout.fillWidth: true }
                                            Button {
                                                text: "Copy full"
                                                onClicked: uiState.copyHistory(index)
                                            }
                                        }
                                        Text { text: meta; color: mutedColor; font.pixelSize: 11 }
                                        Text {
                                            text: players
                                            color: textColor
                                            font.pixelSize: 11
                                            wrapMode: Text.NoWrap
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                height: 120
                                radius: 6
                                color: "#0f1620"
                                border.color: "#1f2a37"
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 4
                                    Text { text: "Legend"; color: textColor; font.pixelSize: 12; font.bold: true }
                                    Text { text: "q: quit  |  b/z/m: mode  |  1-4: sort"; color: mutedColor; font.pixelSize: 11 }
                                    Text { text: "space: manual start/stop  |  n: archive  |  r: fame reset"; color: mutedColor; font.pixelSize: 11 }
                                    Text { text: "1-9: copy history entry"; color: mutedColor; font.pixelSize: 11 }
                                }
                            }
                        }
                    }
                }
            }

            Item {
                Rectangle {
                    anchors.fill: parent
                    color: panelColor
                    radius: 8
                    border.color: borderColor

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Text {
                            text: "AlbionData Scanner"
                            color: textColor
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Text {
                            text: "Status: " + scannerState.statusText + "  |  Updates: " + scannerState.updateText
                            color: mutedColor
                            font.pixelSize: 11
                        }
                        Text {
                            text: "Local repo: " + scannerState.clientDir
                            color: mutedColor
                            font.pixelSize: 11
                            elide: Text.ElideRight
                        }

                        RowLayout {
                            spacing: 10
                            CheckBox {
                                id: disableUploadBox
                                text: "Disable upload (-d)"
                                checked: scannerState.disableUpload
                                onToggled: scannerState.setDisableUpload(checked)
                            }
                            Text {
                                text: "Listen devices (-l):"
                                color: mutedColor
                                font.pixelSize: 11
                            }
                            TextField {
                                id: listenDevicesField
                                Layout.preferredWidth: 260
                                placeholderText: "eth0,wlan0 or MAC list"
                                text: scannerState.listenDevices
                                color: textColor
                                onEditingFinished: scannerState.setListenDevices(text)
                            }
                        }

                        RowLayout {
                            spacing: 10
                            Text {
                                text: "Public ingest (-i):"
                                color: mutedColor
                                font.pixelSize: 11
                            }
                            TextField {
                                id: ingestField
                                Layout.fillWidth: true
                                placeholderText: "https+pow://albion-online-data.com"
                                text: scannerState.publicIngestUrl
                                color: textColor
                                onEditingFinished: scannerState.setPublicIngestUrl(text)
                            }
                        }

                        RowLayout {
                            spacing: 8
                            Button {
                                text: "Check updates"
                                onClicked: scannerState.checkForUpdates()
                            }
                            Button {
                                text: "Sync repo"
                                onClicked: scannerState.syncClientRepo()
                            }
                            Button {
                                text: "Start scanner"
                                enabled: !scannerState.running
                                onClicked: scannerState.startScanner()
                            }
                            Button {
                                text: "Stop scanner"
                                enabled: scannerState.running
                                onClicked: scannerState.stopScanner()
                            }
                            Button {
                                text: "Clear log"
                                onClicked: scannerState.clearLog()
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 6
                            color: "#0f1620"
                            border.color: "#1f2a37"

                            ScrollView {
                                anchors.fill: parent
                                anchors.margins: 8
                                TextArea {
                                    text: scannerState.logText
                                    readOnly: true
                                    wrapMode: Text.NoWrap
                                    color: textColor
                                    font.family: "Consolas"
                                    font.pixelSize: 11
                                    selectByMouse: true
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Shortcut { sequence: "B"; onActivated: uiState.setMode("battle") }
    Shortcut { sequence: "Z"; onActivated: uiState.setMode("zone") }
    Shortcut { sequence: "M"; onActivated: uiState.setMode("manual") }
    Shortcut { sequence: "1"; onActivated: uiState.setSortKey("dps") }
    Shortcut { sequence: "2"; onActivated: uiState.setSortKey("dmg") }
    Shortcut { sequence: "3"; onActivated: uiState.setSortKey("hps") }
    Shortcut { sequence: "4"; onActivated: uiState.setSortKey("heal") }
    Shortcut { sequence: "Q"; onActivated: Qt.quit() }
}
