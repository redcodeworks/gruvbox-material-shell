# gruvbox-material-shell

A Gruvbox Material recolor of **real** GNOME Shell CSS, not a from-scratch
reimplementation of it.

## Why this exists

The obvious way to theme GNOME Shell is to fork an existing from-scratch
SCSS theme (e.g. Fausto-Korpsvart/Gruvbox-GTK-Theme) and recolor it. The
problem: that SCSS is a *parallel reimplementation* of everything GNOME
Shell already does -- every hover state, every border radius, every
overview animation -- maintained independently of GNOME's own code. Any
structural detail the fork doesn't happen to replicate (or hardcodes
wrong) just stays wrong, and any time an upstream GNOME change isn't
mirrored, your theme drifts further from what GNOME actually does.

This repo does the opposite: it extracts the *actual* stock Adwaita Shell
CSS (compiled into `gnome-shell-theme.gresource`) and ships a much smaller
file that **only overrides color declarations**, using the exact same
selectors as the real stylesheet. GNOME Shell's theme loading is additive
(`St.Theme`'s default/user/extension three-tier stylesheet cascade, see
`Main.setThemeStylesheet()` in the `user-theme` extension) -- a custom
theme layers on top of the gresource-baked default rather than replacing
it, so any selector we *don't* touch falls through to real, current
Adwaita behavior automatically.

## Layout

- `reference/` -- the real stock `gnome-shell-{dark,light}.css` and
  `pad-osd.css`, extracted verbatim from `gnome-shell-theme.gresource`
  via `Gio.Resource`, committed as a frozen diffing baseline. **Not**
  loaded at runtime -- exists purely so a future GNOME Shell upgrade can
  be diffed against this snapshot to catch upstream selector/structure
  changes that might silently break the overrides below.
  Extracted from GNOME Shell 50.5 (2026-10-09).
- `gnome-shell-dark.css`, `gnome-shell-light.css` -- the actual theme,
  hand-written plain CSS (no SASS/build step). A `@define-color` palette
  block at the top (same token names as
  [nox-dotfiles](https://github.com/redcodeworks/nox-dotfiles)'s
  `gtk-4.0/gtk.css`), then selector overrides grouped by surface.
- `install.sh` -- copies the two theme files plus `reference/pad-osd.css`
  into `~/.themes/Gruvbox-Material-Shell/gnome-shell/`.

## Install

```
./install.sh
gsettings set org.gnome.shell.extensions.user-theme name 'Gruvbox-Material-Shell'
```

Log out and back in -- GNOME Shell doesn't hot-reload theme CSS.
