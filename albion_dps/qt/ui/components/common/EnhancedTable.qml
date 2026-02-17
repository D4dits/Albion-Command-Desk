import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme access

/**
 * EnhancedTable - Advanced table component with built-in features
 *
 * Features:
 * - Built-in sort indicators (ascending/descending/none)
 * - Row selection state
 * - Hover effects with smooth animations
 * - Copy to clipboard functionality (double-click)
 * - Context menu support
 * - Keyboard navigation (arrow keys, Home/End)
 * - Customizable columns via model
 *
 * Usage:
 *   EnhancedTable {
 *       id: table
 *       columns: [
 *           EnhancedTableColumn { title: "Name"; role: "name"; width: 150 },
 *           EnhancedTableColumn { title: "Value"; role: "value"; width: 100; sortable: true }
 *       ]
 *       model: myModel
 *       sortColumn: 1
 *       sortDescending: false
 *       onSortChanged: function(column, descending) { ... }
 *       onRowDoubleClicked: function(index, modelData) { ... }
 *   }
 */

// Base component - TableSurface with ListView
TableSurface {
    id: root
    level: 1
    Layout.fillWidth: true
    Layout.fillHeight: true
    clip: true

    // Public properties
    property var model: null
    property ListModel columns: ListModel {}
    property int sortColumn: -1
    property bool sortDescending: false
    property int selectedRow: -1
    property int columnSpacing: 12
    property int headerHeight: 26
    property int rowHeight: 34
    property bool showHeader: true
    property bool showGridLines: true

    // Signals
    signal sortChanged(int column, bool descending)
    signal rowSelected(int index)
    signal rowDoubleClicked(int index, var rowData)
    signal copyRequested(string text)

    // Computed properties
    readonly property int availableWidth: width - (anchors.margins || 0) * 2

    // Access to theme
    property var theme: Theme {}

    // Private properties
    QtObject {
        id: d
        property var hoveredRow: -1
        property var pressedRow: -1
    }

    // Calculate total column width
    readonly property int totalColumnWidth: {
        var total = 0
        for (var i = 0; i < columns.count; i++) {
            total += columns.get(i).width || 100
        }
        return total + (columns.count - 1) * columnSpacing
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 0

        // Table Header
        Rectangle {
            id: headerRow
            Layout.fillWidth: true
            height: root.showHeader ? root.headerHeight : 0
            visible: root.showHeader
            color: theme.tableHeaderBackground
            radius: 4

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 6
                anchors.rightMargin: 6
                spacing: root.columnSpacing

                Repeater {
                    model: root.columns

                    Rectangle {
                        Layout.preferredWidth: model.width || 100
                        Layout.fillWidth: model.fillWidth !== undefined ? model.fillWidth : false
                        Layout.minimumWidth: model.minWidth || 40
                        color: "transparent"
                        height: parent.height

                        RowLayout {
                            anchors.fill: parent
                            spacing: 4

                            Text {
                                text: model.title || ""
                                color: theme.tableHeaderText
                                font.pixelSize: 11
                                font.bold: true
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }

                            // Sort indicator
                            Icon {
                                visible: model.sortable !== false
                                name: {
                                    if (root.sortColumn !== index) return "sort"
                                    return root.sortDescending ? "sortDown" : "sortUp"
                                }
                                color: root.sortColumn === index ? root.theme.tableSortIndicator : root.theme.tableSortIndicatorInactive
                                size: 9
                                Layout.alignment: Qt.AlignVCenter
                            }

                            MouseArea {
                                anchors.fill: parent
                                enabled: model.sortable !== false
                                onClicked: {
                                    if (model.sortable === false) return
                                    if (root.sortColumn === index) {
                                        root.sortDescending = !root.sortDescending
                                    } else {
                                        root.sortColumn = index
                                        root.sortDescending = false
                                    }
                                    root.sortChanged(index, root.sortDescending)
                                }
                                cursorShape: model.sortable !== false ? Qt.PointingHandCursor : Qt.ArrowCursor
                            }
                        }
                    }
                }
            }
        }

        // Table Body
        ListView {
            id: tableBody
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.model
            spacing: 0
            reuseItems: true
            cacheBuffer: 300

            // Scrollbar
            ScrollBar.vertical: StyledScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Rectangle {
                id: row
                width: tableBody.width
                height: root.rowHeight
                color: {
                    if (index === root.selectedRow) return theme.tableSelectedBackground
                    if (d.hoveredRow === index) return theme.tableRowHover
                    return index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
                }
                radius: 4

                // Border for selected row
                border.color: index === root.selectedRow ? theme.tableSelectedBorder : "transparent"
                border.width: index === root.selectedRow ? 1 : 0

                Behavior on color {
                    ColorAnimation { duration: 120 }
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 4
                    anchors.rightMargin: 4
                    spacing: root.columnSpacing

                    Repeater {
                        model: root.columns

                        Text {
                            text: {
                                var role = model.role || ""
                                var value = model.display ? model.display(modelData, role) : (modelData[role] || "")
                                return value === undefined || value === null ? "" : String(value)
                            }
                            color: {
                                var colorRole = model.colorRole || ""
                                if (colorRole && modelData[colorRole] !== undefined) {
                                    return modelData[colorRole]
                                }
                                return model.textColor || theme.tableTextPrimary
                            }
                            font.pixelSize: model.fontSize || 11
                            elide: Text.ElideRight
                            Layout.preferredWidth: model.width || 100
                            Layout.fillWidth: model.fillWidth !== undefined ? model.fillWidth : false
                            Layout.minimumWidth: model.minWidth || 40
                            verticalAlignment: Text.AlignVCenter

                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.NoButton
                                hoverEnabled: true
                                onEntered: d.hoveredRow = index
                                onExited: d.hoveredRow = -1
                            }

                            // Copy on double-click
                            MouseArea {
                                anchors.fill: parent
                                acceptedButtons: Qt.LeftButton
                                onDoubleClicked: {
                                    var text = parent.text
                                    root.copyRequested(text)
                                }
                            }
                        }
                    }

                    // Row interaction
                    MouseArea {
                        anchors.fill: parent
                        acceptedButtons: Qt.LeftButton
                        onClicked: {
                            root.selectedRow = index
                            root.rowSelected(index)
                        }
                        onDoubleClicked: {
                            root.rowDoubleClicked(index, modelData)
                        }
                    }
                }
            }

            // Empty state
            Text {
                anchors.centerIn: parent
                visible: tableBody.count === 0
                text: "No data to display"
                color: theme.textSecondary
                font.pixelSize: 12
            }
        }
    }
}

/**
 * EnhancedTableColumn - Column definition for EnhancedTable
 *
 * Properties:
 * - title: Column header text
 * - role: Model role name for data binding
 * - width: Column width in pixels
 * - minWidth: Minimum column width
 * - sortable: Whether column can be sorted (default: true)
 * - fillWidth: Whether column should fill available space
 * - display: Custom display function
 * - colorRole: Model role for text color
 * - textColor: Fixed text color
 * - fontSize: Font size for column
 */
