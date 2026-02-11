import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: root
    visible: true
    width: 1120
    height: 720
    title: "Albion Command Desk"
    icon: "command_desk_icon.xpm"
    color: "#0b0f14"

    property color textColor: "#e6edf3"
    property color mutedColor: "#9aa4af"
    property color accentColor: "#4aa3ff"
    property color panelColor: "#131a22"
    property color borderColor: "#1f2a37"
    property int compactControlHeight: 24
    property int marketColumnSpacing: 6
    property int marketSetupPanelWidth: Math.max(300, Math.min(370, Math.round(width * 0.30)))
    property int marketInputsItemWidth: Math.max(150, Math.min(240, Math.round(width * 0.17)))
    property int marketInputsQtyWidth: 62
    property int marketInputsStockWidth: 72
    property int marketInputsBuyWidth: 62
    property int marketInputsCityWidth: 118
    property int marketInputsModeWidth: 96
    property int marketInputsManualWidth: 74
    property int marketInputsUnitWidth: 78
    property int marketInputsAgeWidth: 76
    property int marketInputsTotalMinWidth: 120
    property int marketInputsContentMinWidth: marketInputsItemWidth
        + marketInputsQtyWidth
        + marketInputsCityWidth
        + marketInputsModeWidth
        + marketInputsManualWidth
        + marketInputsUnitWidth
        + marketInputsAgeWidth
        + marketInputsTotalMinWidth
        + marketInputsStockWidth
        + marketInputsBuyWidth
        + marketColumnSpacing * 9
        + 12
    property int marketOutputsItemWidth: Math.max(145, Math.min(230, Math.round(width * 0.16)))
    property int marketOutputsQtyWidth: 58
    property int marketOutputsCityWidth: 108
    property int marketOutputsModeWidth: 92
    property int marketOutputsManualWidth: 70
    property int marketOutputsUnitWidth: 74
    property int marketOutputsGrossWidth: 82
    property int marketOutputsFeeWidth: 74
    property int marketOutputsTaxWidth: 74
    property int marketOutputsNetMinWidth: 116
    property int marketOutputsContentMinWidth: marketOutputsItemWidth
        + marketOutputsQtyWidth
        + marketOutputsCityWidth
        + marketOutputsModeWidth
        + marketOutputsManualWidth
        + marketOutputsUnitWidth
        + marketOutputsGrossWidth
        + marketOutputsFeeWidth
        + marketOutputsTaxWidth
        + marketOutputsNetMinWidth
        + marketColumnSpacing * 9
        + 12
    property bool meterView: viewTabs.currentIndex === 0
    property bool scannerView: viewTabs.currentIndex === 1
    property bool marketView: viewTabs.currentIndex === 2
    property bool marketDiagnosticsVisible: false

    function formatInt(value) {
        var n = Number(value)
        if (!isFinite(n)) {
            return "0"
        }
        var whole = Math.round(n)
        var sign = whole < 0 ? "-" : ""
        var raw = Math.abs(whole).toString()
        return sign + raw.replace(/\B(?=(\d{3})+(?!\d))/g, " ")
    }

    function formatFixed(value, decimals) {
        var n = Number(value)
        if (!isFinite(n)) {
            n = 0
        }
        var fixed = n.toFixed(Math.max(0, decimals))
        var parts = fixed.split(".")
        var whole = Number(parts[0] || "0")
        if (parts.length === 1 || decimals <= 0) {
            return formatInt(whole)
        }
        return formatInt(whole) + "." + parts[1]
    }

    function adpAgeColor(ageText) {
        var raw = String(ageText || "").trim().toLowerCase()
        if (raw === "manual") {
            return "#79c0ff"
        }
        if (raw === "n/a" || raw === "unknown" || raw.length === 0) {
            return mutedColor
        }
        var minutes = 0
        var dayMatch = raw.match(/(\d+)\s*d/)
        if (dayMatch) {
            minutes += parseInt(dayMatch[1]) * 1440
        }
        var hourMatch = raw.match(/(\d+)\s*h/)
        if (hourMatch) {
            minutes += parseInt(hourMatch[1]) * 60
        }
        var minuteMatch = raw.match(/(\d+)\s*m/)
        if (minuteMatch) {
            minutes += parseInt(minuteMatch[1])
        } else if (raw.indexOf("<1m") >= 0) {
            minutes += 0
        }
        if (minutes <= 20) {
            return "#2ea043"
        }
        if (minutes <= 60) {
            return "#e3b341"
        }
        return "#ff7b72"
    }

    function copyCellText(value) {
        marketSetupState.copyText(String(value === undefined || value === null ? "" : value))
    }

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
                        text: "Albion Command Desk"
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
                                  + "  |  Crafts: " + marketSetupState.craftPlanEnabledCount + "/" + marketSetupState.craftPlanCount
                                  + "  |  Inputs: " + formatInt(marketSetupState.inputsTotalCost)
                                  + "  |  Net: " + formatInt(marketSetupState.netProfitValue))
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

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text {
                                text: "AlbionData Scanner"
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
                                ToolTip.text: "Albion Data uploader control.\nUse it to check/sync client repo, start or stop scanner,\nand monitor detailed runtime logs."
                            }
                            Item { Layout.fillWidth: true }
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
                                text: "Start scanner (sudo)"
                                enabled: !scannerState.running
                                onClicked: scannerState.startScannerSudo()
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
                            clip: true

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

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Text {
                                text: "Market"
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
                                ToolTip.text: "Craft profitability workspace.\nConfigure setup, pull AOData prices, build craft list,\nand analyze Inputs/Outputs/Results with profit metrics."
                            }
                            Item { Layout.fillWidth: true }
                        }

                        Text {
                            text: marketSetupState.validationText.length === 0
                                ? "Configuration valid."
                                : "Validation: " + marketSetupState.validationText
                            color: marketSetupState.validationText.length === 0 ? "#7ee787" : "#ff7b72"
                            font.pixelSize: 11
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Text {
                                Layout.fillWidth: true
                                text: (marketSetupState.priceFetchInProgress ? "[loading] " : "")
                                    + "Prices: " + marketSetupState.pricesSource + "  |  " + marketSetupState.pricesStatusText
                                color: marketSetupState.pricesSource === "fallback" ? "#ffb86b" : mutedColor
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Text {
                                    text: "Region"
                                    color: mutedColor
                                    font.pixelSize: 11
                                }
                                ComboBox {
                                    implicitWidth: 110
                                    implicitHeight: 24
                                    font.pixelSize: 11
                                    model: ["europe", "west", "east"]
                                    currentIndex: Math.max(0, model.indexOf(marketSetupState.region))
                                    onActivated: marketSetupState.setRegion(currentText)
                                }

                                CheckBox {
                                    id: premiumCheck
                                    implicitHeight: 24
                                    checked: marketSetupState.premium
                                    text: "Premium"
                                    palette.windowText: textColor
                                    palette.text: textColor
                                    onToggled: marketSetupState.setPremium(checked)
                                }

                                Item { Layout.fillWidth: true }

                                Button {
                                    text: marketSetupState.refreshPricesButtonText
                                    implicitHeight: 24
                                    enabled: marketSetupState.canRefreshPrices
                                    onClicked: marketSetupState.refreshPrices()
                                }
                                Button {
                                    text: "Show raw AOData"
                                    implicitHeight: 24
                                    onClicked: marketSetupState.showAoDataRaw()
                                }
                                Button {
                                    text: marketDiagnosticsVisible ? "Hide diagnostics" : "Show diagnostics"
                                    implicitHeight: 24
                                    onClicked: marketDiagnosticsVisible = !marketDiagnosticsVisible
                                }
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
                            onCurrentIndexChanged: marketSetupState.setActiveMarketTab(currentIndex)
                            Component.onCompleted: marketSetupState.setActiveMarketTab(currentIndex)
                            background: Rectangle {
                                color: "transparent"
                                border.width: 0
                            }

                            TabButton {
                                id: marketOverviewTab
                                text: "Setup"
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
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: marketDiagnosticsVisible ? 110 : 0
                            Layout.minimumHeight: marketDiagnosticsVisible ? 82 : 0
                            Layout.maximumHeight: marketDiagnosticsVisible ? 140 : 0
                            visible: marketDiagnosticsVisible
                            radius: 6
                            color: "#0f1620"
                            border.color: "#1f2a37"
                            clip: true

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 6
                                spacing: 4

                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        text: "Market diagnostics"
                                        color: textColor
                                        font.pixelSize: 11
                                        font.bold: true
                                    }
                                    Item { Layout.fillWidth: true }
                                    Button {
                                        text: "Clear"
                                        implicitHeight: 20
                                        font.pixelSize: 10
                                        onClicked: marketSetupState.clearDiagnostics()
                                    }
                                }

                                ScrollView {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    TextArea {
                                        text: marketSetupState.diagnosticsText
                                        readOnly: true
                                        wrapMode: Text.NoWrap
                                        color: mutedColor
                                        font.family: "Consolas"
                                        font.pixelSize: 10
                                        selectByMouse: true
                                    }
                                }
                            }
                        }

                        StackLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            currentIndex: marketTabs.currentIndex

                            RowLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 12

                            Rectangle {
                                Layout.preferredWidth: marketSetupPanelWidth
                                Layout.minimumWidth: 300
                                Layout.maximumWidth: 390
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

                                            Text { text: "Craft Search"; color: mutedColor; font.pixelSize: 11 }
                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 6

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 6

                                                    TextField {
                                                        id: recipeSearchInput
                                                        Layout.fillWidth: true
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        placeholderText: "e.g. mistcaller 5.2"
                                                        onTextChanged: marketSetupState.setRecipeSearchQuery(text)
                                                        onAccepted: {
                                                            marketSetupState.addFirstRecipeOption()
                                                            focus = false
                                                        }
                                                    }
                                                }

                                                Rectangle {
                                                    Layout.fillWidth: true
                                                    Layout.preferredHeight: 170
                                                    visible: recipeSearchInput.activeFocus && recipeSuggestions.count > 0
                                                    radius: 4
                                                    color: "#111b28"
                                                    border.color: "#1f2a37"

                                                    ListView {
                                                        id: recipeSuggestions
                                                        anchors.fill: parent
                                                        anchors.margins: 4
                                                        clip: true
                                                        reuseItems: true
                                                        cacheBuffer: 600
                                                        model: marketSetupState.recipeOptionsModel

                                                        delegate: Rectangle {
                                                            width: ListView.view.width
                                                            height: 26
                                                            color: recipeId === marketSetupState.recipeId
                                                                ? "#1b2635"
                                                                : (index % 2 === 0 ? "#111b28" : "#0f1620")

                                                            RowLayout {
                                                                anchors.fill: parent
                                                                anchors.margins: 4
                                                                spacing: 6
                                                                Text {
                                                                    text: displayName
                                                                    color: textColor
                                                                    font.pixelSize: 11
                                                                    Layout.fillWidth: true
                                                                    elide: Text.ElideRight
                                                                }
                                                                Text {
                                                                    text: "T" + tier + "." + enchant
                                                                    color: mutedColor
                                                                    font.pixelSize: 11
                                                                    Layout.preferredWidth: 58
                                                                    horizontalAlignment: Text.AlignRight
                                                                }
                                                            }

                                                            MouseArea {
                                                                anchors.fill: parent
                                                                onClicked: {
                                                                    marketSetupState.addRecipeAtIndex(index)
                                                                }
                                                            }
                                                        }
                                                    }

                                                    Text {
                                                        anchors.centerIn: parent
                                                        visible: recipeSuggestions.count === 0
                                                        text: "No matches"
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                    }
                                                }
                                            }

                                            Text { text: "Craft City"; color: mutedColor; font.pixelSize: 11 }
                                            ComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: [
                                                    "Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien",
                                                    "Arthur's Rest", "Merlyn's Rest", "Morgana's Rest"
                                                ]
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

                                            Text { text: "Default Runs"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 1
                                                to: 10000
                                                editable: true

                                                value: marketSetupState.craftRuns
                                                onValueModified: marketSetupState.setCraftRuns(value)
                                            }

                                            Text { text: "Usage Fee (1-999)"; color: mutedColor; font.pixelSize: 11 }
                                            SpinBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                from: 1
                                                to: 999
                                                stepSize: 1
                                                editable: true

                                                value: Math.round(marketSetupState.stationFeePercent)
                                                textFromValue: function(v) { return String(v) }
                                                valueFromText: function(t, _locale) {
                                                    var p = parseFloat(t)
                                                    return isNaN(p) ? value : Math.round(p)
                                                }
                                                onValueModified: marketSetupState.setStationFeePercent(value)
                                            }

                                            Text { text: "Market Fees % (auto)"; color: mutedColor; font.pixelSize: 11 }
                                            Text {
                                                Layout.fillWidth: true
                                                text: marketSetupState.premium
                                                    ? "4.0% (tax) + 2.5% (setup) = " + Number(marketSetupState.marketTaxPercent).toFixed(1) + "%"
                                                    : "8.0% (tax) + 2.5% (setup) = " + Number(marketSetupState.marketTaxPercent).toFixed(1) + "%"
                                                color: textColor
                                                font.pixelSize: 11
                                            }

                                            Text { text: "Default Daily Bonus"; color: mutedColor; font.pixelSize: 11 }
                                            ComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["0%", "10%", "20%"]
                                                currentIndex: Math.max(0, model.indexOf(String(marketSetupState.dailyBonusPreset) + "%"))
                                                onActivated: marketSetupState.setDailyBonusPreset(currentText)
                                            }

                                            Text { text: "Use Focus (RRR)"; color: mutedColor; font.pixelSize: 11 }
                                            CheckBox {
                                                id: focusRrrCheck
                                                Layout.fillWidth: true
                                                checked: marketSetupState.focusEnabled
                                                text: checked ? "Enabled" : "Disabled"
                                                indicator: Rectangle {
                                                    implicitWidth: 14
                                                    implicitHeight: 14
                                                    radius: 3
                                                    border.color: "#6b7b8f"
                                                    color: focusRrrCheck.checked ? "#2ea043" : "transparent"
                                                }
                                                contentItem: Text {
                                                    leftPadding: focusRrrCheck.indicator.width + 8
                                                    text: focusRrrCheck.text
                                                    color: focusRrrCheck.checked ? "#7ee787" : "#f2b8b5"
                                                    font.pixelSize: 11
                                                    verticalAlignment: Text.AlignVCenter
                                                }
                                                onToggled: marketSetupState.setFocusEnabled(checked)
                                            }
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            radius: 4
                                            color: "#111b28"
                                            border.color: "#1f2a37"
                                            implicitHeight: 130

                                            ColumnLayout {
                                                anchors.fill: parent
                                                anchors.margins: 8
                                                spacing: 6

                                                Text {
                                                    text: "Presets"
                                                    color: textColor
                                                    font.pixelSize: 11
                                                    font.bold: true
                                                }

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 6
                                                    Text {
                                                        text: "Saved"
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: 42
                                                    }
                                                    ComboBox {
                                                        id: presetCombo
                                                        Layout.fillWidth: true
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        model: marketSetupState.presetNames
                                                        currentIndex: Math.max(0, model.indexOf(marketSetupState.selectedPresetName))
                                                        onActivated: {
                                                            marketSetupState.setSelectedPresetName(currentText)
                                                            presetNameField.text = currentText
                                                        }
                                                    }
                                                }

                                                TextField {
                                                    id: presetNameField
                                                    Layout.fillWidth: true
                                                    implicitHeight: compactControlHeight
                                                    font.pixelSize: 11
                                                    placeholderText: "preset name"
                                                    text: marketSetupState.selectedPresetName
                                                }

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 6
                                                    Button {
                                                        text: "Save"
                                                        Layout.fillWidth: true
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        onClicked: {
                                                            var name = presetNameField.text.trim()
                                                            if (!name.length && presetCombo.currentText) {
                                                                name = String(presetCombo.currentText).trim()
                                                            }
                                                            marketSetupState.savePreset(name)
                                                            presetNameField.text = name
                                                        }
                                                    }
                                                    Button {
                                                        text: "Load"
                                                        Layout.fillWidth: true
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        enabled: presetNameField.text.trim().length > 0 || String(presetCombo.currentText || "").trim().length > 0
                                                        onClicked: {
                                                            var name = presetNameField.text.trim()
                                                            if (!name.length && presetCombo.currentText) {
                                                                name = String(presetCombo.currentText).trim()
                                                            }
                                                            marketSetupState.loadPreset(name)
                                                            presetNameField.text = name
                                                        }
                                                    }
                                                    Button {
                                                        text: "Del"
                                                        Layout.fillWidth: true
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        enabled: presetNameField.text.trim().length > 0 || String(presetCombo.currentText || "").trim().length > 0
                                                        onClicked: {
                                                            var name = presetNameField.text.trim()
                                                            if (!name.length && presetCombo.currentText) {
                                                                name = String(presetCombo.currentText).trim()
                                                            }
                                                            marketSetupState.deletePreset(name)
                                                            presetNameField.text = name
                                                        }
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
                                radius: 6
                                color: "#0f1620"
                                border.color: "#1f2a37"

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 8

                                    RowLayout {
                                        Layout.fillWidth: true
                                        Text {
                                            text: "Crafts Table"
                                            color: textColor
                                            font.pixelSize: 12
                                            font.bold: true
                                        }
                                        Item { Layout.fillWidth: true }
                                        Text {
                                            text: marketSetupState.craftPlanEnabledCount + "/" + marketSetupState.craftPlanCount + " active"
                                            color: mutedColor
                                            font.pixelSize: 11
                                        }
                                        Button {
                                            text: "Clear"
                                            implicitHeight: 20
                                            implicitWidth: 52
                                            font.pixelSize: 10
                                            onClicked: marketSetupState.clearCraftPlan()
                                        }
                                    }

                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 22
                                        radius: 4
                                        color: "#111b28"
                                        border.color: "#1f2a37"
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 6
                                            Text { text: "On"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 24 }
                                            Text { text: "Craft"; color: mutedColor; font.pixelSize: 10; Layout.fillWidth: true }
                                            Text { text: "Tier"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 46 }
                                            Text { text: "City"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 118 }
                                            Text { text: "Bonus"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 70 }
                                            Text { text: "RRR"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 54 }
                                            Text { text: "Runs"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 68 }
                                            Text { text: "P/L%"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 54 }
                                            Text { text: ""; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 40 }
                                        }
                                    }

                                    ListView {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        Layout.preferredHeight: Math.max(190, Math.min(420, 86 + marketSetupState.craftPlanCount * 24))
                                        clip: true
                                        spacing: 1
                                        reuseItems: true
                                        cacheBuffer: 600
                                        model: marketSetupState.craftPlanModel

                                        delegate: Rectangle {
                                            width: ListView.view.width
                                            height: 32
                                            color: recipeId === marketSetupState.recipeId
                                                ? "#1b2635"
                                                : (index % 2 === 0 ? "#0f1620" : "#101924")

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: 4
                                                anchors.rightMargin: 4
                                                spacing: 6

                                                CheckBox {
                                                    id: enabledCheck
                                                    Layout.preferredWidth: 24
                                                    checked: isEnabled
                                                    text: ""
                                                    indicator: Rectangle {
                                                        implicitWidth: 12
                                                        implicitHeight: 12
                                                        radius: 2
                                                        border.color: "#5f6b7a"
                                                        color: enabledCheck.checked ? accentColor : "transparent"
                                                    }
                                                    contentItem: Item { implicitWidth: 0; implicitHeight: 0 }
                                                    onToggled: marketSetupState.setPlanRowEnabled(rowId, checked)
                                                }

                                                Text {
                                                    Layout.fillWidth: true
                                                    text: displayName
                                                    color: textColor
                                                    font.pixelSize: 10
                                                    elide: Text.ElideRight
                                                }

                                                Text {
                                                    Layout.preferredWidth: 46
                                                    text: "T" + tier + "." + enchant
                                                    color: mutedColor
                                                    font.pixelSize: 10
                                                }

                                                ComboBox {
                                                    Layout.preferredWidth: 118
                                                    implicitHeight: 24
                                                    font.pixelSize: 10
                                                    model: [
                                                        "Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien",
                                                        "Arthur's Rest", "Merlyn's Rest", "Morgana's Rest"
                                                    ]
                                                    currentIndex: Math.max(0, model.indexOf(craftCity))
                                                    onActivated: marketSetupState.setPlanRowCraftCity(rowId, currentText)
                                                }

                                                ComboBox {
                                                    Layout.preferredWidth: 70
                                                    implicitHeight: 24
                                                    font.pixelSize: 10
                                                    model: ["0%", "10%", "20%"]
                                                    currentIndex: Math.max(0, model.indexOf(String(Math.round(Number(dailyBonusPercent))) + "%"))
                                                    onActivated: marketSetupState.setPlanRowDailyBonus(rowId, currentText)
                                                }

                                                Text {
                                                    Layout.preferredWidth: 54
                                                    text: returnRatePercent === undefined || returnRatePercent === null
                                                        ? "-"
                                                        : Number(returnRatePercent).toFixed(1) + "%"
                                                    color: mutedColor
                                                    font.pixelSize: 10
                                                    horizontalAlignment: Text.AlignRight
                                                }

                                                TextField {
                                                    Layout.preferredWidth: 68
                                                    implicitHeight: 24
                                                    font.pixelSize: 10
                                                    text: String(runs)
                                                    color: textColor
                                                    horizontalAlignment: TextInput.AlignHCenter
                                                    verticalAlignment: TextInput.AlignVCenter
                                                    topPadding: 2
                                                    bottomPadding: 2
                                                    leftPadding: 3
                                                    rightPadding: 3
                                                    inputMethodHints: Qt.ImhDigitsOnly
                                                    background: Rectangle {
                                                        radius: 2
                                                        color: "#0f1620"
                                                        border.color: "#2a3a51"
                                                    }
                                                    onEditingFinished: {
                                                        var parsed = parseInt(text)
                                                        if (isNaN(parsed) || parsed < 1) {
                                                            parsed = 1
                                                        }
                                                        marketSetupState.setPlanRowRuns(rowId, parsed)
                                                        text = String(parsed)
                                                    }
                                                }

                                                Text {
                                                    Layout.preferredWidth: 54
                                                    text: profitPercent === undefined || profitPercent === null
                                                        ? "-"
                                                        : Number(profitPercent).toFixed(1) + "%"
                                                    color: profitPercent === undefined || profitPercent === null
                                                        ? mutedColor
                                                        : (Number(profitPercent) >= 0 ? "#7ee787" : "#ff7b72")
                                                    font.pixelSize: 10
                                                    horizontalAlignment: Text.AlignRight
                                                }

                                                Button {
                                                    Layout.preferredWidth: 40
                                                    implicitHeight: 22
                                                    font.pixelSize: 10
                                                    text: "Del"
                                                    onClicked: marketSetupState.removePlanRow(rowId)
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

                                ScrollView {
                                    id: marketInputsScroll
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true

                                    ColumnLayout {
                                        width: Math.max(marketInputsScroll.availableWidth, marketInputsContentMinWidth)
                                        spacing: 6

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 24
                                            radius: 4
                                            color: "#111b28"

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                spacing: marketColumnSpacing
                                                Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsItemWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Need"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsQtyWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Stock"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsStockWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Buy"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsBuyWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsCityWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Mode"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsModeWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Manual"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsManualWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Unit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsUnitWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "ADP age"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsAgeWidth; horizontalAlignment: Text.AlignLeft }
                                                Text {
                                                    text: "Total"
                                                    color: mutedColor
                                                    font.pixelSize: 11
                                                    Layout.fillWidth: true
                                                    Layout.minimumWidth: marketInputsTotalMinWidth
                                                    horizontalAlignment: Text.AlignLeft
                                                }
                                            }
                                        }

                                        ListView {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: Math.max(200, marketSetupState.inputsModel.rowCount() * 28)
                                            clip: true
                                            reuseItems: true
                                            cacheBuffer: 600
                                            model: marketSetupState.inputsModel

                                            delegate: Rectangle {
                                                width: ListView.view.width
                                                height: 28
                                                color: index % 2 === 0 ? "#0f1620" : "#101924"

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.margins: 4
                                                    spacing: marketColumnSpacing
                                                    Text {
                                                        text: item
                                                        color: textColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketInputsItemWidth
                                                        elide: Text.ElideRight
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: formatInt(quantity)
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketInputsQtyWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    TextField {
                                                        Layout.preferredWidth: marketInputsStockWidth
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        text: stockQuantity > 0 ? formatFixed(stockQuantity, 2) : ""
                                                        placeholderText: "0"
                                                        onEditingFinished: marketSetupState.setInputStockQuantity(itemId, text)
                                                    }
                                                    Text {
                                                        text: formatFixed(buyQuantity, 2)
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketInputsBuyWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: city
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketInputsCityWidth
                                                        elide: Text.ElideRight
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    ComboBox {
                                                        Layout.preferredWidth: marketInputsModeWidth
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        model: ["buy_order", "sell_order", "average"]
                                                        currentIndex: Math.max(0, model.indexOf(priceType))
                                                        onActivated: marketSetupState.setInputPriceType(itemId, currentText)
                                                    }
                                                    TextField {
                                                        Layout.preferredWidth: marketInputsManualWidth
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        text: manualPrice > 0 ? String(manualPrice) : ""
                                                        placeholderText: "-"
                                                        inputMethodHints: Qt.ImhDigitsOnly
                                                        onEditingFinished: marketSetupState.setInputManualPrice(itemId, text)
                                                    }
                                                    Text {
                                                        text: formatInt(unitPrice)
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketInputsUnitWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: priceAgeText
                                                        color: adpAgeColor(priceAgeText)
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketInputsAgeWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: formatInt(totalCost)
                                                        color: textColor
                                                        font.pixelSize: 11
                                                        Layout.fillWidth: true
                                                        Layout.minimumWidth: marketInputsTotalMinWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                }
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
                                        Text { text: "Total input cost"; color: mutedColor; font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Text {
                                            text: formatInt(marketSetupState.inputsTotalCost)
                                            color: textColor
                                            font.pixelSize: 12
                                            font.bold: true
                                            MouseArea {
                                                anchors.fill: parent
                                                acceptedButtons: Qt.LeftButton
                                                onDoubleClicked: copyCellText(parent.text)
                                            }
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
                                    text: "Outputs"
                                    color: textColor
                                    font.pixelSize: 12
                                    font.bold: true
                                }

                                ScrollView {
                                    id: marketOutputsScroll
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true

                                    ColumnLayout {
                                        width: Math.max(marketOutputsScroll.availableWidth, marketOutputsContentMinWidth)
                                        spacing: 6

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 24
                                            radius: 4
                                            color: "#111b28"

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                spacing: marketColumnSpacing
                                                Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsItemWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Qty"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsQtyWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsCityWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Mode"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsModeWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Manual"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsManualWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Unit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsUnitWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Gross"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsGrossWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Fee"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsFeeWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Tax"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsTaxWidth; horizontalAlignment: Text.AlignLeft }
                                                Text {
                                                    text: "Net"
                                                    color: mutedColor
                                                    font.pixelSize: 11
                                                    Layout.fillWidth: true
                                                    Layout.minimumWidth: marketOutputsNetMinWidth
                                                    horizontalAlignment: Text.AlignLeft
                                                }
                                            }
                                        }

                                        ListView {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: Math.max(200, marketSetupState.outputsModel.rowCount() * 28)
                                            clip: true
                                            reuseItems: true
                                            cacheBuffer: 600
                                            model: marketSetupState.outputsModel

                                            delegate: Rectangle {
                                                width: ListView.view.width
                                                height: 28
                                                color: index % 2 === 0 ? "#0f1620" : "#101924"

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.margins: 4
                                                    spacing: marketColumnSpacing
                                                    Text {
                                                        text: item
                                                        color: textColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketOutputsItemWidth
                                                        elide: Text.ElideRight
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: formatFixed(quantity, 2)
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketOutputsQtyWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: city
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketOutputsCityWidth
                                                        elide: Text.ElideRight
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    ComboBox {
                                                        Layout.preferredWidth: marketOutputsModeWidth
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        model: ["sell_order", "buy_order", "average"]
                                                        currentIndex: Math.max(0, model.indexOf(priceType))
                                                        onActivated: marketSetupState.setOutputPriceType(itemId, currentText)
                                                    }
                                                    TextField {
                                                        Layout.preferredWidth: marketOutputsManualWidth
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        text: manualPrice > 0 ? String(manualPrice) : ""
                                                        placeholderText: "-"
                                                        inputMethodHints: Qt.ImhDigitsOnly
                                                        onEditingFinished: marketSetupState.setOutputManualPrice(itemId, text)
                                                    }
                                                    Text {
                                                        text: formatInt(unitPrice)
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketOutputsUnitWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: formatInt(totalValue)
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketOutputsGrossWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: formatInt(feeValue)
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketOutputsFeeWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: formatInt(taxValue)
                                                        color: mutedColor
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketOutputsTaxWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: formatInt(netValue)
                                                        color: textColor
                                                        font.pixelSize: 11
                                                        Layout.fillWidth: true
                                                        Layout.minimumWidth: marketOutputsNetMinWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                }
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
                                        Text { text: "Gross output"; color: mutedColor; font.pixelSize: 11 }
                                        Text {
                                            text: formatInt(marketSetupState.outputsTotalValue)
                                            color: textColor
                                            font.pixelSize: 12
                                            font.bold: true
                                            MouseArea {
                                                anchors.fill: parent
                                                acceptedButtons: Qt.LeftButton
                                                onDoubleClicked: copyCellText(parent.text)
                                            }
                                        }
                                        Text { text: "|"; color: mutedColor; font.pixelSize: 11 }
                                        Text { text: "Net output"; color: mutedColor; font.pixelSize: 11 }
                                        Text {
                                            text: formatInt(marketSetupState.outputsNetValue)
                                            color: textColor
                                            font.pixelSize: 12
                                            font.bold: true
                                            MouseArea {
                                                anchors.fill: parent
                                                acceptedButtons: Qt.LeftButton
                                                onDoubleClicked: copyCellText(parent.text)
                                            }
                                        }
                                        Item { Layout.fillWidth: true }
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

                            ScrollView {
                                id: marketResultsScroll
                                anchors.fill: parent
                                anchors.margins: 10
                                clip: true

                                ColumnLayout {
                                    width: Math.max(640, marketResultsScroll.availableWidth)
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
                                        Text { text: "Investment: " + formatInt(marketSetupState.inputsTotalCost); color: mutedColor; font.pixelSize: 11 }
                                        Text { text: "Revenue: " + formatInt(marketSetupState.outputsTotalValue); color: mutedColor; font.pixelSize: 11 }
                                        Text { text: "Net: " + formatInt(marketSetupState.netProfitValue); color: marketSetupState.netProfitValue >= 0 ? "#7ee787" : "#ff7b72"; font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Text { text: "Margin: " + formatFixed(marketSetupState.marginPercent, 2) + "%"; color: marketSetupState.marginPercent >= 0 ? "#7ee787" : "#ff7b72"; font.pixelSize: 11 }
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
                                    Layout.preferredHeight: Math.max(120, Math.round(root.height * 0.32))
                                    Layout.minimumHeight: 96
                                    clip: true
                                    reuseItems: true
                                    cacheBuffer: 800
                                    model: marketSetupState.resultsItemsModel

                                    delegate: Rectangle {
                                        width: ListView.view.width
                                        height: 26
                                        color: index % 2 === 0 ? "#0f1620" : "#101924"
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 6
                                            Text {
                                                text: item
                                                color: textColor
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 145
                                                elide: Text.ElideRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: city
                                                color: mutedColor
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 100
                                                elide: Text.ElideRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatFixed(quantity, 2)
                                                color: mutedColor
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 55
                                                horizontalAlignment: Text.AlignRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(revenue)
                                                color: mutedColor
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 70
                                                horizontalAlignment: Text.AlignRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(cost)
                                                color: mutedColor
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 70
                                                horizontalAlignment: Text.AlignRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(feeValue)
                                                color: mutedColor
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 55
                                                horizontalAlignment: Text.AlignRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(taxValue)
                                                color: mutedColor
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 55
                                                horizontalAlignment: Text.AlignRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(profit)
                                                color: profit >= 0 ? "#7ee787" : "#ff7b72"
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 70
                                                horizontalAlignment: Text.AlignRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatFixed(marginPercent, 1) + "%"
                                                color: marginPercent >= 0 ? "#7ee787" : "#ff7b72"
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 60
                                                horizontalAlignment: Text.AlignRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatFixed(demandProxy, 1) + "%"
                                                color: mutedColor
                                                font.pixelSize: 11
                                                Layout.fillWidth: true
                                                horizontalAlignment: Text.AlignRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
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
                                    Layout.preferredHeight: Math.max(84, Math.round(root.height * 0.17))
                                    Layout.minimumHeight: 72
                                    Layout.maximumHeight: 180
                                    radius: 4
                                    color: "#111b28"
                                    border.color: "#1f2a37"

                                    ListView {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        clip: true
                                        reuseItems: true
                                        cacheBuffer: 300
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
                                                    text: formatFixed(value, 2)
                                                    color: (label === "Net profit" && value < 0) ? "#ff7b72" : textColor
                                                    font.pixelSize: 11
                                                    MouseArea {
                                                        anchors.fill: parent
                                                        acceptedButtons: Qt.LeftButton
                                                        onDoubleClicked: copyCellText(parent.text)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
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
