# -*- coding: utf-8 -*-
"""Shared source-driven figure styling."""
from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon

import base_style as S

# ------------------------------------------------------------------ re-export frozen geometry
MM = S.MM
FULL_W_MM = S.FULL_W_MM
HALF_W_MM = S.HALF_W_MM
FULL_W = S.FULL_W
HALF_W = S.HALF_W
GUTTER_MM = S.GUTTER_MM
MARGIN_MM = S.MARGIN_MM
MIN_PANEL_MM = S.MIN_PANEL_MM
mm2pt = S.mm2pt
ramp_color = S.ramp_color
finalize = S.finalize
tiff_lzw_verify = S.tiff_lzw_verify
panel_letter = S.panel_letter
clean = S.clean
hide_all = S.hide_all
cell_absent = S.cell_absent

# ------------------------------------------------------------------ V3 spacing rhythm (mm)
SPACE = dict(page_margin_left=3.0, page_margin_right=3.0, page_margin_top=5.0,
             page_margin_bottom=4.0, column_gutter=6.0, panel_gutter=6.0,
             band_gap_small=5.0, band_gap_medium=7.0, band_gap_large=9.0,
             panel_padding=3.0, heading_to_content=2.5, glyph_row_pitch_min=6.0,
             separator_breathing_room=8.0, minimum_panel_width=30.0)

# ------------------------------------------------------------------ authoritative panel boxes
#: FIGSTYLE_V3.json -> page_geometry.panel_boxes_mm.  Each value is
#: ``[x0_mm, y0_mm_from_page_top, x1_mm, y1_mm_from_page_top]`` on a 178 mm wide page.
PAGE_BOXES = {
    "Fig1": {"page_h": 190.0,
             "a": [3.0, 5.0, 175.0, 50.0], "b": [3.0, 55.0, 175.0, 91.0],
             "c": [3.0, 98.0, 175.0, 142.0], "d": [3.0, 146.0, 175.0, 186.0]},
    "Fig2": {"page_h": 195.0,
             # ARB-14 rebalance: panel d's unused bottom slack (19.1 mm of dead band after the
             # ARB-13 consolidation) funds the a/b band.  a/b grow 79 -> 87 mm, which lets panel
             # b's eleven rows use a 7.15 mm pitch and therefore a legal >=5 mm inter-row run;
             # c keeps its exact 48 mm size and merely shifts 8 mm down, d shrinks 49 -> 41 mm.
             # Inter-panel gaps stay on scale: 5 (a/b->c), 5 (c->d), 4 mm page-bottom margin.
             "a": [3.0, 5.0, 84.0, 92.0], "b": [90.0, 5.0, 175.0, 92.0],
             "c": [3.0, 97.0, 175.0, 145.0], "d": [3.0, 150.0, 175.0, 191.0]},
    "Fig3": {"page_h": 190.0,
             "a": [3.0, 5.0, 175.0, 51.0], "b": [3.0, 56.0, 175.0, 102.0],
             "c_left": [3.0, 107.0, 84.0, 186.0], "c_right": [90.0, 107.0, 175.0, 186.0]},
    "Fig4": {"page_h": 195.0,
             "a": [3.0, 5.0, 92.0, 79.0], "b": [98.0, 5.0, 175.0, 79.0],
             "c": [3.0, 84.0, 175.0, 114.0],
             # y=152, leaving 97 x 39 mm (11.0 % of the page) of dead paper in the lower-left
             # quadrant while e ran to 191. d is extended to 174, which keeps the page at 195.0 mm
             # and satisfies FIGSTYLE_V3's own "zero empty slack at the page bottom".
             "d": [3.0, 120.0, 100.0, 174.0],
             "e": [106.0, 120.0, 175.0, 191.0]},
    "Fig5": {"page_h": 195.0,
             # ARB-10 N6: panel b was the emptiest object in the whole set (31 mm of box for two
             # numbers and two captions).  b is reduced to 21 mm and the stack shifts up 10 mm
             # with the 5 mm gap rhythm preserved; the page drops from 205 to 195 mm, still under
             # the 205 mm ceiling, and the 4 mm bottom margin is unchanged.
             "a": [3.0, 5.0, 175.0, 52.0], "b": [3.0, 57.0, 175.0, 78.0],
             "c": [3.0, 83.0, 175.0, 138.0], "d": [3.0, 143.0, 103.0, 191.0],
             "e": [109.0, 143.0, 175.0, 191.0]},
}

#: anchor panel per figure (FIGSTYLE_V3.json -> anchor_policy)
ANCHOR = {"Fig1": "c", "Fig2": "c", "Fig3": "c", "Fig4": "a", "Fig5": "c"}

#: panel letter / heading offsets.  FIGSTYLE_V3.json says the heading sits at ``x0 + 2.2 mm``,
#: but the bold 3.60 mm letter's own advance width is 2.0 mm starting at x0 + 0.6 mm, so 2.2 mm
#: physically collides with the letter ("aThe 36 fixed positions").  V3 uses x0 + 5.0 mm, which
#: keeps a 2.4 mm gap and is applied identically in all five figures.
LETTER_DX_MM = 0.6
LETTER_DY_MM = 3.5
HEADING_DX_MM = 5.0
HEADING_DY_MM = -0.5

#: Arial cap height / em, used to lock the letter and heading baselines to the same y
CAP_RATIO = 0.716

#: vertical band reserved at the top of every panel box for letter + heading
HEAD_RESERVE_MM = 5.0


def page_h(figkey):
    return PAGE_BOXES[figkey]["page_h"]


def box_mm(figkey, panel):
    """(x0, y0, x1, y1) in mm from the page top-left, from the authoritative table."""
    b = PAGE_BOXES[figkey][panel]
    return float(b[0]), float(b[1]), float(b[2]), float(b[3])


def box_wh_mm(figkey, panel):
    x0, y0, x1, y1 = box_mm(figkey, panel)
    return x1 - x0, y1 - y0


def head(fig, ax, figkey, panel, heading, weight="semibold", color=None):
    """Panel letter + heading with locked baselines, at the top of the panel box.

    FIGSTYLE_V3.json: letter at ``x0 + 0.6 mm``, heading at ``x0 + 2.2 mm``, both with
    ``baseline y = content_top + 3.5 mm``.  matplotlib anchors text by its box, so the two
    anchors are derived from Arial's cap height instead of being guessed.
    """
    x0, y0, x1, y1 = box_mm(figkey, panel)
    ph = page_h(figkey)
    base = y0 + LETTER_DY_MM
    letter_top = base - CAP_RATIO * FONT_MM["PANEL_LETTER"]
    head_top = base - CAP_RATIO * FONT_MM["PANEL_TITLE"]
    fig.text((x0 + LETTER_DX_MM) / FULL_W_MM, 1.0 - letter_top / ph, panel,
             fontsize=FS("PANEL_LETTER"), fontweight="bold", color=COL["INK"],
             ha="left", va="top")
    if heading:
        ax.text(HEADING_DX_MM / (x1 - x0), 1.0 - (head_top - y0) / (y1 - y0), heading,
                transform=ax.transAxes, fontsize=FS("PANEL_TITLE"), fontweight=weight,
                color=color or COL["INK"], ha="left", va="top")


def content_box_mm(figkey, panel):
    """Panel box minus the reserved letter/heading band."""
    x0, y0, x1, y1 = box_mm(figkey, panel)
    return x0, y0 + HEAD_RESERVE_MM, x1, y1


# ------------------------------------------------------------------ V3 palette (AMD-02)
COL = dict(
    # ---- organ identity ---------------------------------------------------------------
    # AMD-02: slate darkened #7C8A99 -> #647285 (4.90:1) because it carries BTB row labels
    BTB="#647285", BTB_DK="#647285",
    BBB="#4A6E96", BBB_DK="#37587D",          # 5.30:1 / 7.36:1
    # ---- evidence states --------------------------------------------------------------
    SUPPORTED="#2F7E78",                       # primary-supported deep teal (only meaning)
    NOT_SUPPORTED="#4A5057",                   # neutral charcoal: non-support, OPEN marker
    SPEC_SUPPORTED="#4A5057",                  # green deleted; specificity support = filled charcoal
    RING="#C9CDD1",                            # partial -> RING glyph, RULE_STRONG outline
    # ---- post-freeze sensitivity: ONE hue, TWO values (AMD-02) ------------------------
    SENSITIVITY="#A9762F",                     # mark value, 3.95:1 (>= 3:1 non-text)
    SENSITIVITY_DK="#A9762F",
    SENSITIVITY_TEXT="#8F6014",                # the ONLY amber value permitted to carry type
    # ---- not evaluable ----------------------------------------------------------------
    NOT_EVALUABLE="#F4F3F1", NOT_EVALUABLE_HATCH="#C2BEB8",
    # ---- structural ink ---------------------------------------------------------------
    INK="#23282D", INK2="#6B7076",             # the only two values that may carry text
    RULE="#EAECED", RULE_STRONG="#C9CDD1",
    WARN="#A9762F",
    PAPER="#FFFFFF",
)
#: AMD-02 colour_system.text_colour_contract.  INK and INK2 are the only values permitted to
#: carry type; state colours are carried by glyphs.  (BTB slate 4.90:1 and BBB blue 5.30:1 also
#: clear the 4.5:1 lettering threshold and are named as row/label colours by
#: state_encoding_matrix, so they are used for organ-identity row and column labels only.)
TEXT_INKS = ("#23282D", "#6B7076")
#: AMD-02 deleted INK3 (#9BA0A5, 2.64:1) outright; the key is intentionally absent so that any
#: accidental use of the old token raises KeyError instead of shipping a failing grey.
STATE_LABEL_COLOURS = ("#647285", "#4A6E96")
# aliases kept so V2-era call sites keep their meaning
COL.update(dict(
    PRIMARY_ELIGIBLE=COL["BBB_DK"],
    STABLE_INELIGIBLE=COL["RULE_STRONG"],
    REPLICATED=COL["SUPPORTED"],
    PARTIAL=COL["RING"],
    PRIMARY_NULL=COL["INK"],
    SENSITIVITY_RING=COL["SENSITIVITY_DK"],
    POS="#A8BFD4", NEG="#C1926F", MID="#F7F5F2",
    RAMP_LOW="#F3F5F7", RAMP_MID="#A8BFD4", RAMP_HIGH=COL["BBB_DK"],
    NEG_OUTLINE=COL["INK"],
))
RAMP = [COL["RAMP_LOW"], COL["RAMP_MID"], COL["RAMP_HIGH"]]

FORBIDDEN_COLOURS = S.FORBIDDEN_COLOURS

# amber budget (FIGSTYLE_V3.json -> sensitivity_accent.amber_budget as amended by AMD-02 and
# is incompatible with the locked captions (Fig2b's five exclusion ticks, Fig3b's six diamonds),
# so max_marks_per_panel is withdrawn.  The weight cap is the gate.
AMBER_BUDGET = dict(count_capped=False,
                    max_ink_area_mm2_per_panel=12.0,
                    max_ink_share_of_figure_pct=1.0,
                    max_text_words_per_figure=4, max_labels_per_figure=1,
                    permitted_forms=["thin rule/tick <= 0.45 pt (decorative)",
                                     "thin rule/stem <= 0.60 pt (data-bearing)",
                                     "small OPEN outline glyph <= 0.65 pt",
                                     "ONE label per figure, <= 4 words, #8F6014"],
                    forbidden_forms=["any amber fill, cell, block, bar, chip, badge",
                                     "any amber background tint, frame or border",
                                     "any amber rule above 0.90 pt",
                                     "any amber text other than the one <= 4-word label"])
#: the one amber value permitted as type (AMD-02), and its four-word label cap
AMBER_TEXT = COL["SENSITIVITY_TEXT"]

# ------------------------------------------------------------------ V3 strokes (pt @ 178 mm)
STROKE = dict(HAIR=0.25, RULE=0.30, AXIS=0.35, TICK=0.35, SECONDARY=0.45, CONNECTOR=0.45,
              MAIN=0.60, GLYPH=0.65, EMPHASIS=0.90, DATA_MAIN=0.60, DATA_SECONDARY=0.45,
              HATCH=0.30, AXIS_FRAME=0.35)
Z = dict(BAND=1.2, CELL=1.5, FILL=2.0, RULE=2.4, GLYPH=5.0, TEXT=6.0)

#: marker diameters (pt), FIGSTYLE_V3.json -> markers.size_pt
MARKER = dict(data_marker=3.0, row_glyph=3.2, big_glyph=3.8, bullet=2.2)

#: half-length in mm of a median tick drawn across a reference bar
TICK_HALF_MM = 1.4

# ------------------------------------------------------------------ V3 type scale (mm)
# AMD-01: the floor is 1.90 mm, identical to V2; the top of the scale is raised instead.
FONT_MM = dict(PANEL_LETTER=3.60, PANEL_TITLE=2.80, SUBSECTION=2.45, AXIS=2.10, BODY=2.10,
               TICK=1.95, LEGEND=1.95, ANNOTATION=1.90, FIGURE_TITLE=3.10,
               BIG_NUMBER=5.20, MID_NUMBER=3.40)
_FS = {k: S.mm2pt(v) for k, v in FONT_MM.items()}


def FS(token):
    return _FS[token]


MIN_FONT_PT = _FS["ANNOTATION"] - 0.01          # re-derived from the 1.90 mm token (AMD-01)
S.MIN_FONT_PT = MIN_FONT_PT

FONT_FAMILY = S.FONT_FAMILY
FONT_FILE_KEYS = S.FONT_FILE_KEYS

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": FONT_FAMILY,
    "font.size": FS("TICK"),
    "axes.linewidth": STROKE["AXIS_FRAME"],
    "axes.edgecolor": COL["RULE_STRONG"],
    "axes.labelcolor": COL["INK"],
    "axes.labelsize": FS("AXIS"),
    "xtick.color": COL["INK2"],
    "ytick.color": COL["INK2"],
    "xtick.labelsize": FS("TICK"),
    "ytick.labelsize": FS("TICK"),
    "xtick.major.width": STROKE["TICK"],
    "ytick.major.width": STROKE["TICK"],
    "xtick.major.size": 1.4,
    "ytick.major.size": 1.4,
    "legend.fontsize": FS("LEGEND"),
    "legend.frameon": False,
    "text.color": COL["INK"],
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "hatch.linewidth": STROKE["HATCH"],
    # FIGSTYLE_V3.json font.mathtext: no mathtext anywhere (it silently falls back to
    # DejaVu Italic and is the source of the V2 Fig5d stray glyph).
    "mathtext.default": "regular",
    "mathtext.fontset": "dejavusans",
})

DRAWN = S.DRAWN
_register = S._register
CUR_FIG = None


# ------------------------------------------------------------------ text primitives
def panel(fig, x_mm, y_mm_top, letter, page_h_mm):
    """Panel letter: bold INK, no decoration (FIGSTYLE_V3.json -> panel_letter)."""
    return fig.text(x_mm / FULL_W_MM, 1.0 - y_mm_top / page_h_mm, letter,
                    fontsize=FS("PANEL_LETTER"), fontweight="bold", color=COL["INK"],
                    ha="left", va="top")


def title(ax, x, y, s, color=None, ha="left", va="top", transform=None, weight="semibold"):
    """Panel heading: semibold, 3-6 words, sentence case, INK."""
    return ax.text(x, y, s, transform=transform or ax.transAxes, fontsize=FS("PANEL_TITLE"),
                   fontweight=weight, color=color or COL["INK"], ha=ha, va=va)


def subtitle(ax, x, y, s, color=None, ha="left", va="top", transform=None, linespacing=1.3,
             size=None, weight="semibold"):
    return ax.text(x, y, s, transform=transform or ax.transAxes,
                   fontsize=FS(size or "SUBSECTION"), fontweight=weight,
                   color=color or COL["INK2"], ha=ha, va=va, linespacing=linespacing)


def body(ax, x, y, s, color=None, ha="left", va="top", transform=None, linespacing=1.3,
         size="BODY", weight="normal", style="normal", rotation=0):
    return ax.text(x, y, s, transform=transform or ax.transAxes, fontsize=FS(size),
                   fontweight=weight, style=style, color=color or COL["INK"], ha=ha, va=va,
                   linespacing=linespacing, rotation=rotation)


def annot(ax, x, y, s, color=None, ha="left", va="top", transform=None, linespacing=1.3,
          weight="normal", style="normal", size=None, rotation=0):
    # ARB-15: the default was ANNOTATION, the 1.90 mm floor, which flat-lined the lower half of
    # FIGSTYLE_V3's hierarchy -- a tick value, a column head, a state key and a footnote all
    # shipped at the same size.  Plain reference text (row labels, column heads, comparator
    # names, tick values, convention keys) now defaults to LEGEND 1.95 mm; strings whose role is
    # decode-critical are raised to AXIS 2.10 mm explicitly at the call site; only genuinely
    # tertiary text is still set with size="ANNOTATION".
    return ax.text(x, y, s, transform=transform or ax.transAxes,
                   fontsize=FS(size or "LEGEND"),
                   fontweight=weight, style=style, color=color or COL["INK2"], ha=ha, va=va,
                   linespacing=linespacing, rotation=rotation)


def figure_title(fig, x_mm, y_mm_top, s, page_h_mm, color=None):
    """Kept for API compatibility only. V3 forbids an in-canvas figure title; never call it."""
    return fig.text(x_mm / FULL_W_MM, 1.0 - y_mm_top / page_h_mm, s,
                    fontsize=FS("FIGURE_TITLE"), fontweight="bold", color=color or COL["INK"],
                    ha="left", va="top")


def number(ax, x, y, s, size="BIG_NUMBER", color=None, ha="center", va="center",
           weight="bold"):
    """The one permitted visual anchor device: a large figure set in ink or a state colour."""
    return ax.text(x, y, s, transform=ax.transAxes, fontsize=FS(size), fontweight=weight,
                   color=color or COL["INK"], ha=ha, va=va)


# ------------------------------------------------------------------ rules / separators
def rule(ax, x0, x1, y, color=None, lw=None, transform=None, alpha=1.0, ls="-"):
    return ax.plot([x0, x1], [y, y], color=color or COL["RULE"],
                   lw=STROKE["RULE"] if lw is None else lw, solid_capstyle="butt",
                   transform=transform or ax.transAxes, alpha=alpha, zorder=Z["RULE"], ls=ls)


def vrule(ax, x, y0, y1, color=None, lw=None, transform=None, alpha=1.0, ls="-"):
    return ax.plot([x, x], [y0, y1], color=color or COL["RULE"],
                   lw=STROKE["RULE"] if lw is None else lw, solid_capstyle="butt",
                   transform=transform or ax.transAxes, alpha=alpha, ls=ls, zorder=Z["RULE"])


def gate(ax, x, y0, y1, label=None, label_dx=0.010, label_dy=0.020, transform=None,
         color=None, ha="left", va="bottom"):
    """The one emphasis-strength element of a panel: the unchanged 0.70 coverage gate."""
    tr = transform or ax.transAxes
    col = color or COL["INK2"]
    ax.plot([x, x], [y0, y1], color=col, lw=STROKE["EMPHASIS"], solid_capstyle="butt",
            transform=tr, zorder=Z["RULE"] + 0.5, clip_on=False)
    if label:
        # ARB-15: the gate label is decode-critical ("0.70 gate" tells the reader what the one
        # emphasis-strength rule means), so it is set at the AXIS token, not at the floor.
        ax.text(x + label_dx, y1 + label_dy, label, transform=tr, fontsize=FS("AXIS"),
                color=COL["INK2"], ha=ha, va=va, zorder=Z["TEXT"])
    return col


def band(ax, x0, x1, y, lw=None, kind="sensitivity", transform=None):
    """Primary vs post-freeze sensitivity marker: a single thin rule, never a box frame."""
    col = COL["SENSITIVITY_DK"] if kind == "sensitivity" else COL["INK"]
    return ax.plot([x0, x1], [y, y], color=col,
                   lw=(STROKE["SECONDARY"] if lw is None else lw), solid_capstyle="butt",
                   transform=transform or ax.transAxes, zorder=Z["RULE"] + 0.5)


def zero_line(ax, x0, x1, y, transform=None, color=None, lw=None):
    """One unified zero line per panel, 0.45 pt RULE_STRONG (never an emphasis weight)."""
    return ax.plot([x0, x1], [y, y], color=color or COL["RULE_STRONG"],
                   lw=STROKE["SECONDARY"] if lw is None else lw, solid_capstyle="butt",
                   transform=transform or ax.transAxes, zorder=Z["RULE"])


def thin_frame(ax, x0, y0, w, h, color=None, lw=None, z=None):
    """Retained for API compatibility. V3 forbids frames: do not call this in a V3 figure."""
    return ax.add_patch(Rectangle((x0, y0), w, h, facecolor="none",
                                  edgecolor=color or COL["SENSITIVITY_DK"],
                                  lw=STROKE["EMPHASIS"] if lw is None else lw,
                                  transform=ax.transAxes, zorder=z or (Z["BAND"] + 0.2),
                                  clip_on=False))


def arrow(ax, x0, y0, x1, y1, color=None, lw=None, ms=4.0, transform=None, ls="-", z=None,
          head=True):
    if not head:
        return ax.plot([x0, x1], [y0, y1], color=color or COL["INK2"],
                       lw=STROKE["SECONDARY"] if lw is None else lw, ls=ls,
                       solid_capstyle="butt", transform=transform or ax.transAxes,
                       zorder=z or Z["GLYPH"])
    from matplotlib.patches import FancyArrowPatch
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=ms,
                                 lw=STROKE["SECONDARY"] if lw is None else lw, ls=ls,
                                 color=color or COL["INK2"], shrinkA=0, shrinkB=0,
                                 transform=transform or ax.transAxes, zorder=z or Z["GLYPH"]))


def struck_through(ax, x0, x1, y, slash_half=0.010, color=None, transform=None, ls_dash=(0, (2.4, 1.8))):
    """Prohibited backward direction: 0.45 pt dashed rule + one short slash, no arrow head."""
    tr = transform or ax.transAxes
    col = color or COL["INK2"]
    ax.plot([x0, x1], [y, y], color=col, lw=STROKE["SECONDARY"], ls=ls_dash,
            solid_capstyle="butt", transform=tr, zorder=Z["GLYPH"])
    xm = (x0 + x1) / 2.0
    ax.plot([xm - slash_half, xm + slash_half], [y - slash_half, y + slash_half],
            color=col, lw=STROKE["SECONDARY"], solid_capstyle="butt", transform=tr,
            zorder=Z["GLYPH"])
    return col


def connector(ax, pts, color=None, lw=None, ls="-", z=None):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return ax.plot(xs, ys, color=color or COL["RULE_STRONG"],
                   lw=STROKE["SECONDARY"] if lw is None else lw, ls=ls,
                   solid_capstyle="round", zorder=z or Z["RULE"])


# ------------------------------------------------------------------ state glyphs
def open_marker(ax, x, y, marker="o", s=22, ec=None, lw=None, z=None):
    """non-support / non-replication: OPEN marker, charcoal outline, no fill."""
    ax.scatter([x], [y], marker=marker, s=s, facecolors="white",
               edgecolors=ec or COL["NOT_SUPPORTED"],
               linewidths=STROKE["GLYPH"] if lw is None else lw, zorder=z or Z["GLYPH"])
    _register("open_marker", x=float(x), y=float(y))


def filled_marker(ax, x, y, color, marker="o", s=22, ec="none", lw=0.0, z=None, alpha=1.0):
    ax.scatter([x], [y], marker=marker, s=s, facecolors=color, edgecolors=ec,
               linewidths=lw, zorder=z or Z["GLYPH"], alpha=alpha)
    _register("filled_marker", x=float(x), y=float(y), color=color)


def solid_marker(ax, x, y, color, s=22, z=None):
    return filled_marker(ax, x, y, color, s=s, z=z)


def ring_marker(ax, x, y, color=None, s=22, lw=None, z=None):
    """partial: RING glyph, RULE_STRONG outline, never filled (green and pale steel deleted)."""
    ax.scatter([x], [y], marker="o", s=s, facecolors="white",
               edgecolors=color or COL["RING"],
               linewidths=STROKE["GLYPH"] if lw is None else lw, zorder=z or Z["GLYPH"])
    _register("ring_marker", x=float(x), y=float(y))


def ring_outline(ax, x, y, color=None, s=27, lw=None, z=None):
    """A hollow ring drawn OVER another glyph (e.g. the Fig3a Spearman ring over a filled teal
    replication dot).  facecolors='none' so the underlying state colour stays visible; a filled
    ring would paint the state out, which is how the first Fig3a render lost C01's teal."""
    ax.scatter([x], [y], marker="o", s=s, facecolors="none",
               edgecolors=color or COL["SENSITIVITY"],
               linewidths=STROKE["GLYPH"] if lw is None else lw,
               zorder=(z or Z["GLYPH"]) + 1.0)
    _register("ring_outline", x=float(x), y=float(y))


def partial_ring(ax, x, y, color=None, s=36, lw=1.8, z=None):
    """The ``partial`` state as a GENUINE ring: a thick annulus on a white face, deliberately
    larger and heavier than the open non-support marker (ARB-08 P4).  With a same-size thin
    hollow circle the two states differed only in stroke colour and were identical in greyscale;
    now filled / ring / open / hatch are four distinct shapes with no colour needed."""
    ax.scatter([x], [y], marker="o", s=s, facecolors="white",
               edgecolors=color or COL["INK2"], linewidths=lw, zorder=z or Z["GLYPH"])
    _register("partial_ring", x=float(x), y=float(y))


def open_diamond(ax, x, y, s=24, color=None, z=None, lw=None):
    """BTB generality warning: open amber diamond only, never filled."""
    ax.scatter([x], [y], marker="D", s=s, facecolors="white",
               edgecolors=color or COL["SENSITIVITY_DK"],
               linewidths=STROKE["GLYPH"] if lw is None else lw, zorder=z or Z["GLYPH"])
    _register("warning_diamond", x=float(x), y=float(y))


warning_diamond = open_diamond


def open_square(ax, x, y, s=16, color=None, z=None):
    """A 1.5 mm open amber square outline (Fig5b 78.1 % marker)."""
    ax.scatter([x], [y], marker="s", s=s, facecolors="white",
               edgecolors=color or COL["SENSITIVITY_DK"], linewidths=STROKE["GLYPH"],
               zorder=z or Z["GLYPH"])
    _register("open_square", x=float(x), y=float(y))


def rho_glyph(ax, x, y, fillstyle, ms=4.0, color=None, z=None):
    """ARB-18: one fixed-size magnitude square, coded by FILL STATE alone.

    fillstyle "none" = LOW, "bottom" = MID, "full" = HIGH.  Achromatic, because the amber budget
    permits no fill; square, because circles in Fig5 already mean sensitivity-positive (filled
    teal) and evaluable (open).  The column carries no axis and no numeric values, so the glyph
    cannot be read as a value on the neighbouring 0.000-0.018 delta-cosine scale.
    """
    col = color or COL["INK2"]
    ax.plot([x], [y], marker="s", markersize=ms, fillstyle=fillstyle,
            markerfacecolor="none" if fillstyle == "none" else col,
            markeredgecolor=col, markeredgewidth=STROKE["GLYPH"], linestyle="none",
            zorder=z or Z["GLYPH"])
    _register("rho_glyph", x=float(x), y=float(y), fillstyle=fillstyle)


def hatched_field(ax, x, y, w, h, z=None):
    """NOT_EVALUABLE: #F4F3F1 fill + #C2BEB8 hatch at 0.30 pt, no border, achromatic."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=COL["NOT_EVALUABLE"],
                           edgecolor="none", lw=0, zorder=z or Z["CELL"]))
    ax.add_patch(Rectangle((x, y), w, h, facecolor="none",
                           edgecolor=COL["NOT_EVALUABLE_HATCH"], lw=0, hatch="////",
                           zorder=(z or Z["CELL"]) + 0.1))
    _register("not_evaluable_cell", x=float(x), y=float(y), source="hatch")


def not_evaluable_swatch(ax, x, y, w=0.020, h=0.055, z=None):
    return hatched_field(ax, x, y - h / 2, w, h, z)


def cell_not_evaluable(ax, x, y, w=1.0, h=1.0, lw=None, z=None):
    return hatched_field(ax, x, y, w, h, z)


def hatch_swatch(ax, x, y, w=0.020, h=0.055, z=None):
    return not_evaluable_swatch(ax, x, y, w, h, z)


def cell_plain(ax, x, y, w=1.0, h=1.0, z=None):
    """EVALUABLE cell ground: pure white, no border, so the marker is the only mark."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor="none", lw=0,
                           zorder=z or Z["CELL"]))
    _register("evaluable_cell", x=float(x), y=float(y))


def cell_convergent(ax, x, y, w=1.0, h=1.0, color=None, z=None):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color or COL["SUPPORTED"],
                           edgecolor="none", lw=0, zorder=z or Z["FILL"]))
    _register("convergent_cell", x=float(x), y=float(y))


def marker_nonconvergent(ax, x, y, s=22, z=None):
    return open_marker(ax, x, y, s=s, z=z)


def dot_interval(ax, x, lo, hi, color, ms=2.8, lw=None, z=None):
    ax.plot([x, x], [lo, hi], color=color, lw=STROKE["SECONDARY"] if lw is None else lw,
            solid_capstyle="butt", zorder=z or Z["FILL"])
    # scatter, not plot(marker=...): a one-point Line2D leaves an empty stroked path on the
    # default colour cycle in the SVG/PDF (ARB-06).  scatter's s = ms**2 keeps the diameter.
    ax.scatter([x], [(lo + hi) / 2.0], marker="o", s=ms ** 2, facecolors=color,
               edgecolors="none", zorder=(z or Z["FILL"]) + 0.1)
    _register("interval", x=float(x), lo=float(lo), hi=float(hi))


def seg_bar(ax, x0, y, w, fractions, colors, h=0.24, gap=0.0, z=None):
    x = x0
    for f, c in zip(fractions, colors):
        ww = w * f
        ax.add_patch(Rectangle((x, y), max(ww, 0.0), h, facecolor=c, edgecolor="none",
                               lw=0, zorder=z or Z["FILL"]))
        x += ww + gap
    _register("stacked_bar", x=float(x0), y=float(y))


def dumbbell(ax, y, xa, xb, color_a, color_b, lw=None, ms=3.4, s=20, conn_color=None,
             ms_b=None):
    """Two-point dumbbell: neutral connector, OPEN start (organ colour), FILLED end (state).

    The two ends are scatter collections, not one-point ``Line2D`` artists: a one-point
    ``ax.plot(marker=...)`` leaves an empty stroked path on the default colour cycle in the
    delivered SVG/PDF (ARB-06).  ``s = ms**2`` preserves the rendered diameter.
    """
    ax.plot([xa, xb], [y, y], color=conn_color or COL["RULE"],
            lw=STROKE["SECONDARY"] if lw is None else lw, solid_capstyle="round",
            zorder=Z["FILL"])
    ax.scatter([xa], [y], marker="o", s=ms ** 2, facecolors="white", edgecolors=color_a,
               linewidths=STROKE["GLYPH"], zorder=Z["GLYPH"])
    d_b = ms_b if ms_b else ms * 1.08
    ax.scatter([xb], [y], marker="o", s=d_b ** 2, facecolors=color_b, edgecolors="none",
               zorder=Z["GLYPH"])
    _register("dumbbell", y=float(y), a=float(xa), b=float(xb))


def lollipop(ax, y, x0, xv, color, lw=None, ms=3.2, z=None):
    ax.plot([x0, xv], [y, y], color=color, lw=STROKE["MAIN"] if lw is None else lw,
            solid_capstyle="butt", zorder=z or Z["FILL"])
    ax.scatter([xv], [y], marker="o", s=ms ** 2, facecolors=color, edgecolors="none",
               zorder=(z or Z["FILL"]) + 0.2)
    _register("lollipop", y=float(y), v=float(xv))


# ------------------------------------------------------------------ measure (V3 font gate)
def measure(fig, overlap_area_px=110.0, min_font_pt=None, allow_out_of_canvas=()):
    """Identical gate to the frozen V1 layer; the minimum is re-derived from 1.90 mm."""
    return S.measure(fig, overlap_area_px=overlap_area_px,
                     min_font_pt=MIN_FONT_PT if min_font_pt is None else min_font_pt,
                     allow_out_of_canvas=allow_out_of_canvas)


# ------------------------------------------------------------------ V1/V2 compatibility shims
def bracket(ax, x0, y0, x1, y1, kind="primary", lw=None, transform=None, label=None,
            label_va="bottom", color=None):
    tr = transform or ax.transAxes
    col = color or (COL["INK"] if kind == "primary" else COL["SENSITIVITY_DK"])
    ax.plot([x0, x0, x1, x1], [y0, y1, y1, y1], transform=tr, color=col,
            lw=STROKE["EMPHASIS"] if lw is None else lw, clip_on=False,
            solid_capstyle="butt", zorder=Z["RULE"])
    if label:
        ax.text(x0, y1, label, transform=tr, fontsize=FS("ANNOTATION"), color=col,
                fontweight="bold", ha="left", va=label_va)
    return col


def band_label(fig, x, y, kind, ha="left", va="center", text=None):
    if kind == "primary":
        col, txt = COL["INK"], "PRESPECIFIED PRIMARY"
    else:
        col, txt = COL["SENSITIVITY_DK"], "POST-FREEZE SENSITIVITY"
    return fig.text(x, y, text or txt, fontsize=FS("SUBSECTION"), fontweight="semibold",
                    color=col, ha=ha, va=va)


def subsection(ax, x, y, s, color=None, ha="left", va="top", transform=None, italic=False):
    return subtitle(ax, x, y, s, color=color, ha=ha, va=va, transform=transform)
