"""
presets.py
----------
Curated parameter combinations that approximate the look of classic
pixel-art eras. These are stylistic presets (not exact hardware palette
emulation) tuned to give a recognizable retro feel with this app's
pipeline (pixel size, color count, dithering, and pre-pixelization
brightness/contrast/saturation/sharpness adjustments).
"""

from typing import Optional

# Every preset defines the full set of sliders it controls.
# "Custom" is intentionally excluded here - it means "leave whatever
# the user has already set alone".
STYLE_PRESETS = {
    "Classic Gameboy": {
        "pixel_size": 6,
        "color_count": 4,
        "dither": True,
        "brightness": 1.0,
        "contrast": 1.3,
        "saturation": 0.15,
        "sharpness": 1.0,
    },
    "NES Retro": {
        "pixel_size": 5,
        "color_count": 25,
        "dither": False,
        "brightness": 1.0,
        "contrast": 1.15,
        "saturation": 1.3,
        "sharpness": 1.1,
    },
    "SNES 16-bit": {
        "pixel_size": 4,
        "color_count": 32,
        "dither": False,
        "brightness": 1.0,
        "contrast": 1.05,
        "saturation": 1.15,
        "sharpness": 1.0,
    },
    "Modern Pixel Art": {
        "pixel_size": 6,
        "color_count": 48,
        "dither": False,
        "brightness": 1.0,
        "contrast": 1.0,
        "saturation": 1.05,
        "sharpness": 1.05,
    },
    "Minimal 8-color": {
        "pixel_size": 10,
        "color_count": 8,
        "dither": True,
        "brightness": 1.0,
        "contrast": 1.2,
        "saturation": 1.1,
        "sharpness": 1.0,
    },
    "Arcade Style": {
        "pixel_size": 8,
        "color_count": 16,
        "dither": True,
        "brightness": 1.0,
        "contrast": 1.25,
        "saturation": 1.3,
        "sharpness": 1.1,
    },
}

PRESET_NAMES = ["Custom"] + list(STYLE_PRESETS.keys())


def get_preset(name: str) -> Optional[dict]:
    """Return the parameter dict for a preset name, or None for 'Custom'."""
    return STYLE_PRESETS.get(name)
