"""
pixelizer.py
------------
Turns a (background-removed) RGBA image into clean, crisp pixel art.

Two modes are supported:

- Auto mode (default, matches the original app's behavior): the image
  is downscaled by a `pixel_size` block factor, quantized, and scaled
  back up to (approximately) its original resolution.

- Canvas mode (used by fixed Canvas Size / Sprite Mode): the subject is
  placed onto a small square grid of exactly `canvas_size` x `canvas_size`
  "pixels" (using fit/fill/center placement), then quantized. This is
  the classic way sprite tools produce a true fixed-resolution sprite.

In both modes, an `output_scale` multiplier (1x/2x/4x/8x) is applied at
the end using Nearest Neighbor upscaling, so exported pixels stay crisp
at any zoom level.
"""

from PIL import Image
import numpy as np

from utils import place_on_canvas


def _downscale_by_block(image: Image.Image, pixel_size: int) -> Image.Image:
    """
    Shrink the image so each resulting pixel represents a `pixel_size`
    block of the original image. Uses a box filter for clean averaging.
    """
    width, height = image.size
    small_width = max(1, width // pixel_size)
    small_height = max(1, height // pixel_size)
    return image.resize((small_width, small_height), resample=Image.BOX)


def _quantize_colors(rgb_image: Image.Image, color_count: int, dither: bool) -> Image.Image:
    """
    Reduce the image to an adaptive palette of `color_count` colors.

    Args:
        rgb_image: an RGB (no alpha) PIL image.
        color_count: number of colors in the output palette (8-64).
        dither: whether to apply Floyd-Steinberg dithering.

    Returns:
        An RGB PIL image using only `color_count` distinct colors.
    """
    dither_mode = Image.FLOYDSTEINBERG if dither else Image.NONE
    quantized = rgb_image.quantize(
        colors=color_count,
        method=Image.MEDIANCUT,
        dither=dither_mode,
    )
    return quantized.convert("RGB")


def _rebuild_alpha_mask(alpha_channel: np.ndarray, threshold: int = 128) -> np.ndarray:
    """
    Convert a (possibly soft/anti-aliased) alpha channel into a crisp
    binary mask so pixel-art edges stay hard instead of blurry.
    """
    return np.where(alpha_channel >= threshold, 255, 0).astype(np.uint8)


def _quantize_rgba(image: Image.Image, color_count: int, dither: bool) -> Image.Image:
    """Split an RGBA image, quantize its colors, and rebuild a crisp alpha mask."""
    arr = np.array(image)
    rgb = Image.fromarray(arr[:, :, :3], mode="RGB")
    alpha = arr[:, :, 3]

    quantized_rgb = _quantize_colors(rgb, color_count, dither)
    crisp_alpha = _rebuild_alpha_mask(alpha)

    result_arr = np.dstack([np.array(quantized_rgb), crisp_alpha])
    return Image.fromarray(result_arr, mode="RGBA")


def _zero_out_transparent_rgb(image: Image.Image) -> Image.Image:
    """Force fully-transparent pixels to RGB(0,0,0) to avoid stray color fringes."""
    arr = np.array(image)
    transparent_mask = arr[:, :, 3] == 0
    arr[transparent_mask] = [0, 0, 0, 0]
    return Image.fromarray(arr, mode="RGBA")


def _upscale_nearest(image: Image.Image, multiplier: int) -> Image.Image:
    """Scale an image up by an integer multiplier using Nearest Neighbor."""
    if multiplier <= 1:
        return image
    width, height = image.size
    return image.resize((width * multiplier, height * multiplier), resample=Image.NEAREST)


def pixelize(
    image: Image.Image,
    pixel_size: int = 8,
    color_count: int = 16,
    dither: bool = False,
    canvas_size: int = None,
    fit_mode: str = "fit",
    output_scale: int = 1,
) -> Image.Image:
    """
    Convert an RGBA image into pixel art.

    Args:
        image: RGBA PIL image (background already removed / cropped).
        pixel_size: size in original pixels of one "pixel art block" (4-64).
                    Only used in Auto mode (canvas_size is None).
        color_count: number of colors in the reduced palette (8-64).
        dither: whether to apply Floyd-Steinberg dithering during quantization.
        canvas_size: if set, switches to Canvas/Sprite mode - the subject
            is placed on a fixed canvas_size x canvas_size pixel grid
            instead of being scaled relative to its own resolution.
        fit_mode: "fit" (contain), "fill" (cover), or "center" - only
            used in Canvas mode.
        output_scale: final integer multiplier (1, 2, 4, or 8) applied
            with Nearest Neighbor upscaling for crisp export at higher
            resolution.

    Returns:
        RGBA PIL image containing the final pixel art.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    if canvas_size:
        # --- Canvas / Sprite mode ---
        grid = place_on_canvas(image, canvas_size, mode=fit_mode)
        quantized = _quantize_rgba(grid, color_count, dither)
        final = _upscale_nearest(quantized, max(1, int(output_scale)))
    else:
        # --- Auto mode (original block-based behavior) ---
        original_size = image.size
        small = _downscale_by_block(image, pixel_size)
        quantized_small = _quantize_rgba(small, color_count, dither)
        # Restore to (approximately) the original resolution first,
        # matching the classic behavior of this app...
        base = quantized_small.resize(original_size, resample=Image.NEAREST)
        # ...then apply any additional export scale on top.
        final = _upscale_nearest(base, max(1, int(output_scale)))

    return _zero_out_transparent_rgb(final)
