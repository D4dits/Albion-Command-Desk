import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../../." // for Theme access

/**
 * ToastManager - Notification manager for displaying toast messages
 */
Item {
    id: root

    // Public properties
    property int maxToasts: 4
    property int defaultDuration: 3000
    property int toastSpacing: 8
    property int toastMargin: 16
    property int toastMinWidth: 260
    property int toastMaxWidth: 420
    property real toastWidthRatio: 0.34
    property bool showProgress: true

    // Access to theme
    property var theme: null

    // Private properties
    property var toasts: []

    // Signal to show a toast (convenience method)
    function show(type, title, message, duration) {
        if (duration === undefined) duration = root.defaultDuration
        addToast(type, title, message, duration)
    }

    // Add a toast notification
    function addToast(type, title, message, duration) {
        // Remove oldest toast if max limit reached
        if (toasts.length >= maxToasts) {
            removeToast(0)
        }

        // Create toast component
        var toast = toastComponent.createObject(root, {
            type: type || "info",
            title: title || "",
            message: message || "",
            duration: duration || root.defaultDuration,
            showProgress: root.showProgress
        })

        toast.width = resolveToastWidth()
        toast.anchors.right = parent.right
        toast.anchors.margins = root.toastMargin
        toast.y = root.height + toast.height
        toast.visible = true

        // Connect dismissed signal
        toast.dismissed.connect(function() {
            removeToast(toasts.indexOf(toast))
        })

        // Add to array
        toasts.push(toast)
        repositionToasts()
    }

    // Remove a toast by index
    function removeToast(index) {
        if (index >= 0 && index < toasts.length) {
            var toast = toasts[index]
            toast.visible = false

            // Destroy toast after animation completes
            removeTimer.createObject(root, {
                toast: toast,
                index: index
            })
        }
    }

    // Reposition all toasts
    function repositionToasts() {
        var totalHeight = root.toastMargin

        for (var i = toasts.length - 1; i >= 0; i--) {
            var toast = toasts[i]
            var targetY = root.height - totalHeight - toast.height

            // Animate to new position
            toast.y = Qt.binding(function() { return targetY })
            totalHeight += toast.height + root.toastSpacing
        }
    }

    function resolveToastWidth() {
        var maxAllowed = Math.max(160, root.width - (root.toastMargin * 2))
        var preferred = Math.max(root.toastMinWidth, Math.round(root.width * root.toastWidthRatio))
        return Math.max(160, Math.min(root.toastMaxWidth, Math.min(maxAllowed, preferred)))
    }

    function refreshToastGeometry() {
        var w = resolveToastWidth()
        for (var i = 0; i < toasts.length; i++) {
            toasts[i].width = w
        }
        repositionToasts()
    }

    onWidthChanged: refreshToastGeometry()
    onHeightChanged: repositionToasts()

    // Component for creating toasts
    Component {
        id: toastComponent
        Toast {}
    }

    // Component for delayed removal
    Component {
        id: removeTimer
        Timer {
            id: timer
            interval: 200
            property var toast: null
            property int index: -1
            onTriggered: {
                if (toast) {
                    toast.destroy()
                    toasts.splice(index, 1)
                }
            }
        }
    }

    // Convenience methods for different toast types
    function showSuccess(title, message, duration) {
        show("success", title, message, duration)
    }

    function showWarning(title, message, duration) {
        show("warning", title, message, duration)
    }

    function showError(title, message, duration) {
        show("error", title, message, duration)
    }

    function showInfo(title, message, duration) {
        show("info", title, message, duration)
    }

    // Clear all toasts
    function clearAll() {
        for (var i = toasts.length - 1; i >= 0; i--) {
            removeToast(i)
        }
    }
}
