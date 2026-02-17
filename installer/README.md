# Installer Creation Guide

This directory contains scripts and configurations for building installers for all supported platforms.

## Platform-Specific Installers

### Windows (NSIS)
- **Script**: `windows/installer.nsi`
- **Output**: `AlbionCommandDesk-Setup-1.0.0.exe`
- **Requirements**: NSIS 3.0+ from https://nsis.sourceforge.io/

**Building:**
```bash
cd installer/windows
# First build the PyInstaller executable
pyinstaller --onefile --windowed ^
  --icon=../../albion_dps/qt/ui/command_desk_icon.ico ^
  --add-data "../../albion_dps/qt/ui;albion_dps/qt/ui" ^
  --name "AlbionCommandDesk" ^
  ../../../albion_dps/cli.py

# Build the installer
makensis installer.nsi
```

**Installer Features:**
- Main application files
- Optional Npcap installation (required for scanner)
- Optional auto-start on boot
- Start Menu shortcuts
- Desktop shortcut
- Uninstaller

### Linux (.deb and .rpm)
- **Script**: `linux/build.sh`
- **Output**: `albion-command-desk-1.0.0_amd64.deb`, `.rpm`
- **Requirements**: dpkg-deb, alien (or rpmbuild)

**Building:**
```bash
cd installer/linux
chmod +x build.sh
./build.sh
```

**Package Features:**
- System-wide installation to `/usr/bin`
- Desktop entry with icon
- Automatic capability setting for packet capture (sudo or setcap)
- Menu integration
- Uninstall support

### macOS (.dmg)
- **Script**: `macos/build.sh`
- **Output**: `AlbionCommandDesk-1.0.0-macOS.dmg`
- **Requirements**: Xcode Command Line Tools, PyInstaller

**Building:**
```bash
cd installer/macos
chmod +x build.sh
./build.sh
```

**Package Features:**
- Signed .app bundle (if certificate available)
- Drag-and-drop DMG installer
- Proper Info.plist with all metadata
- Retina display support
- Gatekeeper compatibility

## Build Pipeline

### Automated Build Script

Run from project root:

```bash
#!/bin/bash
# build-all.sh - Build all installers

set -e

VERSION="1.0.0"

echo "Building Albion Command Desk v$VERSION installers..."

# Build PyInstaller executable for each platform
case "$(uname -s)" in
    Linux*)     ./installer/linux/build.sh ;;
    Darwin*)    ./installer/macos/build.sh ;;
    MINGW*|MSYS*|CYGWIN*)
                cd installer/windows
                makensis installer.nsi
                ;;
    *)          echo "Unsupported platform" ;;
esac

echo "All installers built successfully!"
```

## Pre-Flight Checklist

Before building installers:

1. **Update version numbers** in:
   - `windows/installer.nsi` (APP_VERSION)
   - `linux/build.sh` (APP_VERSION)
   - `macos/build.sh` (APP_VERSION)
   - Main application version

2. **Test the application**:
   - All features work correctly
   - No console errors
   - Scanner works with packet capture

3. **Prepare assets**:
   - `command_desk_icon.ico` (Windows)
   - `command_desk_icon.png` (Linux)
   - `command_desk_icon.icns` (macOS - generate from PNG)

4. **Dependencies verified**:
   - All required libraries included
   - Qt plugins bundled
   - Theme files included

## Post-Build Testing

### Windows
- [ ] Install on clean Windows 10/11
- [ ] Npcap installation prompt works
- [ ] Scanner functions correctly
- [ ] Uninstall removes all files

### Linux
- [ ] Install on Ubuntu/Debian
- [ ] Desktop entry appears in menu
- [ ] Scanner works with setcap or sudo
- [ ] Uninstall works via package manager

### macOS
- [ ] DMG opens and shows app
- [ ] Drag to Applications works
- [ ] App launches (may need right-click Open first time)
- [ ] Scanner works with sudo

## Distribution

### GitHub Releases

Create release with all installers:
```
AlbionCommandDesk-1.0.0-win64.exe      (Windows)
albion-command-desk-1.0.0_amd64.deb    (Linux Debian/Ubuntu)
albion-command-desk-1.0.0-1.x86_64.rpm (Linux Fedora/RHEL)
AlbionCommandDesk-1.0.0-macOS.dmg      (macOS)
```

### Code Signing (Optional)

**Windows:**
```bash
signtool sign /f certificate.pfx /p password /t timestamp_url AlbionCommandDesk-Setup.exe
```

**macOS:**
```bash
codesign --deep --force --verify --verbose \
  --sign 'Developer ID Application: Your Name' \
  AlbionCommandDesk.app
```

**Linux:**
- Sign .deb with debsign
- Sign .rpm with rpmsign

## Troubleshooting

### Windows: Antivirus Flags
- False positives common with PyInstaller
- Submit to VirusTotal for verification
- Consider code signing to reduce flags

### Linux: Permission Issues
```bash
# If scanner doesn't work without sudo
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/albion-command-desk
```

### macOS: "App is damaged" error
```bash
# Remove quarantine attribute
sudo xattr -cr /Applications/AlbionCommandDesk.app
```

## Automated CI/CD

Example GitHub Actions workflow:

```yaml
name: Build Installers

on:
  push:
    tags:
      - 'v*'

jobs:
  windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build NSIS installer
        run: |
          choco install nsis
          pyinstaller albion_dps/cli.py --onefile --windowed
          cd installer/windows
          makensis installer.nsi
      - name: Upload
        uses: actions/upload-artifact@v3
        with:
          name: windows-installer
          path: installer/windows/*.exe

  linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build deb/rpm
        run: |
          cd installer/linux
          ./build.sh
      - name: Upload
        uses: actions/upload-artifact@v3
        with:
          name: linux-packages
          path: installer/linux/*.deb

  macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build DMG
        run: |
          cd installer/macos
          ./build.sh
      - name: Upload
        uses: actions/upload-artifact@v3
        with:
          name: macos-dmg
          path: installer/macos/*.dmg
```
