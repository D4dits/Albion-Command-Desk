import QtQuick 2.15
import QtQuick.Layouts 1.15
import "." // for AppButton access

/**
 * UpdateBanner - Update notification banner with Open/Dismiss buttons
 *
 * Displays:
 * - Update message text
 * - Open button to navigate to update URL
 * - Dismiss button to hide banner
 * - Animated show/hide
 */
Rectangle {
    id: root
    visible: true
    opacity: bannerVisible ? 1.0 : 0.0
    enabled: bannerVisible

    // Properties
    property bool bannerVisible: false
    property string bannerText: ""
    property string bannerUrl: ""
    property string bannerNotesUrl: ""
    property int minWidth: 270
    property int maxWidth: 420
    property int bannerHeight: 32
    property int availableWidth: 0
    readonly property string shortBannerText: {
        var text = String(root.bannerText || "").trim()
        if (text.length === 0) {
            return "Update available"
        }
        var versions = text.match(/v?\d+\.\d+\.\d+/g)
        if (versions && versions.length >= 2) {
            return versions[0] + " -> " + versions[versions.length - 1]
        }
        return text.replace(/^Update available:\s*/i, "Update: ")
    }

    // Signals
    signal dismissBanner()

    // Access to theme
    property var theme: null

    // Computed width
    Layout.preferredWidth: Math.max(minWidth, Math.min(maxWidth, availableWidth * 0.34))
    Layout.preferredHeight: bannerHeight
    radius: theme.shellPillRadius
    color: theme.shellBannerBackground
    border.color: theme.shellBannerBorder

    Behavior on opacity {
        NumberAnimation {
            duration: 180
            easing.type: Easing.OutCubic
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 6
        spacing: 6

        Text {
            Layout.fillWidth: true
            text: root.shortBannerText
            color: theme.shellBannerText
            font.pixelSize: 12
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
        }

        AppButton {
            id: updateOpenButton
            text: "Install"
            variant: "primary"
            compact: true
            implicitHeight: theme.shellActionHeight
            implicitWidth: 62
            onClicked: {
                if (root.bannerUrl.length > 0) {
                    Qt.openUrlExternally(root.bannerUrl)
                }
            }
        }

        AppButton {
            id: updateNotesButton
            visible: root.bannerNotesUrl.length > 0
            text: "Notes"
            variant: "secondary"
            compact: true
            implicitHeight: theme.shellActionHeight
            implicitWidth: 56
            onClicked: {
                if (root.bannerNotesUrl.length > 0) {
                    Qt.openUrlExternally(root.bannerNotesUrl)
                }
            }
        }

        AppButton {
            id: updateDismissButton
            text: "x"
            variant: "ghost"
            compact: true
            implicitHeight: theme.shellActionHeight
            implicitWidth: 28
            onClicked: root.dismissBanner()
        }
    }
}
