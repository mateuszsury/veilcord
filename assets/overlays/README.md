# AR Overlay Assets

This directory contains PNG images with alpha channels for AR face overlays.

## File Format

- **Format:** PNG with alpha channel (RGBA)
- **Recommended Dimensions:** 512x512 pixels or larger
- **Bit Depth:** 8-bit per channel (32-bit total)

## Naming Convention

Built-in overlays use the following naming:

- `glasses_round.png` - Round frame glasses
- `glasses_aviator.png` - Aviator style glasses
- `sunglasses_black.png` - Dark sunglasses
- `party_hat.png` - Colorful party hat
- `crown.png` - Gold crown
- `mask_venetian.png` - Venetian masquerade mask
- `cat_ears.png` - Cat ears
- `dog_filter.png` - Dog face filter

## Custom Overlays

To add custom overlays:

1. Create a PNG image with transparent background
2. Save to this directory with descriptive name
3. Use `AROverlay(OverlayType.CUSTOM, "path/to/your/overlay.png")`
4. Optionally configure anchor points via `OverlayAnchor` dataclass

## Anchor Points

Overlays are positioned using MediaPipe Face Mesh landmarks (0-477):

- **Eyes:** Landmarks 33 (left), 263 (right)
- **Forehead:** Landmark 10
- **Nose tip:** Landmark 1
- **Chin:** Landmark 152
- **Ears:** Landmarks 234 (left), 454 (right)

See `src/effects/video/face_tracker.py` for complete landmark reference.

## Testing Without Assets

If overlay files are missing, the system automatically generates colored placeholder shapes for testing.
