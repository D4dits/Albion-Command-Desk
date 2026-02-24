import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for all component access
import "components" as Components

/**
 * MarketTab - Main market tab container
 *
 * Contains the complete market workspace with:
 * - Header with title and help
 * - Status bar with controls
 * - Diagnostics panel (conditionally visible)
 * - Tab bar (Setup, Inputs, Outputs, Results)
 * - Tab content areas
 */
CardPanel {
    id: root
    level: 1
    anchors.fill: parent

    // Market state properties (bound to parent's marketSetupState)
    property string region: "europe"
    property bool premium: false
    property bool priceFetchInProgress: false
    property bool priceFetchPending: false
    property string validationText: ""
    property string pricesSource: ""
    property string listActionText: ""
    property string pricesStatusText: ""
    property string refreshPricesButtonText: "Refresh prices"
    property bool canRefreshPrices: true
    property bool marketStatusExpanded: false
    property bool marketDiagnosticsVisible: false
    property string diagnosticsText: ""

    property string craftCity: ""
    property string defaultBuyCity: ""
    property string defaultSellCity: ""
    property int craftRuns: 1
    property real stationFeePercent: 0
    property real marketTaxPercent: 0
    property int dailyBonusPreset: 0
    property bool focusEnabled: false

    property string searchQuery: ""
    property var recipeTierFilters: []
    property var recipeEnchantFilters: []
    property int suggestionsCount: 0
    property var recipeOptionsModel: null
    property string currentRecipeId: ""

    property var presetNames: []
    property string selectedPresetName: ""

    property var craftPlanModel: null
    property int craftPlanCount: 0
    property int craftPlanEnabledCount: 0
    property string craftPlanSortKey: "added"
    property bool craftPlanSortDescending: false
    property bool hideRowsWithoutFreshPrices: false

    property var inputsModel: null
    property int inputsTotalCost: 0
    property var selectedInputItemIds: []
    property var outputsModel: null
    property int outputsTotalValue: 0
    property int outputsNetValue: 0
    property var selectedOutputItemIds: []
    property real netProfitValue: 0
    property var resultsItemsModel: null
    property int marginPercent: 0
    property real resultsInputCost: 0
    property real resultsOutputValue: 0
    property real resultsNetValue: 0
    property real resultsMarginPercent: 0
    property string resultsSortKey: "profit"
    property bool marketBreakdownExpanded: false
    property var breakdownModel: null
    property real craftPlanPendingContentY: -1
    property string inputsSearchQuery: ""
    property string outputsSearchQuery: ""
    property string resultsSearchQuery: ""
    property bool inputsShowOnOnly: false
    property bool outputsShowOnOnly: false

    // Layout flags
    property int marketColumnSpacing: 6
    property int marketSetupPanelWidth: 296
    property int marketSetupTwoColumnMinWidth: 820
    property bool marketSetupStackedLayout: width < marketSetupTwoColumnMinWidth
    property int marketSetupPanelActiveWidth: marketSetupStackedLayout ? -1 : marketSetupPanelWidth
    property int compactControlHeight: 24
    property bool narrowLayout: width < 1160
    property double priceFetchStartedAtMs: 0
    property int priceFetchElapsedSeconds: 0

    // Computed widths for tables
    readonly property int marketInputsItemWidth: Math.max(narrowLayout ? 130 : 150, Math.min(240, Math.round(width * (narrowLayout ? 0.15 : 0.17))))
    readonly property int marketInputsQtyWidth: 62
    readonly property int marketInputsStockWidth: 72
    readonly property int marketInputsBuyWidth: 62
    readonly property int marketInputsCityWidth: 118
    readonly property int marketInputsModeWidth: 96
    readonly property int marketInputsManualWidth: 74
    readonly property int marketInputsUnitWidth: 78
    readonly property int marketInputsAgeWidth: 76
    readonly property int marketInputsTotalMinWidth: 120
    readonly property int marketInputsContentMinWidth: marketInputsItemWidth + marketInputsQtyWidth + marketInputsCityWidth + marketInputsModeWidth + marketInputsManualWidth + marketInputsUnitWidth + marketInputsAgeWidth + marketInputsTotalMinWidth + marketInputsStockWidth + marketInputsBuyWidth + marketColumnSpacing * 9 + 12

    readonly property int marketOutputsItemWidth: Math.max(narrowLayout ? 130 : 145, Math.min(230, Math.round(width * (narrowLayout ? 0.14 : 0.16))))
    readonly property int marketOutputsQtyWidth: 58
    readonly property int marketOutputsCityWidth: 108
    readonly property int marketOutputsModeWidth: 92
    readonly property int marketOutputsManualWidth: 70
    readonly property int marketOutputsUnitWidth: 74
    readonly property int marketOutputsAgeWidth: 76
    readonly property int marketOutputsGrossWidth: 82
    readonly property int marketOutputsFeeWidth: 74
    readonly property int marketOutputsTaxWidth: 74
    readonly property int marketOutputsNetMinWidth: 116
    readonly property int marketOutputsContentMinWidth: marketOutputsItemWidth + marketOutputsQtyWidth + marketOutputsCityWidth + marketOutputsModeWidth + marketOutputsManualWidth + marketOutputsUnitWidth + marketOutputsAgeWidth + marketOutputsGrossWidth + marketOutputsFeeWidth + marketOutputsTaxWidth + marketOutputsNetMinWidth + marketColumnSpacing * 10 + 12

    readonly property int marketResultsItemWidth: Math.max(narrowLayout ? 180 : 220, Math.min(340, Math.round(width * (narrowLayout ? 0.24 : 0.28))))

    // Signals
    signal setRegion(string region)
    signal setPremium(bool premium)
    signal refreshPrices()
    signal clearDiagnostics()
    signal setActiveMarketTab(int index)

    signal setCraftCity(string city)
    signal setDefaultBuyCity(string city)
    signal setDefaultSellCity(string city)
    signal setCraftRuns(int runs)
    signal setStationFeePercent(real percent)
    signal setDailyBonusPreset(string bonus)
    signal setFocusEnabled(bool enabled)
    signal setRecipeSearchQuery(string query)
    signal addFirstRecipeOption()
    signal addFilteredRecipeOptions()
    signal addRecipeFamily()
    signal setRecipeTierFilters(var filters)
    signal setRecipeEnchantFilters(var filters)
    signal addRecipeAtIndex(int index)
    signal setSelectedPresetName(string name)
    signal savePreset(string name)
    signal loadPreset(string name)
    signal deletePreset(string name)
    signal setCraftPlanSortKey(string key)
    signal toggleCraftPlanSortDescending()
    signal clearCraftPlan()
    signal setPlanRowEnabled(var rowId, bool enabled)
    signal setPlanRowCraftCity(var rowId, string city)
    signal setPlanRowDailyBonus(var rowId, string bonus)
    signal setPlanRowRuns(var rowId, int runs)
    signal removePlanRow(var rowId)
    signal setHideRowsWithoutFreshPrices(bool enabled)
    signal setInputStockQuantity(var itemId, string qty)
    signal setInputPriceType(var itemId, string type)
    signal setInputManualPrice(var itemId, string price)
    signal setOutputPriceType(var itemId, string type)
    signal setOutputManualPrice(var itemId, string price)
    signal setResultsSortKey(string key)
    signal copyText(string text)

    // Helper functions
    property var priceSourceColor: function(source) {
        var source = String(source || "").toLowerCase()
        if (source === "fallback" || source === "stale_cache") return root.theme.stateWarning
        if (source === "live" || source === "cache") return root.theme.stateSuccess
        return root.theme.textMuted
    }
    property var validationColor: function(isValid) { return root.theme.stateSuccess }
    property var tableRowColor: function(index) { return index % 2 === 0 ? root.theme.tableRowEven : root.theme.tableRowOdd }
    property var tableRowStrongColor: function(index) { return index % 2 === 0 ? root.theme.surfaceInteractive : root.theme.tableRowEven }
    property var itemLabelWithTier: function(labelValue, itemIdValue) {
        var label = String(labelValue || "").trim()
        var itemId = String(itemIdValue || "").trim().toUpperCase()
        if (itemId.length === 0) return label

        var tierMatch = itemId.match(/^T(\d+)_/)
        if (!tierMatch) return label
        var tier = parseInt(tierMatch[1], 10)
        if (!isFinite(tier) || tier <= 0) return label

        var enchant = 0
        var enchantMatch = itemId.match(/@(\d+)$/)
        if (enchantMatch) {
            enchant = parseInt(enchantMatch[1], 10)
            if (!isFinite(enchant) || enchant < 0) enchant = 0
        } else {
            var levelMatch = itemId.match(/_LEVEL(\d+)$/)
            if (levelMatch) {
                enchant = parseInt(levelMatch[1], 10)
                if (!isFinite(enchant) || enchant < 0) enchant = 0
            }
        }

        var suffix = enchant > 0 ? (" T" + tier + "." + enchant) : (" T" + tier)
        var withoutTier = label.replace(/\s+(?:T?\d+(?:\.\d+)?)\s*$/i, "").trim()
        var baseLabel = withoutTier.length > 0 ? withoutTier : label
        return baseLabel + suffix
    }
    property var itemLabelWithTierParts: function(label, tier, enchant) {
        if (!isFinite(tier) || tier <= 0) return label
        var suffix = enchant > 0 ? (" T" + tier + "." + enchant) : (" T" + tier)
        return label + suffix
    }
    property var signedValueColor: function(value) {
        var n = Number(value)
        if (!isFinite(n)) return root.theme.textMuted
        if (n > 0) return root.theme.stateSuccess
        if (n < 0) return root.theme.stateDanger
        return root.theme.stateInfo
    }
    property var adpAgeColor: function(ageText) {
        var raw = String(ageText || "").trim().toLowerCase()
        if (raw === "manual") return root.theme.stateInfo
        if (raw === "n/a" || raw === "unknown" || raw.length === 0) return root.theme.textMuted
        var minutes = 0
        var dayMatch = raw.match(/(\d+)\s*d/)
        if (dayMatch) minutes += parseInt(dayMatch[1]) * 1440
        var hourMatch = raw.match(/(\d+)\s*h/)
        if (hourMatch) minutes += parseInt(hourMatch[1]) * 60
        var minuteMatch = raw.match(/(\d+)\s*m/)
        if (minuteMatch) minutes += parseInt(minuteMatch[1])
        else if (raw.indexOf("<1m") >= 0) minutes += 0
        if (minutes <= 20) return root.theme.stateSuccess
        if (minutes <= 60) return root.theme.stateWarning
        return root.theme.stateDanger
    }
    property var formatInt: function(value) {
        var n = Number(value)
        if (!isFinite(n)) return "0"
        var whole = Math.round(n)
        var sign = whole < 0 ? "-" : ""
        var raw = Math.abs(whole).toString()
        return sign + raw.replace(/\B(?=(\d{3})+(?!\d))/g, " ")
    }
    property var formatFixed: function(value, decimals) {
        var n = Number(value)
        if (!isFinite(n)) n = 0
        var fixed = n.toFixed(Math.max(0, decimals))
        var parts = fixed.split(".")
        var whole = Number(parts[0] || "0")
        if (parts.length === 1 || decimals <= 0) return formatInt(whole)
        return formatInt(whole) + "." + parts[1]
    }
    property var formatElapsed: function(totalSeconds) {
        var seconds = Math.max(0, Number(totalSeconds) || 0)
        var mm = Math.floor(seconds / 60)
        var ss = seconds % 60
        var mmText = mm < 10 ? ("0" + mm) : String(mm)
        var ssText = ss < 10 ? ("0" + ss) : String(ss)
        return mmText + ":" + ssText
    }
    property var copyCellText: function(value) {
        root.copyText(String(value === undefined || value === null ? "" : value))
    }
    property var matchesSearch: function(itemText, queryText) {
        var query = String(queryText || "").trim().toLowerCase()
        if (query.length === 0) {
            return true
        }
        return String(itemText || "").toLowerCase().indexOf(query) >= 0
    }
    property var containsItemId: function(itemId, listValue) {
        var target = String(itemId || "")
        if (target.length === 0 || !listValue) {
            return false
        }
        for (var i = 0; i < listValue.length; i += 1) {
            if (String(listValue[i]) === target) {
                return true
            }
        }
        return false
    }

    // Access to theme
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary

    onPriceFetchInProgressChanged: {
        if (priceFetchInProgress) {
            priceFetchStartedAtMs = Date.now()
            priceFetchElapsedSeconds = 0
            fetchElapsedTimer.start()
        } else {
            fetchElapsedTimer.stop()
            priceFetchElapsedSeconds = 0
        }
    }

    Timer {
        id: fetchElapsedTimer
        interval: 1000
        repeat: true
        running: false
        onTriggered: {
            if (!root.priceFetchInProgress) {
                stop()
                root.priceFetchElapsedSeconds = 0
                return
            }
            root.priceFetchElapsedSeconds = Math.max(
                0,
                Math.floor((Date.now() - root.priceFetchStartedAtMs) / 1000)
            )
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // Header with title and help button
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

        // Status bar
        MarketStatusBar {
            Layout.fillWidth: true
            theme: root.theme
            textColor: root.textColor
            mutedColor: root.mutedColor
            priceFetchInProgress: root.priceFetchInProgress
            validationText: root.validationText
            pricesSource: root.pricesSource
            listActionText: root.listActionText
            region: root.region
            premium: root.premium
            refreshPricesButtonText: root.refreshPricesButtonText
            canRefreshPrices: root.canRefreshPrices
            statusExpanded: root.marketStatusExpanded
            diagnosticsVisible: root.marketDiagnosticsVisible
            pricesStatusText: root.pricesStatusText
            priceSourceColor: root.priceSourceColor
            validationColor: root.validationColor
            onSetRegion: function(region) { root.setRegion(region) }
            onSetPremium: function(premium) { root.setPremium(premium) }
            onRefreshPrices: root.refreshPrices()
            onToggleStatusExpanded: root.marketStatusExpanded = !root.marketStatusExpanded
            onToggleDiagnosticsVisible: root.marketDiagnosticsVisible = !root.marketDiagnosticsVisible
        }

        // Diagnostics panel (conditionally visible)
        MarketDiagnostics {
            Layout.fillWidth: true
            visible: root.marketDiagnosticsVisible
            theme: root.theme
            textColor: root.textColor
            mutedColor: root.mutedColor
            diagnosticsText: root.diagnosticsText
            onClearDiagnostics: root.clearDiagnostics()
        }

        // Tab bar
        TabBar {
            id: marketTabs
            Layout.fillWidth: true
            implicitHeight: 30
            spacing: theme.spacingCompact
            padding: 0
            onCurrentIndexChanged: {
                root.setActiveMarketTab(currentIndex)
            }
            Component.onCompleted: root.setActiveMarketTab(currentIndex)
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

        // Tab content
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: marketTabs.currentIndex

            // Setup Tab
            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: root.marketSetupStackedLayout ? 1 : 2
                columnSpacing: 12
                rowSpacing: 12

                MarketSetupPanel {
                    Layout.column: 0
                    Layout.row: 0
                    Layout.fillHeight: true
                    Layout.fillWidth: root.marketSetupStackedLayout
                    Layout.preferredWidth: root.marketSetupStackedLayout ? -1 : root.marketSetupPanelActiveWidth
                    Layout.minimumWidth: root.marketSetupStackedLayout ? 260 : root.marketSetupPanelActiveWidth
                    Layout.maximumWidth: root.marketSetupStackedLayout ? 16777215 : root.marketSetupPanelActiveWidth
                    marketSetupStackedLayout: root.marketSetupStackedLayout
                    marketSetupPanelActiveWidth: root.marketSetupPanelActiveWidth
                    compactControlHeight: root.compactControlHeight
                    craftCity: root.craftCity
                    defaultBuyCity: root.defaultBuyCity
                    defaultSellCity: root.defaultSellCity
                    craftRuns: root.craftRuns
                    stationFeePercent: root.stationFeePercent
                    premium: root.premium
                    marketTaxPercent: root.marketTaxPercent
                    dailyBonusPreset: root.dailyBonusPreset
                    focusEnabled: root.focusEnabled
                    craftPlanModel: root.craftPlanModel
                    craftPlanCount: root.craftPlanCount
                    craftPlanEnabledCount: root.craftPlanEnabledCount
                    craftPlanSortKey: root.craftPlanSortKey
                    craftPlanSortDescending: root.craftPlanSortDescending
                    currentRecipeId: root.currentRecipeId
                    searchQuery: root.searchQuery
                    recipeTierFilters: root.recipeTierFilters
                    recipeEnchantFilters: root.recipeEnchantFilters
                    suggestionsCount: root.suggestionsCount
                    recipeOptionsModel: root.recipeOptionsModel
                    presetNames: root.presetNames
                    selectedPresetName: root.selectedPresetName
                    theme: root.theme
                    textColor: root.textColor
                    mutedColor: root.mutedColor
                    accentColor: root.accentColor
                    tableRowStrongColor: root.tableRowStrongColor
                    tableRowColor: root.tableRowColor
                    itemLabelWithTierParts: root.itemLabelWithTierParts
                    signedValueColor: root.signedValueColor
                    copyCellText: root.copyCellText
                    craftPlanPendingContentY: root.craftPlanPendingContentY
                    onSetCraftCity: function(city) { root.setCraftCity(city) }
                    onSetDefaultBuyCity: function(city) { root.setDefaultBuyCity(city) }
                    onSetDefaultSellCity: function(city) { root.setDefaultSellCity(city) }
                    onSetCraftRuns: function(runs) { root.setCraftRuns(runs) }
                    onSetStationFeePercent: function(percent) { root.setStationFeePercent(percent) }
                    onSetDailyBonusPreset: function(bonus) { root.setDailyBonusPreset(bonus) }
                    onSetFocusEnabled: function(enabled) { root.setFocusEnabled(enabled) }
                    onSetRecipeSearchQuery: function(query) { root.setRecipeSearchQuery(query) }
                    onAddFirstRecipeOption: root.addFirstRecipeOption()
                    onAddFilteredRecipeOptions: root.addFilteredRecipeOptions()
                    onAddRecipeFamily: root.addRecipeFamily()
                    onSetRecipeTierFilters: function(filters) { root.setRecipeTierFilters(filters) }
                    onSetRecipeEnchantFilters: function(filters) { root.setRecipeEnchantFilters(filters) }
                    onAddRecipeAtIndex: function(index) { root.addRecipeAtIndex(index) }
                    onSetSelectedPresetName: function(name) { root.setSelectedPresetName(name) }
                    onSavePreset: function(name) { root.savePreset(name) }
                    onLoadPreset: function(name) { root.loadPreset(name) }
                    onDeletePreset: function(name) { root.deletePreset(name) }
                }

                MarketCraftsTable {
                    Layout.column: root.marketSetupStackedLayout ? 0 : 1
                    Layout.row: root.marketSetupStackedLayout ? 1 : 0
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: 0
                    craftPlanModel: root.craftPlanModel
                    craftPlanCount: root.craftPlanCount
                    craftPlanEnabledCount: root.craftPlanEnabledCount
                    craftPlanSortKey: root.craftPlanSortKey
                    craftPlanSortDescending: root.craftPlanSortDescending
                    hideRowsWithoutFreshPrices: root.hideRowsWithoutFreshPrices
                    currentRecipeId: root.currentRecipeId
                    compactControlHeight: root.compactControlHeight
                    craftPlanPendingContentY: root.craftPlanPendingContentY
                    theme: root.theme
                    textColor: root.textColor
                    mutedColor: root.mutedColor
                    accentColor: root.accentColor
                    tableRowColor: root.tableRowColor
                    itemLabelWithTierParts: root.itemLabelWithTierParts
                    signedValueColor: root.signedValueColor
                    copyCellText: root.copyCellText
                    onSetCraftPlanSortKey: function(key) { root.setCraftPlanSortKey(key) }
                    onToggleCraftPlanSortDescending: root.toggleCraftPlanSortDescending()
                    onClearCraftPlan: root.clearCraftPlan()
                    onSetPlanRowEnabled: function(rowId, enabled) { root.setPlanRowEnabled(rowId, enabled) }
                    onSetPlanRowCraftCity: function(rowId, city) { root.setPlanRowCraftCity(rowId, city) }
                    onSetPlanRowDailyBonus: function(rowId, bonus) { root.setPlanRowDailyBonus(rowId, bonus) }
                    onSetPlanRowRuns: function(rowId, runs) { root.setPlanRowRuns(rowId, runs) }
                    onRemovePlanRow: function(rowId) { root.removePlanRow(rowId) }
                    onSetHideRowsWithoutFreshPrices: function(enabled) { root.setHideRowsWithoutFreshPrices(enabled) }
                }
            }

            // Inputs Tab
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

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: "Search"
                            color: mutedColor
                            font.pixelSize: 11
                        }
                        AppTextField {
                            Layout.preferredWidth: 240
                            implicitHeight: compactControlHeight
                            font.pixelSize: 11
                            placeholderText: "item name"
                            text: root.inputsSearchQuery
                            onTextChanged: root.inputsSearchQuery = text
                        }
                        AppCheckBox {
                            text: "Only On items"
                            checked: root.inputsShowOnOnly
                            onToggled: root.inputsShowOnOnly = checked
                        }
                        Item { Layout.fillWidth: true }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 24
                        radius: 4
                        color: "#111b28"
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: marketColumnSpacing
                            Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsItemWidth; elide: Text.ElideRight }
                            Text { text: "Need"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsQtyWidth }
                            Text { text: "Stock"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsStockWidth }
                            Text { text: "Buy"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsBuyWidth }
                            Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsCityWidth; elide: Text.ElideRight }
                            Text { text: "Mode"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsModeWidth }
                            Text { text: "Manual"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsManualWidth }
                            Text { text: "Unit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsUnitWidth }
                            Text { text: "ADP age"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsAgeWidth }
                            Text { text: "Total"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true; Layout.minimumWidth: marketInputsTotalMinWidth }
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 120
                        clip: true
                        model: root.inputsModel

                        delegate: Rectangle {
                            readonly property bool searchMatches: root.matchesSearch(item, root.inputsSearchQuery)
                            readonly property bool onMatches: !root.inputsShowOnOnly
                                || root.containsItemId(itemId, root.selectedInputItemIds)
                            width: ListView.view.width
                            height: (searchMatches && onMatches) ? 30 : 0
                            visible: searchMatches && onMatches
                            color: tableRowColor(index)

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 4
                                spacing: marketColumnSpacing

                                Text {
                                    text: itemLabelWithTier(item, itemId)
                                    color: textColor
                                    font.pixelSize: 11
                                    Layout.preferredWidth: marketInputsItemWidth
                                    elide: Text.ElideRight
                                    MouseArea {
                                        anchors.fill: parent
                                        acceptedButtons: Qt.LeftButton
                                        onDoubleClicked: root.copyCellText(parent.text)
                                    }
                                }
                                Text { text: formatInt(quantity); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsQtyWidth }

                                TextField {
                                    Layout.preferredWidth: marketInputsStockWidth
                                    implicitHeight: compactControlHeight
                                    font.pixelSize: 11
                                    text: stockQuantity > 0 ? formatFixed(stockQuantity, 2) : ""
                                    placeholderText: "0"
                                    onEditingFinished: root.setInputStockQuantity(itemId, text)
                                }

                                Text { text: formatFixed(buyQuantity, 2); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsBuyWidth }
                                Text { text: city; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsCityWidth; elide: Text.ElideRight }

                                ComboBox {
                                    Layout.preferredWidth: marketInputsModeWidth
                                    implicitHeight: compactControlHeight
                                    font.pixelSize: 11
                                    model: ["buy_order", "sell_order", "average"]
                                    currentIndex: Math.max(0, model.indexOf(priceType))
                                    onActivated: root.setInputPriceType(itemId, currentText)
                                }

                                TextField {
                                    Layout.preferredWidth: marketInputsManualWidth
                                    implicitHeight: compactControlHeight
                                    font.pixelSize: 11
                                    text: manualPrice > 0 ? String(manualPrice) : ""
                                    placeholderText: "-"
                                    inputMethodHints: Qt.ImhDigitsOnly
                                    onEditingFinished: root.setInputManualPrice(itemId, text)
                                }

                                Text { text: formatInt(unitPrice); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketInputsUnitWidth }
                                Text { text: priceAgeText; color: adpAgeColor(priceAgeText); font.pixelSize: 11; Layout.preferredWidth: marketInputsAgeWidth }
                                Text { text: formatInt(totalCost); color: textColor; font.pixelSize: 11; Layout.fillWidth: true; Layout.minimumWidth: marketInputsTotalMinWidth }
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
                            Text { text: formatInt(root.inputsTotalCost); color: textColor; font.pixelSize: 12; font.bold: true }
                        }
                    }
                }
            }

            // Outputs Tab
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

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: "Search"
                            color: mutedColor
                            font.pixelSize: 11
                        }
                        AppTextField {
                            Layout.preferredWidth: 240
                            implicitHeight: compactControlHeight
                            font.pixelSize: 11
                            placeholderText: "item name"
                            text: root.outputsSearchQuery
                            onTextChanged: root.outputsSearchQuery = text
                        }
                        AppCheckBox {
                            text: "Only On items"
                            checked: root.outputsShowOnOnly
                            onToggled: root.outputsShowOnOnly = checked
                        }
                        Item { Layout.fillWidth: true }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 24
                        radius: 4
                        color: "#111b28"
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: marketColumnSpacing
                            Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsItemWidth; elide: Text.ElideRight }
                            Text { text: "Qty"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsQtyWidth }
                            Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsCityWidth; elide: Text.ElideRight }
                            Text { text: "Mode"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsModeWidth }
                            Text { text: "Manual"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsManualWidth }
                            Text { text: "Unit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsUnitWidth }
                            Text { text: "ADP age"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsAgeWidth }
                            Text { text: "Gross"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsGrossWidth }
                            Text { text: "Fee"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsFeeWidth }
                            Text { text: "Tax"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsTaxWidth }
                            Text { text: "Net"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true; Layout.minimumWidth: marketOutputsNetMinWidth }
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 120
                        clip: true
                        model: root.outputsModel

                        delegate: Rectangle {
                            readonly property bool searchMatches: root.matchesSearch(item, root.outputsSearchQuery)
                            readonly property bool onMatches: !root.outputsShowOnOnly
                                || root.containsItemId(itemId, root.selectedOutputItemIds)
                            width: ListView.view.width
                            height: (searchMatches && onMatches) ? 30 : 0
                            visible: searchMatches && onMatches
                            color: tableRowColor(index)

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 4
                                spacing: marketColumnSpacing

                                Text {
                                    text: itemLabelWithTier(item, itemId)
                                    color: textColor
                                    font.pixelSize: 11
                                    Layout.preferredWidth: marketOutputsItemWidth
                                    elide: Text.ElideRight
                                    MouseArea {
                                        anchors.fill: parent
                                        acceptedButtons: Qt.LeftButton
                                        onDoubleClicked: root.copyCellText(parent.text)
                                    }
                                }
                                Text { text: formatFixed(quantity, 2); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsQtyWidth }
                                Text { text: city; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsCityWidth; elide: Text.ElideRight }

                                ComboBox {
                                    Layout.preferredWidth: marketOutputsModeWidth
                                    implicitHeight: compactControlHeight
                                    font.pixelSize: 11
                                    model: ["sell_order", "buy_order", "average"]
                                    currentIndex: Math.max(0, model.indexOf(priceType))
                                    onActivated: root.setOutputPriceType(itemId, currentText)
                                }

                                TextField {
                                    Layout.preferredWidth: marketOutputsManualWidth
                                    implicitHeight: compactControlHeight
                                    font.pixelSize: 11
                                    text: manualPrice > 0 ? String(manualPrice) : ""
                                    placeholderText: "-"
                                    inputMethodHints: Qt.ImhDigitsOnly
                                    onEditingFinished: root.setOutputManualPrice(itemId, text)
                                }

                                Text { text: formatInt(unitPrice); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsUnitWidth }
                                Text { text: priceAgeText; color: adpAgeColor(priceAgeText); font.pixelSize: 11; Layout.preferredWidth: marketOutputsAgeWidth }
                                Text { text: formatInt(totalValue); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsGrossWidth }
                                Text { text: formatInt(feeValue); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsFeeWidth }
                                Text { text: formatInt(taxValue); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: marketOutputsTaxWidth }
                                Text { text: formatInt(netValue); color: textColor; font.pixelSize: 11; Layout.fillWidth: true; Layout.minimumWidth: marketOutputsNetMinWidth }
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
                            Text { text: formatInt(root.outputsTotalValue); color: textColor; font.pixelSize: 12; font.bold: true }
                            Text { text: "|"; color: mutedColor; font.pixelSize: 11 }
                            Text { text: "Net output"; color: mutedColor; font.pixelSize: 11 }
                            Text { text: formatInt(root.outputsNetValue); color: textColor; font.pixelSize: 12; font.bold: true }
                            Item { Layout.fillWidth: true }
                        }
                    }
                }
            }

            // Results Tab
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
                        Text { text: "Results"; color: textColor; font.pixelSize: 12; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: "Sort"; color: mutedColor; font.pixelSize: 11 }
                        ComboBox {
                            Layout.preferredWidth: 120
                            implicitHeight: compactControlHeight
                            font.pixelSize: 11
                            model: ["profit", "margin", "revenue"]
                            currentIndex: Math.max(0, model.indexOf(root.resultsSortKey))
                            onActivated: root.setResultsSortKey(currentText)
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text { text: "Search"; color: mutedColor; font.pixelSize: 11 }
                        AppTextField {
                            Layout.preferredWidth: 240
                            implicitHeight: compactControlHeight
                            font.pixelSize: 11
                            placeholderText: "item name"
                            text: root.resultsSearchQuery
                            onTextChanged: root.resultsSearchQuery = text
                        }
                        Item { Layout.fillWidth: true }
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
                            Text { text: "Investment: " + formatInt(root.resultsInputCost); color: mutedColor; font.pixelSize: 11 }
                            Text { text: "Revenue: " + formatInt(root.resultsOutputValue); color: mutedColor; font.pixelSize: 11 }
                            Text { text: "Net: " + formatInt(root.resultsNetValue); color: signedValueColor(root.resultsNetValue); font.pixelSize: 11 }
                            Item { Layout.fillWidth: true }
                            Text { text: "Margin: " + formatFixed(root.resultsMarginPercent, 2) + "%"; color: signedValueColor(root.resultsMarginPercent); font.pixelSize: 11 }
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
                            Text { text: "Item"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 200; elide: Text.ElideRight }
                            Text { text: "City"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 92 }
                            Text { text: "Qty"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 58 }
                            Text { text: "Revenue"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 84 }
                            Text { text: "Cost"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 84 }
                            Text { text: "Fee"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 68 }
                            Text { text: "Tax"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 68 }
                            Text { text: "Profit"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 84 }
                            Text { text: "Margin"; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 70 }
                            Text { text: "Demand"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true }
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 120
                        clip: true
                        model: root.resultsItemsModel

                        delegate: Rectangle {
                            readonly property bool searchMatches: root.matchesSearch(item, root.resultsSearchQuery)
                            width: ListView.view.width
                            height: searchMatches ? 28 : 0
                            visible: searchMatches
                            color: tableRowColor(index)

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 4
                                spacing: 6

                                Text {
                                    text: itemLabelWithTier(item, itemId)
                                    color: textColor
                                    font.pixelSize: 11
                                    Layout.preferredWidth: 200
                                    elide: Text.ElideRight
                                    MouseArea {
                                        anchors.fill: parent
                                        acceptedButtons: Qt.LeftButton
                                        onDoubleClicked: root.copyCellText(parent.text)
                                    }
                                }
                                Text { text: city; color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 92; elide: Text.ElideRight }
                                Text { text: formatFixed(quantity, 2); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 58; horizontalAlignment: Text.AlignRight }
                                Text { text: formatInt(revenue); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 84; horizontalAlignment: Text.AlignRight }
                                Text { text: formatInt(cost); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 84; horizontalAlignment: Text.AlignRight }
                                Text { text: formatInt(feeValue); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 68; horizontalAlignment: Text.AlignRight }
                                Text { text: formatInt(taxValue); color: mutedColor; font.pixelSize: 11; Layout.preferredWidth: 68; horizontalAlignment: Text.AlignRight }
                                Text { text: formatInt(profit); color: signedValueColor(profit); font.pixelSize: 11; Layout.preferredWidth: 84; horizontalAlignment: Text.AlignRight }
                                Text { text: formatFixed(marginPercent, 1) + "%"; color: signedValueColor(marginPercent); font.pixelSize: 11; Layout.preferredWidth: 70; horizontalAlignment: Text.AlignRight }
                                Text { text: formatFixed(demandProxy, 1) + "%"; color: mutedColor; font.pixelSize: 11; Layout.fillWidth: true; horizontalAlignment: Text.AlignRight }
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: root.priceFetchInProgress || root.priceFetchPending
        z: 200
        color: Qt.rgba(6 / 255, 14 / 255, 24 / 255, 0.72)

        MouseArea {
            anchors.fill: parent
            enabled: parent.visible
            acceptedButtons: Qt.AllButtons
        }

        TableSurface {
            anchors.centerIn: parent
            width: Math.min(560, root.width - 48)
            height: overlayContent.implicitHeight + 28
            level: 1

            ColumnLayout {
                id: overlayContent
                anchors.fill: parent
                anchors.margins: 14
                spacing: 8

                Components.Spinner {
                    Layout.alignment: Qt.AlignHCenter
                    size: "lg"
                    active: root.priceFetchInProgress
                    theme: root.theme
                }

                Text {
                    Layout.fillWidth: true
                    text: "Fetching market prices..."
                    color: root.textColor
                    font.pixelSize: 14
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: root.pricesStatusText.length > 0 ? root.pricesStatusText : "Preparing AO Data request..."
                    color: root.mutedColor
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }

                Text {
                    Layout.fillWidth: true
                    text: "Elapsed: " + root.formatElapsed(root.priceFetchElapsedSeconds)
                        + "  |  Large plans (400+ IDs) may take up to ~40s."
                    color: root.theme.stateInfo
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }
    }
}
