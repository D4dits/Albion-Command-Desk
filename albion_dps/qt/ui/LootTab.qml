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
    property int uniqueLooters: 0
    property int uniqueItems: 0
    property string latestLootSummary: ""
    property string logPath: ""
    property string logDirectoryUrl: ""
    property string searchQuery: ""
    property string sourceFilter: "all"
    property var sourceFilterOptions: ["all", "player", "mob", "silver", "system"]
    property var eventsModel: null
    property var topLootersModel: null
    property var topItemsModel: null

    signal setSearchQuery(string value)
    signal setSourceFilter(string value)
    signal copyLatestSummary()
    signal copyCurrentView()
    signal exportCurrentView()
    signal openLogFolder()

    function cardValue(value) {
        return String(value === undefined || value === null ? 0 : value)
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

            RowLayout {
                Layout.fillWidth: true
                spacing: theme.spacingSection

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

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
                }

                Flow {
                    Layout.preferredWidth: compactLayout ? 210 : 280
                    spacing: 8

                    Repeater {
                        model: [
                            { title: "Events", value: root.eventCount },
                            { title: "Qty", value: root.totalQuantity },
                            { title: "Looters", value: root.uniqueLooters },
                            { title: "Items", value: root.uniqueItems }
                        ]

                        delegate: Rectangle {
                            width: compactLayout ? 100 : 132
                            height: 64
                            radius: theme.cornerRadiusCard
                            color: theme.surfaceRaised
                            border.color: theme.borderSubtle

                            Column {
                                anchors.centerIn: parent
                                spacing: 3

                                Text {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: root.cardValue(modelData.value)
                                    color: theme.textPrimary
                                    font.pixelSize: 20
                                    font.bold: true
                                }
                                Text {
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    text: modelData.title
                                    color: theme.textMuted
                                    font.pixelSize: 11
                                    font.letterSpacing: 0.5
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: theme.cornerRadiusCard
                color: theme.surfaceRaised
                border.color: theme.borderSubtle
                implicitHeight: compactLayout ? 128 : 84

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

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
                                            Text {
                                                Layout.fillWidth: true
                                                text: itemName
                                                color: theme.textPrimary
                                                font.pixelSize: 12
                                                elide: Text.ElideRight
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
                                            color: sourceKind === "mob" ? theme.stateWarning : (sourceKind === "player" ? theme.stateInfo : theme.surfaceRaised)
                                            implicitHeight: 22

                                            Text {
                                                anchors.centerIn: parent
                                                text: sourceName
                                                color: sourceKind === "mob" ? theme.surfaceApp : theme.textPrimary
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
                    }
                }

                ColumnLayout {
                    Layout.preferredWidth: compactLayout ? 220 : 270
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

                            Text {
                                text: "Top Looters"
                                color: theme.textPrimary
                                font.pixelSize: 14
                                font.bold: true
                            }

                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
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

                            ListView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
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
                        }
                    }
                }
            }
        }
    }
}
