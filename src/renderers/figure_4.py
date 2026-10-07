# -*- coding: utf-8 -*-
"""Render one figure from supplied source tables."""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import figure_style as S
import figure_common as C



import argparse

# Added so the released renderer (a) imports without executing a render, (b) answers
# --help, (c) fails gracefully when the data root is absent, and (d) supports --dry-run.
# The frozen render body inside main() is unchanged, statement for statement; see
FIG_NAME = 'Fig4'
REQUIRED_SOURCE_TABLES = (
    "FIG4_A_primary_6x6_matrix.csv",
    "FIG4_B_feature_coverage.csv",
    "FIG4_C_matched_null_effect.csv",
    "FIG4_D_null_distributions.csv",
    "FIG4_E_effect_size_context.csv",
)
_REQUIRED_RELS = tuple("figure_source_data/" + _n for _n in REQUIRED_SOURCE_TABLES)


def _cli(argv=None):
    """Parse the released renderer's command line (portability prelude)."""
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description=(__doc__ or "").strip().split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Portability\n"
            "-----------\n"
            "The released package does NOT redistribute the third-party data.  Point this\n"
            "renderer at your own reconstruction of the analysis project either with\n"
            "  --data-root DIR\n"
            "or with the environment variable\n"
            "  " + C.DATA_ROOT_ENV_VAR + "=<dir>\n"
            "Use --dry-run to print the resolved configuration and the required frozen\n"
            "source tables without rendering anything.\n"
        ),
    )
    parser.add_argument("--data-root", metavar="DIR", default=None,
                        help="root of the analysis project (overrides $" + C.DATA_ROOT_ENV_VAR + ")")
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve configuration and report what would be rendered; needs no data")
    return parser.parse_args(argv)


def _dry_run_report(args):
    """Machine-readable configuration report.  Reads no data file contents."""
    import bbbtb_common as _B
    if args.data_root:
        _B.set_data_root(args.data_root)
    report = _B.check_sources(required=_REQUIRED_RELS)
    stem = C.STEM_V3[FIG_NAME]
    root = report["data_root"]
    report.update(
        figure=FIG_NAME,
        mode="dry-run",
        renderer=os.path.basename(__file__),
        would_write_figure=(None if root is None
                            else os.path.join(root, "figures", "main", stem)),
        would_write_qc_json=(None if root is None
                             else os.path.join(root, "runs", C.RUN_ID, "logs",
                                               os.path.basename(__file__)[:-3] + "_measure.json")),
        renders_data=False,
    )
    return report




def main(argv=None):
    """Released entry point for Fig4.  Renders nothing unless the frozen inputs are present."""
    args = _cli(argv)
    if args.dry_run:
        print(json.dumps(_dry_run_report(args), indent=1, ensure_ascii=False))
        return 0
    try:
        C.require_files(_REQUIRED_RELS, what="the Fig4 render")
        C.ensure_output_dirs()
    except (C.DataRootNotConfigured, C.DataSourceMissing) as exc:
        sys.stderr.write("\n" + os.path.basename(__file__) + ": cannot render Fig4.\n")
        sys.stderr.write(str(exc) + "\n")
        return 2

    SD = C.SRC
    rd = lambda n: pd.read_csv(os.path.join(SD, n))

    FIG = "Fig4"
    PAGE_H_MM = S.page_h(FIG)
    W = S.FULL_W
    fig = plt.figure(figsize=(W, PAGE_H_MM * S.MM))

    BTB = list(C.BTB_FAM)
    PROG = list(C.BBB_CAP)
    SH = {p: "C%02d" % int(p[-3:]) for p in PROG}
    BSH = {p: "F%03d" % int(p[-3:]) for p in BTB}


    def canvas(panel):
        """Axis occupying exactly the authoritative panel box."""
        x0, y0, x1, y1 = S.box_mm(FIG, panel)
        ax = fig.add_axes([x0 / S.FULL_W_MM, (PAGE_H_MM - y1) / PAGE_H_MM,
                           (x1 - x0) / S.FULL_W_MM, (y1 - y0) / PAGE_H_MM])
        S.hide_all(ax)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return ax


    # ------------------------------------------------------------------ frozen sources (unchanged)
    A4 = rd("FIG4_A_primary_6x6_matrix.csv")
    B4 = rd("FIG4_B_feature_coverage.csv")
    B4 = B4[B4.side == "BTB"].reset_index(drop=True)
    C4 = rd("FIG4_C_matched_null_effect.csv")
    D4 = rd("FIG4_D_null_distributions.csv")
    E4 = rd("FIG4_E_effect_size_context.csv")
    mS = A4.pivot(index="BTB_program", columns="BBB_program", values="cell_state").loc[BTB, PROG]

    # ================================================================== PANEL A — 6x6 matrix (anchor)
    axA = canvas("a")
    S.head(fig, axA, FIG, "a", "The 36 fixed positions")

    AX0, AX1 = S.box_mm(FIG, "a")[0], S.box_mm(FIG, "a")[2]
    AY0, AY1 = S.box_mm(FIG, "a")[1], S.box_mm(FIG, "a")[3]
    LABEL_GUTTER_MM = 4.6                      # row label column (F001 ...)
    CELL_X0_MM = AX0 + LABEL_GUTTER_MM
    CELL_BLOCK_W = AX1 - CELL_X0_MM            # flush to the panel box; whitespace delimits cells
    PITCH = CELL_BLOCK_W / 6.0
    CELL_INSET_MM = 1.3                        # per-side whitespace: cells are told apart by
                                               # whitespace alone, never by a border
    TITLE_MM = AY0 + S.HEAD_RESERVE_MM + 1.4   # column / row identity
    COLLBL_MM = TITLE_MM + 3.4                 # C01 ... C06
    TOP_MM = COLLBL_MM + 2.2
    BOT_MM = AY1 - 11.8                        # clear of the three stacked foot lines
    ROW_H = (BOT_MM - TOP_MM) / 6.0


    def axx(mm):
        return (mm - AX0) / (AX1 - AX0)


    def axy(mm):
        return 1.0 - (mm - AY0) / (AY1 - AY0)


    S.annot(axA, axx(CELL_X0_MM + CELL_BLOCK_W / 2.0), axy(TITLE_MM),
            "BBB Capillary program", color=S.COL["INK2"], ha="center", va="center",
            size="AXIS")
    S.annot(axA, 0.0, axy(TITLE_MM), "BTB", color=S.COL["INK2"], ha="left", va="center",
            size="AXIS")
    for j, p in enumerate(PROG):                                  # column labels
        S.annot(axA, axx(CELL_X0_MM + PITCH * (j + 0.5)), axy(COLLBL_MM), SH[p],
                color=S.COL["BBB_DK"], weight="bold", ha="center", va="center")
    for i, f in enumerate(BTB):                                   # row labels
        y_mm = TOP_MM + ROW_H * (i + 0.5)
        S.annot(axA, 0.0, axy(y_mm), BSH[f], color=S.COL["BTB_DK"], weight="bold",
                ha="left", va="center")
        for j, p in enumerate(PROG):
            x_mm = CELL_X0_MM + PITCH * j
            st = mS.loc[f, p]
            if st == "NOT_EVALUABLE":
                S.cell_not_evaluable(axA, axx(x_mm + CELL_INSET_MM), axy(y_mm + ROW_H / 2 - CELL_INSET_MM),
                                     (PITCH - 2 * CELL_INSET_MM) / (AX1 - AX0),
                                     (ROW_H - 2 * CELL_INSET_MM) / (AY1 - AY0))
            else:
                S.cell_plain(axA, axx(x_mm + CELL_INSET_MM), axy(y_mm + ROW_H / 2 - CELL_INSET_MM),
                             (PITCH - 2 * CELL_INSET_MM) / (AX1 - AX0),
                             (ROW_H - 2 * CELL_INSET_MM) / (AY1 - AY0))
                if st == "CONVERGENT":
                    S.filled_marker(axA, axx(x_mm + PITCH / 2), axy(y_mm), S.COL["SUPPORTED"], s=34)
                else:
                    S.open_marker(axA, axx(x_mm + PITCH / 2), axy(y_mm), s=34,
                                  ec=S.COL["NOT_SUPPORTED"])
    #: the panel-a headline is computed from the frozen cell states, never typed in.
    N_NOT_EVAL = int((mS == "NOT_EVALUABLE").to_numpy().sum())
    N_EVAL = int((mS != "NOT_EVALUABLE").to_numpy().sum())
    N_CONV = int((mS == "CONVERGENT").to_numpy().sum())
    BH_Q = float(A4["bh_q"].max())
    S.annot(axA, 0.0, axy(AY1 - 8.6),
            "%d not evaluable   \u00b7   %d evaluable   \u00b7   %d convergent   \u00b7   "
            "BH q = %.1f" % (N_NOT_EVAL, N_EVAL, N_CONV, BH_Q),
            color=S.COL["INK"], weight="semibold", va="center", size="AXIS")
    S.annot(axA, 0.0, axy(AY1 - 5.1), "hatched, not evaluable   \u00b7   open, evaluable",
            color=S.COL["INK2"], va="center", size="AXIS")
    # ARB-09 item 9: the state-semantics lock, restored
    S.annot(axA, 0.0, axy(AY1 - 1.9), "not evaluable is never a negative result",
            color=S.COL["INK"], weight="semibold", va="center", size="AXIS")

    # ================================================================== PANEL B — coverage side rail
    axB = canvas("b")
    S.head(fig, axB, FIG, "b", "Why 30 were not evaluable")

    BX0, BX1 = S.box_mm(FIG, "b")[0], S.box_mm(FIG, "b")[2]
    BY0, BY1 = S.box_mm(FIG, "b")[1], S.box_mm(FIG, "b")[3]
    B_LBL_R = BX0 + 13.0                       # right edge of the F001..F006 labels
    AXIS_X0, AXIS_X1 = BX0 + 14.0, BX1 - 15.0  # 0.00 .. 1.00
    ROW_TOP, ROW_BOT = BY0 + S.HEAD_RESERVE_MM + 2.0, BY1 - 15.0
    BPITCH = (ROW_BOT - ROW_TOP) / 5.0


    def bx(mm):
        return (mm - BX0) / (BX1 - BX0)


    def by(mm):
        return 1.0 - (mm - BY0) / (BY1 - BY0)


    GATE_MM = AXIS_X0 + (AXIS_X1 - AXIS_X0) * 0.70
    S.gate(axB, bx(GATE_MM), by(ROW_BOT + 2.4), by(ROW_TOP - 2.4), label="0.70 gate",
           label_dx=0.008, label_dy=0.012)
    for i, r in enumerate(B4.itertuples()):
        y_mm = ROW_TOP + BPITCH * i
        gx = AXIS_X0 + (AXIS_X1 - AXIS_X0) * float(r.coverage)
        S.annot(axB, bx(B_LBL_R), by(y_mm), r.program_id.replace("BTB_FAM_", "F"),
                color=S.COL["BTB_DK"], weight="bold", ha="right", va="center")
        S.rule(axB, bx(AXIS_X0), bx(gx), by(y_mm), color=S.COL["RULE_STRONG"],
               lw=S.STROKE["SECONDARY"])
        if bool(r.evaluable):
            S.filled_marker(axB, bx(gx), by(y_mm), S.COL["SUPPORTED"], s=20)
        else:
            S.open_marker(axB, bx(gx), by(y_mm), s=20, ec=S.COL["NOT_SUPPORTED"])
        # ARB-03 item 1: keep V2's printed precision exactly (%.3f), never re-round a retained value
        S.annot(axB, bx(gx + 3.0), by(y_mm), "%.3f" % float(r.coverage), color=S.COL["INK2"],
                va="center", size="AXIS")
    AXIS_Y = ROW_BOT + 4.2
    S.rule(axB, bx(AXIS_X0), bx(AXIS_X1), by(AXIS_Y), color=S.COL["RULE_STRONG"])
    for xv in (0.00, 0.70, 1.00):
        S.annot(axB, bx(AXIS_X0 + (AXIS_X1 - AXIS_X0) * xv), by(AXIS_Y + 1.2), "%.2f" % xv,
                color=S.COL["INK2"], ha="center", va="top")
    # ARB-10 N4: the quantity the six points are, in the legend's own words, and the mechanism line
    S.annot(axB, bx(BX0), by(AXIS_Y + 4.0), "top200 coverage of the frozen BTB program set",
            color=S.COL["INK2"], va="top", size="AXIS")
    S.annot(axB, bx(BX0), by(AXIS_Y + 8.2), "evaluability is set by BTB coverage, not by the BBB",
            color=S.COL["INK"], weight="semibold", va="top", size="AXIS")

    # ================================================================== PANEL C — six evaluable pairs
    axC = canvas("c")
    S.head(fig, axC, FIG, "c", "The six evaluable pairs")
    S.annot(axC, 1.0, 1.0 - (S.HEAD_RESERVE_MM - 1.5) / 30.0,
            "open, observed   \u00b7   bar, null median\u2013q95   \u00b7   tick, null median",
            color=S.COL["INK2"], ha="right", va="center")

    CX0, CX1 = S.box_mm(FIG, "c")[0], S.box_mm(FIG, "c")[2]
    CY0, CY1 = S.box_mm(FIG, "c")[1], S.box_mm(FIG, "c")[3]
    CLO, CHI = 0.700, 0.735
    C_AX0, C_AX1 = CX0 + 26.0, CX0 + 122.0
    C_ROWS = [CY0 + 9.4 + 3.2 * i for i in range(6)]           # all six rows inside the 30 mm box
    # ARB-11 item 1: the constant BTB half of every pair id is stated ONCE as a shared row-label
    # header instead of being repeated on all six rows.  No datum is lost — the family is a
    # positional label and the assertion guarantees it really is constant across the six rows.
    C_PFX = "F%03d \u00d7" % int(str(C4.pair_id.iloc[0]).split("_")[1][1:])
    C_FAM = str(C4.pair_id.iloc[0]).split("_")[1]
    assert C4.pair_id.astype(str).str.contains(C_FAM).all(), \
        "Fig4c pair ids do not share one BTB family"


    def cx(v):
        return (C_AX0 + (float(v) - CLO) / (CHI - CLO) * (C_AX1 - C_AX0) - CX0) / (CX1 - CX0)


    def cy(mm):
        return 1.0 - (mm - CY0) / (CY1 - CY0)


    S.annot(axC, 0.0, cy(CY0 + 6.2), C_PFX, color=S.COL["INK2"], weight="bold", ha="left",
            va="center")


    for i, r in enumerate(C4.itertuples()):
        y_mm = C_ROWS[i]
        S.body(axC, 0.0, cy(y_mm), SH[r.BBB_program],
               color=S.COL["INK"], ha="left", va="center")
        # the matched-null reference is ONE legible object: a median-to-q95 bar plus the median
        # tick at its left end (FIGSTYLE_V3 + the frozen legend define both, so both are drawn)
        axC.plot([cx(r.null_median), cx(r.null_q95)], [cy(y_mm), cy(y_mm)],
                 color=S.COL["INK2"], lw=S.STROKE["SECONDARY"], solid_capstyle="butt",
                 zorder=S.Z["FILL"])
        axC.plot([cx(r.null_median), cx(r.null_median)],
                 [cy(y_mm) - S.TICK_HALF_MM / 30.0, cy(y_mm) + S.TICK_HALF_MM / 30.0],
                 color=S.COL["INK2"], lw=S.STROKE["DATA_MAIN"], solid_capstyle="butt",
                 zorder=S.Z["FILL"] + 0.1)
        S.open_marker(axC, cx(r.observed_cosine), cy(y_mm), s=22, ec=S.COL["NOT_SUPPORTED"])
        # ARB-10 N5: the six p values are ONE right-aligned column, as V2 drew them, not a diagonal
        S.annot(axC, 1.0 - 5.0 / (CX1 - CX0), cy(y_mm), "p = %.4f" % float(r.empirical_p),
                color=S.COL["INK2"], ha="right", va="center", size="AXIS")
    C_AXIS_Y = CY0 + 26.6
    S.rule(axC, cx(CLO), cx(CHI), cy(C_AXIS_Y), color=S.COL["RULE_STRONG"])
    for xv in np.linspace(CLO, CHI, 4):
        S.annot(axC, cx(xv), cy(C_AXIS_Y + 1.1), "%.3f" % xv, color=S.COL["INK2"],
                ha="center", va="top")

    # ================================================================== PANEL D — matched-null distributions
    axD = canvas("d")
    S.head(fig, axD, FIG, "d", "Matched-null distributions")
    S.annot(axD, 1.0, 1.0 - (S.HEAD_RESERVE_MM - 1.5) / (S.box_mm(FIG, "d")[3] - S.box_mm(FIG, "d")[1]),
            "solid, observed   \u00b7   dashed, null median", color=S.COL["INK2"],
            ha="right", va="center", size="AXIS")

    DX0, DX1 = S.box_mm(FIG, "d")[0], S.box_mm(FIG, "d")[2]
    DY0, DY1 = S.box_mm(FIG, "d")[1], S.box_mm(FIG, "d")[3]
    XDR = (0.702, 0.740)
    NBINS = 46
    # three matched-null distributions stacked inside ONE axes on ONE shared x-axis, exactly as the
    # art direction asks ("share one x-axis instead of three separate axes"); each band is normalised
    # to its own maximum so the three shapes stay comparable.  ARB-01 item 1: each distribution also
    # carries its own pair id, in the empty left tail of its own band.
    D_PAIRS = ["PAIR_B06_C02", "PAIR_B06_C01", "PAIR_B06_C03"]   # V2's representative set and order
    axD.set_xlim(*XDR)
    axD.set_ylim(-0.42, 3.10)
    BAND_H = 0.74
    for k, pid in enumerate(D_PAIRS):
        row = C4[C4.pair_id == pid].iloc[0]
        v = D4[D4.pair_id == pid].null_cosine.values
        cnt, edges = np.histogram(v, bins=NBINS, range=XDR)
        base = k + 0.06
        scale = BAND_H / max(cnt.max(), 1)
        axD.bar(edges[:-1], cnt * scale, width=(XDR[1] - XDR[0]) / NBINS * 0.84,
                bottom=base, align="edge", facecolor=S.COL["RULE"], edgecolor=S.COL["BTB"],
                linewidth=S.STROKE["DATA_SECONDARY"], zorder=S.Z["FILL"])
        S.rule(axD, XDR[0], XDR[1], base, color=S.COL["RULE_STRONG"], lw=S.STROKE["RULE"])
        axD.plot([row.observed_cosine, row.observed_cosine], [base, base + BAND_H],
                 color=S.COL["INK"], lw=S.STROKE["MAIN"], solid_capstyle="butt",
                 zorder=S.Z["GLYPH"])
        axD.plot([row.null_median, row.null_median], [base, base + BAND_H],
                 color=S.COL["INK2"], lw=S.STROKE["DATA_SECONDARY"], ls=(0, (2.0, 1.4)),
                 zorder=S.Z["GLYPH"])
        # ARB-15: which pair each histogram shows is decode-critical, so it is set at the AXIS
        # token rather than the floor.
        axD.text(XDR[0] + 0.0006, base + 0.20, "F%03d \u00d7 %s"
                 % (int(str(pid).split("_")[1][1:]), SH[str(row.BBB_program)]),
                 fontsize=S.FS("AXIS"), color=S.COL["INK"], ha="left", va="bottom",
                 zorder=S.Z["TEXT"])
    # the one shared x-axis
    S.rule(axD, XDR[0], XDR[1], 0.0, color=S.COL["RULE_STRONG"], lw=S.STROKE["AXIS"])
    for xv, al in ((XDR[0], "left"), ((XDR[0] + XDR[1]) / 2.0, "center"), (XDR[1], "right")):
        axD.plot([xv, xv], [0.0, -0.07], color=S.COL["RULE_STRONG"], lw=S.STROKE["TICK"],
                 zorder=S.Z["RULE"])
        # ARB-15: axis tick values are supporting reference text, one step off the floor.
        axD.text(xv, -0.10, "%.3f" % xv, fontsize=S.FS("LEGEND"), color=S.COL["INK2"],
                 ha=al, va="top", zorder=S.Z["TEXT"])

    # ================================================================== PANEL E — effect-size context
    axE = canvas("e")
    S.head(fig, axE, FIG, "e", "Effect-size context")

    EX0, EX1 = S.box_mm(FIG, "e")[0], S.box_mm(FIG, "e")[2]
    EY0, EY1 = S.box_mm(FIG, "e")[1], S.box_mm(FIG, "e")[3]
    ELO, EHI = -0.045, 0.020
    E_AX0, E_AX1 = EX0 + 16.0, EX0 + 44.0
    E_ROWS = [EY0 + 11.0 + 10.8 * i for i in range(6)]         # use the full 71 mm box height
    # ARB-11 item 1: the constant BTB half of every pair id is stated ONCE as a shared row-label
    # header here too, and the value column gets a proper column header instead of a bare rail
    E_PFX = "F%03d \u00d7" % int(str(E4.BTB_program.iloc[0])[-3:])
    assert E4.BTB_program.astype(str).nunique() == 1, "Fig4e rows do not share one BTB family"


    def ex(v):
        return (E_AX0 + (float(v) - ELO) / (EHI - ELO) * (E_AX1 - E_AX0) - EX0) / (EX1 - EX0)


    def ey(mm):
        return 1.0 - (mm - EY0) / (EY1 - EY0)


    S.annot(axE, 0.0, ey(EY0 + 7.4), E_PFX, color=S.COL["INK2"], weight="bold", ha="left",
            va="center")
    S.annot(axE, 50.0 / (EX1 - EX0), ey(EY0 + 7.4), "Spearman", color=S.COL["INK2"],
            weight="bold", ha="left", va="center")


    S.vrule(axE, ex(0.0), ey(E_ROWS[-1] + 4.4), ey(E_ROWS[0] - 4.4), color=S.COL["RULE_STRONG"],
            lw=S.STROKE["SECONDARY"])
    S.annot(axE, ex(0.0), ey(E_ROWS[0] - 6.0), "0", color=S.COL["INK2"], ha="center", va="top")
    for i, r in enumerate(E4.itertuples()):
        y_mm = E_ROWS[i]
        S.body(axE, 0.0, ey(y_mm), SH[r.BBB_program],
               color=S.COL["INK"], ha="left", va="center")
        S.lollipop(axE, ey(y_mm), ex(0.0), ex(r.observed_spearman), S.COL["SENSITIVITY"],
                   ms=S.MARKER["data_marker"])
        S.annot(axE, (EX0 + 50.0 - EX0) / (EX1 - EX0), ey(y_mm),
                "%+.3f" % float(r.observed_spearman), color=S.COL["INK2"], va="center", size="AXIS")

    # ------------------------------------------------------------------ export + QC
    paths = S.finalize(fig, C.FIGS_MAIN, C.STEM_V3[FIG])
    rec = S.measure(fig)
    rec.update(
        figure=C.STEM_V3[FIG],
        panel_boxes_mm={k: list(v) for k, v in S.PAGE_BOXES[FIG].items() if k != "page_h"},
        visual_anchor=S.ANCHOR[FIG],
        core_message=("The prespecified cross-barrier analysis was limited by evaluability and "
                      "showed no convergence among the pairs that could be formally tested."),
        panels=["a 6x6 fixed-position matrix (anchor)", "b coverage side rail",
                "c six evaluable pairs", "d matched-null distributions", "e effect-size context"],
        design_source=["FIGSTYLE_V3.json", "FIGSTYLE_V3.md", "FIGURE_V3_ART_DIRECTION.md",
                       "AMD-01 (type floor 1.90 mm, no mathtext)"],
        files={k: os.path.relpath(v, C.ROOT).replace("\\", "/") for k, v in paths.items()},
        source_tables=["FIG4_A_primary_6x6_matrix.csv", "FIG4_B_feature_coverage.csv",
                       "FIG4_C_matched_null_effect.csv", "FIG4_D_null_distributions.csv",
                       "FIG4_E_effect_size_context.csv"],
    )
    os.makedirs(C.LOGS_V3, exist_ok=True)
    json.dump(rec, open(os.path.join(C.LOGS_V3, "figure_4_render.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False, default=str)
    print(json.dumps({k: rec[k] for k in ("figure", "canvas_mm", "canvas_overflow", "panel_overflow",
                                          "text_overlap", "font_family_violations",
                                          "font_below_minimum", "label_outside_axis",
                                          "whitespace_fraction", "n_text_items")},
                     ensure_ascii=False, default=str))
    for o in rec["overlaps"]:
        print("  OVL", o)
    for o in rec["out_of_canvas"]:
        print("  OOC", o)
    for o in rec["panel_overflow_detail"][:8]:
        print("  POV", o)


if __name__ == "__main__":
    raise SystemExit(main())
