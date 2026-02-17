import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for all component access

/**
 * MarketSetupPanel - Setup sub-tab for market configuration
 *
 * Contains:
 * - Craft search with suggestions
 * - Preset management
 * - City selection (Craft/Buy/Sell)
 * - Additional settings (Runs, Fee, Bonus, Focus)
 * - Crafts table
 */
TableSurface {
    id: root
    level: 1
    Layout.fillHeight: true
    Layout.fillWidth: marketSetupStackedLayout
    Layout.preferredWidth: marketSetupStackedLayout ? -1 : marketSetupPanelActiveWidth
    Layout.minimumWidth: marketSetupStackedLayout ? 260 : marketSetupPanelActiveWidth
    Layout.maximumWidth: marketSetupStackedLayout ? 16777215 : marketSetupPanelActiveWidth

    // Layout flags
    property bool marketSetupStackedLayout: false
    property int marketSetupPanelActiveWidth: 330
    property int compactControlHeight: 24

    // Market state properties (bound to parent's marketSetupState)
    property string craftCity: ""
    property string defaultBuyCity: ""
    property string defaultSellCity: ""
    property int craftRuns: 1
    property real stationFeePercent: 0
    property bool premium: false
    property real marketTaxPercent: 0
    property int dailyBonusPreset: 0
    property bool focusEnabled: false
    property var craftPlanModel: null
    property int craftPlanCount: 0
    property int craftPlanEnabledCount: 0
    property string craftPlanSortKey: "added"
    property bool craftPlanSortDescending: false
    property string currentRecipeId: ""

    // Search state
    property string searchQuery: ""
    property int recipeEnchantFilter: -1
    property int suggestionsCount: 0
    property var recipeOptionsModel: null

    // Presets state
    property var presetNames: []
    property string selectedPresetName: ""

    // Signals
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

    // Helper functions
    property var tableRowStrongColor: function(index) {
        return index % 2 === 0 ? theme.surfaceInteractive : theme.tableRowEven
    }
    property var tableRowColor: function(index) {
        return index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
    }
    property var itemLabelWithTierParts: function(label, tier, enchant) { return label }
    property var signedValueColor: function(value) { return theme.stateSuccess }
    property var copyCellText: function(text) {}

    // For scroll position restoration
    property real craftPlanPendingContentY: -1

    // Access to theme
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary

    ScrollView {
        id: marketSetupScroll
        anchors.fill: parent
        anchors.margins: 10
        clip: true
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

        ColumnLayout {
            width: Math.max(0, parent.width - 14)
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
                MarketCraftSearch {
                    Layout.columnSpan: 2
                    Layout.fillWidth: true
                    theme: root.theme
                    textColor: root.textColor
                    mutedColor: root.mutedColor
                    compactControlHeight: root.compactControlHeight
                    searchQuery: root.searchQuery
                    recipeEnchantFilter: root.recipeEnchantFilter
                    suggestionsCount: root.suggestionsCount
                    recipeOptionsModel: root.recipeOptionsModel
                    currentRecipeId: root.currentRecipeId
                    tableRowStrongColor: root.tableRowStrongColor
                    onSetRecipeSearchQuery: root.setRecipeSearchQuery(query)
                    onAddFirstRecipeOption: root.addFirstRecipeOption()
                    onAddFilteredRecipeOptions: root.addFilteredRecipeOptions()
                    onAddRecipeFamily: root.addRecipeFamily()
                    onSetRecipeEnchantFilter: root.setRecipeEnchantFilter(filter)
                    onAddRecipeAtIndex: function(index) { root.addRecipeAtIndex(index) }
                }

                Text { text: "Craft City"; color: mutedColor; font.pixelSize: 11 }
                AppComboBox {
                    Layout.fillWidth: true
                    implicitHeight: root.compactControlHeight
                    font.pixelSize: 11
                    model: [
                        "Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien",
                        "Arthur's Rest", "Merlyn's Rest", "Morgana's Rest"
                    ]
                    currentIndex: Math.max(0, model.indexOf(root.craftCity))
                    onActivated: root.setCraftCity(currentText)
                }

                Text { text: "Buy City"; color: mutedColor; font.pixelSize: 11 }
                AppComboBox {
                    Layout.fillWidth: true
                    implicitHeight: root.compactControlHeight
                    font.pixelSize: 11
                    model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                    currentIndex: Math.max(0, model.indexOf(root.defaultBuyCity))
                    onActivated: root.setDefaultBuyCity(currentText)
                }

                Text { text: "Sell City"; color: mutedColor; font.pixelSize: 11 }
                AppComboBox {
                    Layout.fillWidth: true
                    implicitHeight: root.compactControlHeight
                    font.pixelSize: 11
                    model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                    currentIndex: Math.max(0, model.indexOf(root.defaultSellCity))
                    onActivated: root.setDefaultSellCity(currentText)
                }

                Text { text: "Default Runs"; color: mutedColor; font.pixelSize: 11 }
                AppSpinBox {
                    Layout.fillWidth: true
                    implicitHeight: root.compactControlHeight
                    font.pixelSize: 11
                    from: 1
                    to: 10000
                    editable: true
                    value: root.craftRuns
                    onValueModified: root.setCraftRuns(value)
                }

                Text { text: "Usage Fee (1-999)"; color: mutedColor; font.pixelSize: 11 }
                AppSpinBox {
                    Layout.fillWidth: true
                    implicitHeight: root.compactControlHeight
                    font.pixelSize: 11
                    from: 1
                    to: 999
                    stepSize: 1
                    editable: true
                    value: Math.round(root.stationFeePercent)
                    textFromValue: function(v) { return String(v) }
                    valueFromText: function(t, _locale) {
                        var p = parseFloat(t)
                        return isNaN(p) ? value : Math.round(p)
                    }
                    onValueModified: root.setStationFeePercent(value)
                }

                Text { text: "Market Fees % (auto)"; color: mutedColor; font.pixelSize: 11 }
                Text {
                    Layout.fillWidth: true
                    text: root.premium
                        ? "4.0% (tax) + 2.5% (setup) = " + Number(root.marketTaxPercent).toFixed(1) + "%"
                        : "8.0% (tax) + 2.5% (setup) = " + Number(root.marketTaxPercent).toFixed(1) + "%"
                    color: textColor
                    font.pixelSize: 11
                }

                Text { text: "Default Daily Bonus"; color: mutedColor; font.pixelSize: 11 }
                AppComboBox {
                    Layout.fillWidth: true
                    implicitHeight: root.compactControlHeight
                    font.pixelSize: 11
                    model: ["0%", "10%", "20%"]
                    currentIndex: Math.max(0, model.indexOf(String(root.dailyBonusPreset) + "%"))
                    onActivated: root.setDailyBonusPreset(currentText)
                }

                Text { text: "Use Focus (RRR)"; color: theme.tableTextSecondary; font.pixelSize: 11 }
                AppCheckBox {
                    id: focusRrrCheck
                    Layout.fillWidth: true
                    checked: root.focusEnabled
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
                    onToggled: root.setFocusEnabled(checked)
                }
            }

            MarketPresets {
                Layout.fillWidth: true
                theme: root.theme
                textColor: root.textColor
                mutedColor: root.mutedColor
                compactControlHeight: root.compactControlHeight
                presetNames: root.presetNames
                selectedPresetName: root.selectedPresetName
                onSetSelectedPresetName: function(name) { root.setSelectedPresetName(name) }
                onSavePreset: function(name) { root.savePreset(name) }
                onLoadPreset: function(name) { root.loadPreset(name) }
                onDeletePreset: function(name) { root.deletePreset(name) }
            }
        }
    }
}
