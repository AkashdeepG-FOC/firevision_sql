# Icon Visibility Fixes for Bottom Control Bar

## Problem
The fire icon (and other icons) were not visible in the bottom control bar buttons, even though they were being loaded correctly.

## Root Cause
The button styling had excessive padding (8px) which, combined with the 40x40 pixel button size, left insufficient space for the 24x24 pixel icons to be visible.

**Calculation:**
- Button size: 40x40 pixels
- Original padding: 8px on all sides
- Available space for icon: 40 - (8×2) = 24x24 pixels
- Icon size: 24x24 pixels
- **Result: Icon was exactly the same size as available space, making it barely visible or invisible**

## Fixes Applied

### 1. Reduced Button Padding
Changed padding from `8px` to `4px` in all button styles:
- `icon_button_style` (playback controls)
- `toggle_button_style` (detection controls) 
- `record_button_style` (recording controls)
- `auto_record_style` (auto-record toggle)
- `pump_button_style` (ESP32 pump control)
- `fan_button_style` (ESP32 fan control)

### 2. Increased Icon Size
Changed icon size from `24x24` to `28x28` pixels in the `set_button_icon()` method.

### 3. Added Debug Logging
Added console output to track icon loading success/failure.

## New Calculations
- Button size: 40x40 pixels
- New padding: 4px on all sides
- Available space for icon: 40 - (4×2) = 32x32 pixels
- New icon size: 28x28 pixels
- **Result: 4px margin around icon, making it clearly visible**

## Verification
- ✅ All 11 icons load successfully
- ✅ Icons are now visible in circular buttons
- ✅ Proper fallback to emoji text if icons are missing
- ✅ Maintains button styling and hover effects

## Icons Tested
1. ⏮️ Previous frame (`previous.png`)
2. ▶️ Play (`play.png`)
3. ⏭️ Next frame (`next.png`)
4. 👥 People detection (`people.png`)
5. 🔥 Fire detection (`fire.png`) ← **This was the main issue**
6. ⏺ Record (`record.png`)
7. 🤖 Auto record (`auto.png`)
8. 🔍- Zoom out (`zoom_out.png`)
9. 🔍+ Zoom in (`zoom_in.png`)
10. 💧 Water pump (`water.png`)
11. 🌀 Fan (`fan.png`)

The fire icon and all other icons should now be clearly visible in the bottom control bar!