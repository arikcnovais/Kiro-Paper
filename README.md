# Surfn-Paper and Kiro-Paper

Two matching themes that keep Paper's classic look while running on a modern
desktop:

| Component | Theme | What it does |
| --- | --- | --- |
| Icons | **Surfn-Paper** | Paper's folders, category icons, mimetypes, symbolic icons and a broad set of classic app icons layered over the modern **Surfn** icon set. |
| GTK 3 / GTK 4 | **Kiro-Paper** | Paper's palette and flat geometry rewritten with the current GTK CSS node names, so current applications get the intended look instead of falling back to Adwaita. |
| Xfwm4 | **Kiro-Paper** | Slate title bar matching the GTK header bars, white glyphs and a thin neutral frame. |

Paper's original colours are preserved on purpose:

| Role | Colour |
| --- | --- |
| Window background | `#efefef` |
| Base / view background | `#ffffff` |
| Text | `#555555` |
| Header bar | `#636e73` |
| Header bar (backdrop) | `#454d50` |
| Selection / accent | `#9fb0b9` |

## Install

The built themes are committed to this repository, so no build step is
needed:

```bash
git clone <repository-url> Kiro-Paper
cd Kiro-Paper
./install.sh
```

This copies the themes to:

- `~/.local/share/icons/Surfn-Paper`
- `~/.local/share/themes/Kiro-Paper`

Then choose them in **Xfce Settings → Appearance** (Style: `Kiro-Paper`,
Icons: `Surfn-Paper`). For the window decoration use **Window Manager →
Style → Kiro-Paper**.

To remove them again:

```bash
./install.sh --uninstall
```

## Requirements

Surfn-Paper is an overlay theme: `index.theme` declares
`Inherits=Surfn,Paper,hicolor`. Install **Surfn** for the complete icon set
(it is present system-wide on this machine). **Paper** is optional but lets
any icon not copied into the overlay fall through to Paper artwork.

Kiro-Paper needs GTK 3.24+ / GTK 4 and `xfwm4` 4.14+.

## Window corners

The GTK 3/4 side of Kiro-Paper rounds its client-side decorations to 4px and
antialiases them normally. The Xfwm4 side matches that geometry (4px top
corners, square bottom corners, like GTK's `border-radius: 4px 4px 0 0`), but
stock Xfwm4 cannot antialias window frames: decorations live in a depth-24
window and are clipped by a 1-bit shape mask. Partially transparent pixels are
not blended, they are either kept or discarded.

The renderer therefore builds the shape mask at 1x with a pixel-centre circle
test. That produces a clean 1-bit arc instead of the stray bright/dark pixels
you get by downsampling a soft mask. For fully smooth (grey-pixel) corners you
need one of:

- a compositor that rounds windows, such as **picom** with
  `corner-radius = 4` (disable Xfwm4's compositor first), or
- a patched `xfwm4` build with rounded-corner support, such as the
  `xfwm4-rounded-corners` package.

Those are compositor/window-manager changes, not something a theme can do.

## Rebuilding

The generators are only needed when changing the themes. They are not part of
a normal install. Rebuilding the icon theme requires upstream Surfn and Paper
checkouts:

```bash
python3 tools/build-surfn-paper.py \
    --surfn path/to/Surfn \
    --paper path/to/paper-icon-theme/Paper   # regenerate Surfn-Paper
python3 tools/render-kiro-paper-xfwm4.py     # regenerate xfwm4 PNGs
```

Both scripts are deterministic.

## Layout

```
Surfn-Paper/            generated icon theme
Kiro-Paper/
  index.theme           desktop entry (GTK + icon + button layout)
  colors-light.css      Paper light palette
  colors-dark.css       Paper dark palette
  gtk-2.0/              Paper's GTK 2 fallback (unchanged)
  gtk-3.0/gtk.css       light GTK 3 entry point
  gtk-3.0/gtk-dark.css  dark GTK 3 entry point
  gtk-3.0/widgets.css   GTK 3 widget styles
  gtk-4.0/…             GTK 4 equivalents
  xfwm4/                title bar assets + themerc
tools/                  reproducible generators
```

## Dark mode

`gtk-dark.css` is loaded automatically by GTK when an application requests a
dark theme. Set `gtk-application-prefer-dark-theme=1` (or use your desktop's
dark-mode switch) to use the dark palette.

## Credits and licence

Surfn-Paper combines artwork from the **Surfn** icon theme and the
**Paper** icon and GTK themes by Sam Hewitt and contributors. Kiro-Paper
keeps Paper's GTK 2 assets and reuses its palette. See `Kiro-Paper/LICENSE`
(GPL-3.0) and the upstream projects' licences for details.
