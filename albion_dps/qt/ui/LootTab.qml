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
    property string sourceNameFilter: ""
    property string looterFilter: "all"
    property string categoryFilter: "all"
    property string kindFilter: "items"
    property var sourceFilterOptions: ["all", "player", "mob", "system"]
    property var looterFilterOptions: ["all"]
    property var categoryFilterOptions: ["all", "weapon", "armor", "bag", "cape", "mount", "consumable", "resource", "artifact", "other"]
    property var kindFilterOptions: ["items"]
    property var eventsModel: null
    property var topLootersModel: null
    property var topItemsModel: null
    property var topSourcesModel: null
    property var topSilverLootersModel: null

    property bool sessionActive: false
    property string sessionTitle: "Live buffer"
    property string sessionDurationText: "00:00"
    property var sessionOptions: []
    property string selectedSessionId: ""
    property int pendingScopeCount: 0
    property int totalMarketValue: 0
    property int totalLiquidationValue: 0
    property int outstandingMarketValue: 0
    property string pricingStatus: "idle"
    property string priceRegion: "europe"
    property string priceCity: "Bridgewatch"
    property int bufferSeconds: 120
    property string selfGuild: ""
    property string selfAlliance: ""
    property int activeView: 0
    property string settlementEventId: ""
    property string settlementAction: "returned"
    property int settlementMaxQuantity: 1

    readonly property int lootColumnGap: 8
    readonly property int lootTimeWidth: root.compactLayout ? 0 : 52
    readonly property int lootPlayerWidth: root.compactLayout ? 112 : 142
    readonly property int lootQualityWidth: 62
    readonly property int lootQuantityWidth: 42
    readonly property int lootValueWidth: root.compactLayout ? 78 : 92
    readonly property int lootStatusWidth: root.activeView === 2 ? 148 : 100
    readonly property int lootVisibleColumnGaps: root.compactLayout ? 5 : 6

    function lootItemWidth(tableWidth) {
        var fixedWidth = root.lootTimeWidth + root.lootPlayerWidth
            + root.lootQualityWidth + root.lootQuantityWidth
            + root.lootValueWidth + root.lootStatusWidth
            + root.lootColumnGap * root.lootVisibleColumnGaps + 16
        return Math.max(170, Number(tableWidth) - fixedWidth)
    }

    readonly property int playerItemsWidth: 70
    readonly property int playerMarketWidth: root.compactLayout ? 90 : 110
    readonly property int playerInstantWidth: root.compactLayout ? 90 : 110
    readonly property int playerOutstandingWidth: root.compactLayout ? 100 : 120
    readonly property int playerSettleWidth: 138

    function playerNameWidth(tableWidth) {
        var fixedWidth = root.playerItemsWidth + root.playerMarketWidth
            + root.playerInstantWidth + root.playerOutstandingWidth
            + root.playerSettleWidth + root.lootColumnGap * 5 + 16
        return Math.max(150, Number(tableWidth) - fixedWidth)
    }

    signal setSearchQuery(string value)
    signal setSourceFilter(string value)
    signal setSourceNameFilter(string value)
    signal setLooterFilter(string value)
    signal setCategoryFilter(string value)
    signal setKindFilter(string value)
    signal copyLatestSummary()
    signal copyCurrentView()
    signal exportCurrentView()
    signal openLogFolder()
    signal importLog()
    signal useLiveLog()
    signal startSession(string title)
    signal stopSession()
    signal selectSession(int index)
    signal showLiveBuffer()
    signal deleteSelectedSession()
    signal refreshPrices()
    signal setPriceCity(string value)
    signal setPriceRegion(string value)
    signal setBufferSeconds(int value)
    signal setSelfAffiliation(string guildName, string allianceName)
    signal settleEvent(string eventId, string action, int quantity, int actualValue, string note)
    signal resetEventSettlement(string eventId)
    signal settlePlayer(string playerName, string action)
    signal setEventQuality(string eventId, int quality)

    function formatNumber(value) {
        var n = Number(value)
        if (!isFinite(n)) return "0"
        return Math.round(n).toLocaleString(Qt.locale("en_US"), "f", 0)
    }

    function categoryLabel(value) {
        var labels = {
            "all": "All",
            "weapon": "Weapons",
            "armor": "Armor",
            "bag": "Bags",
            "cape": "Capes",
            "mount": "Mounts",
            "consumable": "Consumables",
            "resource": "Resources",
            "artifact": "Artifacts",
            "other": "Other"
        }
        return labels[value] || value
    }

    function categorySymbol(value) {
        var symbols = {
            "weapon": "W", "armor": "A", "bag": "B", "cape": "C",
            "mount": "M", "consumable": "+", "resource": "R",
            "artifact": "*", "other": "?"
        }
        return symbols[value] || "?"
    }

    function categoryColor(value) {
        var colors = {
            "weapon": "#8f5d5d", "armor": "#536d87", "bag": "#6b6250",
            "cape": "#795b84", "mount": "#4f756d", "consumable": "#477a55",
            "resource": "#756744", "artifact": "#806447", "other": "#465567"
        }
        return colors[value] || colors.other
    }

    function openSettlement(eventId, action, quantity) {
        root.settlementEventId = eventId
        root.settlementAction = action
        root.settlementMaxQuantity = Math.max(1, Number(quantity))
        settlementQuantity.value = root.settlementMaxQuantity
        settlementActual.text = ""
        settlementNote.text = ""
        settlementDialog.open()
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
            spacing: 8

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: "Loot"
                        color: theme.textPrimary
                        font.pixelSize: 20
                        font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: root.sessionTitle + "  |  " + root.sessionDurationText
                        color: root.sessionActive ? theme.stateSuccess : theme.textMuted
                        font.pixelSize: 11
                        elide: Text.ElideRight
                    }
                }

                TextField {
                    id: sessionName
                    Layout.preferredWidth: 190
                    visible: !root.sessionActive
                    placeholderText: "Session name"
                    color: theme.textPrimary
                    selectByMouse: true
                    background: Rectangle {
                        radius: 4
                        color: theme.cardLevel1
                        border.color: sessionName.activeFocus ? theme.accentPrimary : theme.borderSubtle
                    }
                }

                AppComboBox {
                    id: lookbackCombo
                    Layout.preferredWidth: 105
                    visible: !root.sessionActive
                    model: [0, 60, 120, 300, 600]
                    currentIndex: Math.max(0, model.indexOf(root.bufferSeconds))
                    textRole: ""
                    displayText: String(currentValue) + "s buffer"
                    onActivated: root.setBufferSeconds(Number(currentValue))
                }

                AppButton {
                    text: root.sessionActive ? "Stop" : "Start"
                    variant: root.sessionActive ? "danger" : "primary"
                    onClicked: {
                        if (root.sessionActive) root.stopSession()
                        else root.startSession(sessionName.text)
                    }
                }

                AppButton {
                    text: "Export"
                    onClicked: root.exportCurrentView()
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: controlsFlow.implicitHeight + 14
                radius: 4
                color: theme.cardLevel1
                border.color: theme.borderSubtle

                Flow {
                    id: controlsFlow
                    anchors.fill: parent
                    anchors.margins: 7
                    spacing: 7

                    TextField {
                        width: 190
                        height: 30
                        placeholderText: "Search player or item"
                        text: root.searchQuery
                        color: theme.textPrimary
                        selectByMouse: true
                        onTextEdited: root.setSearchQuery(text)
                        background: Rectangle {
                            radius: 4
                            color: theme.cardLevel0
                            border.color: parent.activeFocus ? theme.accentPrimary : theme.borderSubtle
                        }
                    }

                    AppComboBox {
                        width: 145
                        model: root.looterFilterOptions
                        currentIndex: Math.max(0, model.indexOf(root.looterFilter))
                        onActivated: root.setLooterFilter(String(currentValue))
                    }

                    AppComboBox {
                        width: 120
                        model: root.sourceFilterOptions
                        currentIndex: Math.max(0, model.indexOf(root.sourceFilter))
                        onActivated: root.setSourceFilter(String(currentValue))
                    }

                    AppComboBox {
                        width: 135
                        model: root.categoryFilterOptions
                        currentIndex: Math.max(0, model.indexOf(root.categoryFilter))
                        displayText: root.categoryLabel(String(currentValue))
                        onActivated: root.setCategoryFilter(String(currentValue))
                    }

                    AppComboBox {
                        width: 92
                        model: ["europe", "west", "east"]
                        currentIndex: Math.max(0, model.indexOf(root.priceRegion))
                        onActivated: root.setPriceRegion(String(currentValue))
                    }

                    TextField {
                        width: 120
                        height: 30
                        text: root.priceCity
                        placeholderText: "Price city"
                        color: theme.textPrimary
                        selectByMouse: true
                        onEditingFinished: root.setPriceCity(text)
                        background: Rectangle {
                            radius: 4
                            color: theme.cardLevel0
                            border.color: parent.activeFocus ? theme.accentPrimary : theme.borderSubtle
                        }
                    }

                    AppButton {
                        text: "Refresh prices"
                        enabled: root.pricingStatus !== "refreshing"
                        onClicked: root.refreshPrices()
                    }

                    Text {
                        height: 30
                        verticalAlignment: Text.AlignVCenter
                        text: root.pricingStatus
                        color: root.pricingStatus.indexOf("error") === 0 ? theme.stateDanger : theme.textMuted
                        font.pixelSize: 10
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 1

                Repeater {
                    model: [
                        { label: "Items", value: root.eventCount },
                        { label: "Players", value: root.uniqueLooters },
                        { label: "Market value", value: root.totalMarketValue },
                        { label: "Instant value", value: root.totalLiquidationValue },
                        { label: "Outstanding", value: root.outstandingMarketValue },
                        { label: "Unclassified", value: root.pendingScopeCount }
                    ]
                    delegate: Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 48
                        color: theme.cardLevel1
                        border.color: theme.borderSubtle
                        Column {
                            anchors.centerIn: parent
                            spacing: 2
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: root.formatNumber(modelData.value)
                                color: modelData.label === "Outstanding" && modelData.value > 0
                                    ? theme.stateWarning : theme.textPrimary
                                font.pixelSize: 15
                                font.bold: true
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.label
                                color: theme.textMuted
                                font.pixelSize: 9
                            }
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 4
                Repeater {
                    model: ["Live", "Players", "Reconcile", "History"]
                    delegate: AppButton {
                        Layout.preferredWidth: 118
                        text: modelData
                        variant: root.activeView === index ? "primary" : "secondary"
                        onClicked: root.activeView = index
                    }
                }
                Item { Layout.fillWidth: true }
                AppButton {
                    text: "Import"
                    onClicked: root.importLog()
                }
                AppButton {
                    visible: root.importedLogActive
                    text: "Back to live"
                    onClicked: root.useLiveLog()
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: historyControls.implicitHeight + 14
                visible: root.activeView === 3
                color: theme.cardLevel1
                border.color: theme.borderSubtle
                radius: 4

                ColumnLayout {
                    id: historyControls
                    anchors.fill: parent
                    anchors.margins: 7
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 7
                        Text {
                            text: "Session"
                            color: theme.textMuted
                            font.pixelSize: 10
                            Layout.preferredWidth: 54
                        }
                        AppComboBox {
                            Layout.fillWidth: true
                            model: root.sessionOptions
                            onActivated: root.selectSession(index)
                        }
                        AppButton { text: "Live buffer"; onClicked: root.showLiveBuffer() }
                        AppButton {
                            text: "Delete"
                            variant: "danger"
                            enabled: root.selectedSessionId.length > 0 && !root.sessionActive
                            onClicked: root.deleteSelectedSession()
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 7
                        Text {
                            text: "Scope"
                            color: theme.textMuted
                            font.pixelSize: 10
                            Layout.preferredWidth: 54
                        }
                        TextField {
                            id: historyGuildField
                            Layout.fillWidth: true
                            placeholderText: "Your guild"
                            text: root.selfGuild
                            color: theme.textPrimary
                            background: Rectangle { color: theme.cardLevel0; border.color: theme.borderSubtle; radius: 4 }
                        }
                        TextField {
                            id: historyAllianceField
                            Layout.fillWidth: true
                            placeholderText: "Your alliance"
                            text: root.selfAlliance
                            color: theme.textPrimary
                            background: Rectangle { color: theme.cardLevel0; border.color: theme.borderSubtle; radius: 4 }
                        }
                        AppButton {
                            text: "Apply"
                            onClicked: root.setSelfAffiliation(historyGuildField.text, historyAllianceField.text)
                        }
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ColumnLayout {
                    anchors.fill: parent
                    visible: root.activeView === 0 || root.activeView === 2 || root.activeView === 3
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 28
                        color: theme.cardLevel1
                        border.color: theme.borderSubtle
                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 8
                            anchors.rightMargin: 8
                            spacing: 8
                            Text { width: root.lootTimeWidth; height: parent.height; visible: width > 0; text: "TIME"; color: theme.textMuted; font.pixelSize: 9; verticalAlignment: Text.AlignVCenter }
                            Text { width: root.lootPlayerWidth; height: parent.height; text: "PLAYER"; color: theme.textMuted; font.pixelSize: 9; verticalAlignment: Text.AlignVCenter }
                            Text { width: root.lootItemWidth(parent.width); height: parent.height; text: "ITEM"; color: theme.textMuted; font.pixelSize: 9; verticalAlignment: Text.AlignVCenter }
                            Text { objectName: "lootHeaderQuality"; width: root.lootQualityWidth; height: parent.height; text: "QUALITY"; color: theme.textMuted; font.pixelSize: 9; verticalAlignment: Text.AlignVCenter }
                            Text { objectName: "lootHeaderQuantity"; width: root.lootQuantityWidth; height: parent.height; text: "QTY"; color: theme.textMuted; font.pixelSize: 9; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                            Text { objectName: "lootHeaderValue"; width: root.lootValueWidth; height: parent.height; text: "VALUE"; color: theme.textMuted; font.pixelSize: 9; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                            Text { objectName: "lootHeaderStatus"; width: root.lootStatusWidth; height: parent.height; text: "STATUS"; color: theme.textMuted; font.pixelSize: 9; verticalAlignment: Text.AlignVCenter }
                        }
                    }

                    ListView {
                        id: lootList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: root.eventsModel
                        spacing: 1
                        boundsBehavior: Flickable.StopAtBounds

                        delegate: Rectangle {
                            width: lootList.width
                            height: 54
                            color: index % 2 === 0 ? theme.cardLevel0 : theme.cardLevel1
                            border.color: theme.borderSubtle

                            Row {
                                x: 8
                                y: 0
                                width: parent.width - 16
                                height: parent.height
                                spacing: 8

                                Text {
                                    width: root.lootTimeWidth
                                    height: parent.height
                                    visible: width > 0
                                    text: timestampText
                                    color: theme.textMuted
                                    font.pixelSize: 9
                                    verticalAlignment: Text.AlignVCenter
                                }
                                Column {
                                    width: root.lootPlayerWidth
                                    height: parent.height
                                    spacing: 0
                                    Text {
                                        width: parent.width
                                        height: parent.height / 2
                                        text: lootedByName
                                        color: theme.textPrimary
                                        font.pixelSize: 10
                                        font.bold: true
                                        elide: Text.ElideRight
                                        verticalAlignment: Text.AlignBottom
                                    }
                                    Text {
                                        width: parent.width
                                        height: parent.height / 2
                                        text: lootedByGuild.length > 0 ? lootedByGuild : lootedByAlliance
                                        color: theme.textMuted
                                        font.pixelSize: 8
                                        elide: Text.ElideRight
                                        verticalAlignment: Text.AlignTop
                                    }
                                }
                                Row {
                                    width: root.lootItemWidth(parent.width)
                                    height: parent.height
                                    spacing: 6
                                    Item {
                                        width: 34
                                        height: 34
                                        anchors.verticalCenter: parent.verticalCenter

                                        Rectangle {
                                            anchors.fill: parent
                                            radius: 4
                                            color: root.categoryColor(category)
                                            border.color: theme.borderStrong
                                            visible: itemIcon.status !== Image.Ready
                                            Text {
                                                anchors.centerIn: parent
                                                text: root.categorySymbol(category)
                                                color: theme.textPrimary
                                                font.pixelSize: 14
                                                font.bold: true
                                            }
                                        }

                                        Image {
                                            id: itemIcon
                                            anchors.fill: parent
                                            source: iconUrl
                                            sourceSize.width: 34
                                            sourceSize.height: 34
                                            fillMode: Image.PreserveAspectFit
                                        }
                                    }
                                    Column {
                                        width: parent.width - 40
                                        height: parent.height
                                        spacing: 0
                                        Text {
                                            width: parent.width
                                            height: parent.height / 2
                                            text: itemName
                                            color: theme.textPrimary
                                            font.pixelSize: 10
                                            font.bold: true
                                            elide: Text.ElideRight
                                            verticalAlignment: Text.AlignBottom
                                        }
                                        Text {
                                            width: parent.width
                                            height: parent.height / 2
                                            text: eligibilityReason + " | " + (sourceName.length > 0 ? sourceName : sourceKind)
                                            color: theme.textMuted
                                            font.pixelSize: 8
                                            elide: Text.ElideRight
                                            verticalAlignment: Text.AlignTop
                                        }
                                    }
                                }
                                AppComboBox {
                                    objectName: "lootRowQuality"
                                    width: root.lootQualityWidth
                                    height: 30
                                    anchors.verticalCenter: parent.verticalCenter
                                    model: ["Q?", "Q1", "Q2", "Q3", "Q4", "Q5"]
                                    currentIndex: Math.max(0, model.indexOf(qualityText))
                                    onActivated: root.setEventQuality(eventId, index)
                                }
                                Text {
                                    objectName: "lootRowQuantity"
                                    width: root.lootQuantityWidth
                                    height: parent.height
                                    text: String(quantity)
                                    color: theme.textPrimary
                                    font.pixelSize: 10
                                    horizontalAlignment: Text.AlignRight
                                    verticalAlignment: Text.AlignVCenter
                                }
                                Column {
                                    objectName: "lootRowValue"
                                    width: root.lootValueWidth
                                    height: parent.height
                                    spacing: 0
                                    Text {
                                        width: parent.width
                                        height: parent.height / 2
                                        text: root.formatNumber(marketValue)
                                        color: marketValue > 0 ? theme.stateSuccess : theme.textDisabled
                                        font.pixelSize: 10
                                        font.bold: true
                                        horizontalAlignment: Text.AlignRight
                                        verticalAlignment: Text.AlignBottom
                                    }
                                    Text {
                                        width: parent.width
                                        height: parent.height / 2
                                        text: valueEstimated ? "estimated" : "priced"
                                        color: valueEstimated ? theme.stateWarning : theme.textMuted
                                        font.pixelSize: 8
                                        horizontalAlignment: Text.AlignRight
                                        verticalAlignment: Text.AlignTop
                                    }
                                }
                                Loader {
                                    objectName: "lootRowStatus"
                                    width: root.lootStatusWidth
                                    height: 30
                                    anchors.verticalCenter: parent.verticalCenter
                                    sourceComponent: root.activeView === 2 ? reconcileControl : statusLabel
                                }
                            }

                            Component {
                                id: statusLabel
                                Text {
                                    width: parent ? parent.width : root.lootStatusWidth
                                    height: parent ? parent.height : 30
                                    text: settlementStatus
                                    color: settlementStatus === "pending" ? theme.stateWarning : theme.stateSuccess
                                    font.pixelSize: 9
                                    font.bold: true
                                    elide: Text.ElideRight
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            Component {
                                id: reconcileControl
                                AppComboBox {
                                    width: parent ? parent.width : root.lootStatusWidth
                                    height: parent ? parent.height : 30
                                    model: ["pending", "returned", "sold", "lost", "allowed", "unreturned", "excluded"]
                                    currentIndex: Math.max(0, model.indexOf(settlementStatus))
                                    onActivated: {
                                        var action = String(currentValue)
                                        if (action === "pending") root.resetEventSettlement(eventId)
                                        else root.openSettlement(eventId, action, outstandingQuantity)
                                    }
                                }
                            }
                        }

                        ScrollBar.vertical: ScrollBar {}

                        Text {
                            anchors.centerIn: parent
                            visible: lootList.count === 0
                            text: "No loot matches the current filters"
                            color: theme.textMuted
                            font.pixelSize: 11
                        }
                    }
                }

                ColumnLayout {
                    anchors.fill: parent
                    visible: root.activeView === 1
                    spacing: 1

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 28
                        color: theme.cardLevel1
                        Row {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: root.lootColumnGap
                            Text { width: root.playerNameWidth(parent.width); height: parent.height; text: "PLAYER"; color: theme.textMuted; font.pixelSize: 9; verticalAlignment: Text.AlignVCenter }
                            Text { objectName: "playersHeaderItems"; width: root.playerItemsWidth; height: parent.height; text: "ITEMS"; color: theme.textMuted; font.pixelSize: 9; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                            Text { width: root.playerMarketWidth; height: parent.height; text: "MARKET"; color: theme.textMuted; font.pixelSize: 9; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                            Text { width: root.playerInstantWidth; height: parent.height; text: "INSTANT"; color: theme.textMuted; font.pixelSize: 9; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                            Text { width: root.playerOutstandingWidth; height: parent.height; text: "OUTSTANDING"; color: theme.textMuted; font.pixelSize: 9; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                            Text { width: root.playerSettleWidth; height: parent.height; text: "SETTLE PLAYER"; color: theme.textMuted; font.pixelSize: 9; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                    ListView {
                        id: playersList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: root.topLootersModel
                        boundsBehavior: Flickable.StopAtBounds
                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 42
                            color: index % 2 === 0 ? theme.cardLevel0 : theme.cardLevel1
                            Row {
                                x: 8
                                y: 0
                                width: parent.width - 16
                                height: parent.height
                                spacing: root.lootColumnGap
                                Column {
                                    width: root.playerNameWidth(parent.width)
                                    height: parent.height
                                    spacing: 0
                                    Text { width: parent.width; height: parent.height / 2; text: label; color: theme.textPrimary; font.pixelSize: 11; font.bold: true; elide: Text.ElideRight; verticalAlignment: Text.AlignBottom }
                                    Text { width: parent.width; height: parent.height / 2; text: sublabel; color: theme.textMuted; font.pixelSize: 8; elide: Text.ElideRight; verticalAlignment: Text.AlignTop }
                                }
                                Text { objectName: "playersRowItems"; width: root.playerItemsWidth; height: parent.height; text: String(quantity); color: theme.textSecondary; font.pixelSize: 10; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                                Text { width: root.playerMarketWidth; height: parent.height; text: root.formatNumber(marketValue); color: theme.stateSuccess; font.pixelSize: 10; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                                Text { width: root.playerInstantWidth; height: parent.height; text: root.formatNumber(liquidationValue); color: theme.textSecondary; font.pixelSize: 10; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                                Text { width: root.playerOutstandingWidth; height: parent.height; text: root.formatNumber(outstandingValue); color: outstandingValue > 0 ? theme.stateWarning : theme.stateSuccess; font.pixelSize: 10; horizontalAlignment: Text.AlignRight; verticalAlignment: Text.AlignVCenter }
                                AppComboBox {
                                    width: root.playerSettleWidth
                                    height: 30
                                    anchors.verticalCenter: parent.verticalCenter
                                    model: ["pending", "returned", "sold", "lost", "allowed", "unreturned", "excluded"]
                                    onActivated: root.settlePlayer(label, String(currentValue))
                                }
                            }
                        }
                        ScrollBar.vertical: ScrollBar {}
                        Text {
                            anchors.centerIn: parent
                            visible: playersList.count === 0
                            text: "No players match the current filters"
                            color: theme.textMuted
                            font.pixelSize: 11
                        }
                    }
                }

            }
        }
    }

    Dialog {
        id: settlementDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: 380
        modal: true
        title: "Settle: " + root.settlementAction
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: root.settleEvent(
            root.settlementEventId,
            root.settlementAction,
            settlementQuantity.value,
            Number(settlementActual.text || 0),
            settlementNote.text
        )

        contentItem: ColumnLayout {
            spacing: 8
            RowLayout {
                Layout.fillWidth: true
                Text { text: "Quantity"; color: theme.textMuted; Layout.preferredWidth: 90 }
                SpinBox {
                    id: settlementQuantity
                    Layout.fillWidth: true
                    from: 1
                    to: Math.max(1, root.settlementMaxQuantity)
                }
            }
            RowLayout {
                Layout.fillWidth: true
                visible: root.settlementAction === "sold"
                Text { text: "Actual silver"; color: theme.textMuted; Layout.preferredWidth: 90 }
                TextField {
                    id: settlementActual
                    Layout.fillWidth: true
                    inputMethodHints: Qt.ImhDigitsOnly
                    placeholderText: "Optional"
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Text { text: "Note"; color: theme.textMuted; Layout.preferredWidth: 90 }
                TextField { id: settlementNote; Layout.fillWidth: true }
            }
        }
    }
}
