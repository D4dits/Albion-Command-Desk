import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, AppButton, AppComboBox, AppCheckBox, AppTextField, TableSurface access

/**
 * MarketCraftsTable - Craft plan table with sorting and editing
 *
 * Provides:
 * - Sort controls (by added/craft/tier/city/p/l)
 * - Crafts list with checkboxes
 * - Per-craft controls (city, bonus, runs)
 * - Delete button per row
 */
TableSurface {
    id: root
    level: 1
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.minimumWidth: 0

    // State properties
    property var craftPlanModel: null
    property int craftPlanCount: 0
    property int craftPlanEnabledCount: 0
    property string craftPlanSortKey: "added"
    property bool craftPlanSortDescending: false
    property string craftPlanSearchQuery: ""
    property string currentRecipeId: ""
    property bool hideRowsWithoutFreshPrices: false
    property bool showEnabledOnly: false

    // Layout flags
    property int compactControlHeight: 24
    readonly property int craftNameColumnWidth: 220
    readonly property int craftTableContentWidth: 8 + craftNameColumnWidth + 24 + 46 + 118 + 70 + 54 + 68 + 54 + 48 + 40 + (9 * 6)

    // Helper functions (injected by parent)
    property var tableRowColor: function(index) {
        return index % 2 === 0 ? root.theme.tableRowEven : root.theme.tableRowOdd
    }
    property var itemLabelWithTierParts: function(label, tier, enchant) { return label }
    property var signedValueColor: function(value) { return root.theme.stateSuccess }
    property var copyCellText: function(text) {}
    property var matchesSearch: function(itemText, queryText) {
        var query = String(queryText || "").trim().toLowerCase()
        if (query.length === 0) {
            return true
        }
        return String(itemText || "").toLowerCase().indexOf(query) >= 0
    }

    // Signals
    signal setCraftPlanSortKey(string key)
    signal toggleCraftPlanSortDescending()
    signal clearCraftPlan()
    signal setPlanRowEnabled(var rowId, bool enabled)
    signal setPlanRowCraftCity(var rowId, string city)
    signal setPlanRowDailyBonus(var rowId, string bonus)
    signal setPlanRowRuns(var rowId, int runs)
    signal removePlanRow(var rowId)
    signal setHideRowsWithoutFreshPrices(bool enabled)

    // For scroll position restoration
    property real craftPlanPendingContentY: -1
    onCraftPlanSearchQueryChanged: craftPlanList.forceLayout()
    onShowEnabledOnlyChanged: craftPlanList.forceLayout()
    onHideRowsWithoutFreshPricesChanged: craftPlanList.forceLayout()

    // Access to theme
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary
    property color crystallizedBadgeFill: "#173247"
    property color crystallizedBadgeBorder: "#4fa7d9"
    property color crystallizedBadgeText: "#a9dcff"

    function craftLabelBase(displayName, variantLabel) {
        var label = String(displayName || "")
        var variant = String(variantLabel || "").trim()
        if (variant.length === 0) {
            return label
        }
        var suffix = " [" + variant + "]"
        if (label.slice(-suffix.length) === suffix) {
            return label.slice(0, label.length - suffix.length)
        }
        return label
    }

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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        // Header with sort controls
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "Crafts Table"
                    color: textColor
                    font.pixelSize: 12
                    font.bold: true
                }
                Text {
                    text: root.craftPlanEnabledCount + "/" + root.craftPlanCount + " active"
                    color: mutedColor
                    font.pixelSize: 11
                }
                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Text { text: "Search"; color: mutedColor; font.pixelSize: 10 }
                AppTextField {
                    width: 170
                    implicitHeight: 20
                    font.pixelSize: 10
                    placeholderText: "craft name"
                    text: root.craftPlanSearchQuery
                    onTextChanged: root.craftPlanSearchQuery = text
                }
                Text { text: "Sort"; color: mutedColor; font.pixelSize: 10 }
                AppComboBox {
                    width: 84
                    implicitHeight: 20
                    font.pixelSize: 10
                    model: ["added", "craft", "tier", "city", "p/l"]
                    currentIndex: {
                        if (root.craftPlanSortKey === "craft") return 1
                        if (root.craftPlanSortKey === "tier") return 2
                        if (root.craftPlanSortKey === "city") return 3
                        if (root.craftPlanSortKey === "pl") return 4
                        return 0
                    }
                    onActivated: {
                        if (currentText === "p/l") {
                            root.setCraftPlanSortKey("pl")
                        } else {
                            root.setCraftPlanSortKey(currentText)
                        }
                    }
                }
                AppButton {
                    text: root.craftPlanSortDescending ? "Desc" : "Asc"
                    implicitHeight: 20
                    implicitWidth: 48
                    fontPixelSize: 10
                    onClicked: root.toggleCraftPlanSortDescending()
                }
                AppButton {
                    text: "Clear"
                    implicitHeight: 20
                    implicitWidth: 52
                    fontPixelSize: 10
                    onClicked: root.clearCraftPlan()
                }
                Item { Layout.fillWidth: true }
                AppCheckBox {
                    text: "Show On only"
                    checked: root.showEnabledOnly
                    onToggled: root.showEnabledOnly = checked
                }
                AppCheckBox {
                    text: "Hide missing ADP prices"
                    checked: root.hideRowsWithoutFreshPrices
                    onToggled: root.setHideRowsWithoutFreshPrices(checked)
                }
            }
        }

        Flickable {
            id: craftTableFlick
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: Math.max(190, Math.min(420, 86 + root.craftPlanCount * 24))
            clip: true
            contentWidth: Math.max(width, root.craftTableContentWidth)
            contentHeight: craftTableViewport.height
            flickableDirection: Flickable.HorizontalFlick
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.horizontal: ScrollBar {
                policy: craftTableFlick.contentWidth > craftTableFlick.width ? ScrollBar.AsNeeded : ScrollBar.AlwaysOff
            }

            Item {
                id: craftTableViewport
                width: craftTableFlick.contentWidth
                height: craftTableFlick.height

                // Table header
                Rectangle {
                    id: craftTableHeader
                    width: parent.width
                    height: 22
                    radius: 4
                    color: theme.tableHeaderBackground
                    border.color: theme.borderSubtle
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 4
                        spacing: 6
                        Text { text: "On"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 24 }
                        Text { text: "Craft"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: root.craftNameColumnWidth; elide: Text.ElideRight }
                        Text { text: "Tier"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 46 }
                        Text { text: "City"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 118 }
                        Text { text: "Bonus"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 70 }
                        Text { text: "RRR"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 54 }
                        Text { text: "Runs"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 68 }
                        Text { text: "P/L%"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 54 }
                        Text { text: "AODP"; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 48 }
                        Text { text: ""; color: mutedColor; font.pixelSize: 10; Layout.preferredWidth: 40 }
                    }
                }

                // Craft list
                ListView {
                    id: craftPlanList
                    anchors.top: craftTableHeader.bottom
                    anchors.topMargin: 1
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    clip: true
                    spacing: 0
                    reuseItems: false
                    cacheBuffer: 0
                    model: root.craftPlanModel

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
                        readonly property string rowSearchText: itemLabelWithTierParts(displayName, tier, enchant)
                        readonly property bool searchMatches: root.matchesSearch(rowSearchText, root.craftPlanSearchQuery)
                        readonly property bool rowHasFreshPrices: hasFreshComponentPrices === undefined || hasFreshComponentPrices === null
                            ? true
                            : Boolean(hasFreshComponentPrices)
                        readonly property bool enabledMatches: !root.showEnabledOnly || Boolean(isEnabled)
                        readonly property bool rowVisible: searchMatches && enabledMatches && (!root.hideRowsWithoutFreshPrices || rowHasFreshPrices)
                        visible: rowVisible
                        height: rowVisible ? 32 : 0
                        color: !rowHasFreshPrices
                            ? "#2b1f1f"
                            : (recipeId === root.currentRecipeId ? "#1b2635" : root.tableRowColor(index))

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 4
                            anchors.rightMargin: 4
                            spacing: 6

                            CheckBox {
                                id: enabledCheck
                                Layout.preferredWidth: 24
                                checked: isEnabled
                                hoverEnabled: true
                                padding: 0
                                spacing: 0
                                indicator: Rectangle {
                                    anchors.centerIn: parent
                                    implicitWidth: 14
                                    implicitHeight: 14
                                    radius: 2
                                    border.color: "#5f6b7a"
                                    color: enabledCheck.checked ? accentColor : root.theme.surfaceInteractive
                                }
                                contentItem: Item { implicitWidth: 0; implicitHeight: 0 }
                                onClicked: {
                                    root.craftPlanPendingContentY = craftPlanList.contentY
                                    root.setPlanRowEnabled(rowId, checked)
                                }
                            }

                            Item {
                                Layout.preferredWidth: root.craftNameColumnWidth
                                Layout.fillHeight: true

                                RowLayout {
                                    anchors.fill: parent
                                    spacing: 6

                                    Text {
                                        Layout.fillWidth: true
                                        text: itemLabelWithTierParts(root.craftLabelBase(displayName, variantLabel), tier, enchant)
                                        color: textColor
                                        font.pixelSize: 10
                                        elide: Text.ElideRight
                                        MouseArea {
                                            anchors.fill: parent
                                            acceptedButtons: Qt.LeftButton
                                            onDoubleClicked: root.copyCellText(parent.text)
                                        }
                                    }

                                    Rectangle {
                                        visible: Boolean(usesCrystallized)
                                        radius: 9
                                        color: root.crystallizedBadgeFill
                                        border.color: root.crystallizedBadgeBorder
                                        implicitHeight: 18
                                        implicitWidth: craftBadgeLabel.implicitWidth + 12

                                        Text {
                                            id: craftBadgeLabel
                                            anchors.centerIn: parent
                                            text: String(variantLabel || "Crystal")
                                            color: root.crystallizedBadgeText
                                            font.pixelSize: 9
                                            font.bold: true
                                        }
                                    }
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
                            onDoubleClicked: root.copyCellText(itemLabelWithTierParts(displayName, tier, enchant))
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
                        onActivated: root.setPlanRowCraftCity(rowId, currentText)
                    }

                    AppComboBox {
                        Layout.preferredWidth: 70
                        implicitHeight: 24
                        font.pixelSize: 10
                        model: ["0%", "10%", "20%"]
                        currentIndex: {
                            var bonus = Number(dailyBonusPercent)
                            if (!isFinite(bonus)) return 0
                            if (bonus >= 19.5) return 2
                            if (bonus >= 9.5) return 1
                            return 0
                        }
                        onActivated: root.setPlanRowDailyBonus(rowId, model[currentIndex])
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
                        id: runsField
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
                            color: root.theme.surfaceInset
                            border.color: "#2a3a51"
                        }
                        function commitRunsValue() {
                            var parsed = parseInt(text)
                            if (isNaN(parsed) || parsed < 1) {
                                parsed = 1
                            }
                            root.craftPlanPendingContentY = craftPlanList.contentY
                            root.setPlanRowRuns(rowId, parsed)
                            text = String(parsed)
                        }
                        onEditingFinished: {
                            commitRunsValue()
                        }
                        onActiveFocusChanged: {
                            if (!activeFocus) {
                                commitRunsValue()
                            }
                        }
                    }

                    Text {
                        Layout.preferredWidth: 54
                        text: profitPercent === undefined || profitPercent === null
                            ? "-"
                            : Number(profitPercent).toFixed(1) + "%"
                        color: profitPercent === undefined || profitPercent === null
                            ? mutedColor
                            : root.signedValueColor(Number(profitPercent))
                        font.pixelSize: 10
                        horizontalAlignment: Text.AlignLeft
                    }

                    Text {
                        Layout.preferredWidth: 48
                        text: rowHasFreshPrices ? "OK" : "MISS"
                        color: rowHasFreshPrices ? root.theme.stateSuccess : root.theme.stateWarning
                        font.pixelSize: 10
                        horizontalAlignment: Text.AlignLeft
                    }

                            AppButton {
                                Layout.preferredWidth: 40
                                implicitHeight: 22
                                fontPixelSize: 10
                                text: "Del"
                                onClicked: {
                                    root.craftPlanPendingContentY = craftPlanList.contentY
                                    root.removePlanRow(rowId)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
