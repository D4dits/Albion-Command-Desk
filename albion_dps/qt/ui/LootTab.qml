import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Item {
    id: root

    property var theme
    property bool compactLayout: false
    property bool importedLogActive: false
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
    property string looterFilter: "all"
    property string categoryFilter: "all"
    property string kindFilter: "all"
    property var sourceFilterOptions: ["all", "player", "mob", "system"]
    property var looterFilterOptions: ["all"]
    property var categoryFilterOptions: ["all", "weapon", "armor", "bag", "cape", "mount", "consumable", "resource", "artifact", "other"]
    property var kindFilterOptions: ["items"]
    property var eventsModel: null
    property var topLootersModel: null
    property var topItemsModel: null
    property var topSourcesModel: null
    property var topSilverLootersModel: null
    property bool stackedControls: width < 1140
    property bool stackedSummary: width < 920
    property bool summaryRail: width >= 1040
    property int summaryRailWidth: compactLayout ? 292 : 312
    property int aggregateColumns: width >= 1050 ? 3 : (width >= 720 ? 2 : 1)
    property int timeColumnWidth: compactLayout ? 50 : 58
    property int looterColumnWidth: compactLayout ? 112 : 136
    property int qtyColumnWidth: compactLayout ? 42 : 48
    property int sourceColumnWidth: compactLayout ? 104 : 118

    signal setSearchQuery(string value)
    signal setSourceFilter(string value)
    signal setLooterFilter(string value)
    signal setCategoryFilter(string value)
    signal setKindFilter(string value)
    signal copyLatestSummary()
    signal copyCurrentView()
    signal exportCurrentView()
    signal openLogFolder()
    signal importLog()
    signal useLiveLog()

    function cardValue(value) {
        var number = Number(value)
        if (!isFinite(number)) {
            return "0"
        }
        var absValue = Math.abs(number)
        if (absValue >= 1000000000) {
            return (number / 1000000000).toFixed(1) + "B"
        }
        if (absValue >= 1000000) {
            return (number / 1000000).toFixed(1) + "M"
        }
        if (absValue >= 1000) {
            return (number / 1000).toFixed(1) + "k"
        }
        return String(Math.round(number))
    }

    function kindLabel(value) {
        return categoryLabel(value)
    }

    function categoryLabel(value) {
        if (value === "all") return "All items"
        if (value === "weapon") return "Weapons"
        if (value === "armor") return "Armor"
        if (value === "bag") return "Bags"
        if (value === "cape") return "Capes"
        if (value === "mount") return "Mounts"
        if (value === "consumable") return "Consumables"
        if (value === "resource") return "Resources"
        if (value === "artifact") return "Artifacts"
        return "Other"
    }

    function sourceLabel(value) {
        var text = String(value || "all")
        if (text.length === 0) {
            return "All"
        }
        return text.charAt(0).toUpperCase() + text.slice(1)
    }

    function categoryBadgeBg(category, sourceKindValue) {
        if (sourceKindValue === "player") {
            return theme.stateDangerBg
        }
        if (category === "resource" || category === "consumable") {
            return theme.stateWarningBg
        }
        return theme.stateSuccessBg
    }

    function categoryBadgeBorder(category, sourceKindValue) {
        if (sourceKindValue === "player") {
            return theme.stateDanger
        }
        if (category === "resource" || category === "consumable") {
            return theme.stateWarning
        }
        return theme.stateSuccess
    }

    function categoryBadgeText(category, sourceKindValue) {
        if (sourceKindValue === "player") {
            return theme.stateDanger
        }
        if (category === "resource" || category === "consumable") {
            return theme.stateWarning
        }
        return theme.stateSuccess
    }

    function categoryBadgeLabel(category) {
        if (category === "all") return "ITEM"
        return root.categoryLabel(category).toUpperCase()
    }

    function rowBackground(sourceKindValue) {
        if (sourceKindValue === "player") {
            return theme.stateDangerBg
        }
        if (sourceKindValue === "mob") {
            return "#171a13"
        }
        return theme.surfaceInteractive
    }

    function rowBorder(sourceKindValue) {
        if (sourceKindValue === "player") {
            return theme.stateDanger
        }
        if (sourceKindValue === "mob") {
            return "#54451d"
        }
        return theme.borderSubtle
    }

    function sourceBadgeBg(kind) {
        if (kind === "mob") {
            return theme.stateWarningBg
        }
        if (kind === "player") {
            return theme.stateDangerBg
        }
        return theme.surfaceRaised
    }

    function sourceBadgeBorder(kind) {
        if (kind === "mob") {
            return theme.stateWarning
        }
        if (kind === "player") {
            return theme.stateDanger
        }
        return theme.borderSubtle
    }

    function sourceBadgeText(kind) {
        if (kind === "mob") {
            return theme.stateWarning
        }
        if (kind === "player") {
            return theme.stateDanger
        }
        return theme.textPrimary
    }

    function statCardBg(title) {
        if (title === "Items" || title === "Unique") {
            return theme.stateSuccessBg
        }
        return theme.surfaceRaised
    }

    function statCardBorder(title) {
        if (title === "Items" || title === "Unique") {
            return theme.stateSuccess
        }
        return theme.borderSubtle
    }

    function statCardValueColor(title) {
        if (title === "Items" || title === "Unique") {
            return theme.stateSuccess
        }
        return theme.textPrimary
    }

    Rectangle {
        anchors.fill: parent
        radius: theme.cornerRadiusPanel
        color: theme.cardLevel0
        border.color: theme.borderStrong
        clip: true

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: theme.spacingSection
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Text {
                        text: "Loot"
                        color: theme.textPrimary
                        font.pixelSize: 20
                        font.bold: true
                    }

                    Text {
                        Layout.fillWidth: true
                        text: latestLootSummary.length > 0
                            ? latestLootSummary
                            : "Party loot log. Import previous logs or inspect the current session feed."
                        color: latestLootSummary.length > 0 ? theme.textSecondary : theme.textMuted
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        maximumLineCount: 2
                    }
                }

                Flow {
                    Layout.preferredWidth: compactLayout ? 330 : 382
                    Layout.maximumWidth: 382
                    spacing: 6

                    Repeater {
                        model: [
                            { title: "Events", value: root.eventCount },
                            { title: "Items", value: root.totalQuantity },
                            { title: "Looters", value: root.uniqueLooters },
                            { title: "Unique", value: root.uniqueItems }
                        ]

                        delegate: Rectangle {
                            width: compactLayout ? 76 : 88
                            height: 26
                            radius: 8
                            color: root.statCardBg(modelData.title)
                            border.color: root.statCardBorder(modelData.title)

                            Row {
                                anchors.centerIn: parent
                                spacing: 5

                                Text {
                                    text: root.cardValue(modelData.value)
                                    color: root.statCardValueColor(modelData.title)
                                    font.pixelSize: 12
                                    font.bold: true
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                                Text {
                                    text: modelData.title
                                    color: theme.textMuted
                                    font.pixelSize: 9
                                    font.letterSpacing: 0.4
                                    anchors.verticalCenter: parent.verticalCenter
                                }
                            }
                        }
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: root.summaryRail ? 2 : 1
                columnSpacing: 8
                rowSpacing: 8

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumWidth: root.summaryRail ? 560 : 0
                    spacing: 8

                    Rectangle {
                        Layout.fillWidth: true
                        radius: theme.radiusLg
                        color: theme.cardLevel2
                        border.color: theme.borderStrong
                        implicitHeight: filterContent.implicitHeight + 16

                        ColumnLayout {
                            id: filterContent
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 6

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                Flow {
                                    Layout.fillWidth: true
                                    spacing: 7

                                    Repeater {
                                        model: root.categoryFilterOptions

                                        delegate: AppButton {
                                            text: root.categoryLabel(modelData)
                                            compact: true
                                            checkable: true
                                            checked: root.categoryFilter === String(modelData)
                                            variant: checked ? "primary" : "secondary"
                                            onClicked: root.setCategoryFilter(String(modelData))
                                        }
                                    }
                                }
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: root.stackedControls ? 1 : 4
                                columnSpacing: 8
                                rowSpacing: 8

                                AppTextField {
                                    Layout.fillWidth: true
                                    Layout.columnSpan: root.stackedControls ? 1 : 2
                                    placeholderText: "Search item, looter, victim, guild..."
                                    text: root.searchQuery
                                    onTextEdited: root.setSearchQuery(text)
                                }

                                AppComboBox {
                                    Layout.fillWidth: true
                                    model: root.looterFilterOptions
                                    currentIndex: Math.max(0, model.indexOf(root.looterFilter))
                                    onActivated: function(index) {
                                        root.setLooterFilter(String(model[index]))
                                    }
                                }

                                AppComboBox {
                                    Layout.fillWidth: true
                                    model: root.sourceFilterOptions
                                    currentIndex: Math.max(0, model.indexOf(root.sourceFilter))
                                    onActivated: function(index) {
                                        root.setSourceFilter(String(model[index]))
                                    }
                                }
                            }

                            Flow {
                                Layout.fillWidth: true
                                spacing: 7

                                Rectangle {
                                    radius: 9
                                    color: theme.stateDangerBg
                                    border.color: theme.stateDanger
                                    implicitHeight: 18
                                    implicitWidth: corpseLegend.implicitWidth + 12

                                    Text {
                                        id: corpseLegend
                                        anchors.centerIn: parent
                                        text: "red = player corpse"
                                        color: theme.stateDanger
                                        font.pixelSize: 9
                                        font.bold: true
                                    }
                                }

                                Rectangle {
                                    radius: 9
                                    color: theme.stateWarningBg
                                    border.color: theme.stateWarning
                                    implicitHeight: 18
                                    implicitWidth: mobLegend.implicitWidth + 12

                                    Text {
                                        id: mobLegend
                                        anchors.centerIn: parent
                                        text: "yellow = mob/container"
                                        color: theme.stateWarning
                                        font.pixelSize: 9
                                        font.bold: true
                                    }
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 5

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    Text {
                                        text: root.importedLogActive ? "Imported log" : "Live session log"
                                        color: root.importedLogActive ? theme.stateInfo : theme.textSecondary
                                        font.pixelSize: 10
                                        font.bold: true
                                    }

                                    Text {
                                        Layout.fillWidth: true
                                        text: logPath.length > 0 ? logPath : "No loot log available yet"
                                        color: theme.textMuted
                                        font.pixelSize: 10
                                        elide: Text.ElideMiddle
                                    }
                                }

                                Flow {
                                    Layout.fillWidth: true
                                    spacing: 6

                                    AppButton {
                                        text: "Import Log"
                                        compact: true
                                        onClicked: root.importLog()
                                    }

                                    AppButton {
                                        visible: root.importedLogActive
                                        text: "Back To Live"
                                        compact: true
                                        onClicked: root.useLiveLog()
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
                    }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: root.summaryRail ? 330 : 220
                    Layout.preferredHeight: root.summaryRail ? 430 : (compactLayout ? 220 : 250)
                    radius: theme.radiusLg
                    color: theme.surfacePanel
                    border.color: theme.borderStrong
                    clip: true

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 6

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Text {
                                text: "Loot Feed"
                                color: theme.textPrimary
                                font.pixelSize: 14
                                font.bold: true
                            }

                            Rectangle {
                                radius: 9
                                color: root.importedLogActive ? theme.stateInfoBg : theme.surfaceRaised
                                border.color: root.importedLogActive ? theme.stateInfo : theme.borderSubtle
                                implicitHeight: 20
                                implicitWidth: recentLootCount.implicitWidth + 14

                                Text {
                                    id: recentLootCount
                                    anchors.centerIn: parent
                                    text: root.importedLogActive ? "Imported view" : (root.eventCount + " rows")
                                    color: root.importedLogActive ? theme.stateInfo : theme.textMuted
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }

                            Item {
                                Layout.fillWidth: true
                            }

                            Text {
                                text: "Source: " + root.sourceLabel(root.sourceFilter)
                                color: theme.textMuted
                                font.pixelSize: 11
                            }

                            Text {
                                text: root.looterFilter === "all" ? "All looters" : root.looterFilter
                                color: theme.textMuted
                                font.pixelSize: 11
                            }

                            Text {
                                text: root.categoryLabel(root.categoryFilter)
                                color: theme.textMuted
                                font.pixelSize: 11
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 26
                            visible: !root.stackedSummary
                            radius: 8
                            color: theme.cardLevel2
                            border.color: theme.borderSubtle

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 8

                                Text { text: "TIME"; color: theme.textMuted; font.pixelSize: 10; font.bold: true; Layout.preferredWidth: root.timeColumnWidth }
                                Text { text: "LOOTER"; color: theme.textMuted; font.pixelSize: 10; font.bold: true; Layout.preferredWidth: root.looterColumnWidth }
                                Text { text: "ITEM"; color: theme.textMuted; font.pixelSize: 10; font.bold: true; Layout.fillWidth: true }
                                Text { text: "QTY"; color: theme.textMuted; font.pixelSize: 10; font.bold: true; horizontalAlignment: Text.AlignRight; Layout.preferredWidth: root.qtyColumnWidth }
                                Text { text: "SOURCE"; color: theme.textMuted; font.pixelSize: 10; font.bold: true; horizontalAlignment: Text.AlignHCenter; Layout.preferredWidth: root.sourceColumnWidth }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: theme.borderSubtle
                        }

                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            ListView {
                                id: lootList
                                anchors.fill: parent
                                clip: true
                                spacing: 4
                                model: root.eventsModel
                                reuseItems: true
                                cacheBuffer: 900

                                delegate: Rectangle {
                                    required property string timestampText
                                    required property string lootedByName
                                    required property string lootedByGuild
                                    required property string itemName
                                    required property string itemId
                                    required property string iconUrl
                                    required property string category
                                    required property int quantity
                                    required property string sourceName
                                    required property string sourceKind
                                    required property bool isSilver
                                    required property string summary

                                    width: lootList.width
                                    radius: theme.radiusLg
                                    color: root.rowBackground(sourceKind)
                                    border.color: root.rowBorder(sourceKind)
                                    border.width: 1
                                    implicitHeight: compactLayout ? 46 : 50

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 6
                                        spacing: 1

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8

                                            Text {
                                                text: timestampText
                                                color: theme.textPrimary
                                                font.pixelSize: 10
                                                Layout.preferredWidth: root.timeColumnWidth
                                            }
                                            Text {
                                                text: lootedByGuild.length > 0 ? (lootedByName + " [" + lootedByGuild + "]") : lootedByName
                                                color: theme.textPrimary
                                                font.pixelSize: 10
                                                Layout.preferredWidth: root.looterColumnWidth
                                                elide: Text.ElideRight
                                            }

                                            Item {
                                                Layout.preferredWidth: iconUrl.length > 0 ? 24 : 0
                                                Layout.preferredHeight: 23
                                                visible: iconUrl.length > 0

                                                Rectangle {
                                                    anchors.fill: parent
                                                    radius: 6
                                                    color: theme.surfaceRaised
                                                    border.color: theme.borderSubtle

                                                    Image {
                                                        anchors.fill: parent
                                                        anchors.margins: 2
                                                        source: iconUrl
                                                        fillMode: Image.PreserveAspectFit
                                                        asynchronous: true
                                                        cache: true
                                                    }
                                                }
                                            }

                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                Layout.minimumWidth: compactLayout ? 140 : 210
                                                spacing: 0
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 6

                                                    Text {
                                                        Layout.fillWidth: true
                                                        text: itemName
                                                        color: sourceKind === "player" ? theme.stateDanger : theme.textPrimary
                                                        font.pixelSize: 11
                                                        font.bold: true
                                                        elide: Text.ElideRight
                                                    }

                                                    Rectangle {
                                                        radius: 9
                                                        color: root.categoryBadgeBg(category, sourceKind)
                                                        border.color: root.categoryBadgeBorder(category, sourceKind)
                                                        implicitHeight: 16
                                                        implicitWidth: kindBadgeText.implicitWidth + 12

                                                        Text {
                                                            id: kindBadgeText
                                                            anchors.centerIn: parent
                                                            text: root.categoryBadgeLabel(category)
                                                            color: root.categoryBadgeText(category, sourceKind)
                                                            font.pixelSize: 8
                                                            font.bold: true
                                                        }
                                                    }
                                                }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: itemId
                                                    color: theme.textDisabled
                                                    font.pixelSize: 8
                                                    elide: Text.ElideRight
                                                    visible: itemId.length > 0
                                                }
                                            }
                                            Text {
                                                text: String(quantity) + "x"
                                                color: sourceKind === "player" ? theme.stateDanger : theme.textPrimary
                                                font.pixelSize: 10
                                                font.bold: true
                                                horizontalAlignment: Text.AlignRight
                                                Layout.preferredWidth: root.qtyColumnWidth
                                            }
                                            Rectangle {
                                                Layout.preferredWidth: root.sourceColumnWidth
                                                radius: 10
                                                color: root.sourceBadgeBg(sourceKind)
                                                border.color: root.sourceBadgeBorder(sourceKind)
                                                border.width: 1
                                                implicitHeight: 18

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: sourceKind === "player"
                                                        ? ("Corpse: " + (sourceName.length > 0 ? sourceName : "player"))
                                                        : (sourceName.length > 0 ? sourceName : "System")
                                                    color: root.sourceBadgeText(sourceKind)
                                                    font.pixelSize: 8
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
                                            font.pixelSize: 9
                                            elide: Text.ElideRight
                                            maximumLineCount: 1
                                        }
                                    }
                                }

                                ScrollBar.vertical: ScrollBar {}
                            }

                            Item {
                                anchors.fill: parent
                                visible: lootList.count === 0

                                Column {
                                    anchors.centerIn: parent
                                    spacing: 8

                                    Text {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: "No item drops in this view"
                                        color: theme.textSecondary
                                        font.pixelSize: 18
                                        font.bold: true
                                    }

                                    Text {
                                        anchors.horizontalCenter: parent.horizontalCenter
                                        text: root.importedLogActive
                                            ? "Try another imported log or change the filters above."
                                            : "Wait for party loot or import an earlier log file."
                                        color: theme.textMuted
                                        font.pixelSize: 12
                                    }
                                }
                            }
                        }
                    }
                }

                }

                GridLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: root.summaryRail
                    Layout.minimumWidth: 0
                    Layout.preferredWidth: root.summaryRail ? root.summaryRailWidth : -1
                    Layout.maximumWidth: root.summaryRail ? root.summaryRailWidth : 16777215
                    Layout.bottomMargin: 2
                    columns: root.summaryRail ? 1 : root.aggregateColumns
                    columnSpacing: 8
                    rowSpacing: 8

                    LootSummaryPanel {
                        Layout.fillWidth: true
                        Layout.fillHeight: root.summaryRail
                        Layout.preferredHeight: root.summaryRail ? 118 : (compactLayout ? 118 : 132)
                        theme: root.theme
                        title: "Top Looters"
                        emptyText: "No looters in this view"
                        accentMode: "neutral"
                        model: root.topLootersModel
                    }

                    LootSummaryPanel {
                        Layout.fillWidth: true
                        Layout.fillHeight: root.summaryRail
                        Layout.preferredHeight: root.summaryRail ? 138 : (compactLayout ? 118 : 132)
                        theme: root.theme
                        title: "Top Items"
                        emptyText: "No item drops in this view"
                        accentMode: "items"
                        model: root.topItemsModel
                    }

                    LootSummaryPanel {
                        Layout.fillWidth: true
                        Layout.fillHeight: root.summaryRail
                        Layout.preferredHeight: root.summaryRail ? 118 : (compactLayout ? 118 : 132)
                        theme: root.theme
                        title: "Looted From Players"
                        emptyText: "No player corpses in this view"
                        accentMode: "danger"
                        model: root.topSourcesModel
                    }
                }
            }
        }
    }
}
