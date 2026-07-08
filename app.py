"""
app.py
------
PIXEL FORGE - a minimalist, 100% local pixel-art creation tool.

Pipeline: upload -> remove background -> adjust -> pixelize
          -> (optional) composite background -> export.

Run with:
    python app.py

Everything happens locally: rembg's ONNX model runs on-device via
onnxruntime, and all image processing uses Pillow/NumPy/OpenCV.
No cloud services, no API keys, no subscriptions.
"""

import gradio as gr

from background import remove_background
from pixelizer import pixelize
from utils import (
    crop_transparent_borders,
    ensure_rgba,
    is_valid_image,
    apply_image_adjustments,
    composite_on_color,
    save_for_export,
)
from presets import PRESET_NAMES, get_preset
from assets import CSS_STYLES, get_logo_html, get_footer_html, get_about_markdown


# ---------------------------------------------------------------------------
# Option maps: translate friendly UI labels into pipeline parameters.
# ---------------------------------------------------------------------------

CANVAS_SIZE_MAP = {
    "Auto": None,
    "32x32": 32,
    "64x64": 64,
    "128x128": 128,
    "256x256": 256,
}

FIT_MODE_MAP = {
    "Fit subject": "fit",
    "Fill canvas": "fill",
    "Center subject": "center",
}

OUTPUT_SCALE_MAP = {"1x": 1, "2x": 2, "4x": 4, "8x": 8}

BACKGROUND_MODES = ["Transparent", "Original background", "White", "Black", "Custom color"]
EXPORT_FORMATS = ["PNG", "JPG", "WEBP"]


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert a '#rrggbb' (or '#rrggbbaa') string into an (R, G, B) tuple."""
    hex_color = (hex_color or "#ffffff").lstrip("#")
    if len(hex_color) >= 6:
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return (255, 255, 255)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def convert_image(
    input_image,
    pixel_size,
    color_count,
    dither,
    export_format,
    output_scale_label,
    background_mode,
    custom_bg_color,
    brightness,
    contrast,
    saturation,
    sharpness,
    edge_refinement,
    canvas_size_label,
    fit_mode_label,
    sprite_mode,
    progress=gr.Progress(),
):
    """Full pipeline triggered by the "Convert" button."""
    if input_image is None:
        raise gr.Error("Please upload an image first.")

    if not is_valid_image(input_image):
        raise gr.Error("The uploaded file doesn't look like a valid image. Please try another one.")

    canvas_size = CANVAS_SIZE_MAP.get(canvas_size_label)
    fit_mode = FIT_MODE_MAP.get(fit_mode_label, "fit")
    output_scale = OUTPUT_SCALE_MAP.get(output_scale_label, 1)

    # Sprite Mode overrides a few settings to guarantee a clean,
    # transparent, fixed-size game asset.
    if sprite_mode:
        background_mode = "Transparent"
        if canvas_size is None:
            canvas_size = 64

    try:
        progress(0.05, desc="Preparing image...")

        if background_mode == "Original background":
            # Skip background removal entirely - keep the photo as-is.
            no_bg = ensure_rgba(input_image)
            cropped = no_bg
        else:
            progress(0.2, desc="Removing background...")
            no_bg = remove_background(input_image, edge_refinement=edge_refinement)
            progress(0.4, desc="Cropping transparent borders...")
            cropped = crop_transparent_borders(no_bg)

        progress(0.5, desc="Applying image adjustments...")
        adjusted = apply_image_adjustments(
            cropped,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
        )

        progress(0.65, desc="Converting to pixel art...")
        pixel_art = pixelize(
            adjusted,
            pixel_size=int(pixel_size),
            color_count=int(color_count),
            dither=dither,
            canvas_size=canvas_size,
            fit_mode=fit_mode,
            output_scale=output_scale,
        )

        if background_mode in ("White", "Black", "Custom color"):
            progress(0.85, desc="Compositing background...")
            if background_mode == "White":
                color = (255, 255, 255)
            elif background_mode == "Black":
                color = (0, 0, 0)
            else:
                color = _hex_to_rgb(custom_bg_color)
            pixel_art = composite_on_color(pixel_art, color)

    except gr.Error:
        raise
    except Exception as exc:
        raise gr.Error(f"Something went wrong while processing the image: {exc}")

    progress(0.95, desc="Exporting...")
    output_path = save_for_export(pixel_art, export_format)
    progress(1.0, desc="Done!")

    return cropped, pixel_art, output_path


def apply_preset(preset_name: str):
    """
    When a Style Preset is chosen, push its values into the pixel size,
    color count, dithering, and adjustment controls. "Custom" leaves
    everything as the user currently has it.
    """
    preset = get_preset(preset_name)
    if preset is None:
        return (gr.update(),) * 7

    return (
        gr.update(value=preset["pixel_size"]),
        gr.update(value=preset["color_count"]),
        gr.update(value=preset["dither"]),
        gr.update(value=preset["brightness"]),
        gr.update(value=preset["contrast"]),
        gr.update(value=preset["saturation"]),
        gr.update(value=preset["sharpness"]),
    )


def toggle_custom_color(background_mode: str):
    """Only show the custom color picker when 'Custom color' is selected."""
    return gr.update(visible=(background_mode == "Custom color"))


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def build_interface() -> gr.Blocks:
    with gr.Blocks(title="PIXEL FORGE", css=CSS_STYLES, theme=gr.themes.Base()) as demo:
        gr.HTML(get_logo_html())

        # Main screen: kept deliberately simple.
        # Note: Gradio components retain their values for the lifetime of
        # a browser session automatically, so settings are "remembered"
        # between conversions without any extra state management here.
        input_image = gr.Image(
            label="Drop image here (or click to upload / paste from clipboard)",
            type="pil",
            height=320,
            sources=["upload", "clipboard"],
        )

        preset = gr.Dropdown(
            choices=PRESET_NAMES, value="Custom", label="Style Preset"
        )

        with gr.Row():
            pixel_size = gr.Slider(minimum=4, maximum=64, value=8, step=1, label="Pixel Size")
            color_count = gr.Slider(minimum=8, maximum=64, value=16, step=1, label="Color Count")

        dither = gr.Checkbox(label="Dithering", value=False)

        # --- Advanced Settings (collapsed by default) ---
        with gr.Accordion("Advanced Settings", open=False):
            gr.Markdown("**Export**")
            with gr.Row():
                export_format = gr.Dropdown(choices=EXPORT_FORMATS, value="PNG", label="Export Format")
                output_scale = gr.Dropdown(choices=list(OUTPUT_SCALE_MAP.keys()), value="1x", label="Output Scale")

            gr.Markdown("**Background**")
            with gr.Row():
                background_mode = gr.Dropdown(choices=BACKGROUND_MODES, value="Transparent", label="Background Options")
                custom_bg_color = gr.ColorPicker(value="#ffffff", label="Custom Color", visible=False)

            gr.Markdown("**Image Adjustments** _(applied before pixelization)_")
            with gr.Row():
                brightness = gr.Slider(minimum=0.5, maximum=1.5, value=1.0, step=0.05, label="Brightness")
                contrast = gr.Slider(minimum=0.5, maximum=1.5, value=1.0, step=0.05, label="Contrast")
            with gr.Row():
                saturation = gr.Slider(minimum=0.0, maximum=2.0, value=1.0, step=0.05, label="Saturation")
                sharpness = gr.Slider(minimum=0.0, maximum=2.0, value=1.0, step=0.05, label="Sharpness")

            gr.Markdown("**Pixel Conversion**")
            edge_refinement = gr.Slider(
                minimum=0, maximum=10, value=0, step=1,
                label="Edge Refinement (hair / fine detail quality)",
            )
            with gr.Row():
                canvas_size = gr.Dropdown(choices=list(CANVAS_SIZE_MAP.keys()), value="Auto", label="Canvas Size")
                fit_mode = gr.Dropdown(choices=list(FIT_MODE_MAP.keys()), value="Fit subject", label="Canvas Placement")

            gr.Markdown("**Sprite Mode**")
            sprite_mode = gr.Checkbox(
                label="Create Game Sprite (transparent, centered, fixed canvas)",
                value=False,
            )

        convert_btn = gr.Button("Convert", variant="primary")

        with gr.Row():
            before_preview = gr.Image(label="Before (background removed)", type="pil", height=320)
            after_preview = gr.Image(label="After (pixel art)", type="pil", height=320)

        download_btn = gr.File(label="Download")

        with gr.Accordion("About", open=False):
            gr.Markdown(get_about_markdown())

        gr.HTML(get_footer_html())

        # --- Wiring ---
        preset.change(
            fn=apply_preset,
            inputs=preset,
            outputs=[pixel_size, color_count, dither, brightness, contrast, saturation, sharpness],
        )

        background_mode.change(
            fn=toggle_custom_color,
            inputs=background_mode,
            outputs=custom_bg_color,
        )

        convert_btn.click(
            fn=convert_image,
            inputs=[
                input_image, pixel_size, color_count, dither,
                export_format, output_scale, background_mode, custom_bg_color,
                brightness, contrast, saturation, sharpness,
                edge_refinement, canvas_size, fit_mode, sprite_mode,
            ],
            outputs=[before_preview, after_preview, download_btn],
        )

    return demo


if __name__ == "__main__":
    app = build_interface()
    app.launch()
