# Cross-Platform Support

## Overview

Albion Command Desk supports Windows, Linux, and macOS with platform-specific considerations.

## Supported Platforms

| Platform | Status | Packet Capture | Notes |
|----------|--------|----------------|-------|
| Windows 10/11 | ✅ Fully Supported | Npcap | Requires Npcap installation |
| Linux (Ubuntu/Debian) | ✅ Supported | libpcap | May require sudo |
| macOS 11+ | ✅ Supported | Native | May require sudo permissions |

## Platform-Specific Configuration

### Windows

**Requirements:**
- Windows 10 or later
- Npcap (installed with NPcap installer)

**Npcap Installation:**
1. Download from: https://npcap.com/
2. Install with default options
3. Ensure "Support raw 802.11 traffic" is unchecked (not needed for Albion)

**Running:**
- No special permissions required
- Scanner works out of the box

### Linux

**Requirements:**
- Ubuntu 20.04+ / Debian 11+ or similar
- libpcap-dev

**Installation:**
```bash
sudo apt-get update
sudo apt-get install libpcap-dev python3-pip
pip install -r requirements.txt
```

**Running Scanner:**
- Requires sudo/root for packet capture:
```bash
sudo python -m albion_dps.cli
```

**Alternative (setcap):**
```bash
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3
# Now can run without sudo:
python -m albion_dps.cli
```

### macOS

**Requirements:**
- macOS 11 (Big Sur) or later
- Xcode Command Line Tools

**Installation:**
```bash
# Install Command Line Tools
xcode-select --install

# Install Python dependencies
pip3 install -r requirements.txt
```

**Running Scanner:**
- Requires sudo for packet capture:
```bash
sudo python3 -m albion_dps.cli
```

**Note:** macOS may prompt for security permissions on first run.

## UI Platform Adjustments

The application automatically adapts to:

### Screen Size Breakpoints
- **Desktop**: >1320px (full layout)
- **Compact**: 1160px-1320px (condensed controls)
- **Narrow**: <1160px (stacked layout)

### Platform Detection

The UI uses Qt's built-in platform detection:

```qml
// Example platform-specific behavior
property bool isWindows: Qt.platform.os === "windows"
property bool isLinux: Qt.platform.os === "linux"
property bool isMacOS: Qt.platform.os === "osx"

// Platform-specific settings
readonly property int platformWindowFlags: {
    if (isWindows) return Qt.Window | Qt.WindowsDefaultButton
    if (isMacOS) return Qt.Window | Qt.WindowFullscreenButtonHint
    return Qt.Window
}
```

### Font Scaling

Text rendering adapts to platform DPI settings:

```qml
font.pixelSize: 12 * (Qt.styleHints.showShortLabelsInContextMenus ? 0.9 : 1.0)
```

### Native Integration

**Windows:**
- Native window frames
- Taskbar integration
- System tray (optional)

**Linux:**
- Follows GTK theme conventions
- Supports Wayland and X11

**macOS:**
- Native fullscreen mode
- Menu bar integration
- Touch Bar support (future)

## Common Issues

### Windows: Scanner Not Working
1. Verify Npcap is installed: Check "Npcap" in installed programs
2. Run installer again with "Install Npcap in WinPcap API-compatible Mode"
3. Restart application

### Linux: Permission Denied
```bash
# Error: Permission denied when capturing packets
# Solution 1: Run with sudo
sudo python -m albion_dps.cli

# Solution 2: Set capabilities (permanent)
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

### macOS: Security Blocked
1. Go to System Preferences > Security & Privacy
2. Allow the application in "Security" section
3. Or run: `sudo python3 -m albion_dps.cli`

## Building for Distribution

### Windows (PyInstaller)
```bash
# Create standalone executable
pyinstaller --onefile --windowed \
  --icon=albion_dps/qt/ui/command_desk_icon.ico \
  --add-data "albion_dps/qt/ui;albion_dps/qt/ui" \
  --name "AlbionCommandDesk" \
  albion_dps/cli.py
```

### Linux (PyInstaller)
```bash
pyinstaller --onefile --windowed \
  --icon=albion_dps/qt/ui/command_desk_icon.png \
  --add-data "albion_dps/qt/ui:albion_dps/qt/ui" \
  --name "albion-command-desk" \
  albion_dps/cli.py
```

### macOS (PyInstaller + create-dmg)
```bash
# Build .app bundle
pyinstaller --windowed \
  --icon=albion_dps/qt/ui/command_desk_icon.icns \
  --add-data "albion_dps/qt/ui:albion_dps/qt/ui" \
  --name "AlbionCommandDesk" \
  --osx-bundle-identifier com.albion.commanddesk \
  albion_dps/cli.py

# Create DMG (optional)
hdiutil create -volname "Albion Command Desk" \
  -srcfolder dist/AlbionCommandDesk.app \
  -ov -format UDZO \
  AlbionCommandDesk.dmg
```

## Testing Checklist

Before releasing, test on:

### Windows
- [ ] Installation on clean Windows 10/11
- [ ] Npcap detection and installation prompt
- [ ] Scanner captures packets correctly
- [ ] DPI scaling (125%, 150%, 200%)
- [ ] Dark mode appearance
- [ ] Window minimize/maximize/close

### Linux
- [ ] Installation on Ubuntu 20.04/22.04
- [ ] Scanner with sudo works
- [ ] Scanner with setcap works
- [ ] Wayland display server compatibility
- [ ] X11 display server compatibility
- [ ] HiDPI display support

### macOS
- [ ] Installation on macOS 11/12/13
- [ ] Security prompt handling
- [ ] Scanner with sudo works
- [ ] Native fullscreen mode
- [ ] Retina display rendering
- [ ] Menu bar appearance

## Platform-Specific Files

```
albion_dps/
├── qt/
│   └── ui/
│       ├── command_desk_icon.ico    # Windows icon
│       ├── command_desk_icon.png    # Linux icon
│       └── command_desk_icon.icns   # macOS icon (generate from .png)
```

### Generating .icns for macOS

```bash
# Install iconutil (comes with Xcode)
# Create iconset folder
mkdir command_desk_icon.iconset

# Convert PNG to multiple sizes
sips -z 16 16     command_desk_icon.png --out command_desk_icon.iconset/icon_16x16.png
sips -z 32 32     command_desk_icon.png --out command_desk_icon.iconset/icon_16x16@2x.png
sips -z 32 32     command_desk_icon.png --out command_desk_icon.iconset/icon_32x32.png
sips -z 64 64     command_desk_icon.png --out command_desk_icon.iconset/icon_32x32@2x.png
sips -z 128 128   command_desk_icon.png --out command_desk_icon.iconset/icon_128x128.png
sips -z 256 256   command_desk_icon.png --out command_desk_icon.iconset/icon_128x128@2x.png
sips -z 256 256   command_desk_icon.png --out command_desk_icon.iconset/icon_256x256.png
sips -z 512 512   command_desk_icon.png --out command_desk_icon.iconset/icon_256x256@2x.png
sips -z 512 512   command_desk_icon.png --out command_desk_icon.iconset/icon_512x512.png
sips -z 1024 1024 command_desk_icon.png --out command_desk_icon.iconset/icon_512x512@2x.png

# Create .icns
iconutil -c icns command_desk_icon.iconset
```
