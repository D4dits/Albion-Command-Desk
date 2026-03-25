# Responsive Layout Plan

This phase defines the supported shell contract for Albion Command Desk and
prevents accidental layout breakage on undersized windows.

## Supported window contract

- Default window: `1240 x 820`
- Minimum supported window: `1180 x 760`
- Compact breakpoint: `< 1320`
- Narrow breakpoint: `< 1160`
- Stacked/mobile-style fallback: `< 980`

## Rules

1. `Theme.qml` owns the shell geometry contract.
2. `Main.qml` consumes tokens instead of hardcoded dimensions.
3. Tabs must degrade cleanly inside the supported minimum size.
4. Unsupported widths should be blocked by minimum window constraints, not left
   to render broken layouts.

## Phase 8 execution order

1. `PH8-UXR-080` - supported window contract
2. `PH8-UXR-081` - Start tab compact redesign
3. `PH8-UXR-082` - Meter adaptive layout redesign
4. `PH8-UXR-083` - Market containment pass
5. `PH8-UXR-084` - Scanner/Settings/Help consistency
6. `PH8-UXR-085` - Header/update CTA redesign
