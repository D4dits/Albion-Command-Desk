import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme, AppButton, AppTextField, AppComboBox access

/**
 * MarketCraftSearch - Recipe search with suggestions dropdown
 *
 * Provides:
 * - Search input for crafting recipes
 * - Add filtered / Add family buttons
 * - Enchant level filter
 * - Suggestions dropdown with matching recipes
 */
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 6

    // State properties
    property string searchQuery: ""
    property int recipeEnchantFilter: -1
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
    signal setRecipeEnchantFilter(int filter)
    signal addRecipeAtIndex(int index)

    // Access to theme
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    // Search input row
    RowLayout {
        Layout.fillWidth: true
        spacing: 6

        AppTextField {
            id: recipeSearchInput
            Layout.fillWidth: true
            implicitHeight: root.compactControlHeight
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
            font.pixelSize: 10
            enabled: root.suggestionsCount > 0
            onClicked: root.addFilteredRecipeOptions()
        }
        AppButton {
            text: "Add family"
            variant: "secondary"
            compact: true
            Layout.fillWidth: true
            implicitHeight: 22
            font.pixelSize: 10
            enabled: root.suggestionsCount > 0 || root.searchQuery.trim().length === 0
            onClicked: root.addRecipeFamily()
        }
    }

    // Filter row
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
                var filterValue = root.recipeEnchantFilter
                if (filterValue < 0) return 0
                return Math.min(5, filterValue + 1)
            }
            onActivated: {
                if (currentIndex <= 0) {
                    root.setRecipeEnchantFilter(-1)
                } else {
                    root.setRecipeEnchantFilter(parseInt(currentText))
                }
            }
        }
        Text {
            text: root.suggestionsCount + " matches"
            color: mutedColor
            font.pixelSize: 10
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignRight
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
