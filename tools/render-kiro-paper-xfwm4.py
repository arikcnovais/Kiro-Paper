#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the XFWM4 decoration used by Kiro-Paper.

The decoration intentionally mirrors ``Kiro-Paper/gtk-3.0/widgets.css``:

  * header bar          #636e73, backdrop #454d50
  * header bottom line  #4f585c / #3c4346
  * frame               #e6e6e6 (theme insensitive background)
  * top radius          4px, matching GTK3's ``decoration { border-radius }``
  * bottom corners      square, matching GTK3's ``4px 4px 0 0`` radius
  * window controls     24px, round hover, close hover #d9534f

Frame pieces are rendered at 1x.  XFWM4 stores decorations in a depth-24
window and clips them with a 1-bit shape mask, so partially transparent pixels
cannot be blended: they are either kept or discarded.  Rendering the mask at 1x
with a pixel-centre test gives a clean, predictable arc instead of the stray
light/dark pixels produced by downsampling an antialiased mask.

Window controls are different: they are opaque tiles with the title-bar colour
baked in.  Their glyphs are still drawn at 4x and downsampled so the text/icon
antialiasing survives in the RGB image.

Usage: python3 tools/render-kiro-paper-xfwm4.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Kiro-Paper" / "xfwm4"

SS = 4          # supersampling factor (window controls only)
H = 28          # title bar height
B = 4           # side / bottom frame width
RADIUS = 4      # top corner radius (GTK3 uses 4px)
TILE = 8        # width of the rounded top corner pieces
BUTTON = 24     # window control size

ACTIVE = "#636e73"
INACTIVE = "#454d50"
LINE_ACTIVE = "#4f585c"
LINE_INACTIVE = "#3c4346"
HIGHLIGHT = "#6c777b"
FRAME = "#e6e6e6"
CLOSE_HOVER = "#d9534f"
CLOSE_PRESSED = "#c9302c"


def rgba(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    value = hex_color.lstrip("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), alpha)


def rounded_mask(w: int, h: int, radii: tuple[int, int, int, int]) -> Image.Image:
    """Return a hard 1-bit L mask with an independent radius per corner.

    ``radii`` is (top-left, top-right, bottom-right, bottom-left).  The mask is
    evaluated at 1x using pixel centres.  XFWM4 thresholding this mask is what
    creates the rounded corner, so no partial alpha is used.
    """
    tl, tr, br, bl = (max(0, min(r, min(w, h))) for r in radii)
    mask = Image.new("L", (w, h), 255)
    pixels = mask.load()

    corners = (
        (tl, 0, 0, 1, 1),
        (tr, w - tr, 0, -1, 1),
        (br, w - br, h - br, -1, -1),
        (bl, 0, h - bl, 1, -1),
    )
    for radius, x0, y0, dx, dy in corners:
        if not radius:
            continue
        cx = x0 + (radius if dx > 0 else 0)
        cy = y0 + (radius if dy > 0 else 0)
        for y in range(y0, y0 + radius):
            for x in range(x0, x0 + radius):
                px = x + 0.5 - cx
                py = y + 0.5 - cy
                if px * px + py * py > radius * radius:
                    pixels[x, y] = 0
    return mask


def save(image: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name)


def header_piece(
    name: str,
    w: int,
    h: int,
    color: str,
    radii: tuple[int, int, int, int] = (0, 0, 0, 0),
    bottom_line: str | None = None,
    top_highlight: str | None = None,
) -> None:
    image = Image.new("RGBA", (w, h), rgba(color))
    draw = ImageDraw.Draw(image)
    if top_highlight:
        # Matches GTK3's headerbar box-shadow: inset 0 1px alpha(white, .06).
        draw.rectangle([0, 0, w - 1, 0], fill=rgba(top_highlight))
    if bottom_line:
        draw.rectangle([0, h - 1, w - 1, h - 1], fill=rgba(bottom_line))
    # Apply the shape last so the highlight/line cannot make a cut pixel opaque.
    image.putalpha(rounded_mask(w, h, radii))
    save(image, name)


def frame_piece(name: str, w: int, h: int) -> None:
    image = Image.new("RGBA", (w, h), rgba(FRAME))
    save(image, name)


def _line(draw: ImageDraw.ImageDraw, points, width: int, ink) -> None:
    # ``points`` are in final (1x) coordinates; the canvas is supersampled.
    scaled = [(int(x * SS), int(y * SS)) for x, y in points]
    draw.line(scaled, fill=ink, width=width, joint="curve")
    half = width // 2
    for x, y in scaled:
        draw.ellipse([x - half, y - half, x + half, y + half], fill=ink)


def button(name: str, glyph: str, state: str) -> None:
    """Draw a 24px round window control matching GTK3's windowcontrols.

    XFWM4 also clips button windows with a 1-bit mask, so a transparent glyph
    would lose its antialiasing and turn into a jagged mask edge.  The
    title-bar colour is therefore baked into the image.  The glyph/hover
    overlay is still drawn at 4x and downsampled, which preserves smooth edges
    in the opaque RGB result.
    """
    bg_color = INACTIVE if state == "inactive" else ACTIVE
    overlay = Image.new("RGBA", (BUTTON * SS, BUTTON * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Round hover / press background, exactly like GTK3's border-radius: 50%.
    if state == "prelight":
        fill = rgba(CLOSE_HOVER) if glyph == "close" else (255, 255, 255, 40)
        draw.ellipse([1 * SS, 1 * SS, (BUTTON - 1) * SS - 1, (BUTTON - 1) * SS - 1], fill=fill)
    elif state == "pressed":
        fill = rgba(CLOSE_PRESSED) if glyph == "close" else (0, 0, 0, 40)
        draw.ellipse([1 * SS, 1 * SS, (BUTTON - 1) * SS - 1, (BUTTON - 1) * SS - 1], fill=fill)

    # Inactive glyphs are dimmed, like a GTK backdrop header bar.
    ink = (255, 255, 255, 255 if state != "inactive" else 140)

    width = max(1, round(1.5 * SS))
    c = BUTTON / 2
    lo, hi = c - 5, c + 5
    mid = c

    if glyph == "close":
        _line(draw, [(lo, lo), (hi, hi)], width, ink)
        _line(draw, [(hi, lo), (lo, hi)], width, ink)
    elif glyph == "hide":
        _line(draw, [(lo, mid), (hi, mid)], width, ink)
    elif glyph == "maximize":
        draw.rounded_rectangle(
            [lo * SS, lo * SS, hi * SS, hi * SS],
            radius=1 * SS,
            outline=ink,
            width=width,
        )
    elif glyph == "maximize-toggled":
        d = 2.5
        draw.rounded_rectangle(
            [(lo) * SS, (lo + d) * SS, (hi - d) * SS, hi * SS],
            radius=1 * SS,
            outline=ink,
            width=width,
        )
        draw.rounded_rectangle(
            [(lo + d) * SS, lo * SS, hi * SS, (hi - d) * SS],
            radius=1 * SS,
            outline=ink,
            width=width,
        )
    elif glyph == "shade":
        _line(draw, [(lo, mid - 2), (mid, mid + 2), (hi, mid - 2)], width, ink)
    elif glyph == "stick":
        draw.ellipse(
            [mid * SS - 3 * SS, lo * SS, mid * SS + 3 * SS, lo * SS + 6 * SS],
            outline=ink,
            width=width,
        )
        _line(draw, [(mid, lo + 4), (mid, hi)], width, ink)
    elif glyph == "menu":
        for y in (mid - 4, mid, mid + 4):
            _line(draw, [(lo, y), (hi, y)], width, ink)
    else:
        raise ValueError(glyph)

    overlay = overlay.resize((BUTTON, BUTTON), Image.Resampling.LANCZOS)
    background = Image.new("RGBA", (BUTTON, BUTTON), rgba(bg_color))
    image = Image.alpha_composite(background, overlay).convert("RGB")
    OUT.mkdir(parents=True, exist_ok=True)
    image.save(OUT / name)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    for state, color, line in (
        ("active", ACTIVE, LINE_ACTIVE),
        ("inactive", INACTIVE, LINE_INACTIVE),
    ):
        # Rounded top corners, then square title-bar tiles.
        highlight = HIGHLIGHT if state == "active" else None
        header_piece(f"top-left-{state}.png", TILE, H, color, (RADIUS, 0, 0, 0), line, highlight)
        header_piece(f"top-right-{state}.png", TILE, H, color, (0, RADIUS, 0, 0), line, highlight)
        header_piece(f"top-{state}.png", 16, H, color, bottom_line=line, top_highlight=highlight)
        for index in range(1, 6):
            header_piece(f"title-{index}-{state}.png", 5, H, color, bottom_line=line, top_highlight=highlight)

        # Flat frame in the GTK background colour.  GTK3 only rounds the top
        # corners (``border-radius: 4px 4px 0 0``), so the bottom stays square.
        frame_piece(f"left-{state}.png", B, 16)
        frame_piece(f"right-{state}.png", B, 16)
        frame_piece(f"bottom-{state}.png", 16, B)
        frame_piece(f"bottom-left-{state}.png", B, B)
        frame_piece(f"bottom-right-{state}.png", B, B)

        # Window controls.
        for glyph in ("close", "hide", "maximize", "maximize-toggled", "shade", "stick", "menu"):
            button(f"{glyph}-{state}.png", glyph, state)
            if state == "active":
                button(f"{glyph}-prelight.png", glyph, "prelight")
                button(f"{glyph}-pressed.png", glyph, "pressed")

    print(f"XFWM4 assets written to {OUT}")


if __name__ == "__main__":
    main()
