# UI Assets Documentation

## Overview

The Albion Command Desk UI is designed to minimize asset dependencies by using:
- QML component-based architecture
- Text-based unicode icons (via Icon component)
- Procedural graphics where possible
- Theme tokens for colors and styling

## Current Assets

### Application Icons
Located in `albion_dps/qt/ui/`:

| File | Purpose | Format | Size |
|------|---------|--------|------|
| `command_desk_icon.ico` | Windows application icon | ICO | - |
| `command_desk_icon.png` | Application icon (PNG) | PNG | - |
| `Logo.png` | Application logo | PNG | - |
| `acd.png` | Legacy logo/reference | PNG | - |

## Icon System

The application uses a text-based icon system via the `Icon` component:
- Located in: `components/common/Icon.qml`
- 20+ predefined icon names (close, check, warning, error, info, arrows, etc.)
- Configurable size and color via theme tokens
- Future-ready for SVG replacement if needed

See `Icon.qml` for the complete icon registry.

## Asset Conventions

1. **Prefer Code Over Assets**: Use QML drawing primitives, text, or the Icon component instead of images
2. **Theme Integration**: All visual elements use Theme.qml tokens for consistency
3. **Responsive Scaling**: Use vector-based approaches (QML shapes) rather than raster images
4. **Minimal Bundle**: Keep distribution size small by avoiding unnecessary assets

## Asset Optimization Status

✅ **Already Optimized**:
- UI uses QML components (no raster images needed)
- Icons are text-based unicode characters
- Color theming handled via CSS-like tokens
- No large sprite sheets or icon font files

## Future Considerations

If adding new visual assets:
1. Prefer SVG format for scalability
2. Optimize file size (remove metadata, compress)
3. Consider inlining critical assets
4. Provide fallbacks for asset loading failures
5. Document usage in this file
