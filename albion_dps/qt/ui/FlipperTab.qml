import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

CardPanel {
    id: root
    level: 1
    anchors.fill: parent

    property string region: "europe"
    property string sourceCity: "Caerleon"
    property int quality: 1
    property real minProfit: 10000
    property real minRoiPercent: 5
    property real riskBufferPercent: 0
    property real saleTaxPercent: 4
    property string searchQuery: ""
    property bool refreshInProgress: false
    property string refreshStatusText: ""
    property string pricesSource: ""
    property int resultsCount: 0
    property int validCount: 0
    property int missingCount: 0
    property real selectedTotalProfit: 0
    property var resultsModel: null
    property var theme: Theme

    signal setRegion(string region)
    signal setSourceCity(string city)
    signal setQuality(int quality)
    signal setMinProfit(string value)
    signal setMinRoiPercent(string value)
    signal setRiskBufferPercent(string value)
    signal setSaleTaxPercent(string value)
    signal setSearchQuery(string value)
    signal refreshFlips()
    signal setRowChecked(string rowKey, bool checked)
    signal copySelectedCsv()
    signal exportSelectedCsv()

    function formatInt(value) {
        var n = Number(value)
        if (!isFinite(n)) return "0"
        var whole = Math.round(n)
        var sign = whole < 0 ? "-" : ""
        var raw = Math.abs(whole).toString()
        return sign + raw.replace(/\B(?=(\d{3})+(?!\d))/g, " ")
    }

    function formatPercent(value) {
        var n = Number(value)
        if (!isFinite(n)) n = 0
        return n.toFixed(1) + "%"
    }

    function sourceColor(source) {
        var value = String(source || "").toLowerCase()
        if (value === "live" || value === "cache" || value === "partial_cache") return theme.stateSuccess
        if (value.indexOf("stale") >= 0) return theme.stateWarning
        if (value === "loading") return theme.stateInfo
        if (value === "error") return theme.stateDanger
        return theme.textMuted
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: theme.spacingPage
        spacing: theme.spacingSection

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            spacing: theme.spacingCompact

            Text {
                text: "Market Flipper"
                color: theme.textPrimary
                font.pixelSize: 16
                font.bold: true
                Layout.alignment: Qt.AlignVCenter
            }

            Rectangle {
                radius: theme.radiusSm
                color: sourceColor(root.pricesSource)
                Layout.preferredWidth: 8
                Layout.preferredHeight: 8
                Layout.alignment: Qt.AlignVCenter
            }

            Text {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                text: root.refreshStatusText
                color: theme.textMuted
                font.pixelSize: 12
                elide: Text.ElideRight
            }

            AppButton {
                text: root.refreshInProgress ? "Refreshing..." : "Refresh flips"
                enabled: !root.refreshInProgress
                Layout.preferredWidth: 124
                Layout.alignment: Qt.AlignVCenter
                onClicked: root.refreshFlips()
            }
            AppButton {
                text: "Copy CSV"
                Layout.preferredWidth: 92
                Layout.alignment: Qt.AlignVCenter
                onClicked: root.copySelectedCsv()
            }
            AppButton {
                text: "Export CSV"
                Layout.preferredWidth: 96
                Layout.alignment: Qt.AlignVCenter
                onClicked: root.exportSelectedCsv()
            }
        }

        TableSurface {
            Layout.fillWidth: true
            Layout.preferredHeight: 86
            level: 0

            RowLayout {
                anchors.fill: parent
                anchors.margins: theme.spacingMd
                spacing: theme.spacingMd

                ColumnLayout {
                    Layout.preferredWidth: 92
                    spacing: 4
                    Text { text: "Region"; color: theme.textMuted; font.pixelSize: 11 }
                    AppComboBox {
                        Layout.fillWidth: true
                        model: ["europe", "west", "east"]
                        currentIndex: Math.max(0, model.indexOf(root.region))
                        onActivated: root.setRegion(currentText)
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 134
                    spacing: 4
                    Text { text: "Buy city"; color: theme.textMuted; font.pixelSize: 11 }
                    AppComboBox {
                        Layout.fillWidth: true
                        model: ["Bridgewatch", "Martlock", "Lymhurst", "Fort Sterling", "Thetford", "Caerleon", "Brecilien"]
                        currentIndex: Math.max(0, model.indexOf(root.sourceCity))
                        onActivated: root.setSourceCity(currentText)
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 70
                    spacing: 4
                    Text { text: "Preferred Q"; color: theme.textMuted; font.pixelSize: 11 }
                    AppSpinBox {
                        from: 1
                        to: 5
                        value: root.quality
                        onValueModified: root.setQuality(value)
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 104
                    spacing: 4
                    Text { text: "Min profit"; color: theme.textMuted; font.pixelSize: 11 }
                    AppTextField {
                        text: String(Math.round(root.minProfit))
                        inputMethodHints: Qt.ImhDigitsOnly
                        onEditingFinished: root.setMinProfit(text)
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 78
                    spacing: 4
                    Text { text: "Min ROI"; color: theme.textMuted; font.pixelSize: 11 }
                    AppTextField {
                        text: String(root.minRoiPercent)
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        onEditingFinished: root.setMinRoiPercent(text)
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 78
                    spacing: 4
                    Text { text: "Buffer %"; color: theme.textMuted; font.pixelSize: 11 }
                    AppTextField {
                        text: String(root.riskBufferPercent)
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        onEditingFinished: root.setRiskBufferPercent(text)
                    }
                }
                ColumnLayout {
                    Layout.preferredWidth: 72
                    spacing: 4
                    Text { text: "Tax %"; color: theme.textMuted; font.pixelSize: 11 }
                    AppTextField {
                        text: String(root.saleTaxPercent)
                        inputMethodHints: Qt.ImhFormattedNumbersOnly
                        onEditingFinished: root.setSaleTaxPercent(text)
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    Text { text: "Search"; color: theme.textMuted; font.pixelSize: 11 }
                    AppTextField {
                        Layout.fillWidth: true
                        placeholderText: "optional: bow, cowl, frost..."
                        text: root.searchQuery
                        onTextChanged: root.setSearchQuery(text)
                        onEditingFinished: root.setSearchQuery(text)
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: theme.spacingCompact
            Repeater {
                model: [
                    { label: "Opportunities", value: root.validCount },
                    { label: "Checked profit", value: root.formatInt(root.selectedTotalProfit) },
                    { label: "Rows checked", value: root.resultsCount },
                    { label: "Filtered/missing", value: root.missingCount }
                ]
                delegate: TableSurface {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 54
                    level: 1
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: theme.spacingMd
                        spacing: 2
                        Text {
                            text: modelData.label
                            color: theme.textMuted
                            font.pixelSize: 11
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: String(modelData.value)
                            color: theme.textPrimary
                            font.pixelSize: 17
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        TableSurface {
            Layout.fillWidth: true
            Layout.fillHeight: true
            level: 0

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text { text: "On"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 38 }
                    Text { text: "Item"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 230 }
                    Text { text: "Tier"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 46 }
                    Text { text: "Q"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 28 }
                    Text { text: "Buy"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 86; horizontalAlignment: Text.AlignRight }
                    Text { text: "Age"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 66 }
                    Text { text: "BM buy"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 86; horizontalAlignment: Text.AlignRight }
                    Text { text: "BM age"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 66 }
                    Text { text: "Tax"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 70; horizontalAlignment: Text.AlignRight }
                    Text { text: "Buffer"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 70; horizontalAlignment: Text.AlignRight }
                    Text { text: "Profit"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 92; horizontalAlignment: Text.AlignRight }
                    Text { text: "ROI"; color: theme.textMuted; font.pixelSize: 11; Layout.preferredWidth: 64; horizontalAlignment: Text.AlignRight }
                    Text { text: "Status"; color: theme.textMuted; font.pixelSize: 11; Layout.fillWidth: true }
                }

                ListView {
                    id: resultList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: root.resultsModel
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Rectangle {
                        width: resultList.width
                        height: 32
                        color: index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 4
                            anchors.rightMargin: 4
                            spacing: 6

                            AppCheckBox {
                                Layout.preferredWidth: 38
                                checked: model.checked
                                enabled: model.valid
                                onToggled: root.setRowChecked(model.rowKey, checked)
                            }
                            Text {
                                text: model.itemName
                                color: model.valid ? theme.textPrimary : theme.textMuted
                                font.pixelSize: 12
                                Layout.preferredWidth: 230
                                elide: Text.ElideRight
                            }
                            Text {
                                text: "T" + model.tier + (model.enchant > 0 ? "." + model.enchant : "")
                                color: theme.textMuted
                                font.pixelSize: 12
                                Layout.preferredWidth: 46
                            }
                            Text {
                                text: String(model.quality)
                                color: theme.textMuted
                                font.pixelSize: 12
                                Layout.preferredWidth: 28
                            }
                            Text { text: root.formatInt(model.sourceSellPrice); color: theme.textPrimary; font.pixelSize: 12; Layout.preferredWidth: 86; horizontalAlignment: Text.AlignRight }
                            Text { text: model.sourceAgeText; color: theme.textMuted; font.pixelSize: 12; Layout.preferredWidth: 66 }
                            Text { text: root.formatInt(model.blackMarketBuyPrice); color: theme.textPrimary; font.pixelSize: 12; Layout.preferredWidth: 86; horizontalAlignment: Text.AlignRight }
                            Text { text: model.blackMarketAgeText; color: theme.textMuted; font.pixelSize: 12; Layout.preferredWidth: 66 }
                            Text { text: root.formatInt(model.taxValue); color: theme.textMuted; font.pixelSize: 12; Layout.preferredWidth: 70; horizontalAlignment: Text.AlignRight }
                            Text { text: root.formatInt(model.bufferValue); color: theme.textMuted; font.pixelSize: 12; Layout.preferredWidth: 70; horizontalAlignment: Text.AlignRight }
                            Text {
                                text: model.valid || model.sourceSellPrice > 0 && model.blackMarketBuyPrice > 0 ? root.formatInt(model.netProfit) : "-"
                                color: model.valid ? theme.stateSuccess : theme.textMuted
                                font.pixelSize: 12
                                font.bold: model.valid
                                Layout.preferredWidth: 92
                                horizontalAlignment: Text.AlignRight
                            }
                            Text {
                                text: model.valid || model.sourceSellPrice > 0 && model.blackMarketBuyPrice > 0 ? root.formatPercent(model.roiPercent) : "-"
                                color: model.valid ? theme.stateSuccess : theme.textMuted
                                font.pixelSize: 12
                                Layout.preferredWidth: 64
                                horizontalAlignment: Text.AlignRight
                            }
                            Text {
                                text: model.valid ? "OK" : model.staleReason
                                color: model.valid ? theme.stateSuccess : theme.stateWarning
                                font.pixelSize: 12
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }
        }
    }
}
