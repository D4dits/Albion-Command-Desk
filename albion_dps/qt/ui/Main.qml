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
    property int compactControlHeight: 24
    property bool meterView: viewTabs.currentIndex === 0
    property bool scannerView: viewTabs.currentIndex === 1
    property bool marketView: viewTabs.currentIndex === 2

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
                            : (scannerView
                                ? "Scanner status: " + scannerState.statusText + "  |  Updates: " + scannerState.updateText
                                : "Market setup  |  Region: " + marketSetupState.region
                                  + "  |  Recipe: " + marketSetupState.recipeDisplayName
                                  + "  |  Inputs: " + marketSetupState.inputsTotalCost.toFixed(0)
                                  + "  |  Net: " + marketSetupState.netProfitValue.toFixed(0))
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
            implicitHeight: 34
            padding: 0
            background: Rectangle {
                color: "transparent"
                border.width: 0
            }
            TabButton {
                id: meterTab
                text: "Meter"
                height: viewTabs.height
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
                height: viewTabs.height
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
            TabButton {
                id: marketTab
                text: "Market"
                height: viewTabs.height
                background: Rectangle {
                    radius: 5
                    color: marketTab.checked ? accentColor : "#0f1620"
                    border.color: marketTab.checked ? accentColor : borderColor
                }
                contentItem: Text {
                    text: marketTab.text
                    color: marketTab.checked ? "#0b0f14" : textColor
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

                        Text {
                            text: "Scanner uses fixed runtime defaults (upload enabled, official public ingest endpoint)."
                            color: mutedColor
                            font.pixelSize: 11
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

            Item {
                Rectangle {
                    anchors.fill: parent
                    color: panelColor
                    radius: 8
                    border.color: borderColor

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 10

                        Text {
                            text: "Market"
                            color: textColor
                            font.pixelSize: 14
                            font.bold: true
                        }

                        Text {
                            text: marketSetupState.validationText.length === 0
                                ? "Configuration valid."
                                : "Validation: " + marketSetupState.validationText
                            color: marketSetupState.validationText.length === 0 ? "#7ee787" : "#ff7b72"
                            font.pixelSize: 11
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                Layout.fillWidth: true
                                text: "Prices: " + marketSetupState.pricesSource + "  |  " + marketSetupState.pricesStatusText
                                color: mutedColor
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }

                            Button {
                                text: "Refresh prices"
                                implicitHeight: 24
                                onClicked: marketSetupState.refreshPrices()
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            text: marketSetupState.listActionText
                            color: mutedColor
                            font.pixelSize: 11
                            elide: Text.ElideRight
                            visible: text.length > 0
                        }

                        TabBar {
                            id: marketTabs
                            Layout.fillWidth: true
                            implicitHeight: 30
                            spacing: 6
                            padding: 0
                            background: Rectangle {
                                color: "transparent"
                                border.width: 0
                            }

                            TabButton {
                                id: marketOverviewTab
                                text: "Setup + Overview"
                                height: marketTabs.height
                                background: Rectangle {
                                    radius: 5
                                    color: marketOverviewTab.checked ? accentColor : "#0f1620"
                                    border.color: marketOverviewTab.checked ? accentColor : borderColor
                                }
                                contentItem: Text {
                                    text: marketOverviewTab.text
                                    color: marketOverviewTab.checked ? "#0b0f14" : textColor
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                            TabButton {
                                id: marketInputsTab
                                text: "Inputs"
                                height: marketTabs.height
                                background: Rectangle {
                                    radius: 5
                                    color: marketInputsTab.checked ? accentColor : "#0f1620"
                                    border.color: marketInputsTab.checked ? accentColor : borderColor
                                }
                                contentItem: Text {
                                    text: marketInputsTab.text
                                    color: marketInputsTab.checked ? "#0b0f14" : textColor
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                            TabButton {
                                id: marketOutputsTab
                                text: "Outputs"
                                height: marketTabs.height
                                background: Rectangle {
                                    radius: 5
                                    color: marketOutputsTab.checked ? accentColor : "#0f1620"
                                    border.color: marketOutputsTab.checked ? accentColor : borderColor
                                }
                                contentItem: Text {
                                    text: marketOutputsTab.text
                                    color: marketOutputsTab.checked ? "#0b0f14" : textColor
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                            TabButton {
                                id: marketResultsTab
                                text: "Results"
                                height: marketTabs.height
                                background: Rectangle {
                                    radius: 5
                                    color: marketResultsTab.checked ? accentColor : "#0f1620"
                                    border.color: marketResultsTab.checked ? accentColor : borderColor
                                }
                                contentItem: Text {
                                    text: marketResultsTab.text
                                    color: marketResultsTab.checked ? "#0b0f14" : textColor
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                            TabButton {
                                id: marketShoppingTab
                                text: "Shopping"
                                height: marketTabs.height
                                background: Rectangle {
                                    radius: 5
                                    color: marketShoppingTab.checked ? accentColor : "#0f1620"
                                    border.color: marketShoppingTab.checked ? accentColor : borderColor
                                }
                                contentItem: Text {
                                    text: marketShoppingTab.text
                                    color: marketShoppingTab.checked ? "#0b0f14" : textColor
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                            TabButton {
                                id: marketSellingTab
                                text: "Selling"
                                height: marketTabs.height
                                background: Rectangle {
                                    radius: 5
                                    color: marketSellingTab.checked ? accentColor : "#0f1620"
                                    border.color: marketSellingTab.checked ? accentColor : borderColor
                                }
                                contentItem: Text {
                                    text: marketSellingTab.text
                                    color: marketSellingTab.checked ? "#0b0f14" : textColor
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: marketTabs.currentIndex === 0
                            spacing: 12

                            Rectangle {
                                Layout.preferredWidth: 276
                                Layout.minimumWidth: 260
                                Layout.maximumWidth: 300
                                Layout.fillHeight: true
                                radius: 6
                                color: "#0f1620"
                                border.color: "#1f2a37"

                                ScrollView {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    clip: true

                                    ColumnLayout {
                                        width: parent.width
                                        spacing: 8

                                        Text {
                                            text: "Setup"
                                            color: textColor
                                            font.pixelSize: 12
                                            font.bold: true
                                        }

                                        GridLayout {
                                            columns: 2
                                            columnSpacing: 8
                                            rowSpacing: 8
                                            width: parent.width

                                            Text { text: "Recipe"; color: mutedColor; font.pixelSize: 11 }
                                            ComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: marketSetupState.recipeOptionsModel
                                                textRole: "displayName"
                                                currentIndex: marketSetupState.recipeIndex
                                                onActivated: marketSetupState.setRecipeIndex(currentIndex)
                                            }

                                            Text { text: "Tier"; color: mutedColor; font.pixelSize: 11 }
                                            Text { text: String(marketSetupState.recipeTier); color: textColor; font.pixelSize: 11 }

                                            Text { text: "Enchant"; color: mutedColor; font.pixelSize: 11 }
                                            Text { text: String(marketSetupState.recipeEnchant); color: textColor; font.pixelSize: 11 }

                                            Text { text: "Region"; color: mutedColor; font.pixelSize: 11 }
                                            ComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["europe", "west", "east"]
                                                currentIndex: Math.max(0, model.indexOf(marketSetupState.region))
                                                onActivated: marketSetupState.setRegion(currentText)
                                            }

                                            Text { text: "Craft City"; color: mutedColor; font.pixelSize: 11 }
                                            ComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                                                currentIndex: Math.max(0, model.indexOf(marketSetupState.craftCity))
                                                onActivated: marketSetupState.setCraftCity(currentText)
                                            }

                                            Text { text: "Buy City"; color: mutedColor; font.pixelSize: 11 }
                                            ComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                                                currentIndex: Math.max(0, model.indexOf(marketSetupState.defaultBuyCity))
                                                onActivated: marketSetupState.setDefaultBuyCity(currentText)
                                            }

                                            Text { text: "Sell City"; color: mutedColor; font.pixelSize: 11 }
                                            ComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                                                currentIndex: Math.max(0, model.indexOf(marketSetupState.defaultSellCity))
                                                onActivated: marketSetupState.setDefaultSellCity(currentText)
                                            }

                                            Text { text: "Premium"; color: mutedColor; font.pixelSize: 11 }
                                            CheckBox {
                                                implicitHeight: compactControlHeight
                                                checked: marketSetupState.premium
                                                text: checked ? "Enabled" : "Disabled"
                                                onToggled: marketSetupState.setPremium(checked)
                                            }

                                            Text { text: "Craft Runs"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 1
                                                to: 10000
                                                editable: true
                                                value: marketSetupState.craftRuns
                                                onValueChanged: marketSetupState.setCraftRuns(value)
                                            }

                                            Text { text: "Quality"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 1
                                                to: 5
                                                editable: true
                                                value: marketSetupState.quality
                                                onValueChanged: marketSetupState.setQuality(value)
                                            }

                                            Text { text: "Station Fee %"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 0
                                                to: 1000
                                                stepSize: 1
                                                editable: true
                                                value: Math.round(marketSetupState.stationFeePercent * 10)
                                                textFromValue: function(v) { return (v / 10.0).toFixed(1) }
                                                valueFromText: function(t, _locale) {
                                                    var p = parseFloat(t)
                                                    return isNaN(p) ? value : Math.round(p * 10)
                                                }
                                                onValueChanged: marketSetupState.setStationFeePercent(value / 10.0)
                                            }

                                            Text { text: "Market Tax %"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 0
                                                to: 1000
                                                stepSize: 1
                                                editable: true
                                                value: Math.round(marketSetupState.marketTaxPercent * 10)
                                                textFromValue: function(v) { return (v / 10.0).toFixed(1) }
                                                valueFromText: function(t, _locale) {
                                                    var p = parseFloat(t)
                                                    return isNaN(p) ? value : Math.round(p * 10)
                                                }
                                                onValueChanged: marketSetupState.setMarketTaxPercent(value / 10.0)
                                            }

                                            Text { text: "Daily Bonus %"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 0
                                                to: 1000
                                                stepSize: 1
                                                editable: true
                                                value: Math.round(marketSetupState.dailyBonusPercent * 10)
                                                textFromValue: function(v) { return (v / 10.0).toFixed(1) }
                                                valueFromText: function(t, _locale) {
                                                    var p = parseFloat(t)
                                                    return isNaN(p) ? value : Math.round(p * 10)
                                                }
                                                onValueChanged: marketSetupState.setDailyBonusPercent(value / 10.0)
                                            }

                                            Text { text: "Return Rate %"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 0
                                                to: 1000
                                                stepSize: 1
                                                editable: true
                                                value: Math.round(marketSetupState.returnRatePercent * 10)
                                                textFromValue: function(v) { return (v / 10.0).toFixed(1) }
                                                valueFromText: function(t, _locale) {
                                                    var p = parseFloat(t)
                                                    return isNaN(p) ? value : Math.round(p * 10)
                                                }
                                                onValueChanged: marketSetupState.setReturnRatePercent(value / 10.0)
                                            }

                                            Text { text: "Hideout Power %"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 0
                                                to: 1000
                                                stepSize: 1
                                                editable: true
                                                value: Math.round(marketSetupState.hideoutPowerPercent * 10)
                                                textFromValue: function(v) { return (v / 10.0).toFixed(1) }
                                                valueFromText: function(t, _locale) {
                                                    var p = parseFloat(t)
                                                    return isNaN(p) ? value : Math.round(p * 10)
                                                }
                                                onValueChanged: marketSetupState.setHideoutPowerPercent(value / 10.0)
                                            }
                                        }
                                    }
                                }
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                radius: 6
                                color: "#0f1620"
                                border.color: "#1f2a37"

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 8

                                    Text {
                                        text: "Overview"
                                        color: textColor
                                        font.pixelSize: 12
                                        font.bold: true
                                    }

                                    GridLayout {
                                        Layout.fillWidth: true
                                        columns: 3
                                        columnSpacing: 8
                                        rowSpacing: 8

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 62
                                            radius: 4
                                            color: "#111b28"
                                            border.color: "#1f2a37"
                                            Column {
                                                anchors.fill: parent
                                                anchors.margins: 8
                                                spacing: 4
                                                Text { text: "Investment"; color: mutedColor; font.pixelSize: 11 }
                                                Text { text: Number(marketSetupState.inputsTotalCost).toFixed(0); color: textColor; font.pixelSize: 14; font.bold: true }
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 62
                                            radius: 4
                                            color: "#111b28"
                                            border.color: "#1f2a37"
                                            Column {
                                                anchors.fill: parent
                                                anchors.margins: 8
                                                spacing: 4
                                                Text { text: "Revenue"; color: mutedColor; font.pixelSize: 11 }
                                                Text { text: Number(marketSetupState.outputsTotalValue).toFixed(0); color: textColor; font.pixelSize: 14; font.bold: true }
                                            }
                                        }
                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 62
                                            radius: 4
                                            color: "#111b28"
                                            border.color: "#1f2a37"
                                            Column {
                                                anchors.fill: parent
                                                anchors.margins: 8
                                                spacing: 4
                                                Text { text: "Net"; color: mutedColor; font.pixelSize: 11 }
                                                Text {
                                                    text: Number(marketSetupState.netProfitValue).toFixed(0)
                                                    color: marketSetupState.netProfitValue >= 0 ? "#7ee787" : "#ff7b72"
                                                    font.pixelSize: 14
                                                    font.bold: true
                                                }
                                            }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 28
                                        radius: 4
                                        color: "#111b28"
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 6
                                            spacing: 12
                                            Text { text: "Margin: " + Number(marketSetupState.marginPercent).toFixed(2) + "%"; color: mutedColor; font.pixelSize: 11 }
                                            Text { text: "Focus used: " + Number(marketSetupState.focusUsed).toFixed(0); color: mutedColor; font.pixelSize: 11 }
                                            Text { text: "SPF: " + Number(marketSetupState.silverPerFocus).toFixed(2); color: mutedColor; font.pixelSize: 11 }
                                            Item { Layout.fillWidth: true }
                                            Text { text: "Recipe: " + marketSetupState.recipeDisplayName; color: textColor; font.pixelSize: 11; elide: Text.ElideRight }
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        radius: 4
                                        color: "#111b28"
                                        border.color: "#1f2a37"
                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 8
                                            spacing: 6
                                            Text { text: "Overview notes"; color: textColor; font.pixelSize: 12; font.bold: true }
                                            Text { text: "Inputs/Outputs tabs: per-item pricing mode and manual prices."; color: mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                            Text { text: "Results tab: sortable per-item profitability and breakdown."; color: mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                            Text { text: "Shopping/Selling tabs: grouped lists with CSV copy/export."; color: mutedColor; font.pixelSize: 11; wrapMode: Text.WordWrap }
                                        }
                                    }
                                }
                            }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: marketTabs.currentIndex === 1
                            radius: 6
                            color: "#0f1620"
                            border.color: "#1f2a37"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                Text {
                                    text: "Inputs"
                                    color: textColor
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 24
                                    radius: 4
                                    color: "#111b28"

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: 8
                                        Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 180 }
                                        Text { text: "Qty"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 140 }
                                        Text { text: "Mode"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 95 }
                                        Text { text: "Manual"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Unit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Total"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true }
                                    }
                                }

                                ListView {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    model: marketSetupState.inputsModel

                                    delegate: Rectangle {
                                        width: ListView.view.width
                                        height: 28
                                        color: index % 2 === 0 ? "#0f1620" : "#101924"

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 8
                                            Text { text: item; color: textColor; font.pixelSize: 11; Layout.preferredWidth: 180; elide: Text.ElideRight }
                                            Text { text: Number(quantity).toFixed(2); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                            ComboBox {
                                                Layout.preferredWidth: 140
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                                                currentIndex: Math.max(0, model.indexOf(city))
                                                onActivated: marketSetupState.setOutputCity(itemId, currentText)
                                            }
                                            ComboBox {
                                                Layout.preferredWidth: 95
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["sell_order", "buy_order", "average", "manual"]
                                                currentIndex: Math.max(0, model.indexOf(priceType))
                                                onActivated: marketSetupState.setInputPriceType(itemId, currentText)
                                            }
                                            TextField {
                                                Layout.preferredWidth: 70
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                text: manualPrice > 0 ? String(manualPrice) : ""
                                                placeholderText: "-"
                                                enabled: priceType === "manual"
                                                inputMethodHints: Qt.ImhDigitsOnly
                                                onEditingFinished: marketSetupState.setInputManualPrice(itemId, text)
                                            }
                                            Text { text: Number(unitPrice).toFixed(0); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                            Text { text: Number(totalCost).toFixed(0); color: textColor; font.pixelSize: 11; Layout.fillWidth: true }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 28
                                    radius: 4
                                    color: "#111b28"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        Text { text: "Total input cost"; color: mutedColor; font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Text { text: Number(marketSetupState.inputsTotalCost).toFixed(0); color: textColor; font.pixelSize: 12; font.bold: true }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: marketTabs.currentIndex === 2
                            radius: 6
                            color: "#0f1620"
                            border.color: "#1f2a37"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                Text {
                                    text: "Outputs"
                                    color: textColor
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 24
                                    radius: 4
                                    color: "#111b28"

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: 8
                                        Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 180 }
                                        Text { text: "Qty"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 110 }
                                        Text { text: "Mode"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 95 }
                                        Text { text: "Manual"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Unit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Total"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true }
                                    }
                                }

                                ListView {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    model: marketSetupState.outputsModel

                                    delegate: Rectangle {
                                        width: ListView.view.width
                                        height: 28
                                        color: index % 2 === 0 ? "#0f1620" : "#101924"

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 8
                                            Text { text: item; color: textColor; font.pixelSize: 11; Layout.preferredWidth: 180; elide: Text.ElideRight }
                                            Text { text: Number(quantity).toFixed(2); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                            Text { text: city; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 110; elide: Text.ElideRight }
                                            ComboBox {
                                                Layout.preferredWidth: 95
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["buy_order", "sell_order", "average", "manual"]
                                                currentIndex: Math.max(0, model.indexOf(priceType))
                                                onActivated: marketSetupState.setOutputPriceType(itemId, currentText)
                                            }
                                            TextField {
                                                Layout.preferredWidth: 70
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                text: manualPrice > 0 ? String(manualPrice) : ""
                                                placeholderText: "-"
                                                enabled: priceType === "manual"
                                                inputMethodHints: Qt.ImhDigitsOnly
                                                onEditingFinished: marketSetupState.setOutputManualPrice(itemId, text)
                                            }
                                            Text { text: Number(unitPrice).toFixed(0); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                            Text { text: Number(totalValue).toFixed(0); color: textColor; font.pixelSize: 11; Layout.fillWidth: true }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 28
                                    radius: 4
                                    color: "#111b28"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        Text { text: "Total output value"; color: mutedColor; font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Text { text: Number(marketSetupState.outputsTotalValue).toFixed(0); color: textColor; font.pixelSize: 12; font.bold: true }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: marketTabs.currentIndex === 3
                            radius: 6
                            color: "#0f1620"
                            border.color: "#1f2a37"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Text {
                                        text: "Results"
                                        color: textColor
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                    Item { Layout.fillWidth: true }
                                    Text {
                                        text: "Sort"
                                        color: mutedColor
                                        font.pixelSize: 11
                                    }
                                    ComboBox {
                                        Layout.preferredWidth: 120
                                        implicitHeight: compactControlHeight
                                        font.pixelSize: 11
                                        model: ["profit", "margin", "revenue"]
                                        currentIndex: Math.max(0, model.indexOf(marketSetupState.resultsSortKey))
                                        onActivated: marketSetupState.setResultsSortKey(currentText)
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 28
                                    radius: 4
                                    color: "#111b28"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 12
                                        Text { text: "Investment: " + Number(marketSetupState.inputsTotalCost).toFixed(0); color: mutedColor; font.pixelSize: 11 }
                                        Text { text: "Revenue: " + Number(marketSetupState.outputsTotalValue).toFixed(0); color: mutedColor; font.pixelSize: 11 }
                                        Text { text: "Net: " + Number(marketSetupState.netProfitValue).toFixed(0); color: marketSetupState.netProfitValue >= 0 ? "#7ee787" : "#ff7b72"; font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Text { text: "Margin: " + Number(marketSetupState.marginPercent).toFixed(2) + "%"; color: marketSetupState.marginPercent >= 0 ? "#7ee787" : "#ff7b72"; font.pixelSize: 11 }
                                        Text { text: "SPF: " + Number(marketSetupState.silverPerFocus).toFixed(2); color: mutedColor; font.pixelSize: 11 }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 24
                                    radius: 4
                                    color: "#111b28"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: 6
                                        Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 145 }
                                        Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 100 }
                                        Text { text: "Qty"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                        Text { text: "Revenue"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Cost"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Fee"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                        Text { text: "Tax"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                        Text { text: "Profit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Margin"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                        Text { text: "Demand"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true }
                                    }
                                }

                                ListView {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 210
                                    clip: true
                                    model: marketSetupState.resultsItemsModel

                                    delegate: Rectangle {
                                        width: ListView.view.width
                                        height: 26
                                        color: index % 2 === 0 ? "#0f1620" : "#101924"
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 6
                                            Text { text: item; color: textColor; font.pixelSize: 11; Layout.preferredWidth: 145; elide: Text.ElideRight }
                                            Text { text: city; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 100; elide: Text.ElideRight }
                                            Text { text: Number(quantity).toFixed(2); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                            Text { text: Number(revenue).toFixed(0); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                            Text { text: Number(cost).toFixed(0); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                            Text { text: Number(feeValue).toFixed(0); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                            Text { text: Number(taxValue).toFixed(0); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                            Text { text: Number(profit).toFixed(0); color: profit >= 0 ? "#7ee787" : "#ff7b72"; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                            Text { text: Number(marginPercent).toFixed(1) + "%"; color: marginPercent >= 0 ? "#7ee787" : "#ff7b72"; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                            Text { text: Number(demandProxy).toFixed(1) + "%"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true }
                                        }
                                    }
                                }

                                Text {
                                    text: "Breakdown"
                                    color: textColor
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    radius: 4
                                    color: "#111b28"
                                    border.color: "#1f2a37"

                                    ListView {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        clip: true
                                        model: marketSetupState.breakdownModel

                                        delegate: Rectangle {
                                            width: ListView.view.width
                                            height: 24
                                            color: index % 2 === 0 ? "#111b28" : "#0f1620"
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                Text { text: label; color: mutedColor; font.pixelSize: 11 }
                                                Item { Layout.fillWidth: true }
                                                Text {
                                                    text: Number(value).toFixed(2)
                                                    color: (label === "Net profit" && value < 0) ? "#ff7b72" : textColor
                                                    font.pixelSize: 11
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: marketTabs.currentIndex === 4
                            radius: 6
                            color: "#0f1620"
                            border.color: "#1f2a37"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                Text { text: "Shopping List"; color: textColor; font.pixelSize: 12; font.bold: true }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Button {
                                        text: "Copy CSV"
                                        implicitHeight: compactControlHeight
                                        onClicked: marketSetupState.copyShoppingCsv()
                                    }
                                    TextField {
                                        id: shoppingExportPath
                                        Layout.fillWidth: true
                                        implicitHeight: compactControlHeight
                                        font.pixelSize: 11
                                        placeholderText: "artifacts/market/shopping.csv"
                                        text: "artifacts/market/shopping.csv"
                                    }
                                    Button {
                                        text: "Export CSV"
                                        implicitHeight: compactControlHeight
                                        onClicked: marketSetupState.exportShoppingCsv(shoppingExportPath.text)
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 24
                                    radius: 4
                                    color: "#111b28"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: 8
                                        Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 220 }
                                        Text { text: "Qty"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90 }
                                        Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 120 }
                                        Text { text: "Mode"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90 }
                                        Text { text: "Unit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 80 }
                                        Text { text: "Total"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true }
                                    }
                                }

                                ListView {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    model: marketSetupState.shoppingModel

                                    delegate: Rectangle {
                                        width: ListView.view.width
                                        height: 28
                                        color: index % 2 === 0 ? "#0f1620" : "#101924"
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 8
                                            Text { text: item; color: textColor; font.pixelSize: 11; Layout.preferredWidth: 220; elide: Text.ElideRight }
                                            Text { text: Number(quantity).toFixed(2); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90 }
                                            Text { text: city; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 120; elide: Text.ElideRight }
                                            Text { text: priceType; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90; elide: Text.ElideRight }
                                            Text { text: Number(unitPrice).toFixed(0); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 80 }
                                            Text { text: Number(totalCost).toFixed(0); color: textColor; font.pixelSize: 11; Layout.fillWidth: true }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 28
                                    radius: 4
                                    color: "#111b28"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        Text { text: "Shopping total"; color: mutedColor; font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Text { text: Number(marketSetupState.inputsTotalCost).toFixed(0); color: textColor; font.pixelSize: 12; font.bold: true }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            visible: marketTabs.currentIndex === 5
                            radius: 6
                            color: "#0f1620"
                            border.color: "#1f2a37"

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                Text { text: "Selling List"; color: textColor; font.pixelSize: 12; font.bold: true }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Button {
                                        text: "Copy CSV"
                                        implicitHeight: compactControlHeight
                                        onClicked: marketSetupState.copySellingCsv()
                                    }
                                    TextField {
                                        id: sellingExportPath
                                        Layout.fillWidth: true
                                        implicitHeight: compactControlHeight
                                        font.pixelSize: 11
                                        placeholderText: "artifacts/market/selling.csv"
                                        text: "artifacts/market/selling.csv"
                                    }
                                    Button {
                                        text: "Export CSV"
                                        implicitHeight: compactControlHeight
                                        onClicked: marketSetupState.exportSellingCsv(sellingExportPath.text)
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 24
                                    radius: 4
                                    color: "#111b28"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: 8
                                        Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 220 }
                                        Text { text: "Qty"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90 }
                                        Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 120 }
                                        Text { text: "Mode"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90 }
                                        Text { text: "Unit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 80 }
                                        Text { text: "Total"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true }
                                    }
                                }

                                ListView {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    model: marketSetupState.sellingModel

                                    delegate: Rectangle {
                                        width: ListView.view.width
                                        height: 28
                                        color: index % 2 === 0 ? "#0f1620" : "#101924"
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 8
                                            Text { text: item; color: textColor; font.pixelSize: 11; Layout.preferredWidth: 220; elide: Text.ElideRight }
                                            Text { text: Number(quantity).toFixed(2); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90 }
                                            Text { text: city; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 120; elide: Text.ElideRight }
                                            Text { text: priceType; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 90; elide: Text.ElideRight }
                                            Text { text: Number(unitPrice).toFixed(0); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 80 }
                                            Text { text: Number(totalValue).toFixed(0); color: textColor; font.pixelSize: 11; Layout.fillWidth: true }
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 28
                                    radius: 4
                                    color: "#111b28"
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        Text { text: "Selling total"; color: mutedColor; font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Text { text: Number(marketSetupState.outputsTotalValue).toFixed(0); color: textColor; font.pixelSize: 12; font.bold: true }
                                    }
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
