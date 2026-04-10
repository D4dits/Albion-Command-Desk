import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Item {
    id: root

    property var theme
    property bool compactLayout: false
    property int eventCount: 0
    property int totalQuantity: 0
    property int itemEventCount: 0
    property int itemTotalQuantity: 0
    property int silverEventCount: 0
    property int silverTotalQuantity: 0
    property int uniqueLooters: 0
    property int uniqueItems: 0
    property string latestLootSummary: ""
    property string logPath: ""
    property string logDirectoryUrl: ""
    property string searchQuery: ""
    property string sourceFilter: "all"
    property string kindFilter: "all"
    property var sourceFilterOptions: ["all", "player", "mob", "silver", "system"]
    property var kindFilterOptions: ["all", "items", "silver"]
    property var eventsModel: null
    property var topLootersModel: null
    property var topItemsModel: null
    property var topSilverLootersModel: null

    signal setSearchQuery(string value)
    signal setSourceFilter(string value)
    signal setKindFilter(string value)
    signal copyLatestSummary()
    signal copyCurrentView()
    signal exportCurrentView()
    signal openLogFolder()

    function cardValue(value) {
        return String(value === undefined || value === null ? 0 : value)
    }

    function kindLabel(value) {
        if (value === "items") {
            return "Items"
        }
        if (value === "silver") {
            return "Silver"
        }
        return "All"
    }

    function lootKindBadgeBg(isSilverValue) {
        return isSilverValue ? theme.stateWarningBg : theme.stateSuccessBg
    }

    function lootKindBadgeBorder(isSilverValue) {
        return isSilverValue ? theme.stateWarning : theme.stateSuccess
    }

    function lootKindBadgeText(isSilverValue) {
        return isSilverValue ? theme.stateWarning : theme.stateSuccess
    }

    function sourceBadgeBg(kind) {
        if (kind === "mob") {
            return theme.stateWarningBg
        }
        if (kind === "player") {
            return theme.stateInfoBg
        }
        if (kind === "silver") {
            return "#33280d"
        }
        return theme.surfaceRaised
    }

    function sourceBadgeBorder(kind) {
        if (kind === "mob") {
            return theme.stateWarning
        }
        if (kind === "player") {
            return theme.stateInfo
        }
        if (kind === "silver") {
            return theme.brandWarmAccent
        }
        return theme.borderSubtle
    }

    function sourceBadgeText(kind) {
        if (kind === "mob") {
            return theme.stateWarning
        }
        if (kind === "player") {
            return theme.stateInfo
        }
        if (kind === "silver") {
            return theme.brandWarmAccent
        }
        return theme.textPrimary
    }

    function statCardBg(title) {
        if (title === "Item Ev" || title === "Items") {
            return theme.stateSuccessBg
        }
        if (title === "Silver Ev") {
            return theme.stateWarningBg
        }
        return theme.surfaceRaised
    }

    function statCardBorder(title) {
        if (title === "Item Ev" || title === "Items") {
            return theme.stateSuccess
        }
        if (title === "Silver Ev") {
            return theme.stateWarning
        }
        return theme.borderSubtle
    }

    function statCardValueColor(title) {
        if (title === "Item Ev" || title === "Items") {
            return theme.stateSuccess
        }
        if (title === "Silver Ev") {
            return theme.stateWarning
        }
        return theme.textPrimary
    }

    Rectangle {
        anchors.fill: parent
        radius: theme.cornerRadiusPanel
        color: theme.surfacePanel
        border.color: theme.borderSubtle

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: theme.spacingSection
            spacing: theme.spacingSection

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10

                Text {
                    text: "Loot"
                    color: theme.textPrimary
                    font.pixelSize: 24
                    font.bold: true
                }

                Text {
                    Layout.fillWidth: true
                    text: latestLootSummary.length > 0
                        ? latestLootSummary
                        : "Party-only loot log. Use search and source filter to inspect recent pickups."
                    color: latestLootSummary.length > 0 ? theme.textMuted : theme.textFaint
                    wrapMode: Text.Wrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Rectangle {
                        radius: 10
                        color: theme.stateInfoBg
                        border.color: theme.stateInfo
                        implicitHeight: 22
                        implicitWidth: partyOnlyBadge.implicitWidth + 16

                        Text {
                            id: partyOnlyBadge
                            anchors.centerIn: parent
                            text: "Party Only"
                            color: theme.stateInfo
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }

                    Rectangle {
                        radius: 10
                        color: root.kindFilter === "silver" ? theme.stateWarningBg : (root.kindFilter === "items" ? theme.stateSuccessBg : theme.surfaceRaised)
                        border.color: root.kindFilter === "silver" ? theme.stateWarning : (root.kindFilter === "items" ? theme.stateSuccess : theme.borderSubtle)
                        implicitHeight: 22
                        implicitWidth: viewBadgeText.implicitWidth + 16

                        Text {
                            id: viewBadgeText
                            anchors.centerIn: parent
                            text: "View: " + root.kindLabel(root.kindFilter)
                            color: root.kindFilter === "silver" ? theme.stateWarning : (root.kindFilter === "items" ? theme.stateSuccess : theme.textPrimary)
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 8

                    Repeater {
                        model: [
                            { title: "Events", value: root.eventCount },
                            { title: "Qty", value: root.totalQuantity },
                            { title: "Looters", value: root.uniqueLooters },
                            { title: "Items", value: root.uniqueItems },
                            { title: "Item Ev", value: root.itemEventCount },
                            { title: "Silver Ev", value: root.silverEventCount }
                        ]

                        delegate: Rectangle {
                            width: compactLayout ? 92 : 116
                            height: 56
                            radius: theme.cornerRadiusCard
                            color: root.statCardBg(modelData.title)
                            border.color: root.statCardBorder(modelData.title)

                            Column {
                                anchors.centerIn: parent
                                spacing: 2

                                Text {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: root.cardValue(modelData.value)
                                    color: root.statCardValueColor(modelData.title)
                                    font.pixelSize: 18
                                    font.bold: true
                                }
                                Text {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: modelData.title
                                    color: theme.textMuted
                                    font.pixelSize: 10
                                    font.letterSpacing: 0.4
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: theme.cornerRadiusCard
                color: theme.cardLevel1
                border.color: theme.borderSubtle
                implicitHeight: compactLayout ? 128 : 84

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Flow {
                            Layout.fillWidth: true
                            spacing: 8

                            Repeater {
                                model: root.kindFilterOptions

                                delegate: AppButton {
                                    text: root.kindLabel(modelData)
                                    compact: true
                                    checkable: true
                                    checked: root.kindFilter === String(modelData)
                                    variant: checked ? "primary" : "secondary"
                                    onClicked: root.setKindFilter(String(modelData))
                                }
                            }
                        }

                        Text {
                            text: "Item qty: " + root.cardValue(root.itemTotalQuantity)
                            color: theme.textMuted
                            font.pixelSize: 11
                        }

                        Text {
                            text: "Silver qty: " + root.cardValue(root.silverTotalQuantity)
                            color: theme.textMuted
                            font.pixelSize: 11
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        AppTextField {
                            id: searchField
                            Layout.fillWidth: true
                            placeholderText: "Search looter, item, source..."
                            text: root.searchQuery
                            onTextEdited: root.setSearchQuery(text)
                        }

                        AppComboBox {
                            id: sourceFilterCombo
                            Layout.preferredWidth: compactLayout ? 110 : 128
                            model: root.sourceFilterOptions
                            currentIndex: Math.max(0, model.indexOf(root.sourceFilter))
                            onActivated: function(index) {
                                root.setSourceFilter(String(model[index]))
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Text {
                            Layout.fillWidth: true
                            text: logPath.length > 0 ? logPath : "Writer not initialized"
                            color: theme.textMuted
                            font.pixelSize: 11
                            elide: Text.ElideMiddle
                        }

                        AppButton {
                            text: "Copy Summary"
                            compact: true
                            onClicked: root.copyLatestSummary()
                        }
                        AppButton {
                            text: "Copy View"
                            compact: true
                            onClicked: root.copyCurrentView()
                        }
                        AppButton {
                            text: "Export View"
                            compact: true
                            onClicked: root.exportCurrentView()
                        }
                        AppButton {
                            text: "Open Folder"
                            compact: true
                            onClicked: root.openLogFolder()
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: theme.spacingSection

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: theme.cornerRadiusCard
                    color: theme.cardLevel1
                    border.color: theme.borderSubtle

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                text: "Recent Loot"
                                color: theme.textPrimary
                                font.pixelSize: 14
                                font.bold: true
                            }

                            Rectangle {
                                radius: 9
                                color: theme.surfaceRaised
                                border.color: theme.borderSubtle
                                implicitHeight: 20
                                implicitWidth: recentLootCount.implicitWidth + 14

                                Text {
                                    id: recentLootCount
                                    anchors.centerIn: parent
                                    text: root.eventCount + " rows"
                                    color: theme.textMuted
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            Text { text: "Time"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 68 }
                            Text { text: "Looter"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 150 }
                            Text { text: "Item"; color: theme.textMuted; font.pixelSize: 11; Layout.fillWidth: true }
                            Text { text: "Qty"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 42 }
                            Text { text: "Source"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 156 }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: theme.borderSubtle
                        }

                        ListView {
                            id: lootList
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            spacing: 6
                            model: root.eventsModel

                            delegate: Rectangle {
                                required property string timestampText
                                required property string lootedByName
                                required property string lootedByGuild
                                required property string itemName
                                required property string itemId
                                required property int quantity
                                required property string sourceName
                                required property string sourceKind
                                required property bool isSilver
                                required property string summary

                                width: lootList.width
                                radius: theme.cornerRadiusCard
                                color: index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
                                border.color: theme.borderSubtle
                                implicitHeight: detailText.implicitHeight + 32

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 6

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 12

                                        Text {
                                            text: timestampText
                                            color: theme.textPrimary
                                            font.pixelSize: 12
                                            Layout.preferredWidth: 68
                                        }
                                        Text {
                                            text: lootedByGuild.length > 0 ? (lootedByName + " [" + lootedByGuild + "]") : lootedByName
                                            color: theme.textPrimary
                                            font.pixelSize: 12
                                            Layout.preferredWidth: 150
                                            elide: Text.ElideRight
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            spacing: 1
                                            RowLayout {
                                                Layout.fillWidth: true
                                                spacing: 6

                                                Text {
                                                    Layout.fillWidth: true
                                                    text: itemName
                                                    color: isSilver ? theme.brandWarmAccent : theme.textPrimary
                                                    font.pixelSize: 12
                                                    font.bold: isSilver
                                                    elide: Text.ElideRight
                                                }

                                                Rectangle {
                                                    radius: 9
                                                    color: root.lootKindBadgeBg(isSilver)
                                                    border.color: root.lootKindBadgeBorder(isSilver)
                                                    implicitHeight: 20
                                                    implicitWidth: kindBadgeText.implicitWidth + 14

                                                    Text {
                                                        id: kindBadgeText
                                                        anchors.centerIn: parent
                                                        text: isSilver ? "SILVER" : "ITEM"
                                                        color: root.lootKindBadgeText(isSilver)
                                                        font.pixelSize: 10
                                                        font.bold: true
                                                    }
                                                }
                                            }
                                            Text {
                                                Layout.fillWidth: true
                                                text: itemId
                                                color: theme.textFaint
                                                font.pixelSize: 10
                                                elide: Text.ElideRight
                                                visible: itemId.length > 0
                                            }
                                        }
                                        Text {
                                            text: String(quantity)
                                            color: theme.textPrimary
                                            font.pixelSize: 12
                                            horizontalAlignment: Text.AlignRight
                                            Layout.preferredWidth: 42
                                        }
                                        Rectangle {
                                            Layout.preferredWidth: 156
                                            radius: 10
                                            color: root.sourceBadgeBg(sourceKind)
                                            border.color: root.sourceBadgeBorder(sourceKind)
                                            border.width: 1
                                            implicitHeight: 22

                                            Text {
                                                anchors.centerIn: parent
                                                text: sourceKind === "silver" ? "Silver" : sourceName
                                                color: root.sourceBadgeText(sourceKind)
                                                font.pixelSize: 11
                                                elide: Text.ElideRight
                                                width: parent.width - 12
                                                horizontalAlignment: Text.AlignHCenter
                                            }
                                        }
                                    }

                                    Text {
                                        id: detailText
                                        Layout.fillWidth: true
                                        text: summary
                                        color: theme.textMuted
                                        font.pixelSize: 11
                                        wrapMode: Text.Wrap
                                    }
                                }
                            }

                            ScrollBar.vertical: ScrollBar {}
                        }

                        Item {
                            anchors.fill: lootList
                            visible: lootList.count === 0

                            Column {
                                anchors.centerIn: parent
                                spacing: 8

                                Text {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: root.kindFilter === "silver"
                                        ? "No silver events yet"
                                        : (root.kindFilter === "items" ? "No item drops yet" : "No loot yet")
                                    color: theme.textPrimary
                                    font.pixelSize: 18
                                    font.bold: true
                                }

                                Text {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: "Party-only data will appear here after loot events are detected."
                                    color: theme.textMuted
                                    font.pixelSize: 12
                                }
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.preferredWidth: compactLayout ? 240 : 300
                    Layout.fillHeight: true
                    spacing: theme.spacingSection

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 188
                        Layout.fillHeight: false
                        radius: theme.cornerRadiusCard
                        color: theme.cardLevel1
                        border.color: theme.borderSubtle

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            Text {
                                text: "Top View Looters"
                                color: theme.textPrimary
                                font.pixelSize: 14
                                font.bold: true
                            }

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                ListView {
                                    id: topLootersList
                                    anchors.fill: parent
                                    clip: true
                                    spacing: 6
                                    model: root.topLootersModel

                                    delegate: Rectangle {
                                        required property string label
                                        required property string sublabel
                                        required property int quantity
                                        required property int eventCount

                                        width: ListView.view.width
                                        radius: theme.cornerRadiusCard
                                        color: index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
                                        border.color: theme.borderSubtle
                                        implicitHeight: 52

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 8

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 2
                                                Text { text: label; color: theme.textPrimary; font.pixelSize: 12; elide: Text.ElideRight }
                                                Text { text: sublabel; color: theme.textFaint; font.pixelSize: 10; elide: Text.ElideRight; visible: sublabel.length > 0 }
                                            }
                                            ColumnLayout {
                                                spacing: 1
                                                Text { text: quantity + "x"; color: theme.textPrimary; font.pixelSize: 12; font.bold: true; horizontalAlignment: Text.AlignRight }
                                                Text { text: eventCount + " ev"; color: theme.textMuted; font.pixelSize: 10; horizontalAlignment: Text.AlignRight }
                                            }
                                        }
                                    }

                                    ScrollBar.vertical: ScrollBar {}
                                }

                                Item {
                                    anchors.fill: parent
                                    visible: topLootersList.count === 0

                                    Text {
                                        anchors.centerIn: parent
                                        text: "No looters in current view"
                                        color: theme.textMuted
                                        font.pixelSize: 12
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: theme.cornerRadiusCard
                        color: theme.cardLevel1
                        border.color: theme.borderSubtle

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            Text {
                                text: "Top Items"
                                color: theme.textPrimary
                                font.pixelSize: 14
                                font.bold: true
                            }

                            Rectangle {
                                radius: 10
                                color: theme.stateSuccessBg
                                border.color: theme.stateSuccess
                                implicitHeight: 22
                                implicitWidth: itemsBadgeText.implicitWidth + 16

                                Text {
                                    id: itemsBadgeText
                                    anchors.centerIn: parent
                                    text: "ITEMS"
                                    color: theme.stateSuccess
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                ListView {
                                    id: topItemsList
                                    anchors.fill: parent
                                    clip: true
                                    spacing: 6
                                    model: root.topItemsModel

                                    delegate: Rectangle {
                                        required property string label
                                        required property string sublabel
                                        required property int quantity
                                        required property int eventCount

                                        width: ListView.view.width
                                        radius: theme.cornerRadiusCard
                                        color: index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
                                        border.color: theme.borderSubtle
                                        implicitHeight: 52

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 8

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 2
                                                Text { text: label; color: theme.textPrimary; font.pixelSize: 12; elide: Text.ElideRight }
                                                Text { text: sublabel; color: theme.textFaint; font.pixelSize: 10; elide: Text.ElideRight; visible: sublabel.length > 0 }
                                            }
                                            ColumnLayout {
                                                spacing: 1
                                                Text { text: quantity + "x"; color: theme.textPrimary; font.pixelSize: 12; font.bold: true; horizontalAlignment: Text.AlignRight }
                                                Text { text: eventCount + " ev"; color: theme.textMuted; font.pixelSize: 10; horizontalAlignment: Text.AlignRight }
                                            }
                                        }
                                    }

                                    ScrollBar.vertical: ScrollBar {}
                                }

                                Item {
                                    anchors.fill: parent
                                    visible: topItemsList.count === 0

                                    Text {
                                        anchors.centerIn: parent
                                        text: "No item drops in current view"
                                        color: theme.textMuted
                                        font.pixelSize: 12
                                    }
                                }
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: theme.cornerRadiusCard
                        color: theme.cardLevel1
                        border.color: theme.borderSubtle

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            Text {
                                text: "Top Silver Looters"
                                color: theme.textPrimary
                                font.pixelSize: 14
                                font.bold: true
                            }

                            Rectangle {
                                radius: 10
                                color: theme.stateWarningBg
                                border.color: theme.stateWarning
                                implicitHeight: 22
                                implicitWidth: silverBadgeText.implicitWidth + 16

                                Text {
                                    id: silverBadgeText
                                    anchors.centerIn: parent
                                    text: "SILVER"
                                    color: theme.stateWarning
                                    font.pixelSize: 11
                                    font.bold: true
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                ListView {
                                    id: topSilverList
                                    anchors.fill: parent
                                    clip: true
                                    spacing: 6
                                    model: root.topSilverLootersModel

                                    delegate: Rectangle {
                                        required property string label
                                        required property string sublabel
                                        required property int quantity
                                        required property int eventCount

                                        width: ListView.view.width
                                        radius: theme.cornerRadiusCard
                                        color: index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
                                        border.color: theme.borderSubtle
                                        implicitHeight: 52

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 8

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 2
                                                Text { text: label; color: theme.textPrimary; font.pixelSize: 12; elide: Text.ElideRight }
                                                Text { text: sublabel; color: theme.textFaint; font.pixelSize: 10; elide: Text.ElideRight; visible: sublabel.length > 0 }
                                            }
                                            ColumnLayout {
                                                spacing: 1
                                                Text { text: quantity + ""; color: theme.textPrimary; font.pixelSize: 12; font.bold: true; horizontalAlignment: Text.AlignRight }
                                                Text { text: eventCount + " ev"; color: theme.textMuted; font.pixelSize: 10; horizontalAlignment: Text.AlignRight }
                                            }
                                        }
                                    }

                                    ScrollBar.vertical: ScrollBar {}
                                }

                                Item {
                                    anchors.fill: parent
                                    visible: topSilverList.count === 0

                                    Text {
                                        anchors.centerIn: parent
                                        text: "No silver events in current view"
                                        color: theme.textMuted
                                        font.pixelSize: 12
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
