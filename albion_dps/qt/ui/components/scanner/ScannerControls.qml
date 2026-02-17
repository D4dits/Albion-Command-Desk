import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../." // for AppButton access

/**
 * ScannerControls - Action buttons bar for scanner operations
 *
 * Provides buttons for:
 * - Check updates
 * - Sync repo
 * - Start scanner
 * - Start scanner (sudo)
 * - Stop scanner
 * - Clear log
 */
Flow {
    id: root
    Layout.fillWidth: true
    spacing: 8

    // Scanner state flags
    property bool scannerRunning: false

    // Signals to notify parent of actions
    signal checkForUpdates()
    signal syncClientRepo()
    signal startScanner()
    signal startScannerSudo()
    signal stopScanner()
    signal clearLog()

    AppButton {
        text: "Check updates"
        compact: true
        onClicked: root.checkForUpdates()
    }
    AppButton {
        text: "Sync repo"
        compact: true
        onClicked: root.syncClientRepo()
    }
    AppButton {
        text: "Start scanner"
        compact: true
        enabled: !root.scannerRunning
        onClicked: root.startScanner()
    }
    AppButton {
        text: "Start scanner (sudo)"
        compact: true
        enabled: !root.scannerRunning
        onClicked: root.startScannerSudo()
    }
    AppButton {
        text: "Stop scanner"
        compact: true
        enabled: root.scannerRunning
        onClicked: root.stopScanner()
    }
    AppButton {
        text: "Clear log"
        compact: true
        onClicked: root.clearLog()
    }
}
