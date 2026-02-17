import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: root
    visible: true
    width: 1120
    height: 720
    title: "Albion Command Desk"
    color: theme.surfaceApp

    Theme {
        id: theme
    }

    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.accentPrimary
    property color panelColor: theme.surfacePanel
    property color borderColor: theme.borderSubtle
    property bool compactLayout: width < theme.breakpointCompact
    property bool narrowLayout: width < theme.breakpointNarrow
    property int compactControlHeight: theme.controlHeightCompact
    property int marketColumnSpacing: theme.marketColumnSpacing
    property int marketSetupPanelWidth: theme.marketSetupPanelWidth
    property bool marketSetupStackedLayout: width < 1020
    property int marketSetupPanelActiveWidth: narrowLayout ? 320 : (compactLayout ? 360 : marketSetupPanelWidth)
    property int marketInputsItemWidth: Math.max(narrowLayout ? 130 : 150, Math.min(240, Math.round(width * (narrowLayout ? 0.15 : 0.17))))
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
    property int marketOutputsItemWidth: Math.max(narrowLayout ? 130 : 145, Math.min(230, Math.round(width * (narrowLayout ? 0.14 : 0.16))))
    property int marketOutputsQtyWidth: 58
    property int marketOutputsCityWidth: 108
    property int marketOutputsModeWidth: 92
    property int marketOutputsManualWidth: 70
    property int marketOutputsUnitWidth: 74
    property int marketOutputsGrossWidth: 82
    property int marketOutputsFeeWidth: 74
    property int marketOutputsTaxWidth: 74
    property int marketOutputsNetMinWidth: 116
    property int marketResultsItemWidth: Math.max(narrowLayout ? 180 : 220, Math.min(340, Math.round(width * (narrowLayout ? 0.24 : 0.28))))
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
    property bool marketStatusExpanded: false
    property bool marketBreakdownExpanded: false
    property real craftPlanPendingContentY: -1
    property int shellHeaderHeight: theme.shellHeaderHeight
    property int shellRightZoneSpacing: theme.shellRightZoneSpacing
    property int shellMeterMetaWidth: theme.shellMeterMetaWidth
    property int shellUpdateControlWidth: theme.shellUpdateControlWidth
    property int shellUpdateBannerMinWidth: theme.shellUpdateBannerMinWidth
    property int shellUpdateBannerMaxWidth: theme.shellUpdateBannerMaxWidth
    property int shellNavHeight: theme.shellNavHeight
    property int shellNavWidthMax: theme.shellNavWidthMax
    property int shellNavWidthMin: theme.shellNavWidthMin
    property int shellNavWidthMinActive: narrowLayout ? 320 : shellNavWidthMin
    property int shellNavAvailableWidth: Math.max(300, root.width - (theme.spacingPage * 2))
    property int shellTabRadius: theme.shellTabRadius
    property color shellTabIdleBackground: theme.shellTabIdleBackground
    property color shellTabActiveText: theme.shellTabActiveText
    property int shellMeterMetaWidthActive: compactLayout ? 0 : shellMeterMetaWidth
    property int shellUpdateControlWidthActive: compactLayout ? 170 : shellUpdateControlWidth
    property int shellUpdateBannerMinWidthActive: compactLayout ? 180 : shellUpdateBannerMinWidth
    property int shellUpdateBannerMaxWidthActive: compactLayout ? 280 : shellUpdateBannerMaxWidth
    property int shellHeaderMargin: narrowLayout ? 8 : 12
    property int shellHeaderZoneSpacing: narrowLayout ? 10 : 20
    property string autoUpdateLabel: narrowLayout ? "Auto" : "Auto update"
    property string payPalButtonLabel: narrowLayout ? "Pay" : "PayPal"
    property string coffeeButtonLabel: narrowLayout ? "Coffee" : "Buy me a coffee"
    property int shellSupportPrimaryWidth: narrowLayout ? 90 : 118
    property int shellSupportSecondaryWidth: narrowLayout ? 98 : 146

    // Phase 0 shell contract:
    // - left zone: title + contextual status
    // - right zone: meter meta -> update banner -> update controls -> support actions
    // - global navigation: TabBar directly below header
    // Phase 1 extraction map:
    // - shellHeader
    // - shellUpdateZone
    // - shellSupportZone

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
            return theme.stateInfo
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
            return theme.stateSuccess
        }
        if (minutes <= 60) {
            return theme.stateWarning
        }
        return theme.stateDanger
    }

    function signedValueColor(value) {
        var n = Number(value)
        if (!isFinite(n)) {
            return mutedColor
        }
        if (n > 0) {
            return theme.stateSuccess
        }
        if (n < 0) {
            return theme.stateDanger
        }
        return theme.stateInfo
    }

    function validationColor(isValid) {
        return isValid ? theme.stateSuccess : theme.stateDanger
    }

    function priceSourceColor(sourceName) {
        var source = String(sourceName || "").toLowerCase()
        if (source === "fallback" || source === "stale_cache") {
            return theme.stateWarning
        }
        if (source === "live" || source === "cache") {
            return theme.stateSuccess
        }
        return mutedColor
    }

    function copyCellText(value) {
        marketSetupState.copyText(String(value === undefined || value === null ? "" : value))
    }

    function tableRowColor(index) {
        return index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
    }

    function tableRowStrongColor(index) {
        return index % 2 === 0 ? theme.surfaceInteractive : theme.tableRowEven
    }

    function itemLabelWithTier(labelValue, itemIdValue) {
        var label = String(labelValue || "").trim()
        var itemId = String(itemIdValue || "").trim().toUpperCase()
        if (itemId.length === 0) {
            return label
        }
        var tierMatch = itemId.match(/^T(\d+)_/)
        if (!tierMatch) {
            return label
        }
        var tier = parseInt(tierMatch[1], 10)
        if (!isFinite(tier) || tier <= 0) {
            return label
        }
        var enchant = 0
        var enchantMatch = itemId.match(/@(\d+)$/)
        if (enchantMatch) {
            enchant = parseInt(enchantMatch[1], 10)
            if (!isFinite(enchant) || enchant < 0) {
                enchant = 0
            }
        } else {
            var levelMatch = itemId.match(/_LEVEL(\d+)$/)
            if (levelMatch) {
                enchant = parseInt(levelMatch[1], 10)
                if (!isFinite(enchant) || enchant < 0) {
                    enchant = 0
                }
            }
        }
        var suffix = enchant > 0 ? (" T" + tier + "." + enchant) : (" T" + tier)
        if (label.length === 0) {
            return suffix.trim()
        }
        var withoutTier = label.replace(/\s+(?:T?\d+(?:\.\d+)?)\s*$/i, "").trim()
        if (withoutTier.length === 0) {
            withoutTier = label
        }
        return withoutTier + suffix
    }

    function itemLabelWithTierParts(labelValue, tierValue, enchantValue) {
        var label = String(labelValue || "").trim()
        var tier = parseInt(tierValue, 10)
        if (!isFinite(tier) || tier <= 0) {
            return label
        }
        var enchant = parseInt(enchantValue, 10)
        if (!isFinite(enchant) || enchant < 0) {
            enchant = 0
        }
        var suffix = enchant > 0 ? (" T" + tier + "." + enchant) : (" T" + tier)
        if (label.length === 0) {
            return suffix.trim()
        }
        var withoutTier = label.replace(/\s+(?:T?\d+(?:\.\d+)?)\s*$/i, "").trim()
        if (withoutTier.length === 0) {
            withoutTier = label
        }
        return withoutTier + suffix
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: theme.spacingPage
        spacing: theme.spacingSection

        Timer {
            id: craftPlanRestoreTimer
            interval: 1
            repeat: false
            onTriggered: {
                if (root.craftPlanPendingContentY < 0) {
                    return
                }
                var maxY = Math.max(0, craftPlanList.contentHeight - craftPlanList.height)
                craftPlanList.contentY = Math.min(root.craftPlanPendingContentY, maxY)
                root.craftPlanPendingContentY = -1
            }
        }

        Rectangle {
            id: shellHeader
            Layout.fillWidth: true
            height: shellHeaderHeight
            color: theme.cardLevel1
            radius: theme.cornerRadiusPanel
            border.color: theme.borderStrong

            RowLayout {
                id: shellHeaderLayout
                anchors.fill: parent
                anchors.margins: shellHeaderMargin
                spacing: shellHeaderZoneSpacing

                ColumnLayout {
                    id: shellLeftZone
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    spacing: 4
                    Text {
                        text: "Albion Command Desk"
                        color: textColor
                        font.pixelSize: 20
                        font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
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
                        elide: Text.ElideRight
                        wrapMode: Text.NoWrap
                    }
                }

                RowLayout {
                    id: shellRightZone
                    Layout.fillWidth: false
                    Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                    Layout.minimumWidth: implicitWidth
                    spacing: narrowLayout ? 6 : shellRightZoneSpacing

                    ColumnLayout {
                        id: shellMeterZone
                        Layout.preferredWidth: shellMeterMetaWidthActive
                        Layout.minimumWidth: shellMeterMetaWidthActive
                        Layout.maximumWidth: shellMeterMetaWidthActive
                        Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                        visible: meterView && !compactLayout
                        opacity: visible ? 1.0 : 0.0
                        enabled: visible
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

                    Rectangle {
                        id: shellUpdateBanner
                        visible: !narrowLayout
                        opacity: uiState.updateBannerVisible ? 1.0 : 0.0
                        enabled: uiState.updateBannerVisible
                        Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                        Layout.preferredWidth: Math.max(shellUpdateBannerMinWidthActive, Math.min(shellUpdateBannerMaxWidthActive, root.width * 0.24))
                        Layout.preferredHeight: theme.shellActionHeight + 4
                        radius: theme.shellPillRadius
                        color: theme.shellBannerBackground
                        border.color: theme.shellBannerBorder

                        Behavior on opacity {
                            NumberAnimation {
                                duration: 180
                                easing.type: Easing.OutCubic
                            }
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 6
                            spacing: 6

                            Text {
                                Layout.fillWidth: true
                                text: uiState.updateBannerText
                                color: theme.shellBannerText
                                font.pixelSize: 12
                                elide: Text.ElideRight
                                wrapMode: Text.NoWrap
                            }

                            AppButton {
                                id: updateOpenButton
                                text: "Open"
                                variant: "primary"
                                compact: true
                                implicitHeight: theme.shellActionHeight
                                implicitWidth: 54
                                onClicked: {
                                    if (uiState.updateBannerUrl.length > 0) {
                                        Qt.openUrlExternally(uiState.updateBannerUrl)
                                    }
                                }
                            }

                            AppButton {
                                id: updateDismissButton
                                text: "x"
                                variant: "ghost"
                                compact: true
                                implicitHeight: theme.shellActionHeight
                                implicitWidth: 28
                                onClicked: uiState.dismissUpdateBanner()
                            }
                        }
                    }

                    ColumnLayout {
                        id: shellUpdateZone
                        Layout.preferredWidth: implicitWidth
                        Layout.minimumWidth: implicitWidth
                        spacing: 2
                        RowLayout {
                            Layout.alignment: Qt.AlignRight
                            spacing: 6
                            AppCheckBox {
                                id: autoUpdateCheckBox
                                implicitHeight: theme.shellActionHeight
                                checked: uiState.updateAutoCheck
                                text: autoUpdateLabel
                                onToggled: uiState.setUpdateAutoCheck(checked)
                            }
                            AppButton {
                                id: checkUpdatesButton
                                text: "Check now"
                                variant: "primary"
                                compact: true
                                implicitHeight: theme.shellActionHeight
                                implicitWidth: narrowLayout ? 78 : 88
                                onClicked: uiState.requestManualUpdateCheck()
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: uiState.updateCheckStatus.length > 0
                            text: uiState.updateCheckStatus
                            color: mutedColor
                            font.pixelSize: 10
                            horizontalAlignment: Text.AlignRight
                            elide: Text.ElideRight
                            wrapMode: Text.NoWrap
                        }
                    }

                    RowLayout {
                        id: shellSupportZone
                        spacing: narrowLayout ? 6 : 8
                        AppButton {
                            id: headerPayPalButton
                            text: payPalButtonLabel
                            variant: "primary"
                            compact: true
                            implicitHeight: theme.shellActionHeight
                            implicitWidth: shellSupportPrimaryWidth
                            onClicked: Qt.openUrlExternally("https://www.paypal.com/donate/?business=albiosuperacc%40linuxmail.org&currency_code=USD&amount=20.00")
                        }
                        AppButton {
                            id: headerCoffeeButton
                            text: coffeeButtonLabel
                            variant: "warm"
                            compact: true
                            implicitHeight: theme.shellActionHeight
                            implicitWidth: shellSupportSecondaryWidth
                            onClicked: Qt.openUrlExternally("https://buycoffee.to/ao-dps/")
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: theme.spacingCompact

            Item { Layout.fillWidth: true }

            TabBar {
                id: viewTabs
                Layout.preferredWidth: Math.min(shellNavWidthMax, Math.max(shellNavWidthMinActive, shellNavAvailableWidth))
                Layout.maximumWidth: Math.min(shellNavWidthMax, shellNavAvailableWidth)
                Layout.minimumWidth: Math.min(shellNavWidthMinActive, shellNavAvailableWidth)
                implicitHeight: shellNavHeight
                padding: 0
                spacing: theme.spacingCompact
                background: Rectangle {
                    color: "transparent"
                    border.width: 0
                }

                ShellTabButton {
                    id: meterTab
                    text: "Meter"
                    activeColor: accentColor
                    inactiveColor: shellTabIdleBackground
                    activeTextColor: shellTabActiveText
                    inactiveTextColor: textColor
                    borderColor: borderColor
                    cornerRadius: shellTabRadius
                    labelPixelSize: 13
                }
                ShellTabButton {
                    id: scannerTab
                    text: "Scanner"
                    activeColor: accentColor
                    inactiveColor: shellTabIdleBackground
                    activeTextColor: shellTabActiveText
                    inactiveTextColor: textColor
                    borderColor: borderColor
                    cornerRadius: shellTabRadius
                    labelPixelSize: 13
                }
                ShellTabButton {
                    id: marketTab
                    text: "Market"
                    activeColor: accentColor
                    inactiveColor: shellTabIdleBackground
                    activeTextColor: shellTabActiveText
                    inactiveTextColor: textColor
                    borderColor: borderColor
                    cornerRadius: shellTabRadius
                    labelPixelSize: 13
                }
            }

            Item { Layout.fillWidth: true }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: viewTabs.currentIndex

            Item {
                RowLayout {
                    anchors.fill: parent
                    spacing: 12

                    CardPanel {
                        level: 1
                        Layout.fillWidth: true
                        Layout.fillHeight: true
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

                            TableSurface {
                                level: 1
                                Layout.fillWidth: true
                                height: 62
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
                                        AppButton {
                                            id: battleButton
                                            text: "Battle"
                                            compact: true
                                            implicitHeight: 24
                                            implicitWidth: 62
                                            variant: checked ? "primary" : "secondary"
                                            checkable: true
                                            checked: uiState.mode === "battle"
                                            onClicked: uiState.setMode("battle")
                                        }
                                        AppButton {
                                            id: zoneButton
                                            text: "Zone"
                                            compact: true
                                            implicitHeight: 24
                                            implicitWidth: 56
                                            variant: checked ? "primary" : "secondary"
                                            checkable: true
                                            checked: uiState.mode === "zone"
                                            onClicked: uiState.setMode("zone")
                                        }
                                        AppButton {
                                            id: manualButton
                                            text: "Manual"
                                            compact: true
                                            implicitHeight: 24
                                            implicitWidth: 64
                                            variant: checked ? "primary" : "secondary"
                                            checkable: true
                                            checked: uiState.mode === "manual"
                                            onClicked: uiState.setMode("manual")
                                        }
                                        Item { Layout.fillWidth: true }
                                        Text {
                                            text: "Sort:"
                                            color: mutedColor
                                            font.pixelSize: 11
                                        }
                                        AppButton {
                                            id: sortDpsButton
                                            text: "DPS"
                                            compact: true
                                            implicitHeight: 24
                                            implicitWidth: 56
                                            variant: checked ? "primary" : "secondary"
                                            checkable: true
                                            checked: uiState.sortKey === "dps"
                                            onClicked: uiState.setSortKey("dps")
                                        }
                                        AppButton {
                                            id: sortDmgButton
                                            text: "DMG"
                                            compact: true
                                            implicitHeight: 24
                                            implicitWidth: 56
                                            variant: checked ? "primary" : "secondary"
                                            checkable: true
                                            checked: uiState.sortKey === "dmg"
                                            onClicked: uiState.setSortKey("dmg")
                                        }
                                        AppButton {
                                            id: sortHpsButton
                                            text: "HPS"
                                            compact: true
                                            implicitHeight: 24
                                            implicitWidth: 56
                                            variant: checked ? "primary" : "secondary"
                                            checkable: true
                                            checked: uiState.sortKey === "hps"
                                            onClicked: uiState.setSortKey("hps")
                                        }
                                        AppButton {
                                            id: sortHealButton
                                            text: "HEAL"
                                            compact: true
                                            implicitHeight: 24
                                            implicitWidth: 60
                                            variant: checked ? "primary" : "secondary"
                                            checkable: true
                                            checked: uiState.sortKey === "heal"
                                            onClicked: uiState.setSortKey("heal")
                                        }
                                    }
                                }
                            }

                        TableSurface {
                                level: 1
                            Layout.fillWidth: true
                                height: 26
                                showTopRule: false

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 6
                                    spacing: 12

                                    Text { text: "Name"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 140 }
                                    Text { text: "Weapon"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 90 }
                                    Text { text: "DMG"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                    Text { text: "HEAL"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                    Text { text: "DPS"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                    Text { text: "HPS"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                    Text { text: "BAR"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.fillWidth: true }
                                }
                            }

                            ListView {
                                id: meterPlayersList
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: uiState.playersModel
                                delegate: Rectangle {
                                    id: meterRow
                                    width: ListView.view.width
                                    height: 34
                                    property bool hovered: meterHoverArea.containsMouse
                                    color: hovered ? theme.tableRowHover : tableRowColor(index)
                                    radius: 4
                                    Behavior on color {
                                        ColorAnimation { duration: 120 }
                                    }

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: 12

                                        Text {
                                            text: name
                                            color: theme.tableTextPrimary
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
                                                    color: theme.tableTextSecondary
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
                                        Text { text: damage; color: theme.tableTextSecondary; font.pixelSize: 12; Layout.preferredWidth: 60 }
                                        Text { text: heal; color: theme.tableTextSecondary; font.pixelSize: 12; Layout.preferredWidth: 60 }
                                        Text { text: dps.toFixed(1); color: theme.tableTextSecondary; font.pixelSize: 12; Layout.preferredWidth: 60 }
                                        Text { text: hps.toFixed(1); color: theme.tableTextSecondary; font.pixelSize: 12; Layout.preferredWidth: 60 }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 10
                                            radius: 4
                                            color: theme.surfaceInset
                                            border.color: theme.borderSubtle
                                            Rectangle {
                                                height: parent.height
                                                width: Math.max(4, parent.width * barRatio)
                                                radius: 4
                                                color: barColor
                                            }
                                        }
                                    }

                                    MouseArea {
                                        id: meterHoverArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        acceptedButtons: Qt.NoButton
                                    }
                                }

                                Text {
                                    anchors.centerIn: parent
                                    visible: meterPlayersList.count === 0
                                    text: uiState.selectedHistoryIndex >= 0
                                        ? "No players in selected history entry."
                                        : "No live combat data yet. Start fighting or switch replay."
                                    color: theme.textSecondary
                                    font.pixelSize: 12
                                    horizontalAlignment: Text.AlignHCenter
                                    wrapMode: Text.WordWrap
                                    width: parent.width - 24
                                }
                            }
                        }
                    }

                    CardPanel {
                        level: 1
                        Layout.preferredWidth: 360
                        Layout.fillHeight: true
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

                            AppButton {
                                visible: uiState.selectedHistoryIndex >= 0
                                text: "Back to live"
                                implicitHeight: 30
                                implicitWidth: 104
                                onClicked: uiState.clearHistorySelection()
                            }

                            ListView {
                                id: historyList
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                spacing: 6
                                rightMargin: 6
                                model: uiState.historyModel
                                delegate: Rectangle {
                                    id: historyRow
                                    width: Math.max(0, ListView.view.width - 6)
                                    height: 98
                                    radius: 6
                                    property bool hovered: historyHover.containsMouse
                                    color: selected
                                        ? theme.tableSelectedBackground
                                        : (hovered ? theme.tableRowHover : tableRowColor(index))
                                    border.color: selected ? theme.tableSelectedBorder : theme.tableDivider
                                    border.width: 1
                                    Behavior on color {
                                        ColorAnimation { duration: 120 }
                                    }
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
                                            AppButton {
                                                text: "Copy"
                                                variant: "ghost"
                                                compact: true
                                                implicitWidth: 64
                                                implicitHeight: 24
                                                onClicked: uiState.copyHistory(index)
                                            }
                                        }
                                        Text { text: meta; color: theme.tableTextSecondary; font.pixelSize: 11 }
                                        Text {
                                            text: players
                                            color: theme.tableTextPrimary
                                            font.pixelSize: 11
                                            wrapMode: Text.NoWrap
                                            elide: Text.ElideRight
                                        }
                                    }

                                    MouseArea {
                                        id: historyHover
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        acceptedButtons: Qt.NoButton
                                    }
                                }

                                Text {
                                    anchors.centerIn: parent
                                    visible: historyList.count === 0
                                    text: "No archived battles yet."
                                    color: theme.textSecondary
                                    font.pixelSize: 12
                                }
                            }

                            TableSurface {
                                level: 1
                                Layout.fillWidth: true
                                height: 120
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
                CardPanel {
                        level: 1
                    anchors.fill: parent
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

                        Flow {
                            Layout.fillWidth: true
                            spacing: 8
                            AppButton {
                                text: "Check updates"
                                compact: true
                                onClicked: scannerState.checkForUpdates()
                            }
                            AppButton {
                                text: "Sync repo"
                                compact: true
                                onClicked: scannerState.syncClientRepo()
                            }
                            AppButton {
                                text: "Start scanner"
                                compact: true
                                enabled: !scannerState.running
                                onClicked: scannerState.startScanner()
                            }
                            AppButton {
                                text: "Start scanner (sudo)"
                                compact: true
                                enabled: !scannerState.running
                                onClicked: scannerState.startScannerSudo()
                            }
                            AppButton {
                                text: "Stop scanner"
                                compact: true
                                enabled: scannerState.running
                                onClicked: scannerState.stopScanner()
                            }
                            AppButton {
                                text: "Clear log"
                                compact: true
                                onClicked: scannerState.clearLog()
                            }
                        }

                        TableSurface {
                                level: 1
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            ScrollView {
                                id: scannerLogView
                                anchors.fill: parent
                                anchors.margins: 8
                                TextArea {
                                    id: scannerLogArea
                                    text: scannerState.logText
                                    readOnly: true
                                    wrapMode: Text.NoWrap
                                    color: textColor
                                    font.family: "Consolas"
                                    font.pixelSize: 11
                                    selectByMouse: true

                                    function followTail() {
                                        cursorPosition = length
                                        if (scannerLogView.contentItem
                                                && scannerLogView.contentItem.contentHeight !== undefined
                                                && scannerLogView.contentItem.height !== undefined) {
                                            scannerLogView.contentItem.contentY = Math.max(
                                                0,
                                                scannerLogView.contentItem.contentHeight - scannerLogView.contentItem.height
                                            )
                                        }
                                    }

                                    onTextChanged: Qt.callLater(followTail)
                                    Component.onCompleted: Qt.callLater(followTail)
                                }
                            }

                            Text {
                                anchors.centerIn: parent
                                visible: scannerState.logText.length === 0
                                text: "Scanner log is empty. Run a scanner action to see diagnostics."
                                color: theme.textSecondary
                                font.pixelSize: 11
                            }
                        }
                    }
                }
            }

            Item {
                CardPanel {
                        level: 1
                    anchors.fill: parent
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

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6

                            Text {
                                Layout.fillWidth: true
                                text: (marketSetupState.priceFetchInProgress ? "[loading] " : "")
                                    + "Status: "
                                    + (marketSetupState.validationText.length === 0 ? "ok" : "invalid")
                                    + "  |  Prices: " + marketSetupState.pricesSource
                                    + (marketSetupState.listActionText.length > 0 ? "  |  " + marketSetupState.listActionText : "")
                                color: marketSetupState.validationText.length === 0
                                    ? priceSourceColor(marketSetupState.pricesSource)
                                    : validationColor(false)
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }

                            Flow {
                                Layout.fillWidth: true
                                spacing: 8

                                Text {
                                    text: "Region"
                                    color: mutedColor
                                    font.pixelSize: 11
                                }
                                AppComboBox {
                                    implicitWidth: 110
                                    implicitHeight: 24
                                    font.pixelSize: 11
                                    model: ["europe", "west", "east"]
                                    currentIndex: Math.max(0, model.indexOf(marketSetupState.region))
                                    onActivated: marketSetupState.setRegion(currentText)
                                }

                                AppCheckBox {
                                    id: premiumCheck
                                    implicitHeight: 24
                                    checked: marketSetupState.premium
                                    text: "Premium"
                                    palette.windowText: textColor
                                    palette.text: textColor
                                    onToggled: marketSetupState.setPremium(checked)
                                }

                                AppButton {
                                    text: marketSetupState.refreshPricesButtonText
                                    compact: true
                                    implicitHeight: 24
                                    enabled: marketSetupState.canRefreshPrices
                                    onClicked: marketSetupState.refreshPrices()
                                }
                                AppButton {
                                    text: marketStatusExpanded ? "Hide details" : "Show details"
                                    compact: true
                                    implicitHeight: 24
                                    onClicked: marketStatusExpanded = !marketStatusExpanded
                                }
                                AppButton {
                                    text: marketDiagnosticsVisible ? "Hide diagnostics" : "Show diagnostics"
                                    compact: true
                                    implicitHeight: 24
                                    onClicked: marketDiagnosticsVisible = !marketDiagnosticsVisible
                                }
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            visible: marketStatusExpanded

                            Text {
                                Layout.fillWidth: true
                                text: marketSetupState.validationText.length === 0
                                    ? "Configuration valid."
                                    : "Validation: " + marketSetupState.validationText
                                color: validationColor(marketSetupState.validationText.length === 0)
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "Prices details: " + marketSetupState.pricesStatusText
                                color: priceSourceColor(marketSetupState.pricesSource)
                                font.pixelSize: 11
                                elide: Text.ElideRight
                            }
                        }

                        TabBar {
                            id: marketTabs
                            Layout.fillWidth: true
                            implicitHeight: 30
                            spacing: theme.spacingCompact
                            padding: 0
                            onCurrentIndexChanged: marketSetupState.setActiveMarketTab(currentIndex)
                            Component.onCompleted: marketSetupState.setActiveMarketTab(currentIndex)
                            background: Rectangle {
                                color: "transparent"
                                border.width: 0
                            }

                            ShellTabButton {
                                id: marketOverviewTab
                                text: "Setup"
                                activeColor: accentColor
                                inactiveColor: shellTabIdleBackground
                                activeTextColor: shellTabActiveText
                                inactiveTextColor: textColor
                                borderColor: borderColor
                                cornerRadius: shellTabRadius
                                labelPixelSize: 11
                            }
                            ShellTabButton {
                                id: marketInputsTab
                                text: "Inputs"
                                activeColor: accentColor
                                inactiveColor: shellTabIdleBackground
                                activeTextColor: shellTabActiveText
                                inactiveTextColor: textColor
                                borderColor: borderColor
                                cornerRadius: shellTabRadius
                                labelPixelSize: 11
                            }
                            ShellTabButton {
                                id: marketOutputsTab
                                text: "Outputs"
                                activeColor: accentColor
                                inactiveColor: shellTabIdleBackground
                                activeTextColor: shellTabActiveText
                                inactiveTextColor: textColor
                                borderColor: borderColor
                                cornerRadius: shellTabRadius
                                labelPixelSize: 11
                            }
                            ShellTabButton {
                                id: marketResultsTab
                                text: "Results"
                                activeColor: accentColor
                                inactiveColor: shellTabIdleBackground
                                activeTextColor: shellTabActiveText
                                inactiveTextColor: textColor
                                borderColor: borderColor
                                cornerRadius: shellTabRadius
                                labelPixelSize: 11
                            }
                        }

                        TableSurface {
                                level: 1
                            Layout.fillWidth: true
                            Layout.preferredHeight: marketDiagnosticsVisible ? 110 : 0
                            Layout.minimumHeight: marketDiagnosticsVisible ? 82 : 0
                            Layout.maximumHeight: marketDiagnosticsVisible ? 140 : 0
                            visible: marketDiagnosticsVisible
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
                                    AppButton {
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

                            GridLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                columns: marketSetupStackedLayout ? 1 : 2
                                columnSpacing: 12
                                rowSpacing: 12

                            TableSurface {
                                level: 1
                                Layout.column: 0
                                Layout.row: 0
                                Layout.fillHeight: true
                                Layout.fillWidth: marketSetupStackedLayout
                                Layout.preferredWidth: marketSetupStackedLayout ? -1 : marketSetupPanelActiveWidth
                                Layout.minimumWidth: marketSetupStackedLayout ? 260 : marketSetupPanelActiveWidth
                                Layout.maximumWidth: marketSetupStackedLayout ? 16777215 : marketSetupPanelActiveWidth
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

                                                    AppTextField {
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

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 6
                                                    AppButton {
                                                        text: "Add filtered"
                                                        variant: "primary"
                                                        compact: true
                                                        Layout.fillWidth: true
                                                        implicitHeight: 22
                                                        font.pixelSize: 10
                                                        enabled: recipeSuggestions.count > 0
                                                        onClicked: marketSetupState.addFilteredRecipeOptions()
                                                    }
                                                    AppButton {
                                                        text: "Add family"
                                                        variant: "secondary"
                                                        compact: true
                                                        Layout.fillWidth: true
                                                        implicitHeight: 22
                                                        font.pixelSize: 10
                                                        enabled: recipeSuggestions.count > 0 || recipeSearchInput.text.trim().length === 0
                                                        onClicked: marketSetupState.addRecipeFamily()
                                                    }
                                                }

                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 6
                                                    Text {
                                                        text: "Enchant"
                                                        color: mutedColor
                                                        font.pixelSize: 10
                                                        Layout.preferredWidth: 52
                                                    }
                                                    AppComboBox {
                                                        implicitWidth: 72
                                                        implicitHeight: 22
                                                        font.pixelSize: 10
                                                        model: ["all", "0", "1", "2", "3", "4"]
                                                        currentIndex: {
                                                            var filterValue = marketSetupState.recipeEnchantFilter
                                                            if (filterValue < 0) return 0
                                                            return Math.min(5, filterValue + 1)
                                                        }
                                                        onActivated: {
                                                            if (currentIndex <= 0) {
                                                                marketSetupState.setRecipeEnchantFilter(-1)
                                                            } else {
                                                                marketSetupState.setRecipeEnchantFilter(parseInt(currentText))
                                                            }
                                                        }
                                                    }
                                                    Text {
                                                        text: recipeSuggestions.count + " matches"
                                                        color: mutedColor
                                                        font.pixelSize: 10
                                                        Layout.fillWidth: true
                                                        horizontalAlignment: Text.AlignRight
                                                    }
                                                }

                                                Rectangle {
                                                    Layout.fillWidth: true
                                                    Layout.preferredHeight: 196
                                                    visible: recipeSearchInput.activeFocus && recipeSuggestions.count > 0
                                                    radius: 4
                                                    color: theme.tableHeaderBackground
                                                    border.color: theme.borderSubtle

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
                                                                : (tableRowStrongColor(index))

                                                            RowLayout {
                                                                anchors.fill: parent
                                                                anchors.margins: 4
                                                                spacing: 6
                                                                Text {
                                                                    text: displayName
                                                                    color: textColor
                                                                    font.pixelSize: 11
                                                                    Layout.fillWidth: true
                                                                    elide: Text.ElideNone
                                                                }
                                                                Text {
                                                                    text: "T" + tier + "." + enchant
                                                                    color: mutedColor
                                                                    font.pixelSize: 11
                                                                    Layout.preferredWidth: 62
                                                                    horizontalAlignment: Text.AlignLeft
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
                                            AppComboBox {
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
                                            AppComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                                                currentIndex: Math.max(0, model.indexOf(marketSetupState.defaultBuyCity))
                                                onActivated: marketSetupState.setDefaultBuyCity(currentText)
                                            }

                                            Text { text: "Sell City"; color: mutedColor; font.pixelSize: 11 }
                                            AppComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                                                currentIndex: Math.max(0, model.indexOf(marketSetupState.defaultSellCity))
                                                onActivated: marketSetupState.setDefaultSellCity(currentText)
                                            }

                                            Text { text: "Default Runs"; color: mutedColor; font.pixelSize: 11 }
                                            AppSpinBox {
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
                                            AppSpinBox {
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
                                            AppComboBox {
                                                Layout.fillWidth: true
                                                implicitHeight: compactControlHeight
                                                font.pixelSize: 11
                                                model: ["0%", "10%", "20%"]
                                                currentIndex: Math.max(0, model.indexOf(String(marketSetupState.dailyBonusPreset) + "%"))
                                                onActivated: marketSetupState.setDailyBonusPreset(currentText)
                                            }

                                            Text { text: "Use Focus (RRR)"; color: theme.tableTextSecondary; font.pixelSize: 11 }
                                            AppCheckBox {
                                                id: focusRrrCheck
                                                Layout.fillWidth: true
                                                checked: marketSetupState.focusEnabled
                                                text: checked ? "Enabled" : "Disabled"
                                                indicator: Rectangle {
                                                    implicitWidth: 14
                                                    implicitHeight: 14
                                                    radius: 3
                                                    border.color: "#6b7b8f"
                                                    color: focusRrrCheck.checked ? theme.stateSuccess : "transparent"
                                                }
                                                contentItem: Text {
                                                    leftPadding: focusRrrCheck.indicator.width + 8
                                                    text: focusRrrCheck.text
                                                    color: focusRrrCheck.checked ? theme.stateSuccess : theme.textDisabled
                                                    font.pixelSize: 11
                                                    verticalAlignment: Text.AlignVCenter
                                                }
                                                onToggled: marketSetupState.setFocusEnabled(checked)
                                            }
                                        }

                                        Rectangle {
                                            Layout.fillWidth: true
                                            radius: 4
                                            color: theme.tableHeaderBackground
                                            border.color: theme.borderSubtle
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
                                                    AppComboBox {
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

                                                AppTextField {
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
                                                    AppButton {
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
                                                    AppButton {
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
                                                    AppButton {
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

                            TableSurface {
                                level: 1
                                Layout.column: marketSetupStackedLayout ? 0 : 1
                                Layout.row: marketSetupStackedLayout ? 1 : 0
                                Layout.fillWidth: true
                                Layout.fillHeight: true
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
                                        Text {
                                            text: "Sort"
                                            color: mutedColor
                                            font.pixelSize: 10
                                        }
                                        AppComboBox {
                                            implicitWidth: 84
                                            implicitHeight: 20
                                            font.pixelSize: 10
                                            model: ["added", "craft", "tier", "city", "p/l"]
                                            currentIndex: {
                                                if (marketSetupState.craftPlanSortKey === "craft") return 1
                                                if (marketSetupState.craftPlanSortKey === "tier") return 2
                                                if (marketSetupState.craftPlanSortKey === "city") return 3
                                                if (marketSetupState.craftPlanSortKey === "pl") return 4
                                                return 0
                                            }
                                            onActivated: {
                                                if (currentText === "p/l") {
                                                    marketSetupState.setCraftPlanSortKey("pl")
                                                } else {
                                                    marketSetupState.setCraftPlanSortKey(currentText)
                                                }
                                            }
                                        }
                                        AppButton {
                                            text: marketSetupState.craftPlanSortDescending ? "Desc" : "Asc"
                                            implicitHeight: 20
                                            implicitWidth: 48
                                            font.pixelSize: 10
                                            onClicked: marketSetupState.toggleCraftPlanSortDescending()
                                        }
                                        AppButton {
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
                                        color: theme.tableHeaderBackground
                                        border.color: theme.borderSubtle
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
                                        id: craftPlanList
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        Layout.preferredHeight: Math.max(190, Math.min(420, 86 + marketSetupState.craftPlanCount * 24))
                                        clip: true
                                        spacing: 1
                                        reuseItems: true
                                        cacheBuffer: 600
                                        model: marketSetupState.craftPlanModel

                                        Connections {
                                            target: craftPlanList.model
                                            function onModelReset() {
                                                if (root.craftPlanPendingContentY >= 0) {
                                                    craftPlanRestoreTimer.restart()
                                                }
                                            }
                                        }

                                        delegate: Rectangle {
                                            width: ListView.view.width
                                            height: 32
                                            color: recipeId === marketSetupState.recipeId
                                                ? "#1b2635"
                                                : (tableRowColor(index))

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.leftMargin: 4
                                                anchors.rightMargin: 4
                                                spacing: 6

                                                AppCheckBox {
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
                                                    text: itemLabelWithTierParts(displayName, tier, enchant)
                                                    color: textColor
                                                    font.pixelSize: 10
                                                    elide: Text.ElideRight
                                                    MouseArea {
                                                        anchors.fill: parent
                                                        acceptedButtons: Qt.LeftButton
                                                        onDoubleClicked: copyCellText(parent.text)
                                                    }
                                                }

                                                Text {
                                                    Layout.preferredWidth: 46
                                                    text: "T" + tier + "." + enchant
                                                    color: mutedColor
                                                    font.pixelSize: 10
                                                    MouseArea {
                                                        anchors.fill: parent
                                                        acceptedButtons: Qt.LeftButton
                                                        onDoubleClicked: copyCellText(itemLabelWithTierParts(displayName, tier, enchant))
                                                    }
                                                }

                                                AppComboBox {
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

                                                AppComboBox {
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
                                                    horizontalAlignment: Text.AlignLeft
                                                }

                                                AppTextField {
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
                                                        color: theme.surfaceInset
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
                                                        : signedValueColor(Number(profitPercent))
                                                    font.pixelSize: 10
                                                    horizontalAlignment: Text.AlignLeft
                                                }

                                                AppButton {
                                                    Layout.preferredWidth: 40
                                                    implicitHeight: 22
                                                    font.pixelSize: 10
                                                    text: "Del"
                                                    onClicked: {
                                                        root.craftPlanPendingContentY = craftPlanList.contentY
                                                        marketSetupState.removePlanRow(rowId)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            }

                        TableSurface {
                                level: 1
                            Layout.fillWidth: true
                            Layout.fillHeight: true
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
                                        height: marketInputsScroll.availableHeight
                                        spacing: 6

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 24
                                            radius: 4
                                            color: theme.tableHeaderBackground

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                spacing: marketColumnSpacing
                                                Text { text: "Item"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsItemWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Need"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsQtyWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Stock"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsStockWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Buy"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsBuyWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "City"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsCityWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Mode"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsModeWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Manual"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsManualWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Unit"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsUnitWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "ADP age"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketInputsAgeWidth; horizontalAlignment: Text.AlignLeft }
                                                Text {
                                                    text: "Total"
                                                    color: theme.tableHeaderText
                                                    font.pixelSize: 11
                                                    Layout.fillWidth: true
                                                    Layout.minimumWidth: marketInputsTotalMinWidth
                                                    horizontalAlignment: Text.AlignLeft
                                                }
                                            }
                                        }

                                        ListView {
                                            id: marketInputsList
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            Layout.minimumHeight: 120
                                            clip: true
                                            reuseItems: true
                                            cacheBuffer: 600
                                            model: marketSetupState.inputsModel

                                            delegate: Rectangle {
                                                id: inputRow
                                                width: ListView.view.width
                                                height: 28
                                                property bool hovered: inputRowHover.containsMouse
                                                color: hovered ? theme.tableRowHover : tableRowColor(index)
                                                radius: 4
                                                Behavior on color {
                                                    ColorAnimation { duration: 120 }
                                                }

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.margins: 4
                                                    spacing: marketColumnSpacing
                                                    Text {
                                                        text: itemLabelWithTier(item, itemId)
                                                        color: theme.tableTextPrimary
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
                                                        color: theme.tableTextSecondary
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketInputsQtyWidth
                                                        horizontalAlignment: Text.AlignLeft
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    AppTextField {
                                                        Layout.preferredWidth: marketInputsStockWidth
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        text: stockQuantity > 0 ? formatFixed(stockQuantity, 2) : ""
                                                        placeholderText: "0"
                                                        onEditingFinished: marketSetupState.setInputStockQuantity(itemId, text)
                                                    }
                                                    Text {
                                                        text: formatFixed(buyQuantity, 2)
                                                        color: theme.tableTextSecondary
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
                                                        color: theme.tableTextSecondary
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketInputsCityWidth
                                                        elide: Text.ElideRight
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    AppComboBox {
                                                        Layout.preferredWidth: marketInputsModeWidth
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        model: ["buy_order", "sell_order", "average"]
                                                        currentIndex: Math.max(0, model.indexOf(priceType))
                                                        onActivated: marketSetupState.setInputPriceType(itemId, currentText)
                                                    }
                                                    AppTextField {
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
                                                        color: theme.tableTextSecondary
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
                                                        color: theme.tableTextPrimary
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

                                                MouseArea {
                                                    id: inputRowHover
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    acceptedButtons: Qt.NoButton
                                                }
                                            }
                                        }

                                        Text {
                                            visible: marketInputsList.count === 0
                                            text: marketSetupState.priceFetchInProgress
                                                ? "Loading input prices..."
                                                : "No input rows. Add craft recipes in Setup."
                                            color: theme.textSecondary
                                            font.pixelSize: 11
                                            Layout.fillWidth: true
                                            horizontalAlignment: Text.AlignHCenter
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 28
                                    radius: 4
                                    color: theme.tableHeaderBackground
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

                        TableSurface {
                                level: 1
                            Layout.fillWidth: true
                            Layout.fillHeight: true
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
                                        height: marketOutputsScroll.availableHeight
                                        spacing: 6

                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 24
                                            radius: 4
                                            color: theme.tableHeaderBackground

                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                spacing: marketColumnSpacing
                                                Text { text: "Item"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsItemWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Qty"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsQtyWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "City"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsCityWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Mode"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsModeWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Manual"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsManualWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Unit"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsUnitWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Gross"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsGrossWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Fee"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsFeeWidth; horizontalAlignment: Text.AlignLeft }
                                                Text { text: "Tax"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketOutputsTaxWidth; horizontalAlignment: Text.AlignLeft }
                                                Text {
                                                    text: "Net"
                                                    color: theme.tableHeaderText
                                                    font.pixelSize: 11
                                                    Layout.fillWidth: true
                                                    Layout.minimumWidth: marketOutputsNetMinWidth
                                                    horizontalAlignment: Text.AlignLeft
                                                }
                                            }
                                        }

                                        ListView {
                                            id: marketOutputsList
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            Layout.minimumHeight: 120
                                            clip: true
                                            reuseItems: true
                                            cacheBuffer: 600
                                            model: marketSetupState.outputsModel

                                            delegate: Rectangle {
                                                id: outputRow
                                                width: ListView.view.width
                                                height: 28
                                                property bool hovered: outputRowHover.containsMouse
                                                color: hovered ? theme.tableRowHover : tableRowColor(index)
                                                radius: 4
                                                Behavior on color {
                                                    ColorAnimation { duration: 120 }
                                                }

                                                RowLayout {
                                                    anchors.fill: parent
                                                    anchors.margins: 4
                                                    spacing: marketColumnSpacing
                                                    Text {
                                                        text: itemLabelWithTier(item, itemId)
                                                        color: theme.tableTextPrimary
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
                                                        color: theme.tableTextSecondary
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
                                                        color: theme.tableTextSecondary
                                                        font.pixelSize: 11
                                                        Layout.preferredWidth: marketOutputsCityWidth
                                                        elide: Text.ElideRight
                                                        MouseArea {
                                                            anchors.fill: parent
                                                            acceptedButtons: Qt.LeftButton
                                                            onDoubleClicked: copyCellText(parent.text)
                                                        }
                                                    }
                                                    AppComboBox {
                                                        Layout.preferredWidth: marketOutputsModeWidth
                                                        implicitHeight: compactControlHeight
                                                        font.pixelSize: 11
                                                        model: ["sell_order", "buy_order", "average"]
                                                        currentIndex: Math.max(0, model.indexOf(priceType))
                                                        onActivated: marketSetupState.setOutputPriceType(itemId, currentText)
                                                    }
                                                    AppTextField {
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
                                                        color: theme.tableTextSecondary
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
                                                        color: theme.tableTextSecondary
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
                                                        color: theme.tableTextSecondary
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
                                                        color: theme.tableTextSecondary
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
                                                        color: theme.tableTextPrimary
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

                                                MouseArea {
                                                    id: outputRowHover
                                                    anchors.fill: parent
                                                    hoverEnabled: true
                                                    acceptedButtons: Qt.NoButton
                                                }
                                            }
                                        }

                                        Text {
                                            visible: marketOutputsList.count === 0
                                            text: marketSetupState.priceFetchInProgress
                                                ? "Loading output prices..."
                                                : "No output rows. Build crafts to generate outputs."
                                            color: theme.textSecondary
                                            font.pixelSize: 11
                                            Layout.fillWidth: true
                                            horizontalAlignment: Text.AlignHCenter
                                        }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 28
                                    radius: 4
                                    color: theme.tableHeaderBackground
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

                        TableSurface {
                                level: 1
                            Layout.fillWidth: true
                            Layout.fillHeight: true
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
                                    AppComboBox {
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
                                    color: theme.tableHeaderBackground
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 12
                                        Text { text: "Investment: " + formatInt(marketSetupState.inputsTotalCost); color: mutedColor; font.pixelSize: 11 }
                                        Text { text: "Revenue: " + formatInt(marketSetupState.outputsTotalValue); color: mutedColor; font.pixelSize: 11 }
                                        Text { text: "Net: " + formatInt(marketSetupState.netProfitValue); color: signedValueColor(marketSetupState.netProfitValue); font.pixelSize: 11 }
                                        Item { Layout.fillWidth: true }
                                        Text { text: "Margin: " + formatFixed(marketSetupState.marginPercent, 2) + "%"; color: signedValueColor(marketSetupState.marginPercent); font.pixelSize: 11 }
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 24
                                    radius: 4
                                    color: theme.tableHeaderBackground
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 4
                                        spacing: 6
                                        Text { text: "Item"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: marketResultsItemWidth }
                                        Text { text: "City"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 100 }
                                        Text { text: "Qty"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                        Text { text: "Revenue"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Cost"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Fee"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                        Text { text: "Tax"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 55 }
                                        Text { text: "Profit"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 70 }
                                        Text { text: "Margin"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.preferredWidth: 60 }
                                        Text { text: "Demand*"; color: theme.tableHeaderText; font.pixelSize: 11; Layout.fillWidth: true }
                                    }
                                }

                                Text {
                                    text: "Demand* = buy_price_max / sell_price_min (AOData). 100% means buy ~= sell."
                                    color: mutedColor
                                    font.pixelSize: 10
                                }

                                ListView {
                                    id: marketResultsList
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    Layout.minimumHeight: 160
                                    clip: true
                                    reuseItems: true
                                    cacheBuffer: 800
                                    model: marketSetupState.resultsItemsModel

                                    delegate: Rectangle {
                                        id: resultRow
                                        width: ListView.view.width
                                        height: 26
                                        property bool hovered: resultRowHover.containsMouse
                                        color: hovered ? theme.tableRowHover : tableRowColor(index)
                                        radius: 4
                                        Behavior on color {
                                            ColorAnimation { duration: 120 }
                                        }
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 4
                                            spacing: 6
                                            Text {
                                                text: itemLabelWithTier(item, itemId)
                                                color: theme.tableTextPrimary
                                                font.pixelSize: 11
                                                Layout.preferredWidth: marketResultsItemWidth
                                                elide: Text.ElideRight
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: city
                                                color: theme.tableTextSecondary
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
                                                color: theme.tableTextSecondary
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 55
                                                horizontalAlignment: Text.AlignLeft
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(revenue)
                                                color: theme.tableTextSecondary
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 70
                                                horizontalAlignment: Text.AlignLeft
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(cost)
                                                color: theme.tableTextSecondary
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 70
                                                horizontalAlignment: Text.AlignLeft
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(feeValue)
                                                color: theme.tableTextSecondary
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 55
                                                horizontalAlignment: Text.AlignLeft
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(taxValue)
                                                color: theme.tableTextSecondary
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 55
                                                horizontalAlignment: Text.AlignLeft
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatInt(profit)
                                                color: signedValueColor(profit)
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 70
                                                horizontalAlignment: Text.AlignLeft
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatFixed(marginPercent, 1) + "%"
                                                color: signedValueColor(marginPercent)
                                                font.pixelSize: 11
                                                Layout.preferredWidth: 60
                                                horizontalAlignment: Text.AlignLeft
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                            Text {
                                                text: formatFixed(demandProxy, 1) + "%"
                                                color: theme.tableTextSecondary
                                                font.pixelSize: 11
                                                Layout.fillWidth: true
                                                horizontalAlignment: Text.AlignLeft
                                                MouseArea {
                                                    anchors.fill: parent
                                                    acceptedButtons: Qt.LeftButton
                                                    onDoubleClicked: copyCellText(parent.text)
                                                }
                                            }
                                        }

                                        MouseArea {
                                            id: resultRowHover
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            acceptedButtons: Qt.NoButton
                                        }
                                    }
                                }

                                Text {
                                    visible: marketResultsList.count === 0
                                    text: marketSetupState.validationText.length > 0
                                        ? ("Fix configuration: " + marketSetupState.validationText)
                                        : (marketSetupState.priceFetchInProgress
                                            ? "Loading results..."
                                            : "No results yet. Refresh prices and review setup.")
                                    color: marketSetupState.validationText.length > 0 ? theme.stateDanger : theme.textSecondary
                                    font.pixelSize: 11
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                    horizontalAlignment: Text.AlignHCenter
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    Text {
                                        text: "Breakdown"
                                        color: textColor
                                        font.pixelSize: 12
                                        font.bold: true
                                    }
                                    Item { Layout.fillWidth: true }
                                    AppButton {
                                        text: marketBreakdownExpanded ? "Hide" : "Show"
                                        implicitHeight: 22
                                        onClicked: marketBreakdownExpanded = !marketBreakdownExpanded
                                    }
                                }

                                Rectangle {
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: 104
                                    Layout.minimumHeight: 84
                                    Layout.maximumHeight: 160
                                    radius: 4
                                    color: theme.tableHeaderBackground
                                    border.color: theme.borderSubtle
                                    visible: marketBreakdownExpanded

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
                                            color: tableRowStrongColor(index)
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                Text { text: label; color: theme.tableTextSecondary; font.pixelSize: 11 }
                                                Item { Layout.fillWidth: true }
                                                Text {
                                                    text: formatFixed(value, 2)
                                                    color: (label === "Net profit" && value < 0) ? theme.stateDanger : theme.tableTextPrimary
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
    Shortcut { sequence: "B"; onActivated: uiState.setMode("battle") }
    Shortcut { sequence: "Z"; onActivated: uiState.setMode("zone") }
    Shortcut { sequence: "M"; onActivated: uiState.setMode("manual") }
    Shortcut { sequence: "1"; onActivated: uiState.setSortKey("dps") }
    Shortcut { sequence: "2"; onActivated: uiState.setSortKey("dmg") }
    Shortcut { sequence: "3"; onActivated: uiState.setSortKey("hps") }
    Shortcut { sequence: "4"; onActivated: uiState.setSortKey("heal") }
    Shortcut { sequence: "Q"; onActivated: Qt.quit() }
}
