#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the Surfn-Paper icon theme.

Surfn-Paper is deliberately a small overlay theme:

  * Surfn supplies the modern, complete icon set (apps, actions, devices,
    mimetypes, status, symbolic icons, ...).
  * Paper supplies the folder artwork and a handful of classic places /
    category icons that give the theme its Paper character.
  * Everything else falls through to Surfn (which in turn falls through to
    Paper, Numix, Papirus, breeze, hicolor, ...).

Only the overlay is generated here.  Surfn and Paper must be installed for
the resulting theme to resolve every icon.

Usage:
    python3 tools/build-surfn-paper.py
    python3 tools/build-surfn-paper.py --paper path/to/Paper --surfn path/to/Surfn
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PAPER = ROOT / "paper-icon-theme" / "Paper"
DEFAULT_SURFN = ROOT / "surfn" / "usr" / "share" / "icons" / "Surfn"
OUT = ROOT / "Surfn-Paper"

# Paper ships these fixed sizes.  Its 512px artwork is the master for the
# interpolated sizes.
PAPER_SIZES = {16: "16x16", 24: "24x24", 32: "32x32", 48: "48x48", 512: "512x512"}
PAPER_2X = {
    16: "16x16@2x",
    24: "24x24@2x",
    32: "32x32@2x",
    48: "48x48@2x",
    512: "512x512@2x",
}

# Surfn-compatible output sizes (including @2x variants).
SIZES = [16, 22, 24, 32, 48, 64, 96, 128]

# Icons copied from Paper's places directory.  Folders are the heart of the
# mix; the extra names keep the Paper look for the most visible places while
# leaving all distro logos and application icons to Surfn.
PLACE_PATTERNS = [
    re.compile(r"^folder([._-].*)?\.png$"),
    re.compile(r"^user-(home|desktop|trash|bookmarks|documents|download|music|pictures|publicshare|templates|videos|network)\.png$"),
    re.compile(r"^(desktop|cs-desktop|show-desktop|trash|trashcan_empty|emptytrash|xfce-trash_empty)\.png$"),
    re.compile(r"^(network|network-server|network-workgroup|network_local|server)\.png$"),
    re.compile(r"^(gnome-fs-(directory|home|desktop|network|server|share|trash-empty)|gtk-directory|inode-directory|stock_folder)\.png$"),
]

# Category icons come wholesale from Paper: they are small, recognisable and
# are exactly the kind of "classic Paper" detail the mix is meant to keep.
COPY_CATEGORIES = True

# Mimetypes and symbolic icons are also taken from Paper.  Surfn stays the
# fallback for everything that is not listed here.
COPY_MIMETYPES = True
COPY_SYMBOLIC = True

# A deliberately broad, classic "Paper" app selection.  These are the icons
# people notice first; the rest of the app grid keeps Surfn's modern artwork.
APP_NAMES = {
    # Browsers
    "firefox", "firefox-esr", "firefox-beta", "firefox-developer-icon",
    "firefox-nightly", "firefox-original", "org.mozilla.Firefox",
    "chromium", "chromium-browser", "google-chrome", "google-chrome-beta",
    "google-chrome-unstable", "chrome", "brave", "opera", "opera-beta",
    "opera-developer", "vivaldi", "vivaldi-snapshot", "vivaldi_browser",
    # Mail / chat / communication
    "thunderbird", "evolution", "evolution-memos", "geary", "pidgin",
    "hexchat", "remmina", "skype", "skypeforlinux", "ghetto-skype",
    "com.skype.Client", "discord", "discord-canary", "syncthing",
    "syncthing-gtk",
    # Office
    "libreoffice", "libreoffice-base", "libreoffice-calc", "libreoffice-draw",
    "libreoffice-impress", "libreoffice-math", "libreoffice-startcenter",
    "libreoffice-writer", "libreoffice-suite",
    "org.libreoffice.LibreOffice", "org.libreoffice.LibreOffice.base",
    "org.libreoffice.LibreOffice.calc", "org.libreoffice.LibreOffice.draw",
    "org.libreoffice.LibreOffice.impress", "org.libreoffice.LibreOffice.math",
    "org.libreoffice.LibreOffice.startcenter",
    "org.libreoffice.LibreOffice.writer",
    "org.libreoffice.LibreOffice-base", "org.libreoffice.LibreOffice-calc",
    "org.libreoffice.LibreOffice-draw", "org.libreoffice.LibreOffice-impress",
    "org.libreoffice.LibreOffice-math", "org.libreoffice.LibreOffice-startcenter",
    "org.libreoffice.LibreOffice-writer",
    "calibre", "calibre-gui", "calibre-viewer", "calibre-ebook-edit",
    "okular", "evince", "org.gnome.Evince", "foliate",
    # Graphics / media
    "gimp", "org.gimp.GIMP", "org.gnome.GIMP", "inkscape",
    "org.inkscape.Inkscape", "blender", "Blender", "krita", "darktable",
    "org.darktable.Darktable", "digikam", "audacity", "kdenlive", "openshot",
    "handbrake", "shotcut", "rawtherapee", "vlc", "org.videolan.VLC", "mpv",
    "totem", "rhythmbox",
    # Development
    "code", "visual-studio-code", "code-oss", "codeblocks", "atom",
    "sublime", "sublime-text", "sublime-text-3", "android-studio",
    "android-sdk", "arduino", "arduino-ide", "gitkraken", "dbeaver",
    "postgresql", "idea", "idea-ultimate", "intellij-idea",
    "intellij-idea-ce", "intellij-idea-community", "intellij-idea-ultimate-edition",
    "intellij_idea", "jetbrains-idea", "pycharm",
    # Games / launchers
    "steam", "steam-icon", "steam-launcher", "steampowered",
    "com.valvesoftware.Steam", "minecraft", "lutris", "heroic",
    "playonlinux", "wine", "winecfg", "wine-winecfg", "wine-help",
    # Files / system tools
    "filezilla", "gparted", "transmission", "transmission-gtk",
    "transmission-qt", "transmission-remote-gtk", "qbittorrent", "deluge",
    "deluge-torrent", "virtualbox", "virtualbox-ose", "vmware",
    "vmware-player", "vmware-workstation", "gnome-boxes", "virt-manager",
    # Misc favourites
    "spotify", "Spotify", "spotify-client", "spotify-beta", "spotify-exe",
    "1password", "authy", "keepass", "keepass2", "keepassx", "keepassx2",
    "keepassxc", "dropbox", "owncloud",
}

# Paper puts its symbolic artwork in per-context folders below scalable/.
SYMBOLIC_CONTEXTS = [
    "actions", "apps", "categories", "devices", "emblems", "emotes",
    "mimetypes", "places", "status",
]

CONTEXT_NAMES = {
    "places": "Places",
    "categories": "Categories",
    "apps": "Applications",
    "mimetypes": "MimeTypes",
    "actions": "Actions",
    "devices": "Devices",
    "emblems": "Emblems",
    "emotes": "Emotes",
    "status": "Status",
}



def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_master(paper: Path, context: str, name: str, size: int, hidpi: bool) -> Path | None:
    """Return the best Paper source for a requested output size."""
    candidates: list[Path] = []

    if hidpi:
        # A matching @2x raster is already the right pixel size.
        if size in PAPER_2X:
            candidates.append(paper / PAPER_2X[size] / context / name)
        candidates.append(paper / PAPER_2X[512] / context / name)
    else:
        if size in PAPER_SIZES:
            candidates.append(paper / PAPER_SIZES[size] / context / name)

    # Highest-quality fallbacks, then the nearest small rasters.
    candidates += [
        paper / PAPER_SIZES[512] / context / name,
        paper / PAPER_SIZES[48] / context / name,
        paper / PAPER_SIZES[32] / context / name,
        paper / PAPER_SIZES[24] / context / name,
        paper / PAPER_SIZES[16] / context / name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def resize(src: Path, dst: Path, size: int) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".svg":
        run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(dst), str(src)])
    else:
        # -background none keeps transparency and prevents a black fringe.
        run([
            "magick", str(src), "-background", "none", "-filter", "Lanczos",
            "-resize", f"{size}x{size}", str(dst),
        ])


def copy_or_render(paper: Path, context: str, name: str, size: int, hidpi: bool, out_dir: Path) -> bool:
    src = find_master(paper, context, name, size, hidpi)
    if src is None:
        return False
    target_size = size * 2 if hidpi else size
    dst = out_dir / name
    if src.suffix.lower() == ".png":
        # Avoid needless resampling when the raster already has the right size.
        try:
            probe = subprocess.check_output(
                ["magick", "identify", "-format", "%w", str(src)], text=True
            ).strip()
            if int(probe) == target_size:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                return True
        except (subprocess.CalledProcessError, ValueError):
            pass
        resize(src, dst, target_size)
    else:
        resize(src, dst, target_size)
    return True


def collect_names(paper: Path, context: str) -> list[str]:
    names: set[str] = set()
    for pdir in PAPER_SIZES.values():
        directory = paper / pdir / context
        if directory.is_dir():
            for entry in directory.iterdir():
                if entry.is_file() or entry.is_symlink():
                    names.add(entry.name)
    return sorted(names)


def selected_places(paper: Path) -> list[str]:
    names = []
    for name in collect_names(paper, "places"):
        if any(pattern.match(name) for pattern in PLACE_PATTERNS):
            names.append(name)
    return names


def selected_apps(paper: Path) -> list[str]:
    """Keep only names that actually exist in Paper, preserving aliases."""
    available = set(collect_names(paper, "apps"))
    return sorted(
        name for name in available
        if Path(name).stem in APP_NAMES
    )


def copy_symbolic(paper: Path, out: Path) -> int:
    """Copy Paper's scalable symbolic artwork into Surfn context folders."""
    count = 0
    for context in SYMBOLIC_CONTEXTS:
        source = paper / "scalable" / context
        target = out / context / "symbolic"
        if not source.is_dir():
            continue
        target.mkdir(parents=True, exist_ok=True)
        for entry in sorted(source.iterdir()):
            if not entry.is_file() or entry.suffix.lower() != ".svg":
                continue
            shutil.copy2(entry, target / entry.name)
            count += 1

    # A handful of generic symbolic icons live at the root of scalable/.
    root = paper / "scalable"
    places_target = out / "places" / "symbolic"
    if root.is_dir():
        places_target.mkdir(parents=True, exist_ok=True)
        for entry in sorted(root.iterdir()):
            if entry.is_file() and entry.suffix.lower() == ".svg":
                shutil.copy2(entry, places_target / entry.name)
                count += 1
    return count


def write_index(out: Path) -> None:
    directories: list[str] = []
    scaled: list[str] = []
    sections: list[str] = []

    raster_contexts = ["places", "categories", "apps", "mimetypes"]
    for context in raster_contexts:
        for size in SIZES:
            d = f"{context}/{size}"
            directories.append(d)
            sections.append(
                f"[{d}]\nSize={size}\nContext={CONTEXT_NAMES[context]}\nType=Fixed\n"
            )
            sd = f"{context}/{size}@2x"
            scaled.append(sd)
            sections.append(
                f"[{sd}]\nSize={size}\nScale=2\nContext={CONTEXT_NAMES[context]}\nType=Fixed\n"
            )

    for context in SYMBOLIC_CONTEXTS:
        d = f"{context}/symbolic"
        directories.append(d)
        sections.append(
            f"[{d}]\nSize=16\nContext={CONTEXT_NAMES[context]}\nMinSize=8\nMaxSize=512\nType=Scalable\n"
        )

    body = f"""[Icon Theme]
Name=Surfn-Paper
Comment=Paper's folders and classic icons over the modern Surfn icon set
Inherits=Surfn,Paper,hicolor
Example=folder
FollowsColorScheme=true
DisplayDepth=32

DesktopDefault=48
DesktopSizes=16,22,24,32,48,64,96,128
ToolbarDefault=22
ToolbarSizes=16,22,24,32,48
SmallDefault=16
SmallSizes=16,22,24,32,48
DialogDefault=32

Directories={','.join(directories)}
ScaledDirectories={','.join(scaled)}

""" + "\n".join(sections)
    (out / "index.theme").write_text(body, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", default=str(DEFAULT_PAPER))
    parser.add_argument("--surfn", default=str(DEFAULT_SURFN))
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()

    paper = Path(args.paper).resolve()
    surfn = Path(args.surfn).resolve()
    out = Path(args.out).resolve()

    if not (paper / "index.theme").is_file():
        sys.exit(f"Paper theme not found at {paper}")
    if not (surfn / "index.theme").is_file():
        sys.exit(f"Surfn theme not found at {surfn}")

    for tool in ("magick", "rsvg-convert"):
        if shutil.which(tool) is None:
            sys.exit(f"Required tool not found: {tool}")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    places = selected_places(paper)
    categories = collect_names(paper, "categories") if COPY_CATEGORIES else []
    apps = selected_apps(paper)
    mimetypes = collect_names(paper, "mimetypes") if COPY_MIMETYPES else []

    if not places:
        sys.exit("No Paper place icons selected - check the source tree")

    total = 0
    raster_sets = [
        ("places", places),
        ("categories", categories),
        ("apps", apps),
        ("mimetypes", mimetypes),
    ]
    for context, names in raster_sets:
        for size in SIZES:
            for hidpi in (False, True):
                directory = out / context / (f"{size}@2x" if hidpi else str(size))
                directory.mkdir(parents=True, exist_ok=True)
                for name in names:
                    if copy_or_render(paper, context, name, size, hidpi, directory):
                        total += 1

    symbolic_total = copy_symbolic(paper, out) if COPY_SYMBOLIC else 0

    write_index(out)

    print(f"Surfn-Paper written to {out}")
    print(f"  place icons   : {len(places)} names x {len(SIZES)} sizes x 2 scales")
    print(f"  category icons: {len(categories)} names x {len(SIZES)} sizes x 2 scales")
    print(f"  app icons     : {len(apps)} names x {len(SIZES)} sizes x 2 scales")
    print(f"  mimetype icons: {len(mimetypes)} names x {len(SIZES)} sizes x 2 scales")
    print(f"  symbolic icons: {symbolic_total}")
    print(f"  files rendered: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
