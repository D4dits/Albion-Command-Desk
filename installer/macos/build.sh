#!/bin/bash
# Albion Command Desk - macOS Package Build Script
# Creates .app bundle and .dmg installer

set -e

APP_NAME="AlbionCommandDesk"
APP_VERSION="1.0.0"
BUNDLE_ID="com.albion.commanddesk"
DIST_DIR="../../dist"
BUILD_DIR="build"

echo "Building macOS packages for $APP_NAME v$APP_VERSION..."

# Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Check if build exists
if [ ! -d "$DIST_DIR/$APP_NAME.app" ]; then
    echo "Error: .app bundle not found at $DIST_DIR/$APP_NAME.app"
    echo "Please run: pyinstaller --onefile --windowed --name $APP_NAME --osx-bundle-identifier $BUNDLE_ID albion_dps/cli.py"
    exit 1
fi

# ============================================
# Create proper .app bundle structure
# ============================================
echo "Creating .app bundle..."

APP_BUNDLE="$BUILD_DIR/$APP_NAME.app"
CONTENTS="$APP_BUNDLE/Contents"

mkdir -p "$CONTENTS"/{MacOS,Resources,Frameworks}

# Copy executable
cp "$DIST_DIR/$APP_NAME.app/Contents/MacOS/$APP_NAME" "$CONTENTS/MacOS/"
chmod +x "$CONTENTS/MacOS/$APP_NAME"

# Create Info.plist
cat > "$CONTENTS/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleName</key>
    <string>Albion Command Desk</string>
    <key>CFBundleDisplayName</key>
    <string>Albion Command Desk</string>
    <key>CFBundleVersion</key>
    <string>$APP_VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$APP_VERSION</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticTermination</key>
    <true/>
    <key>NSSupportsSuddenTermination</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF

# Copy icon (if .icns exists)
if [ -f "../../albion_dps/qt/ui/command_desk_icon.icns" ]; then
    cp "../../albion_dps/qt/ui/command_desk_icon.icns" "$CONTENTS/Resources/"
    echo "Icon copied to .app bundle"
else
    echo "Warning: command_desk_icon.icns not found. App will use default icon."
    echo "Generate .icns using: iconutil -c icns command_desk_icon.iconset"
fi

# ============================================
# Create DMG installer
# ============================================
echo "Creating DMG installer..."

DMG_NAME="$APP_NAME-$APP_VERSION-macOS.dmg"
VOLUME_NAME="Albion Command Desk"

# Create temporary DMG contents
DMG_DIR="$BUILD_DIR/dmg"
mkdir -p "$DMG_DIR"

# Copy .app to DMG directory
cp -R "$APP_BUNDLE" "$DMG_DIR/"

# Create Applications symlink
ln -s /Applications "$DMG_DIR/Applications"

# Create DMG
hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$DMG_DIR" \
    -ov \
    -format UDZO \
    -imagekey zlib-level=9 \
    "$DMG_NAME"

echo "Created DMG: $DMG_NAME"

# ============================================
# Optional: Create notarized package (for distribution)
# ============================================
echo ""
echo "============================================"
echo "macOS package build complete!"
echo "============================================"
echo "Created files:"
ls -lh "$APP_NAME-$APP_VERSION-macOS.dmg" "$APP_BUNDLE" 2>/dev/null || true
echo ""
echo "To install:"
echo "  1. Double-click $DMG_NAME"
echo "  2. Drag $APP_NAME.app to Applications folder"
echo ""
echo "For first run, you may need to:"
echo "  - Right-click app and select 'Open' (to bypass Gatekeeper)"
echo "  - Or run: sudo xattr -cr /Applications/$APP_NAME.app"
echo ""
echo "For App Store distribution, you'll need to:"
echo "  - Code sign the app"
echo "  - Submit for notarization"
echo "  - Create a stapled DMG"
echo ""
echo "Code signing example (requires Apple Developer account):"
echo "  codesign --deep --force --verify --verbose --sign 'Developer ID Application: Your Name' $APP_BUNDLE"
