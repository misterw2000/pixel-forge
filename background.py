"""
background.py
--------------
Handles local background removal using rembg (which runs a local
ONNX model via onnxruntime - no network calls are made once the
model has been downloaded/cached the first time it runs).

Also exposes an "edge refinement" control, mapped onto rembg's
alpha-matting options, for cleaner edges around hair and other
fine details.
"""

from PIL import Image
from rembg import remove, new_session

# The session is created once and reused for every request, since
# loading the ONNX model from disk is the most expensive step.
# "u2net" is rembg's general-purpose default model and works fully offline
# after its first download.
_SESSION = None


def _get_session():
    """Lazily create (and cache) the rembg inference session."""
    global _SESSION
    if _SESSION is None:
        _SESSION = new_session("u2net")
    return _SESSION


def remove_background(image: Image.Image, edge_refinement: int = 0) -> Image.Image:
    """
    Remove the background from an image, returning an RGBA image
    where the background is fully transparent.

    Args:
        image: a PIL Image (any mode).
        edge_refinement: 0-10. 0 disables alpha matting (fast, good
            enough for simple subjects). Values above 0 enable rembg's
            alpha-matting refinement, which produces noticeably cleaner
            edges around hair, fur, and other fine details - at the
            cost of a bit more processing time. Higher values erode the
            trimap less, preserving finer detail.

    Returns:
        RGBA PIL Image with background removed.
    """
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    edge_refinement = max(0, min(10, int(edge_refinement)))

    if edge_refinement == 0:
        return remove(image, session=_get_session())

    # Map the 1-10 slider onto rembg's alpha matting parameters.
    # A smaller erode size keeps more fine detail (hair, wisps, etc.).
    erode_size = max(1, 12 - edge_refinement)

    result = remove(
        image,
        session=_get_session(),
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=erode_size,
    )
    return result
