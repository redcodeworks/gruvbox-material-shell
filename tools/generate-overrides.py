#!/usr/bin/env python3
"""
Generate selector-override CSS by diffing stock GNOME Shell CSS against the
validated Gruvbox-Dark/Light fork's compiled output.

Captures EVERY declared property per selector (not just background-color/
color) -- the first version of this tool only compared those two and
silently missed sizing/shape properties (#panel height, -barlevel-*,
-slider-*, font-weight, border, box-shadow, etc), which produced a theme
that was subtly wrong in dozens of places despite "no parse error".

Usage: generate-overrides.py <stock.css> <fork.css> > overrides.css
"""
import re
import sys
from collections import defaultdict


def parse(path):
    with open(path) as f:
        text = f.read()
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    blocks = re.findall(r'([^{}]+)\{([^{}]*)\}', text)
    result = {}
    order = []
    for selector_text, decl_text in blocks:
        selectors = [s.strip() for s in selector_text.split(',') if s.strip()]
        props = {}
        for line in decl_text.split(';'):
            line = line.strip()
            if not line or ':' not in line:
                continue
            k, v = line.split(':', 1)
            k, v = k.strip(), v.strip()
            props[k] = v
        if not props:
            continue
        for sel in selectors:
            sel = re.sub(r'\s+', ' ', sel)
            if sel not in result:
                order.append(sel)
            result.setdefault(sel, {}).update(props)
    return result, order


# Properties to never pull from the fork even when it differs from stock --
# cases where we deliberately want real Adwaita's own behavior instead of
# the fork's. Keyed by exact selector text as it appears in the fork CSS.
EXCLUDE_PROPS = {
    '#panel': {'height'},  # keep stock's default top-bar height (2026-10-09 request)
    # Gruvbox-Dark's own compiled CSS defines ".quick-toggle" twice (two
    # widget-version blocks); the later one sets color:#1d2021 on the base
    # (unchecked) state, but that declaration demonstrably loses its own
    # cascade tie in Gruvbox-Dark's actual rendering (unchecked toggles show
    # inherited cream text there, confirmed visually). Our parser's
    # last-occurrence-wins merge doesn't model that, so pulling it verbatim
    # + forcing !important made EVERY unchecked toggle's text wrongly dark
    # (2026-10-09 regression). Exclude it; let unchecked toggles inherit.
    '.quick-toggle': {'color'},
    # Fork hardcodes fixed-px spacing/padding around the Activities workspace
    # dots; stock uses em-based values that scale with font size. Visibly
    # different icon spacing vs stock Adwaita (2026-10-09 report) -- keep
    # stock's own spacing instead of the fork's fixed values.
    '#panel .panel-button#panelActivities StBoxLayout': {'padding', 'spacing'},
    # Fork-only addition (stock never sets -natural-hpadding specifically for
    # #panelActivities, only the generic .panel-button default) that widens
    # the Activities button further, compounding the same spacing mismatch.
    '#panel .panel-button#panelActivities': {'-natural-hpadding'},
    # Same mismatch for the right-side system-status icons (VPN, disk,
    # quick-settings grid, night light, keyboard, bluetooth, volume, power):
    # stock uses em-scaled icon-size with horizontal-only padding/margin;
    # fork hardcodes fixed px and switches margin/padding to all-sides,
    # visibly different icon spacing vs stock Adwaita (2026-10-09 report).
    '#panel .panel-button .system-status-icon': {'icon-size', 'margin', 'padding'},
    # Generic panel-button horizontal padding: stock uses 12px (6px minimum
    # under constraint), fork halves it to 6px flat -- affects every panel
    # button's internal width, including the aggregated quick-settings
    # button, compounding the same icon-spacing mismatch (2026-10-09).
    '#panel .panel-button': {'-natural-hpadding'},
}

stock_path, fork_path = sys.argv[1], sys.argv[2]
stock, _ = parse(stock_path)
fork, fork_order = parse(fork_path)

groups = defaultdict(list)
only_in_fork_groups = defaultdict(list)

for sel in fork_order:
    fork_props = fork[sel]
    excluded = EXCLUDE_PROPS.get(sel, set())
    if sel in stock:
        stock_props = stock[sel]
        diff_props = {k: v for k, v in fork_props.items() if k not in excluded and stock_props.get(k) != v}
        if diff_props:
            key = tuple(sorted(diff_props.items()))
            groups[key].append(sel)
    else:
        kept_props = {k: v for k, v in fork_props.items() if k not in excluded}
        if kept_props:
            key = tuple(sorted(kept_props.items()))
            only_in_fork_groups[key].append(sel)


# Properties that must win a same-specificity tie against stock's own
# declaration for the identical selector. Empirically confirmed (2026-10-09)
# that a plain (non-!important) background-color/color override in this
# sparse file loses to stock's plain declaration for the same selector --
# e.g. #panel's background-color lost to stock's #000000, and #dash
# .dash-background's lost to stock's #38383b -- even though the identical
# plain declaration wins when it's part of Gruvbox-Dark's much larger full
# stylesheet. Only applied to selectors stock ALSO defines (force_important),
# never to fork-only selectors, which have no competing stock rule to lose
# to, and never to properties besides background-color/color: forcing
# !important blanket-wide across every property once caused a real
# regression in the quick-settings toggle/arrow interaction, so the scope
# here is deliberately narrow.
FORCE_IMPORTANT_PROPS = {'background-color', 'color'}


def emit(groups, title, force_important=False):
    print(f"/* {title}: {sum(len(v) for v in groups.values())} selectors, {len(groups)} unique rule(s) */")
    for key, sels in groups.items():
        print(",\n".join(sels) + " {")
        for prop, val in key:
            if force_important and prop in FORCE_IMPORTANT_PROPS and '!important' not in val:
                val = f"{val} !important"
            print(f"    {prop}: {val};")
        print("}")


emit(groups, "recolored/restyled vs stock (all differing properties)", force_important=True)
print()
emit(only_in_fork_groups, "fork-only (extension integration, e.g. dash-to-dock)")
