#!/usr/bin/env bash
# Install Surfn-Paper and Kiro-Paper into the user's local XDG data dirs.
#
#   ./install.sh              install both themes for the current user
#   ./install.sh --uninstall  remove them again
#
# The icon theme inherits from Surfn (and Paper when available), so keep
# Surfn installed for the complete icon set.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
THEMES_DIR="$DATA_HOME/themes"
ICONS_DIR="$DATA_HOME/icons"

ICON_THEME="Surfn-Paper"
GTK_THEME="Kiro-Paper"

uninstall() {
    rm -rf "${ICONS_DIR:?}/$ICON_THEME" "${THEMES_DIR:?}/$GTK_THEME"
    echo "Removed $ICON_THEME and $GTK_THEME."
}

install_theme() {
    local src="$1" dest="$2"
    if [[ ! -d "$src" ]]; then
        echo "error: missing source directory: $src" >&2
        exit 1
    fi
    rm -rf "${dest:?}"
    mkdir -p "$(dirname "$dest")"
    cp -a "$src" "$dest"
    echo "Installed $(basename "$dest") -> $dest"
}

case "${1:-}" in
    --uninstall|-u)
        uninstall
        ;;
    "" )
        install_theme "$ROOT/$ICON_THEME" "$ICONS_DIR/$ICON_THEME"
        install_theme "$ROOT/$GTK_THEME" "$THEMES_DIR/$GTK_THEME"
        echo
        echo "Select the themes in Xfce Settings -> Appearance:"
        echo "  Style:  $GTK_THEME"
        echo "  Icons:  $ICON_THEME"
        echo
        echo "Or from a terminal:"
        echo "  xfconf-query -c xsettings -p /Net/ThemeName -s $GTK_THEME"
        echo "  xfconf-query -c xsettings -p /Net/IconThemeName -s $ICON_THEME"
        echo "  xfconf-query -c xfwm4 -p /general/theme -s $GTK_THEME"
        ;;
    * )
        echo "usage: $0 [--uninstall]" >&2
        exit 2
        ;;
esac
