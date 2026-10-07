# -*- coding: utf-8 -*-
"""Shared source-driven figure styling."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D

import bbbtb_common as C

# ------------------------------------------------------------------ canvas (mm)
MM = 1.0 / 25.4
FULL_W_MM = 178.0
HALF_W_MM = 85.0
FULL_W = FULL_W_MM * MM
HALF_W = HALF_W_MM * MM
FULL_H_BUDGET_MM = 225.0
GUTTER_MM = 4.0
MARGIN_MM = 3.0
MIN_PANEL_MM = 14.0

# ------------------------------------------------------------------ colour system
COL = dict(
    # barrier identity
    BTB="#5A6B7B", BBB="#2F5D8A",
    # family state
    PRIMARY_ELIGIBLE="#1F4E79", STABLE_INELIGIBLE="#B9C6D2",
    REPLICATED="#1B7F79", NOT_REPLICATED="#FFFFFF",
    # measurement states
    NOT_EVALUABLE="#E8E8E8", NOT_EVALUABLE_HATCH="#9A9A9A",
    NOT_SUPPORTED="#8C8C8C", SPEC_SUPPORTED="#4C8C4A",
    # bands
    PRIMARY_NULL="#34404A", SENSITIVITY="#E08A3C", SENSITIVITY_RING="#A65A18",
    # diverging scale (only continuous scale allowed)
    POS="#8AA9C9", NEG="#B4643C", MID="#F5F3EF",
    # ramp (only monotone ramp allowed)
    RAMP_LOW="#F2F4F6", RAMP_MID="#8FB0CC", RAMP_HIGH="#1F4E79",
    # ink
    INK="#1A1A1A", INK2="#5C5C5C", RULE="#D8D8D8", WARN="#B07A2A",
)
RAMP = [COL["RAMP_LOW"], COL["RAMP_MID"], COL["RAMP_HIGH"]]

FORBIDDEN_COLOURS = ["#FF0000", "#00FF00", "#0000FF", "jet", "rainbow", "viridis",
                     "#FF0000", "#00FF00"]

# ------------------------------------------------------------------ typography (mm -> pt at final size)
FONT_MM = dict(PANEL_LETTER=3.2, SUBSECTION=2.5, AXIS=2.3, TICK=2.0, LEGEND=2.0,
               ANNOTATION=1.9, FIGURE_TITLE=3.0)
FONT_FAMILY = ["Arial", "Liberation Sans", "DejaVu Sans", "Noto Sans", "Segoe UI"]
FONT_FILE_KEYS = ["arial", "liberationsans", "dejavusans", "notosans", "segoeui"]


def mm2pt(mm):
    return mm / 25.4 * 72.0


def FS(token):
    return mm2pt(FONT_MM[token])


MIN_FONT_PT = FS("ANNOTATION") - 0.01  # 1.9 mm is the smallest permitted type

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": FONT_FAMILY,
    "font.size": FS("TICK"),
    "axes.linewidth": 0.5,
    "axes.edgecolor": COL["RULE"],
    "axes.labelcolor": COL["INK"],
    "axes.labelsize": FS("AXIS"),
    "xtick.color": COL["INK2"],
    "ytick.color": COL["INK2"],
    "xtick.labelsize": FS("TICK"),
    "ytick.labelsize": FS("TICK"),
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "xtick.major.size": 1.6,
    "ytick.major.size": 1.6,
    "legend.fontsize": FS("LEGEND"),
    "legend.frameon": False,
    "text.color": COL["INK"],
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "hatch.linewidth": 0.45,
})

CUR_FIG = None
DRAWN = []


def _register(kind, **kw):
    DRAWN.append(dict(kind=kind, **kw))


# ------------------------------------------------------------------ text helpers
def panel_letter(fig, x, y, s, color=None, italic=False):
    t = fig.text(x, y, s, fontsize=FS("PANEL_LETTER"), fontweight="bold",
                 style="italic" if italic else "normal", color=color or COL["INK"],
                 ha="left", va="top")
    return t


def subsection(ax, x, y, s, color=None, ha="left", va="top", transform=None, italic=False):
    return ax.text(x, y, s, transform=transform or ax.transAxes, fontsize=FS("SUBSECTION"),
                   fontweight="bold", style="italic" if italic else "normal",
                   color=color or COL["INK2"], ha=ha, va=va)


def band_label(fig, x, y, kind, ha="left", va="center", text=None):
    """PRESPECIFIED PRIMARY (dark neutral) vs POST-FREEZE SENSITIVITY (amber)."""
    if kind == "primary":
        col, txt = COL["PRIMARY_NULL"], "PRESPECIFIED PRIMARY"
    else:
        col, txt = COL["SENSITIVITY_RING"], "POST-FREEZE SENSITIVITY"
    return fig.text(x, y, text or txt, fontsize=FS("SUBSECTION"), fontweight="bold",
                    color=col, ha=ha, va=va)


def bracket(ax, x0, y0, x1, y1, kind="primary", lw=1.6, transform=None, label=None,
            label_va="bottom", color=None):
    tr = transform or ax.transAxes
    col = color or (COL["PRIMARY_NULL"] if kind == "primary" else COL["SENSITIVITY_RING"])
    ax.plot([x0, x0, x1, x1], [y0, y1, y1, y1], transform=tr, color=col, lw=lw,
            clip_on=False, solid_capstyle="butt")
    if label:
        ax.text(x0, y1, label, transform=tr, fontsize=FS("ANNOTATION"), color=col,
                fontweight="bold", ha="left", va=label_va)
    return col


def clean(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(s in keep)


def hide_all(ax):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])


# ------------------------------------------------------------------ state glyphs
def cell_not_evaluable(ax, x, y, w=1.0, h=1.0, lw=0.5, z=1.4):
    """NOT_EVALUABLE = achromatic 45-degree hatch. Never red, never a filled colour."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor=COL["NOT_EVALUABLE"],
                           edgecolor=COL["RULE"], lw=lw, zorder=z))
    ax.add_patch(Rectangle((x, y), w, h, facecolor="none", edgecolor=COL["NOT_EVALUABLE_HATCH"],
                           lw=0, hatch="////", zorder=z + 0.1))
    _register("not_evaluable_cell", x=float(x), y=float(y), source="hatch")


def cell_absent(ax, x, y, w=1.0, h=1.0, lw=0.5, z=1.4):
    """No fixed position here (reserved but outside the drawn block): plain empty."""
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=COL["RULE"], lw=lw, zorder=z))


def cell_convergent(ax, x, y, w=1.0, h=1.0, color=None, z=2.0):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=color or COL["REPLICATED"],
                           edgecolor="white", lw=0.5, zorder=z))
    _register("convergent_cell", x=float(x), y=float(y))


def marker_nonconvergent(ax, x, y, s=22, z=5):
    """EVALUABLE non-convergent = open white marker with a dark outline."""
    ax.scatter([x], [y], marker="o", s=s, facecolors="white", edgecolors=COL["NEG_OUTLINE"]
               if "NEG_OUTLINE" in COL else COL["PRIMARY_NULL"], linewidths=0.9, zorder=z)
    _register("open_marker", x=float(x), y=float(y), source="observed_cosine")


COL["NEG_OUTLINE"] = COL["PRIMARY_NULL"]


def open_marker(ax, x, y, marker="o", s=26, ec=None, lw=0.9, z=5):
    ax.scatter([x], [y], marker=marker, s=s, facecolors="white",
               edgecolors=ec or COL["PRIMARY_NULL"], linewidths=lw, zorder=z)
    _register("open_marker", x=float(x), y=float(y))


def filled_marker(ax, x, y, color, marker="o", s=26, ec="none", lw=0.0, z=5):
    ax.scatter([x], [y], marker=marker, s=s, facecolors=color, edgecolors=ec,
               linewidths=lw, zorder=z)
    _register("filled_marker", x=float(x), y=float(y), color=color)


def warning_diamond(ax, x, y, s=30, color=None, z=6):
    """BTB generality warning glyph: open diamond (terminology lock T01)."""
    ax.scatter([x], [y], marker="D", s=s, facecolors="white",
               edgecolors=color or COL["WARN"], linewidths=1.0, zorder=z)
    _register("warning_diamond", x=float(x), y=float(y))


def dot_interval(ax, x, lo, hi, color, ms=3.2, lw=0.9, z=5):
    ax.plot([x, x], [lo, hi], color=color, lw=lw, solid_capstyle="butt", zorder=z)
    ax.plot([x], [(lo + hi) / 2.0], marker="o", ms=ms, color=color, zorder=z + 0.1)
    _register("interval", x=float(x), lo=float(lo), hi=float(hi))


def ramp_color(v, lo, hi):
    """Only continuous scale permitted: #F2F4F6 -> #8FB0CC -> #1F4E79."""
    if hi <= lo:
        return RAMP[2]
    t = min(1.0, max(0.0, (v - lo) / (hi - lo)))
    if t < 0.5:
        a, b, u = RAMP[0], RAMP[1], t / 0.5
    else:
        a, b, u = RAMP[1], RAMP[2], (t - 0.5) / 0.5

    def hx(h):
        h = h.lstrip("#")
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)
    c = hx(a) * (1 - u) + hx(b) * u
    return "#%02X%02X%02X" % tuple(int(round(x)) for x in c)


def seg_bar(ax, x0, y, w, fractions, colors, gap=0.0):
    """100% horizontal stacked bar (composition only, L3 permitted)."""
    x = x0
    for f, c in zip(fractions, colors):
        ww = w * f
        ax.add_patch(Rectangle((x, y), ww, 0.34, facecolor=c, edgecolor="white",
                               lw=0.4, zorder=3))
        x += ww + gap
    _register("stacked_bar", x=float(x0), y=float(y))


# ------------------------------------------------------------------ export
def finalize(fig, outdir, stem, dpi_tiff=600, dpi_png=300, tight=False):
    """Write SVG + PDF (source of truth), 600 dpi LZW TIFF and a PNG preview."""
    global CUR_FIG
    os.makedirs(outdir, exist_ok=True)
    paths = {}
    for ext in ("svg", "pdf", "png", "tiff"):
        p = os.path.join(outdir, "%s.%s" % (stem, ext))
        if ext == "svg":
            fig.savefig(p, format="svg", dpi=dpi_png)
        elif ext == "pdf":
            fig.savefig(p, format="pdf", dpi=dpi_png)
        elif ext == "png":
            fig.savefig(p, format="png", dpi=dpi_png)
        else:
            fig.savefig(p, format="tiff", dpi=dpi_tiff,
                        pil_kwargs={"compression": "tiff_lzw"})
        paths[ext] = p
    _flatten_tiff(paths["tiff"], dpi_tiff)
    CUR_FIG = fig
    return paths


def _flatten_tiff(path, dpi):
    """Flatten any alpha onto white and assert LZW + dpi metadata (submission TIFF)."""
    from PIL import Image
    with Image.open(path) as im:
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            out = bg
        else:
            out = im.convert("RGB")
    out.save(path, format="TIFF", compression="tiff_lzw", dpi=(dpi, dpi))


def tiff_lzw_verify(path):
    from PIL import Image
    with Image.open(path) as im:
        return dict(size=im.size, mode=im.mode, compression=im.info.get("compression"))


# ------------------------------------------------------------------ layout gate
def measure(fig, overlap_area_px=110.0, min_font_pt=None, allow_out_of_canvas=()):
    """Return the automated QC record for one rendered figure."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.get_size_inches() * fig.dpi
    minf = MIN_FONT_PT if min_font_pt is None else min_font_pt
    items, ooc, fontviol, small = [], [], [], []
    texts = list(fig.texts) + [t for ax in fig.axes for t in ax.texts]
    for t in texts:
        s = t.get_text().strip()
        if not s:
            continue
        bb = t.get_window_extent(renderer=r)
        items.append((s.replace("\n", " / ")[:52], bb, t))
        if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > W + 2 or bb.y1 > H + 2:
            ooc.append(dict(text=s[:60], x0=round(bb.x0), y0=round(bb.y0),
                            x1=round(bb.x1), y1=round(bb.y1)))
        try:
            from matplotlib import font_manager as _fm
            fpath = _fm.findfont(t.get_fontproperties(), fallback_to_default=False)
            base = os.path.basename(fpath)
        except Exception:
            base = "UNRESOLVED"
        if base == "UNRESOLVED" or not any(k.lower() in base.lower().replace(" ", "") for k in FONT_FILE_KEYS):
            fontviol.append(dict(text=s[:40], resolved_font=base))
        if t.get_fontsize() < minf - 0.05:
            small.append(dict(text=s[:40], size_pt=round(t.get_fontsize(), 2), min_pt=round(minf, 2)))
    for ax in fig.axes:
        bb = ax.get_window_extent(renderer=r)
        if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > W + 2 or bb.y1 > H + 2:
            ooc.append(dict(axes=str([round(v, 3) for v in ax.get_position().bounds])))
    # panel containment:
    #   panel_overflow      = a DATA MARK (scatter point / bar / histogram / cell) leaves its own axes box
    #   label_outside_axis  = a text item sits outside its axes box, which is legitimate for axis,
    #                         tick and row/column labels; such text must still stay inside the canvas
    #                         and must not collide with another text item (checked by text_overlap)
    panel_ovf, label_out = [], []
    for ai, ax in enumerate(fig.axes):
        ab = ax.get_window_extent(renderer=r)
        for t in ax.texts:
            if not t.get_text().strip():
                continue
            tb = t.get_window_extent(renderer=r)
            if (tb.x0 < ab.x0 - 2 or tb.x1 > ab.x1 + 2 or tb.y0 < ab.y0 - 2 or tb.y1 > ab.y1 + 2):
                label_out.append(dict(panel=ai, text=t.get_text().strip()[:48],
                                      inside_canvas=not (tb.x0 < -2 or tb.y0 < -2 or tb.x1 > W + 2 or tb.y1 > H + 2)))
        for col in ax.collections:
            if getattr(col, "get_clip_on", lambda: True)():
                continue  # clipped artists cannot visually overflow their panel
            try:
                off = col.get_offsets()
                if off is None or len(off) == 0:
                    continue
                pts = ax.transData.transform(np.asarray(off))
            except Exception:
                continue
            out = pts[(pts[:, 0] < ab.x0 - 2) | (pts[:, 0] > ab.x1 + 2) |
                      (pts[:, 1] < ab.y0 - 2) | (pts[:, 1] > ab.y1 + 2)]
            if len(out):
                panel_ovf.append(dict(panel=ai, kind="mark", n_outside=int(len(out)),
                                      sample=[[round(p[0]), round(p[1])] for p in out[:3]]))
    ov = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i][1], items[j][1]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0)
            oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 2 and oy > 2 and ox * oy > overlap_area_px:
                ov.append(dict(a=items[i][0], b=items[j][0], area=round(ox * oy)))
    # whitespace: fraction of the rendered canvas that is pure white (rasterised at 100 dpi)
    whitespace = None
    try:
        import io as _io
        from PIL import Image
        buf = _io.BytesIO()
        fig.savefig(buf, format="png", dpi=100)
        buf.seek(0)
        with Image.open(buf) as im:
            a = np.asarray(im.convert("L"))
        whitespace = float((a >= 250).mean())
    except Exception:
        whitespace = float("nan")
    return dict(canvas_px=[round(W), round(H)],
                canvas_mm=[round(W / fig.dpi / MM, 1), round(H / fig.dpi / MM, 1)],
                canvas_mm_declared=[round(fig.get_size_inches()[0] / MM, 1),
                                    round(fig.get_size_inches()[1] / MM, 1)],
                n_text_items=len(items),
                canvas_overflow=len(ooc), out_of_canvas=ooc,
                panel_overflow=len(panel_ovf), panel_overflow_detail=panel_ovf[:12],
                mark_overflow=len(panel_ovf),
                label_outside_axis=len(label_out),
                labels_outside_axis_all_inside_canvas=all(d["inside_canvas"] for d in label_out),
                text_overlap=len(ov), overlaps=sorted(ov, key=lambda x: -x["area"])[:10],
                font_family_violations=len(fontviol), font_violations=fontviol,
                font_below_minimum=len(small), small_text=small,
                whitespace_fraction=round(whitespace, 3),
                min_font_pt=round(minf, 2))
