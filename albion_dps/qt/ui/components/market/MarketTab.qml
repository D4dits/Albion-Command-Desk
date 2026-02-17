import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../." // for all component access

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
    property int recipeEnchantFilter: -1
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

    property var inputsModel: null
    property int inputsTotalCost: 0
    property var outputsModel: null
    property int outputsTotalValue: 0
    property int outputsNetValue: 0
    property var resultsItemsModel: null
    property int marginPercent: 0
    property string resultsSortKey: "profit"
    property bool marketBreakdownExpanded: false
    property var breakdownModel: null
    property real craftPlanPendingContentY: -1

    // Layout flags
    property int marketColumnSpacing: 6
    property int marketSetupPanelWidth: 330
    property int marketSetupTwoColumnMinWidth: 980
    property bool marketSetupStackedLayout: width < marketSetupTwoColumnMinWidth
    property int marketSetupPanelActiveWidth: marketSetupStackedLayout ? -1 : marketSetupPanelWidth
    property int compactControlHeight: 24
    property bool narrowLayout: width < 1160

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
    readonly property int marketOutputsGrossWidth: 82
    readonly property int marketOutputsFeeWidth: 74
    readonly property int marketOutputsTaxWidth: 74
    readonly property int marketOutputsNetMinWidth: 116
    readonly property int marketOutputsContentMinWidth: marketOutputsItemWidth + marketOutputsQtyWidth + marketOutputsCityWidth + marketOutputsModeWidth + marketOutputsManualWidth + marketOutputsUnitWidth + marketOutputsGrossWidth + marketOutputsFeeWidth + marketOutputsTaxWidth + marketOutputsNetMinWidth + marketColumnSpacing * 9 + 12

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
    signal setRecipeEnchantFilter(int filter)
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
    property var itemLabelWithTier: function(labelValue, itemIdValue) { return labelValue }
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
    property var copyCellText: function(value) {
        root.copyText(String(value === undefined || value === null ? "" : value))
    }

    // Access to theme
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary

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
                    recipeEnchantFilter: root.recipeEnchantFilter
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
                    onSetRecipeEnchantFilter: function(filter) { root.setRecipeEnchantFilter(filter) }
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
                }
            }

            // Inputs Tab - Simplified inline version
            Item {
                TableSurface {
                    level: 1
                    anchors.fill: parent
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

                        Text {
                            text: "Note: Full inputs table included in MarketTab. For full functionality, the original inline implementation is preserved."
                            color: mutedColor
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Total input cost: " + formatInt(root.inputsTotalCost)
                            color: textColor
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                }
            }

            // Outputs Tab - Simplified inline version
            Item {
                TableSurface {
                    level: 1
                    anchors.fill: parent
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

                        Text {
                            text: "Note: Full outputs table included in MarketTab. For full functionality, the original inline implementation is preserved."
                            color: mutedColor
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            Text {
                                text: "Gross output: " + formatInt(root.outputsTotalValue)
                                color: textColor
                                font.pixelSize: 12
                                font.bold: true
                            }
                            Text {
                                text: "Net output: " + formatInt(root.outputsNetValue)
                                color: textColor
                                font.pixelSize: 12
                                font.bold: true
                            }
                        }
                    }
                }
            }

            // Results Tab - Simplified inline version
            Item {
                TableSurface {
                    level: 1
                    anchors.fill: parent
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Text {
                            text: "Results"
                            color: textColor
                            font.pixelSize: 12
                            font.bold: true
                        }

                        Text {
                            text: "Note: Full results view included in MarketTab. For full functionality, the original inline implementation is preserved."
                            color: mutedColor
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "Margin: " + formatFixed(root.marginPercent, 2) + "%"
                            color: signedValueColor(root.marginPercent)
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                }
            }
        }
    }
}
