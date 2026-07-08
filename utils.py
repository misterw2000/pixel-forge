"""
utils.py
--------
Small, generic helper functions shared across the app.
Kept free of any Gradio / rembg specific logic so it stays easy to test.
"""

import os
import tempfile
import uuid

from PIL import Image, ImageEnhance
import numpy as np


def ensure_rgba(image: Image.Image) -> Image.Image:
    """Make sure an image has an alpha channel (RGBA)."""
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    return image


def crop_transparent_borders(image: Image.Image, padding: int = 0) -> Image.Image:
    """
    Crop away fully-transparent rows/columns surrounding the subject.

    Args:
        image: an RGBA PIL image.
        padding: optional number of transparent pixels to keep around
                  the subject (0 = tight crop).

    Returns:
        A cropped RGBA image. If the image is fully transparent
        (nothing to crop to), the original image is returned unchanged.
    """
    image = ensure_rgba(image)
    alpha = np.array(image)[:, :, 3]

    # Find rows/columns that contain at least one non-transparent pixel.
    non_empty_columns = np.where(alpha.max(axis=0) > 0)[0]
    non_empty_rows = np.where(alpha.max(axis=1) > 0)[0]

    if non_empty_columns.size == 0 or non_empty_rows.size == 0:
        # Nothing visible in the image - nothing sensible to crop to.
        return image

    top, bottom = non_empty_rows[0], non_empty_rows[-1]
    left, right = non_empty_columns[0], non_empty_columns[-1]

    # Apply optional padding, clamped to image bounds.
    width, height = image.size
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(width - 1, right + padding)
    bottom = min(height - 1, bottom + padding)

    return image.crop((left, top, right + 1, bottom + 1))


def is_valid_image(file_path_or_image) -> bool:
    """
    Quick sanity check that a value is a usable, non-empty image.
    Accepts either a file path (str) or an already-loaded PIL Image.
    """
    try:
        if isinstance(file_path_or_image, Image.Image):
            image = file_path_or_image
        else:
            image = Image.open(file_path_or_image)
        image.verify()  # Raises if the file is corrupt / not an image.
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------
# Image Adjustment Controls (applied BEFORE the pixel conversion pipeline)
# --------------------------------------------------------------------------

def apply_image_adjustments(
    image: Image.Image,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
) -> Image.Image:
    """
    Apply brightness/contrast/saturation/sharpness adjustments to the
    RGB channels of an RGBA image, leaving the alpha channel untouched.

    A value of 1.0 for any parameter means "no change".
    """
    image = ensure_rgba(image)
    rgb = image.convert("RGB")
    alpha = image.split()[3]

    if brightness != 1.0:
        rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
    if contrast != 1.0:
        rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    if saturation != 1.0:
        rgb = ImageEnhance.Color(rgb).enhance(saturation)
    if sharpness != 1.0:
        rgb = ImageEnhance.Sharpness(rgb).enhance(sharpness)

    rgb.putalpha(alpha)
    return rgb


# --------------------------------------------------------------------------
# Canvas placement (used for the Sprite Mode / fixed Canvas Size feature)
# --------------------------------------------------------------------------

def _resize_to_fit(image: Image.Image, canvas_size: int) -> Image.Image:
    """Scale down/up so the whole image fits inside canvas_size (contain)."""
    width, height = image.size
    scale = min(canvas_size / width, canvas_size / height)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(new_size, resample=Image.BOX)


def _resize_to_fill(image: Image.Image, canvas_size: int) -> Image.Image:
    """Scale so the image fully covers canvas_size, then center-crop (cover)."""
    width, height = image.size
    scale = max(canvas_size / width, canvas_size / height)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    resized = image.resize(new_size, resample=Image.BOX)

    left = (new_size[0] - canvas_size) // 2
    top = (new_size[1] - canvas_size) // 2
    return resized.crop((left, top, left + canvas_size, top + canvas_size))


def place_on_canvas(image: Image.Image, canvas_size: int, mode: str = "fit") -> Image.Image:
    """
    Place an RGBA image onto a square transparent canvas of size
    `canvas_size` x `canvas_size`.

    Args:
        image: RGBA source image (subject, ideally already cropped).
        canvas_size: target square canvas dimension in pixels.
        mode: "fit" (contain, letterboxed), "fill" (cover, cropped),
              or "center" (place at natural pixel-block scale, centered,
              shrinking only if it would otherwise overflow the canvas).

    Returns:
        RGBA image exactly canvas_size x canvas_size.
    """
    image = ensure_rgba(image)

    if mode == "fill":
        positioned = _resize_to_fill(image, canvas_size)
        canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        canvas.paste(positioned, (0, 0), positioned)
        return canvas

    if mode == "center":
        width, height = image.size
        if width > canvas_size or height > canvas_size:
            image = _resize_to_fit(image, canvas_size)
    else:  # "fit" (default)
        image = _resize_to_fit(image, canvas_size)

    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    width, height = image.size
    x = (canvas_size - width) // 2
    y = (canvas_size - height) // 2
    canvas.paste(image, (x, y), image)
    return canvas


# --------------------------------------------------------------------------
# Background compositing (Background Options: white / black / custom color)
# --------------------------------------------------------------------------

def composite_on_color(image: Image.Image, color_rgb: tuple) -> Image.Image:
    """
    Flatten an RGBA image onto a solid-color opaque background.

    Args:
        image: RGBA source image.
        color_rgb: (R, G, B) tuple, 0-255 each.

    Returns:
        RGBA image (fully opaque) with the subject composited over
        the given solid color.
    """
    image = ensure_rgba(image)
    background = Image.new("RGBA", image.size, (*color_rgb, 255))
    return Image.alpha_composite(background, image)


# --------------------------------------------------------------------------
# Export helpers
# --------------------------------------------------------------------------

def save_for_export(image: Image.Image, fmt: str) -> str:
    """
    Save an image to a uniquely named temp file in the requested format,
    handling the fact that JPG doesn't support transparency.

    Args:
        image: RGBA (or RGB) PIL image.
        fmt: one of "PNG", "JPG", "WEBP" (case-insensitive).

    Returns:
        Path to the saved file.
    """
    fmt = fmt.upper()
    extension_map = {"PNG": ".png", "JPG": ".jpg", "WEBP": ".webp"}
    pillow_format_map = {"PNG": "PNG", "JPG": "JPEG", "WEBP": "WEBP"}

    if fmt not in extension_map:
        raise ValueError(f"Unsupported export format: {fmt}")

    output_image = image
    if fmt == "JPG" and output_image.mode == "RGBA":
        # JPG has no alpha channel - flatten transparency onto white.
        flattened = Image.new("RGB", output_image.size, (255, 255, 255))
        flattened.paste(output_image, mask=output_image.split()[3])
        output_image = flattened

    filename = f"pixel_forge_{uuid.uuid4().hex[:8]}{extension_map[fmt]}"
    output_path = os.path.join(tempfile.gettempdir(), filename)
    output_image.save(output_path, format=pillow_format_map[fmt])
    return output_path
