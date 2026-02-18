import QtQuick 2.15
import QtQuick.Layouts 1.15
import "." // for Theme, AppButton, AppTextField, AppComboBox access

/**
 * MarketPresets - Preset management for market configurations
 *
 * Provides:
 * - Preset selection dropdown
 * - Preset name input
 * - Save/Load/Delete buttons
 */
Rectangle {
    id: root
    Layout.fillWidth: true
    radius: 4
    color: theme.tableHeaderBackground
    border.color: theme.borderSubtle
    implicitHeight: 130

    // Properties
    property var presetNames: []
    property string selectedPresetName: ""
    property int compactControlHeight: 24

    // Signals
    signal setSelectedPresetName(string name)
    signal savePreset(string name)
    signal loadPreset(string name)
    signal deletePreset(string name)

    // Access to theme
    property var theme: null
    property color textColor: theme.textPrimary
    property color mutedColor: theme.textMuted

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 8
        spacing: 6

        Text {
            text: "Presets"
            color: textColor
            font.pixelSize: 11
            font.bold: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Text {
                text: "Saved"
                color: mutedColor
                font.pixelSize: 11
                Layout.preferredWidth: 42
            }
            AppComboBox {
                id: presetCombo
                Layout.fillWidth: true
                implicitHeight: root.compactControlHeight
                font.pixelSize: 11
                model: root.presetNames
                currentIndex: Math.max(0, model.indexOf(root.selectedPresetName))
                onActivated: {
                    root.setSelectedPresetName(currentText)
                    presetNameField.text = currentText
                }
            }
        }

        AppTextField {
            id: presetNameField
            Layout.fillWidth: true
            implicitHeight: root.compactControlHeight
            font.pixelSize: 11
            placeholderText: "preset name"
            text: root.selectedPresetName
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            AppButton {
                text: "Save"
                Layout.fillWidth: true
                implicitHeight: root.compactControlHeight
                fontPixelSize: 11
                onClicked: {
                    var name = presetNameField.text.trim()
                    if (!name.length && presetCombo.currentText) {
                        name = String(presetCombo.currentText).trim()
                    }
                    root.savePreset(name)
                    presetNameField.text = name
                }
            }
            AppButton {
                text: "Load"
                Layout.fillWidth: true
                implicitHeight: root.compactControlHeight
                font.pixelSize: 11
                enabled: presetNameField.text.trim().length > 0 || String(presetCombo.currentText || "").trim().length > 0
                onClicked: {
                    var name = presetNameField.text.trim()
                    if (!name.length && presetCombo.currentText) {
                        name = String(presetCombo.currentText).trim()
                    }
                    root.loadPreset(name)
                    presetNameField.text = name
                }
            }
            AppButton {
                text: "Del"
                Layout.fillWidth: true
                implicitHeight: root.compactControlHeight
                font.pixelSize: 11
                enabled: presetNameField.text.trim().length > 0 || String(presetCombo.currentText || "").trim().length > 0
                onClicked: {
                    var name = presetNameField.text.trim()
                    if (!name.length && presetCombo.currentText) {
                        name = String(presetCombo.currentText).trim()
                    }
                    root.deletePreset(name)
                    presetNameField.text = name
                }
            }
        }
    }
}
