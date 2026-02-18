#!/bin/bash
# Albion Command Desk - Linux Package Build Script
# Creates .deb and .rpm packages

set -e

APP_NAME="albion-command-desk"
APP_VERSION="1.0.0"
DIST_DIR="../../dist"
BUILD_DIR="build"
DEB_DIR="$BUILD_DIR/deb"
RPM_DIR="$BUILD_DIR/rpm"

echo "Building Linux packages for $APP_NAME v$APP_VERSION..."

# Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$DEB_DIR" "$RPM_DIR"

# Check if PyInstaller build exists
if [ ! -f "$DIST_DIR/albion-command-desk" ]; then
    echo "Error: PyInstaller build not found at $DIST_DIR/albion-command-desk"
    echo "Please run: pyinstaller albion_dps/cli.py --onefile --name albion-command-desk"
    exit 1
fi

# ============================================
# Build .deb package
# ============================================
echo "Creating .deb package..."

DEB_ROOT="$DEB_DIR/$APP_NAME"
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/usr/share/applications"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_ROOT/usr/share/doc/$APP_NAME"

# Copy executable
cp "$DIST_DIR/albion-command-desk" "$DEB_ROOT/usr/bin/"
chmod +x "$DEB_ROOT/usr/bin/albion-command-desk"

# Copy desktop entry
cat > "$DEB_ROOT/usr/share/applications/$APP_NAME.desktop" <<EOF
[Desktop Entry]
Name=Albion Command Desk
Comment=DPS meter and crafting calculator for Albion Online
Exec=/usr/bin/albion-command-desk
Icon=albion-command-desk
Terminal=false
Type=Application
Categories=Game;Utility;
StartupNotify=true
EOF

# Copy icon
cp "../../albion_dps/qt/ui/command_desk_icon.png" "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"

# Create control file
cat > "$DEB_ROOT/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $APP_VERSION
Architecture: amd64
Maintainer: Albion Command Desk <noreply@example.com>
Depends: libpcap0.8, libqt6gui6, libqt6widgets6, libqt6network6
Section: games
Priority: optional
Homepage: https://github.com/albioncommanddesk
Description: DPS meter and crafting calculator for Albion Online
 Albion Command Desk is a comprehensive tool for Albion Online players,
 featuring a real-time DPS meter, market crafting workspace, and
 scanner functionality.
EOF

# Create conffiles (empty for now)
touch "$DEB_ROOT/DEBIAN/conffiles"

# Create postinst script
cat > "$DEB_ROOT/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e

# Set capabilities for packet capture (requires sudo)
echo "Setting capabilities for packet capture..."
if command -v setcap &> /dev/null; then
    if sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/albion-command-desk 2>/dev/null; then
        echo "Capabilities set successfully. The scanner can now run without sudo."
        echo "If you still get permission errors, run: sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/albion-command-desk"
    else
        echo "Warning: Could not set capabilities. You may need to run the scanner with sudo."
    fi
else
    echo "Warning: setcap not found. Scanner may require sudo to run."
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications || true
fi

exit 0
EOF
chmod 755 "$DEB_ROOT/DEBIAN/postinst"

# Create postrm script
cat > "$DEB_ROOT/DEBIAN/postrm" <<'EOF'
#!/bin/bash
set -e

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications || true
fi

exit 0
EOF
chmod 755 "$DEB_ROOT/DEBIAN/postrm"

# Calculate installed size
INSTALLED_SIZE=$(du -sk "$DEB_ROOT" | cut -f1)
echo "Installed-Size: $INSTALLED_SIZE" >> "$DEB_ROOT/DEBIAN/control"

# Build .deb
dpkg-deb --build "$DEB_ROOT" "$APP_NAME-${APP_VERSION}_amd64.deb"
echo "Created .deb package: $APP_NAME-${APP_VERSION}_amd64.deb"

# ============================================
# Build .rpm package (using alien or rpmbuild)
# ============================================
echo "Creating .rpm package..."

# Try using alien first (easier)
if command -v alien &> /dev/null; then
    alien --to-rpm --scripts "$APP_NAME-${APP_VERSION}_amd64.deb"
    echo "Created .rpm package using alien"
elif command -v rpmbuild &> /dev/null; then
    # Create RPM using rpmbuild
    RPM_ROOT="$RPM_DIR/rpmbuild"
    mkdir -p "$RPM_ROOT/SOURCES"
    mkdir -p "$RPM_ROOT/SPECS"
    mkdir -p "$RPM_ROOT/BUILD"
    mkdir -p "$RPM_ROOT/RPMS"
    mkdir -p "$RPM_ROOT/SRPMS"

    # Create spec file
    cat > "$RPM_ROOT/SPECS/$APP_NAME.spec" <<EOF
Name:           $APP_NAME
Version:        $APP_VERSION
Release:        1%{?dist}
Summary:        DPS meter and crafting calculator for Albion Online
License:        MIT
URL:            https://github.com/albioncommanddesk
Source0:        %{name}-%{version}.tar.gz

Requires:       libpcap, qt6-qtbase-gui, qt6-qtbase-network

%description
Albion Command Desk is a comprehensive tool for Albion Online players,
featuring a real-time DPS meter, market crafting workspace, and
scanner functionality.

%prep
%setup -q

%build
# No build needed, using pre-built binary

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps

install -m 755 ../../dist/albion-command-desk %{buildroot}/usr/bin/
install -m 644 ../$APP_NAME.desktop %{buildroot}/usr/share/applications/
install -m 644 ../../albion_dps/qt/ui/command_desk_icon.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png

%post
# Set capabilities for packet capture
if command -v setcap &> /dev/null; then
    setcap cap_net_raw,cap_net_admin=eip /usr/bin/albion-command-desk 2>/dev/null || true
fi

if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications || true
fi

%postun
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database -q /usr/share/applications || true
fi

%files
/usr/bin/albion-command-desk
/usr/share/applications/$APP_NAME.desktop
/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png

%changelog
* $(date +'%a %b %d %Y') Builder <noreply@example.com> - $APP_VERSION-1
- Initial package
EOF

    # Build RPM
    rpmbuild --define "_topdir $RPM_ROOT" -ba "$RPM_ROOT/SPECS/$APP_NAME.spec"
    cp "$RPM_ROOT/RPMS/x86_64/$APP_NAME-$APP_VERSION-1.*.rpm" .
    echo "Created .rpm package"
else
    echo "Warning: Neither alien nor rpmbuild found. Skipping .rpm creation."
    echo "To create .rpm packages, install: sudo apt-get install alien or rpmbuild"
fi

echo ""
echo "============================================"
echo "Linux package build complete!"
echo "============================================"
echo "Created files:"
ls -lh *.deb *.rpm 2>/dev/null || true
echo ""
echo "Install .deb: sudo dpkg -i $APP_NAME-${APP_VERSION}_amd64.deb"
echo "Install .rpm: sudo rpm -i $APP_NAME-${APP_VERSION}-1.*.rpm"
