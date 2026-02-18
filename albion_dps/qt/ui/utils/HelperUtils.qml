pragma Singleton
import QtQuick 2.15

/**
 * HelperUtils - Collection of utility functions for the application
 *
 * Provides helper functions for:
 * - Color calculations
 * - Text formatting
 * - Item label processing
 */
QtObject {
    /**
     * Format integer with thousands separator (space)
     */
    function formatInt(value) {
        var n = Number(value)
        if (!isFinite(n)) return "0"
        var whole = Math.round(n)
        var sign = whole < 0 ? "-" : ""
        var raw = Math.abs(whole).toString()
        return sign + raw.replace(/\B(?=(\d{3})+(?!\d))/g, " ")
    }

    /**
     * Format fixed-point number with thousands separator
     */
    function formatFixed(value, decimals) {
        var n = Number(value)
        if (!isFinite(n)) {
            n = 0
        }
        var fixed = n.toFixed(Math.max(0, decimals))
        var parts = fixed.split(".")
        var whole = Number(parts[0] || "0")
        if (parts.length === 1 || decimals <= 0) {
            return formatInt(whole)
        }
        return formatInt(whole) + "." + parts[1]
    }

    /**
     * Get color for data source (live/cache/manual)
     */
    function sourceColor(source, theme, mutedColor) {
        if (source === "manual") {
            return theme.stateWarning
        }
        if (source === "live" || source === "cache") {
            return theme.stateSuccess
        }
        return mutedColor
    }

    /**
     * Get table row color (even/odd)
     */
    function tableRowColor(index, theme) {
        return index % 2 === 0 ? theme.tableRowEven : theme.tableRowOdd
    }

    /**
     * Get strong table row color (for interactive rows)
     */
    function tableRowStrongColor(index, theme) {
        return index % 2 === 0 ? theme.surfaceInteractive : theme.tableRowEven
    }

    /**
     * Format item label with tier and enchant from itemId
     * Extracts tier from itemId pattern (e.g., "T4_SWORD@1" or "T4_SWORD_LEVEL1")
     */
    function itemLabelWithTier(labelValue, itemIdValue) {
        var label = String(labelValue || "").trim()
        var itemId = String(itemIdValue || "").trim().toUpperCase()
        if (itemId.length === 0) {
            return label
        }
        var tierMatch = itemId.match(/^T(\d+)_/)
        if (!tierMatch) {
            return label
        }
        var tier = parseInt(tierMatch[1], 10)
        if (!isFinite(tier) || tier <= 0) {
            return label
        }
        var enchant = 0
        var enchantMatch = itemId.match(/@(\d+)$/)
        if (enchantMatch) {
            enchant = parseInt(enchantMatch[1], 10)
            if (!isFinite(enchant) || enchant < 0) {
                enchant = 0
            }
        } else {
            var levelMatch = itemId.match(/_LEVEL(\d+)$/)
            if (levelMatch) {
                enchant = parseInt(levelMatch[1], 10)
                if (!isFinite(enchant) || enchant < 0) {
                    enchant = 0
                }
            }
        }
        var suffix = enchant > 0 ? (" T" + tier + "." + enchant) : (" T" + tier)
        if (label.length === 0) {
            return suffix.trim()
        }
        var withoutTier = label.replace(/\s+(?:T?\d+(?:\.\d+)?)\s*$/i, "").trim()
        if (withoutTier.length === 0) {
            withoutTier = label
        }
        return withoutTier + suffix
    }

    /**
     * Format item label with tier and enchant from separate values
     */
    function itemLabelWithTierParts(labelValue, tierValue, enchantValue) {
        var label = String(labelValue || "").trim()
        var tier = parseInt(tierValue, 10)
        if (!isFinite(tier) || tier <= 0) {
            return label
        }
        var enchant = parseInt(enchantValue, 10)
        if (!isFinite(enchant) || enchant < 0) {
            enchant = 0
        }
        var suffix = enchant > 0 ? (" T" + tier + "." + enchant) : (" T" + tier)
        if (label.length === 0) {
            return suffix.trim()
        }
        var withoutTier = label.replace(/\s+(?:T?\d+(?:\.\d+)?)\s*$/i, "").trim()
        if (withoutTier.length === 0) {
            withoutTier = label
        }
        return withoutTier + suffix
    }
}
