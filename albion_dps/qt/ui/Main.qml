import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for AppHeader, AppShell, AppButton, AppCheckBox, AppComboBox, Theme, ShellTabButton
import "components"  // All components available directly
import "utils" 1.0 as Utils
import "utils" 1.0 as HelperUtils

ApplicationWindow {
    id: root
    visible: true
    width: 1120
    height: 720
    title: "Albion Command Desk"
    color: Theme.surfaceApp

    property var theme: Theme

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
    property int marketSetupTwoColumnMinWidth: 820
    property bool marketSetupStackedLayout: width < marketSetupTwoColumnMinWidth
    property int marketSetupPanelActiveWidth: marketSetupStackedLayout ? -1 : marketSetupPanelWidth
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
    property string payPalButtonLabel: "PayPal"
    property string coffeeButtonLabel: "Buy me a Coffee"
    property int shellSupportPrimaryWidth: narrowLayout ? 108 : 118
    property int shellSupportSecondaryWidth: narrowLayout ? 156 : 166

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
        var text = String(value === undefined || value === null ? "" : value)
        marketSetupState.copyText(text)
        toastManager.showSuccess("Copied to clipboard", text.length > 50 ? text.substring(0, 50) + "..." : text)
    }

    function copyText(text) {
        marketSetupState.copyText(String(text))
        toastManager.showSuccess("Copied to clipboard", text.length > 50 ? text.substring(0, 50) + "..." : text)
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

        // Shell Header - Extracted component
        AppHeader {
            id: shellHeader
            Layout.fillWidth: true
            headerHeight: shellHeaderHeight
            headerMargin: shellHeaderMargin
            zoneSpacing: shellHeaderZoneSpacing
            meterView: root.meterView
            scannerView: root.scannerView
            marketView: root.marketView
            compactLayout: root.compactLayout
            narrowLayout: root.narrowLayout
            meterMetaWidth: shellMeterMetaWidth
            rightZoneSpacing: shellRightZoneSpacing
            meterMode: uiState.mode
            meterZone: uiState.zone
            meterTimeText: uiState.timeText
            meterFameText: uiState.fameText
            meterFamePerHourText: uiState.famePerHourText
            scannerStatusText: scannerState.statusText
            scannerUpdateText: scannerState.updateText
            marketRegion: marketSetupState.region
            marketCraftPlanEnabledCount: marketSetupState.craftPlanEnabledCount
            marketCraftPlanCount: marketSetupState.craftPlanCount
            marketInputsTotalCost: marketSetupState.inputsTotalCost
            marketNetProfitValue: marketSetupState.netProfitValue
            updateBannerVisible: uiState.updateBannerVisible
            updateBannerText: uiState.updateBannerText
            updateBannerUrl: uiState.updateBannerUrl
            updateAutoCheck: uiState.updateAutoCheck
            updateCheckStatus: uiState.updateCheckStatus
            autoUpdateLabel: root.autoUpdateLabel
            payPalLabel: root.payPalButtonLabel
            coffeeLabel: root.coffeeButtonLabel
            supportPayPalWidth: root.shellSupportPrimaryWidth
            supportCoffeeWidth: root.shellSupportSecondaryWidth
            theme: root.theme
            textColor: root.textColor
            mutedColor: root.mutedColor
            formatInt: root.formatInt
            onSetUpdateAutoCheck: function(checked) {
                uiState.setUpdateAutoCheck(checked)
                toastManager.showInfo(checked ? "Auto-update enabled" : "Auto-update disabled", "")
            }
            onRequestManualUpdateCheck: function() {
                uiState.requestManualUpdateCheck()
                toastManager.showInfo("Checking for updates", "Looking for new version...")
            }
            onDismissUpdateBanner: function() {
                uiState.dismissUpdateBanner()
                toastManager.showInfo("Update dismissed", "")
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
                    id: meterTabButton
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
                    id: scannerTabButton
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
                    id: marketTabButton
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

            // Add fade-in animation for tab transitions
            property int prevIndex: -1
            onCurrentIndexChanged: {
                prevIndex = currentIndex
            }

            // Meter Tab - Extracted component
            Item {
                id: meterTabContainer
                opacity: viewTabs.currentIndex === 0 ? 1.0 : 0.0
                visible: true
                Layout.fillHeight: true
                Behavior on opacity {
                    NumberAnimation {
                        duration: Utils.AnimationUtils.durationNormal
                        easing.type: Utils.AnimationUtils.easingOut
                    }
                }

                MeterTab {
                    id: meterTab
                    anchors.fill: parent

                    // State properties from uiState
                    mode: uiState.mode
                    zone: uiState.zone
                    sortKey: uiState.sortKey
                    selectedHistoryIndex: uiState.selectedHistoryIndex
                    timeText: uiState.timeText
                    fameText: uiState.fameText
                    famePerHourText: uiState.famePerHourText

                    // Models
                    playersModel: uiState.playersModel
                    historyModel: uiState.historyModel

                    // UI flags
                    compactLayout: root.compactLayout

                    // Theme access
                    theme: root.theme

                    // Signal handlers
                    onSetMode: function(mode) { uiState.setMode(mode) }
                    onSetSortKey: function(sortKey) { uiState.setSortKey(sortKey) }
                    onClearHistorySelection: function() {
                        uiState.clearHistorySelection()
                        toastManager.showInfo("Selection cleared", "History selection cleared")
                    }
                    onSelectHistory: function(index) { uiState.selectHistory(index) }
                    onCopyHistory: function(index) {
                        uiState.copyHistory(index)
                        toastManager.showSuccess("Copied to clipboard", "Battle data copied")
                    }
                }
            }
            // Scanner Tab - Extracted component
            Item {
                id: scannerTabContainer
                opacity: viewTabs.currentIndex === 1 ? 1.0 : 0.0
                visible: true
                Layout.fillHeight: true
                Behavior on opacity {
                    NumberAnimation {
                        duration: Utils.AnimationUtils.durationNormal
                        easing.type: Utils.AnimationUtils.easingOut
                    }
                }

                ScannerTab {
                    id: scannerTab
                    anchors.fill: parent

                    // State properties from scannerState
                    statusText: scannerState.statusText
                    updateText: scannerState.updateText
                    clientDir: scannerState.clientDir
                    scannerRunning: scannerState.running
                    logText: scannerState.logText

                    // Theme access
                    theme: root.theme

                    // Signal handlers
                    onCheckForUpdates: function() {
                        scannerState.checkForUpdates()
                        toastManager.showInfo("Checking for updates", "Scanner data update check started")
                    }
                    onSyncClientRepo: function() {
                        scannerState.syncClientRepo()
                        toastManager.showInfo("Syncing client repo", "Client repository sync started")
                    }
                    onStartScanner: function() {
                        scannerState.startScanner()
                        toastManager.showSuccess("Scanner started", "Packet capture is now running")
                    }
                    onStartScannerSudo: function() {
                        scannerState.startScannerSudo()
                        toastManager.showSuccess("Scanner started", "Packet capture is now running (with elevated permissions)")
                    }
                    onStopScanner: function() {
                        scannerState.stopScanner()
                        toastManager.showInfo("Scanner stopped", "Packet capture has been stopped")
                    }
                    onClearLog: function() {
                        scannerState.clearLog()
                        toastManager.showInfo("Log cleared", "Scanner log has been cleared")
                    }
                }
            }

            // Market Tab - Extracted component (inline Inputs/Outputs/Results preserved for full functionality)
            Item {
                id: marketTabContainer
                opacity: viewTabs.currentIndex === 2 ? 1.0 : 0.0
                visible: true
                Layout.fillHeight: true
                Behavior on opacity {
                    NumberAnimation {
                        duration: Utils.AnimationUtils.durationNormal
                        easing.type: Utils.AnimationUtils.easingOut
                    }
                }

                MarketTab {
                id: marketTab
                anchors.fill: parent

                // Market state properties from marketSetupState
                region: marketSetupState.region
                premium: marketSetupState.premium
                priceFetchInProgress: marketSetupState.priceFetchInProgress
                validationText: marketSetupState.validationText
                pricesSource: marketSetupState.pricesSource
                listActionText: marketSetupState.listActionText
                pricesStatusText: marketSetupState.pricesStatusText
                refreshPricesButtonText: marketSetupState.refreshPricesButtonText
                canRefreshPrices: marketSetupState.canRefreshPrices
                marketStatusExpanded: marketStatusExpanded
                marketDiagnosticsVisible: marketDiagnosticsVisible
                diagnosticsText: marketSetupState.diagnosticsText

                craftCity: marketSetupState.craftCity
                defaultBuyCity: marketSetupState.defaultBuyCity
                defaultSellCity: marketSetupState.defaultSellCity
                craftRuns: marketSetupState.craftRuns
                stationFeePercent: marketSetupState.stationFeePercent
                marketTaxPercent: marketSetupState.marketTaxPercent
                dailyBonusPreset: marketSetupState.dailyBonusPreset
                focusEnabled: marketSetupState.focusEnabled

                searchQuery: marketSetupState.searchQuery || ""
                recipeEnchantFilter: marketSetupState.recipeEnchantFilter
                suggestionsCount: marketSetupState.recipeOptionsModel.rowCount()
                recipeOptionsModel: marketSetupState.recipeOptionsModel
                currentRecipeId: marketSetupState.recipeId || ""

                presetNames: marketSetupState.presetNames
                selectedPresetName: marketSetupState.selectedPresetName || ""

                craftPlanModel: marketSetupState.craftPlanModel
                craftPlanCount: marketSetupState.craftPlanCount
                craftPlanEnabledCount: marketSetupState.craftPlanEnabledCount
                craftPlanSortKey: marketSetupState.craftPlanSortKey
                craftPlanSortDescending: marketSetupState.craftPlanSortDescending

                inputsModel: marketSetupState.inputsModel
                inputsTotalCost: marketSetupState.inputsTotalCost
                outputsModel: marketSetupState.outputsModel
                outputsTotalValue: marketSetupState.outputsTotalValue
                outputsNetValue: marketSetupState.outputsNetValue
                resultsItemsModel: marketSetupState.resultsItemsModel
                marginPercent: marketSetupState.marginPercent
                resultsSortKey: marketSetupState.resultsSortKey
                marketBreakdownExpanded: marketBreakdownExpanded
                breakdownModel: marketSetupState.breakdownModel

                // Layout flags
                compactControlHeight: compactControlHeight

                // Theme access
                theme: root.theme

                // Signal handlers
                onSetRegion: function(region) { marketSetupState.setRegion(region) }
                onSetPremium: function(premium) { marketSetupState.setPremium(premium) }
                onRefreshPrices: function() {
                    marketSetupState.refreshPrices()
                    toastManager.showInfo("Refreshing prices", "Fetching market prices...")
                }
                onClearDiagnostics: function() {
                    marketSetupState.clearDiagnostics()
                    toastManager.showInfo("Diagnostics cleared", "")
                }
                onSetActiveMarketTab: function(index) { marketSetupState.setActiveMarketTab(index) }
                onSetCraftCity: function(city) { marketSetupState.setCraftCity(city) }
                onSetDefaultBuyCity: function(city) { marketSetupState.setDefaultBuyCity(city) }
                onSetDefaultSellCity: function(city) { marketSetupState.setDefaultSellCity(city) }
                onSetCraftRuns: function(runs) { marketSetupState.setCraftRuns(runs) }
                onSetStationFeePercent: function(percent) { marketSetupState.setStationFeePercent(percent) }
                onSetDailyBonusPreset: function(bonus) { marketSetupState.setDailyBonusPreset(bonus) }
                onSetFocusEnabled: function(enabled) { marketSetupState.setFocusEnabled(enabled) }
                onSetRecipeSearchQuery: function(query) { marketSetupState.setRecipeSearchQuery(query) }
                onAddFirstRecipeOption: marketSetupState.addFirstRecipeOption()
                onAddFilteredRecipeOptions: marketSetupState.addFilteredRecipeOptions()
                onAddRecipeFamily: marketSetupState.addRecipeFamily()
                onSetRecipeEnchantFilter: function(filter) { marketSetupState.setRecipeEnchantFilter(filter) }
                onAddRecipeAtIndex: function(index) { marketSetupState.addRecipeAtIndex(index) }
                onSetSelectedPresetName: function(name) { marketSetupState.setSelectedPresetName(name) }
                onSavePreset: function(name) {
                    marketSetupState.savePreset(name)
                    toastManager.showSuccess("Preset saved", name)
                }
                onLoadPreset: function(name) {
                    marketSetupState.loadPreset(name)
                    toastManager.showInfo("Preset loaded", name)
                }
                onDeletePreset: function(name) {
                    marketSetupState.deletePreset(name)
                    toastManager.showWarning("Preset deleted", name)
                }
                onSetCraftPlanSortKey: function(key) { marketSetupState.setCraftPlanSortKey(key) }
                onToggleCraftPlanSortDescending: marketSetupState.toggleCraftPlanSortDescending()
                onClearCraftPlan: function() {
                    marketSetupState.clearCraftPlan()
                    toastManager.showInfo("Craft plan cleared", "")
                }
                onSetPlanRowEnabled: function(rowId, enabled) { marketSetupState.setPlanRowEnabled(rowId, enabled) }
                onSetPlanRowCraftCity: function(rowId, city) { marketSetupState.setPlanRowCraftCity(rowId, city) }
                onSetPlanRowDailyBonus: function(rowId, bonus) { marketSetupState.setPlanRowDailyBonus(rowId, bonus) }
                onSetPlanRowRuns: function(rowId, runs) { marketSetupState.setPlanRowRuns(rowId, runs) }
                onRemovePlanRow: function(rowId) { marketSetupState.removePlanRow(rowId) }
                onSetInputStockQuantity: function(itemId, qty) { marketSetupState.setInputStockQuantity(itemId, qty) }
                onSetInputPriceType: function(itemId, type) { marketSetupState.setInputPriceType(itemId, type) }
                onSetInputManualPrice: function(itemId, price) { marketSetupState.setInputManualPrice(itemId, price) }
                onSetOutputPriceType: function(itemId, type) { marketSetupState.setOutputPriceType(itemId, type) }
                onSetOutputManualPrice: function(itemId, price) { marketSetupState.setOutputManualPrice(itemId, price) }
                onSetResultsSortKey: function(key) { marketSetupState.setResultsSortKey(key) }
                onCopyText: function(text) { root.copyText(text) }
                }
            }
        }

    }
    // Toast notifications overlay
    ToastManager {
        id: toastManager
        anchors.fill: parent
        theme: root.theme
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
