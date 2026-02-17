import QtQuick 2.15
import QtQuick.Layouts 1.15
import "." // for AppButton access

/**
 * SupportButtons - PayPal and Buy Me a Coffee donation buttons
 *
 * Provides two donation buttons:
 * - PayPal button
 * - Buy Me a Coffee button
 */
RowLayout {
    id: root
    spacing: 8

    // Layout properties
    property int spacingOverride: 8

    // Button labels (responsive to narrow layout)
    property string payPalLabel: "PayPal"
    property string coffeeLabel: "Buy me a coffee"
    property int payPalWidth: 118
    property int coffeeWidth: 146
    property int buttonHeight: 28

    // Access to theme
    property var theme: Theme {}

    spacing: root.spacingOverride

    AppButton {
        id: headerPayPalButton
        text: root.payPalLabel
        variant: "primary"
        compact: true
        implicitHeight: root.buttonHeight
        implicitWidth: root.payPalWidth
        onClicked: Qt.openUrlExternally("https://www.paypal.com/donate/?business=albiosuperacc%40linuxmail.org&currency_code=USD&amount=20.00")
    }
    AppButton {
        id: headerCoffeeButton
        text: root.coffeeLabel
        variant: "warm"
        compact: true
        implicitHeight: root.buttonHeight
        implicitWidth: root.coffeeWidth
        onClicked: Qt.openUrlExternally("https://buycoffee.to/ao-dps/")
    }
}
