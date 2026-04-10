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
    property string kindFilter: "all"
    property var sourceFilterOptions: ["all", "player", "mob", "silver", "system"]
    property var kindFilterOptions: ["all", "items", "silver"]
    property var eventsModel: null
    property var topLootersModel: null
    property var topItemsModel: null
    property var topSilverLootersModel: null
    property bool stackedControls: width < 1140
    property bool stackedSummary: width < 920
    property int aggregateColumns: width >= 1050 ? 3 : (width >= 720 ? 2 : 1)
    property int timeColumnWidth: compactLayout ? 56 : 64
    property int looterColumnWidth: compactLayout ? 136 : 164
    property int qtyColumnWidth: compactLayout ? 48 : 56
    property int sourceColumnWidth: compactLayout ? 124 : 140

    signal setSearchQuery(string value)
    signal setSourceFilter(string value)
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
        if (value === "items") {
            return "Items"
        }
        if (value === "silver") {
            return "Silver"
        }
        return "All"
    }

    function sourceLabel(value) {
        var text = String(value || "all")
        if (text.length === 0) {
            return "All"
        }
        return text.charAt(0).toUpperCase() + text.slice(1)
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
        color: theme.cardLevel0
        border.color: theme.borderStrong
        clip: true

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
                        : "Party loot log. Import previous logs or inspect the current session feed."
                    color: latestLootSummary.length > 0 ? theme.textSecondary : theme.textMuted
                    wrapMode: Text.Wrap
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
                            radius: theme.radiusLg
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
                radius: theme.radiusLg
                color: theme.cardLevel2
                border.color: theme.borderStrong
                implicitHeight: compactLayout ? 176 : 140

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 10

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

                    GridLayout {
                        Layout.fillWidth: true
                        columns: root.stackedControls ? 1 : 3
                        columnSpacing: 10
                        rowSpacing: 10

                        AppTextField {
                            Layout.fillWidth: true
                            Layout.columnSpan: root.stackedControls ? 1 : 2
                            placeholderText: "Search looter, item, source..."
                            text: root.searchQuery
                            onTextEdited: root.setSearchQuery(text)
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

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                text: root.importedLogActive ? "Imported log" : "Live session log"
                                color: root.importedLogActive ? theme.stateInfo : theme.textSecondary
                                font.pixelSize: 11
                                font.bold: true
                            }

                            Text {
                                Layout.fillWidth: true
                                text: logPath.length > 0 ? logPath : "No loot log available yet"
                                color: theme.textMuted
                                font.pixelSize: 11
                                elide: Text.ElideMiddle
                            }
                        }

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

            ColumnLayout {
                Layout.fillWidth: true
                spacing: theme.spacingSection

                Rectangle {
                    Layout.fillWidth: true
                    radius: theme.radiusLg
                    color: theme.surfacePanel
                    border.color: theme.borderStrong
                    clip: true

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

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
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12
                            visible: !root.stackedSummary

                            Text { text: "Time"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: root.timeColumnWidth }
                            Text { text: "Looter"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: root.looterColumnWidth }
                            Text { text: "Item"; color: theme.textMuted; font.pixelSize: 11; Layout.fillWidth: true }
                            Text { text: "Qty"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: root.qtyColumnWidth }
                            Text { text: "Source"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: root.sourceColumnWidth }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: theme.borderSubtle
                        }

                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: compactLayout ? 260 : 300
                            clip: true

                            ListView {
                                id: lootList
                                anchors.fill: parent
                                clip: true
                                spacing: 6
                                model: root.eventsModel

                                delegate: Rectangle {
                                    required property string timestampText
                                    required property string lootedByName
                                    required property string lootedByGuild
                                    required property string itemName
                                    required property string itemId
                                    required property string iconUrl
                                    required property int quantity
                                    required property string sourceName
                                    required property string sourceKind
                                    required property bool isSilver
                                    required property string summary

                                    width: lootList.width
                                    radius: theme.radiusLg
                                    color: isSilver ? "#171d12" : theme.surfaceInteractive
                                    border.color: isSilver ? "#4f431f" : theme.borderSubtle
                                    border.width: 1
                                    implicitHeight: compactLayout ? 68 : 72

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        spacing: 4

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 10

                                            Text {
                                                text: timestampText
                                                color: theme.textPrimary
                                                font.pixelSize: 11
                                                Layout.preferredWidth: root.timeColumnWidth
                                            }
                                            Text {
                                                text: lootedByGuild.length > 0 ? (lootedByName + " [" + lootedByGuild + "]") : lootedByName
                                                color: theme.textPrimary
                                                font.pixelSize: 11
                                                Layout.preferredWidth: root.looterColumnWidth
                                                elide: Text.ElideRight
                                            }

                                            Item {
                                                Layout.preferredWidth: iconUrl.length > 0 ? 28 : 0
                                                Layout.preferredHeight: 28
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
                                                Layout.minimumWidth: compactLayout ? 180 : 260
                                                spacing: 1
                                                RowLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 6

                                                    Text {
                                                        Layout.fillWidth: true
                                                        text: itemName
                                                        color: isSilver ? theme.brandWarmAccent : theme.textPrimary
                                                        font.pixelSize: 12
                                                        font.bold: true
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
                                                            font.pixelSize: 9
                                                            font.bold: true
                                                        }
                                                    }
                                                }
                                                Text {
                                                    Layout.fillWidth: true
                                                    text: itemId
                                                    color: theme.textDisabled
                                                    font.pixelSize: 9
                                                    elide: Text.ElideRight
                                                    visible: itemId.length > 0
                                                }
                                            }
                                            Text {
                                                text: isSilver ? String(quantity) : (String(quantity) + "x")
                                                color: isSilver ? theme.brandWarmAccent : theme.textPrimary
                                                font.pixelSize: 11
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
                                                implicitHeight: 22

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: sourceKind === "silver" ? "Silver" : (sourceName.length > 0 ? sourceName : "System")
                                                    color: root.sourceBadgeText(sourceKind)
                                                    font.pixelSize: 10
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
                                            font.pixelSize: 10
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
                                        text: root.kindFilter === "silver"
                                            ? "No silver events in this view"
                                            : (root.kindFilter === "items" ? "No item drops in this view" : "No loot events in this view")
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

                GridLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    columns: root.aggregateColumns
                    columnSpacing: theme.spacingSection
                    rowSpacing: theme.spacingSection

                    LootSummaryPanel {
                        Layout.fillWidth: true
                        theme: root.theme
                        title: "Top Looters"
                        emptyText: "No looters in this view"
                        accentMode: "neutral"
                        model: root.topLootersModel
                    }

                    LootSummaryPanel {
                        Layout.fillWidth: true
                        theme: root.theme
                        title: "Top Items"
                        emptyText: "No item drops in this view"
                        accentMode: "items"
                        model: root.topItemsModel
                    }

                    LootSummaryPanel {
                        Layout.fillWidth: true
                        theme: root.theme
                        title: "Top Silver"
                        emptyText: "No silver events in this view"
                        accentMode: "silver"
                        valueSuffix: ""
                        model: root.topSilverLootersModel
                    }
                }
            }
        }
    }
}
