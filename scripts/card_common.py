"""Shared SVG primitives for the dive instrument cards.

Both cards (dive computer, forecast) are screens of one console: same frame,
palette, and typography. Pure functions only — no I/O here.
"""

from xml.sax.saxutils import escape

PALETTES = {
    "day": {
        "depth0": "#e0f7fa",
        "depth1": "#80deea",
        "depth2": "#26c6da",
        "depth3": "#0097a7",
        "depth4": "#006064",
        "abyss": "#041c26",
        "accent": "#ff6d00",
        "text": "#063a44",
        "bg": "#f4fdff",
    },
    "night": {
        "depth0": "#0d2137",
        "depth1": "#14455c",
        "depth2": "#1b6e85",
        "depth3": "#22a3b8",
        "depth4": "#5ee7df",
        "abyss": "#020d13",
        "accent": "#ff8a50",
        "text": "#d8f6ff",
        "bg": "#071a24",
    },
}

MONO = "ui-monospace,Menlo,Consolas,monospace"


def esc(s):
    return escape(str(s))


def bar(x, y, w, frac, palette, h=10):
    """A rounded track with an accent fill proportional to frac (clamped 0..1)."""
    frac = max(0.0, min(1.0, frac))
    fill_w = round(w * frac)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" '
        f'fill="{palette["depth1"]}" opacity="0.45"/>'
        f'<rect x="{x}" y="{y}" width="{fill_w}" height="{h}" rx="{h / 2}" '
        f'fill="{palette["accent"]}"/>'
    )


def card(title, rows_svg, palette, width, height, footer_svg=""):
    """Instrument frame: bezel, small-caps title, accent underline, injected rows."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{esc(title)}">
  <rect x="1.5" y="1.5" width="{width - 3}" height="{height - 3}" rx="14" fill="{palette["bg"]}" stroke="{palette["depth3"]}" stroke-width="1.5"/>
  <rect x="1.5" y="1.5" width="{width - 3}" height="{height - 3}" rx="14" fill="none" stroke="{palette["depth1"]}" stroke-width="0.5" opacity="0.6"/>
  <text x="24" y="34" font-family="{MONO}" font-size="15" font-weight="700" letter-spacing="4" fill="{palette["text"]}">{esc(title)}</text>
  <rect x="24" y="42" width="46" height="3" rx="1.5" fill="{palette["accent"]}"/>
  {rows_svg}
  {footer_svg}
</svg>
"""
