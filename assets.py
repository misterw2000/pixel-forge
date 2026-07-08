"""
assets.py
---------
Static branding assets for PIXEL FORGE: a hand-built pixel-art logo
(pure SVG, no external image files or fonts required) and the CSS
theme that gives the interface its dark, retro-arcade look.

Everything here is self-contained markup/CSS - no network requests,
no external font files - so the app's "100% local" guarantee holds
even for the branding.
"""

# A small pixel-grid hammer-and-anvil icon, drawn as a grid of <rect>
# elements (each "pixel" is an 8x8 square) using a limited retro palette.
_LOGO_ICON_SVG = """
<svg width="48" height="48" viewBox="0 0 8 8" shape-rendering="crispEdges"
     xmlns="http://www.w3.org/2000/svg">
  <!-- Anvil body -->
  <rect x="1" y="5" width="6" height="1" fill="#5a5a6e"/>
  <rect x="2" y="6" width="4" height="1" fill="#3f3f4e"/>
  <rect x="1" y="4" width="1" height="1" fill="#7a7a8e"/>
  <rect x="6" y="4" width="1" height="1" fill="#7a7a8e"/>
  <rect x="2" y="4" width="4" height="1" fill="#8a8aa0"/>
  <!-- Hammer handle -->
  <rect x="4" y="0" width="1" height="3" fill="#c98a3c"/>
  <!-- Hammer head -->
  <rect x="3" y="0" width="3" height="1" fill="#ff5d5d"/>
  <rect x="3" y="1" width="3" height="1" fill="#e23e3e"/>
  <!-- Spark -->
  <rect x="6" y="2" width="1" height="1" fill="#ffe45c"/>
</svg>
""".strip()


def get_logo_html() -> str:
    """Return the full PIXEL FORGE logo block (icon + pixel-style title)."""
    return f"""
    <div class="pf-logo">
        <div class="pf-logo-icon">{_LOGO_ICON_SVG}</div>
        <div class="pf-logo-text">
            <span class="pf-logo-title">PIXEL&nbsp;FORGE</span>
            <span class="pf-logo-subtitle">local pixel art creation tool</span>
        </div>
    </div>
    """


def get_footer_html() -> str:
    """Return the small retro-style developer credit footer."""
    return """
    <div class="pf-footer">
        PIXEL FORGE &nbsp;·&nbsp; created by misterwAI &nbsp;·&nbsp; &copy; 2026 misterwAI
    </div>
    """


def get_about_markdown() -> str:
    """Return the About section content (Markdown)."""
    return """
### PIXEL FORGE

A minimalist offline pixel art creation tool.

**Created by misterwAI**
© 2026 misterwAI

- No cloud services
- No API dependencies
- 100% local creation
"""


# Custom CSS: dark background, hard pixel edges, monospace "pixel" type.
# Uses only system/web-safe monospace fonts so the retro look never
# depends on downloading a font from the internet.
CSS_STYLES = """
:root {
    --pf-bg: #0d0d12;
    --pf-panel: #16161f;
    --pf-border: #2e2e3e;
    --pf-accent: #ff5d5d;
    --pf-accent-2: #5cffe0;
    --pf-text: #e6e6f0;
    --pf-text-dim: #8a8aa0;
}

.gradio-container {
    background: var(--pf-bg) !important;
    font-family: 'Courier New', ui-monospace, monospace !important;
    color: var(--pf-text) !important;
}

/* --- Logo header --- */
.pf-logo {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 10px 4px 4px 4px;
}
.pf-logo-icon svg { image-rendering: pixelated; display: block; }
.pf-logo-title {
    display: block;
    font-family: 'Courier New', ui-monospace, monospace;
    font-weight: 700;
    font-size: 28px;
    letter-spacing: 4px;
    color: var(--pf-accent-2);
    text-shadow:
        2px 0 0 var(--pf-accent),
        0 2px 0 rgba(0,0,0,0.6);
}
.pf-logo-subtitle {
    display: block;
    font-size: 12px;
    letter-spacing: 2px;
    color: var(--pf-text-dim);
    text-transform: uppercase;
    margin-top: 2px;
}

/* --- Footer credits --- */
.pf-footer {
    text-align: center;
    padding: 14px 0 4px 0;
    font-size: 11px;
    letter-spacing: 1px;
    color: var(--pf-text-dim);
    border-top: 1px dashed var(--pf-border);
    margin-top: 10px;
    text-transform: uppercase;
}

/* --- General panel / block styling: hard pixel edges, no rounded corners --- */
.gradio-container .block,
.gradio-container .form,
.gradio-container button,
.gradio-container input,
.gradio-container select,
.gradio-container textarea {
    border-radius: 0 !important;
}

.gradio-container .block {
    border-color: var(--pf-border) !important;
    background: var(--pf-panel) !important;
}

/* Primary action button: retro arcade "insert coin" feel */
button.primary {
    background: var(--pf-accent) !important;
    color: #1a0505 !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border: 2px solid #1a0505 !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.6) !important;
}
button.primary:hover {
    background: var(--pf-accent-2) !important;
}
"""
