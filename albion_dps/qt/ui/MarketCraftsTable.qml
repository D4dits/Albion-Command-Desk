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
    property string currentRecipeId: ""

    // Layout flags
    property int compactControlHeight: 24

    // Helper functions (injected by parent)
    property var tableRowColor: function(index) {
        return index % 2 === 0 ? root.theme.tableRowEven : root.theme.tableRowOdd
    }
    property var itemLabelWithTierParts: function(label, tier, enchant) { return label }
    property var signedValueColor: function(value) { return root.theme.stateSuccess }
    property var copyCellText: function(text) {}

    // Signals
    signal setCraftPlanSortKey(string key)
    signal toggleCraftPlanSortDescending()
    signal clearCraftPlan()
    signal setPlanRowEnabled(var rowId, bool enabled)
    signal setPlanRowCraftCity(var rowId, string city)
    signal setPlanRowDailyBonus(var rowId, string bonus)
    signal setPlanRowRuns(var rowId, int runs)
    signal removePlanRow(var rowId)

    // For scroll position restoration
    property real craftPlanPendingContentY: -1

    // Access to theme
    property var theme: Theme {}
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted
    property color accentColor: theme.brandPrimary

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
                text: root.craftPlanEnabledCount + "/" + root.craftPlanCount + " active"
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
                font.pixelSize: 10
                onClicked: root.toggleCraftPlanSortDescending()
            }
            AppButton {
                text: "Clear"
                implicitHeight: 20
                implicitWidth: 52
                font.pixelSize: 10
                onClicked: root.clearCraftPlan()
            }
        }

        // Table header
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

        // Craft list
        ListView {
            id: craftPlanList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.preferredHeight: Math.max(190, Math.min(420, 86 + root.craftPlanCount * 24))
            clip: true
            spacing: 1
            reuseItems: true
            cacheBuffer: 600
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
                height: 32
                color: recipeId === root.currentRecipeId
                    ? "#1b2635"
                    : root.tableRowColor(index)

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
                        onToggled: root.setPlanRowEnabled(rowId, checked)
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
                            onDoubleClicked: root.copyCellText(parent.text)
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
                        currentIndex: Math.max(0, model.indexOf(String(Math.round(Number(dailyBonusPercent))) + "%"))
                        onActivated: root.setPlanRowDailyBonus(rowId, currentText)
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
                            color: root.theme.surfaceInset
                            border.color: "#2a3a51"
                        }
                        onEditingFinished: {
                            var parsed = parseInt(text)
                            if (isNaN(parsed) || parsed < 1) {
                                parsed = 1
                            }
                            root.setPlanRowRuns(rowId, parsed)
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
                            : root.signedValueColor(Number(profitPercent))
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
                            root.removePlanRow(rowId)
                        }
                    }
                }
            }
        }
    }
}
