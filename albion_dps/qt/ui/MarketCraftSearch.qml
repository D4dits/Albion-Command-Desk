import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, AppButton, AppTextField, AppComboBox access

/**
 * MarketCraftSearch - Recipe search with suggestions dropdown
 *
 * Provides:
 * - Search input for crafting recipes
 * - Add filtered / Add family buttons
 * - Tier + enchant multiselect filters
 * - Suggestions dropdown with matching recipes
 */
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 6

    // State properties
    property string searchQuery: ""
    property var recipeTierFilters: []
    property var recipeEnchantFilters: []
    property int suggestionsCount: 0
    property var recipeOptionsModel: null
    property string currentRecipeId: ""

    // Layout flags
    property int compactControlHeight: 24

    // Helper functions (injected by parent)
    property var tableRowStrongColor: function(index) {
        return index % 2 === 0 ? root.theme.surfaceInteractive : root.theme.tableRowEven
    }

    // Signals
    signal setRecipeSearchQuery(string query)
    signal addFirstRecipeOption()
    signal addFilteredRecipeOptions()
    signal addRecipeFamily()
    signal setRecipeTierFilters(var filters)
    signal setRecipeEnchantFilters(var filters)
    signal addRecipeAtIndex(int index)

    // Access to theme
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    function _asArray(items) {
        if (!items) {
            return []
        }
        if (Array.isArray(items)) {
            return items.slice()
        }
        var out = []
        var len = Number(items.length)
        if (!isNaN(len) && len > 0) {
            for (var i = 0; i < len; i += 1) {
                out.push(items[i])
            }
            return out
        }
        return out
    }

    function _containsFilter(items, value) {
        var list = _asArray(items)
        for (var i = 0; i < list.length; i += 1) {
            if (Number(list[i]) === Number(value)) {
                return true
            }
        }
        return false
    }

    function _toggleFilter(items, value) {
        var list = _asArray(items)
        var out = []
        var found = false
        for (var i = 0; i < list.length; i += 1) {
            var candidate = Number(list[i])
            if (candidate === Number(value)) {
                found = true
                continue
            }
            out.push(candidate)
        }
        if (!found) {
            out.push(Number(value))
        }
        out.sort(function(a, b) { return a - b })
        return out
    }

    function _formatTierSelection() {
        if (!root.recipeTierFilters || root.recipeTierFilters.length === 0) {
            return "all"
        }
        var values = _asArray(root.recipeTierFilters).sort(function(a, b) { return Number(a) - Number(b) })
        var labels = []
        for (var i = 0; i < values.length; i += 1) {
            labels.push("T" + Number(values[i]))
        }
        return labels.join(", ")
    }

    function _formatEnchantSelection() {
        if (!root.recipeEnchantFilters || root.recipeEnchantFilters.length === 0) {
            return "all"
        }
        var values = _asArray(root.recipeEnchantFilters).sort(function(a, b) { return Number(a) - Number(b) })
        var labels = []
        for (var i = 0; i < values.length; i += 1) {
            labels.push(String(Number(values[i])))
        }
        return labels.join(", ")
    }

    // Search input row
    RowLayout {
        Layout.fillWidth: true
        spacing: 6

        AppTextField {
            id: recipeSearchInput
            Layout.fillWidth: true
            implicitHeight: Math.max(root.compactControlHeight, 26)
            font.pixelSize: 11
            placeholderText: "e.g. mistcaller 5.2"
            text: root.searchQuery
            onTextChanged: root.setRecipeSearchQuery(text)
            onAccepted: {
                root.addFirstRecipeOption()
                focus = false
            }
        }
    }

    // Action buttons row
    RowLayout {
        Layout.fillWidth: true
        spacing: 6
        AppButton {
            text: "Add filtered"
            variant: "primary"
            compact: true
            Layout.fillWidth: true
            implicitHeight: 22
            fontPixelSize: 10
            enabled: root.suggestionsCount > 0
            onClicked: root.addFilteredRecipeOptions()
        }
        AppButton {
            text: "Add family"
            variant: "secondary"
            compact: true
            Layout.fillWidth: true
            implicitHeight: 22
            fontPixelSize: 10
            enabled: root.suggestionsCount > 0 || root.searchQuery.trim().length === 0
            onClicked: root.addRecipeFamily()
        }
    }

    // Filter rows
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3

            Text {
                text: "Tier"
                color: mutedColor
                font.pixelSize: 10
            }
            Flow {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: [4, 5, 6, 7, 8]
                    delegate: AppButton {
                        readonly property int filterValue: Number(modelData)
                        readonly property bool selected: root._containsFilter(root.recipeTierFilters, filterValue)
                        text: selected ? ("\u2713 T" + filterValue) : ("T" + filterValue)
                        compact: true
                        implicitHeight: 20
                        implicitWidth: selected ? 52 : 40
                        fontPixelSize: 10
                        variant: selected ? "primary" : "secondary"
                        onClicked: root.setRecipeTierFilters(root._toggleFilter(root.recipeTierFilters, filterValue))
                    }
                }
                AppButton {
                    readonly property bool selected: !root.recipeTierFilters || root.recipeTierFilters.length === 0
                    text: selected ? "\u2713 All" : "All"
                    compact: true
                    implicitHeight: 20
                    implicitWidth: selected ? 58 : 44
                    fontPixelSize: 10
                    variant: selected ? "primary" : "secondary"
                    onClicked: root.setRecipeTierFilters([])
                }
            }
            Text {
                text: "Selected: " + root._formatTierSelection()
                color: mutedColor
                font.pixelSize: 10
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3

            Text {
                text: "Enchant"
                color: mutedColor
                font.pixelSize: 10
            }
            Flow {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: [0, 1, 2, 3, 4]
                    delegate: AppButton {
                        readonly property int filterValue: Number(modelData)
                        readonly property bool selected: root._containsFilter(root.recipeEnchantFilters, filterValue)
                        text: selected ? ("\u2713 " + filterValue) : String(filterValue)
                        compact: true
                        implicitHeight: 20
                        implicitWidth: selected ? 42 : 30
                        fontPixelSize: 10
                        variant: selected ? "primary" : "secondary"
                        onClicked: root.setRecipeEnchantFilters(root._toggleFilter(root.recipeEnchantFilters, filterValue))
                    }
                }
                AppButton {
                    readonly property bool selected: !root.recipeEnchantFilters || root.recipeEnchantFilters.length === 0
                    text: selected ? "\u2713 All" : "All"
                    compact: true
                    implicitHeight: 20
                    implicitWidth: selected ? 58 : 44
                    fontPixelSize: 10
                    variant: selected ? "primary" : "secondary"
                    onClicked: root.setRecipeEnchantFilters([])
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "Selected: " + root._formatEnchantSelection()
                    color: mutedColor
                    font.pixelSize: 10
                    Layout.fillWidth: true
                }
                Text {
                    text: root.suggestionsCount + " matches"
                    color: mutedColor
                    font.pixelSize: 10
                    horizontalAlignment: Text.AlignRight
                }
            }
        }
    }

    // Suggestions dropdown
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: 196
        visible: recipeSearchInput.activeFocus && root.suggestionsCount > 0
        radius: 4
        color: root.theme.tableHeaderBackground
        border.color: root.theme.borderSubtle

        ListView {
            id: recipeSuggestions
            anchors.fill: parent
            anchors.margins: 4
            clip: true
            reuseItems: true
            cacheBuffer: 600
            model: root.recipeOptionsModel

            delegate: Rectangle {
                width: ListView.view.width
                height: 26
                color: recipeId === root.currentRecipeId
                    ? "#1b2635"
                    : root.tableRowStrongColor(index)

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 4
                    spacing: 6
                    Text {
                        text: displayName
                        color: root.textColor
                        font.pixelSize: 11
                        Layout.fillWidth: true
                        elide: Text.ElideNone
                    }
                    Text {
                        text: "T" + tier + "." + enchant
                        color: root.mutedColor
                        font.pixelSize: 11
                        Layout.preferredWidth: 62
                        horizontalAlignment: Text.AlignLeft
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        root.addRecipeAtIndex(index)
                    }
                }
            }
        }

        Text {
            anchors.centerIn: parent
            visible: recipeSuggestions.count === 0
            text: "No matches"
            color: root.mutedColor
            font.pixelSize: 11
        }
    }
}
