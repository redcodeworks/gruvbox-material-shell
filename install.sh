#!/usr/bin/env bash
# Installs this theme as two GNOME Shell themes, Gruvbox-Material-Shell-Dark
# and Gruvbox-Material-Shell-Light, under ~/.themes. GNOME Shell has no
# light/dark auto-switching mechanism (confirmed: the stock theme ships as
# two entirely separate compiled CSS files), so -- same as every other
# theme in this project -- light and dark are separate named themes you
# switch between manually via the user-theme extension.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
DEST_DIR="${1:-$HOME/.themes}"

for variant in Dark Light; do
    name="Gruvbox-Material-Shell-${variant}"
    theme_dir="${DEST_DIR}/${name}"
    lower="$(echo "$variant" | tr '[:upper:]' '[:lower:]')"
    css_file="${REPO_DIR}/gnome-shell-${lower}.css"

    rm -rf "$theme_dir"
    mkdir -p "$theme_dir/gnome-shell"
    cp "$css_file" "$theme_dir/gnome-shell/gnome-shell.css"
    cp "$REPO_DIR/reference/pad-osd.css" "$theme_dir/gnome-shell/pad-osd.css"
    cp -r "$REPO_DIR/assets-${lower}" "$theme_dir/gnome-shell/assets"

    cat > "$theme_dir/index.theme" <<EOF
[Desktop Entry]
Type=X-GNOME-Metatheme
Name=${name}
Comment=Gruvbox Material recolor of real GNOME Shell CSS
EOF

    echo "Installed ${name} -> ${theme_dir}"
done

echo
echo "Switch with:"
echo "  gsettings set org.gnome.shell.extensions.user-theme name 'Gruvbox-Material-Shell-Dark'"
echo "(log out/in afterward -- GNOME Shell doesn't hot-reload theme CSS)"
