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
    property int minWidth: 270
    property int maxWidth: 420
    property int bannerHeight: 32
    property int availableWidth: 0

    // Signals
    signal dismissBanner()

    // Access to theme
    property var theme: null

    // Computed width
    Layout.preferredWidth: Math.max(minWidth, Math.min(maxWidth, availableWidth * 0.24))
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
            text: root.bannerText
            color: theme.shellBannerText
            font.pixelSize: 12
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
        }

        AppButton {
            id: updateOpenButton
            text: "Open"
            variant: "primary"
            compact: true
            implicitHeight: theme.shellActionHeight
            implicitWidth: 54
            onClicked: {
                if (root.bannerUrl.length > 0) {
                    Qt.openUrlExternally(root.bannerUrl)
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
