import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme access

/**
 * Icon - Consistent icon component with color and size control
 *
 * Features:
 * - Text-based icons (unicode/special characters)
 * - Configurable size and color
 * - Predefined icon names for consistency
 * - Rotation support
 * - Opacity control
 *
 * Usage:
 *   Icon {
 *       name: "close"
 *       size: 16
 *       color: theme.textPrimary
 *   }
 *
 * Available icons:
 * - close: ×
 * - check: ✓
 * - warning: ⚠
 * - error: ✕
 * - info: ℹ
 * - sortUp: ▲
 * - sortDown: ▼
 * - sort: ⇅
 * - plus: +
 * - minus: −
 * - arrowRight: →
 * - arrowLeft: ←
 * - arrowDown: ▼
 * - arrowUp: ▲
 * - dots: ⋯
 * - copy: ⧉
 * - refresh: ↻
 * - settings: ⚙
 */
Text {
    id: root

    // Public properties
    property string name: ""
    property int size: theme.iconSizeMd
    property real rotation: 0
    // Icon character mapping
    readonly property var iconChars: {
        "close": "\u00D7",           // ×
        "check": "\u2713",           // ✓
        "warning": "\u26A0",         // ⚠
        "error": "\u2715",           // ✕
        "info": "\u2139",            // ℹ
        "sortUp": "\u25B2",          // ▲
        "sortDown": "\u25BC",        // ▼
        "sort": "\u21C5",            // ⇅
        "plus": "\u002B",            // +
        "minus": "\u2212",           // −
        "arrowRight": "\u2192",      // →
        "arrowLeft": "\u2190",       // ←
        "arrowDown": "\u25BC",       // ▼
        "arrowUp": "\u25B2",         // ▲
        "dots": "\u22EF",            // ⋯
        "copy": "\u22C9",            // ⧉
        "refresh": "\u21BB",         // ↻
        "settings": "\u2699",        // ⚙
        "menu": "\u2630",            // ☰
        "search": "\u2315",          // ⌕
        "star": "\u2605",            // ★
        "heart": "\u2665",           // ♥
        "bookmark": "\u2316",         // ⌖
    }

    // Access to theme
    property var theme: Theme {}

    // Set text content from icon name
    text: iconChars[name] || name

    // Apply styling
    font.pixelSize: size
    color: theme.textPrimary
    font.bold: false
    horizontalAlignment: Text.AlignHCenter
    verticalAlignment: Text.AlignVCenter

    // Smooth transitions
    Behavior on color {
        ColorAnimation {
            duration: 150
            easing.type: Easing.OutCubic
        }
    }

    Behavior on opacity {
        NumberAnimation {
            duration: 150
            easing.type: Easing.OutCubic
        }
    }

    Behavior on rotation {
        NumberAnimation {
            duration: 200
            easing.type: Easing.OutCubic
        }
    }

    // Helper function to get icon character programmatically
    function getIconChar(iconName) {
        return iconChars[iconName] || iconName
    }

    // Helper function to check if icon exists
    function hasIcon(iconName) {
        return iconChars[iconName] !== undefined
    }
}
