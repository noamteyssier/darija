"""Render the PWA icons from the logo in assets/common.js. Run: uv run --with pillow python scripts/build_icons.py"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "icons"
BG, FG = "#282828", "#fabd2f"
S = 4  # supersample


def logo(size, scale):
    """Logo centred on the background; scale is the logo's share of the canvas (viewBox 40, logo spans 9..31)."""
    n = size * S
    im = Image.new("RGB", (n, n), BG)
    d = ImageDraw.Draw(im)
    u = n * scale / 22  # pixels per viewBox unit, logo box is 22 wide
    c = n / 2
    w = max(1, round(2.2 * u))
    h = 11 * u
    d.rectangle([c - h, c - h, c + h, c + h], outline=FG, width=w)
    r = h * 2 ** 0.5
    d.polygon([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], outline=FG, width=w)
    d.ellipse([c - 3.2 * u, c - 3.2 * u, c + 3.2 * u, c + 3.2 * u], fill=FG)
    return im.resize((size, size), Image.LANCZOS)


# The rotated square reaches 11*sqrt2 = 15.6 units from centre, so 0.55 of the canvas keeps it clear of the edge.
logo(180, 0.55).save(OUT / "apple-touch-icon.png")
logo(192, 0.55).save(OUT / "icon-192.png")
logo(512, 0.55).save(OUT / "icon-512.png")
logo(512, 0.40).save(OUT / "icon-maskable-512.png")
