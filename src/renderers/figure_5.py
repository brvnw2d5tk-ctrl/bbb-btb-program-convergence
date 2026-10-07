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
FIG_NAME = 'Fig5'
REQUIRED_SOURCE_TABLES = (
    "FIG5_A_feature_universe_coverage.csv",
    "FIG5_B_gate_failure_decomposition.csv",
    "FIG5_C_biotype_composition.csv",
    "FIG5_D_primary_vs_PC.csv",
    "FIG5_E_seven_sensitivity_pairs.csv",
    "FIG5_F_interpretive_schematic.csv",
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
    """Released entry point for Fig5.  Renders nothing unless the frozen inputs are present."""
    args = _cli(argv)
    if args.dry_run:
        print(json.dumps(_dry_run_report(args), indent=1, ensure_ascii=False))
        return 0
    try:
        C.require_files(_REQUIRED_RELS, what="the Fig5 render")
        C.ensure_output_dirs()
    except (C.DataRootNotConfigured, C.DataSourceMissing) as exc:
        sys.stderr.write("\n" + os.path.basename(__file__) + ": cannot render Fig5.\n")
        sys.stderr.write(str(exc) + "\n")
        return 2

    SD = C.SRC
    rd = lambda n: pd.read_csv(os.path.join(SD, n))

    FIG = "Fig5"
    PAGE_H_MM = S.page_h(FIG)
    W = S.FULL_W
    fig = plt.figure(figsize=(W, PAGE_H_MM * S.MM))

    BTB = list(C.BTB_FAM)
    PROG = list(C.BBB_CAP)
    SH = {p: "C%02d" % int(p[-3:]) for p in PROG}
    BSH = {p: "F%03d" % int(p[-3:]) for p in BTB}


    def canvas(panel):
        x0, y0, x1, y1 = S.box_mm(FIG, panel)
        ax = fig.add_axes([x0 / S.FULL_W_MM, (PAGE_H_MM - y1) / PAGE_H_MM,
                           (x1 - x0) / S.FULL_W_MM, (y1 - y0) / PAGE_H_MM])
        S.hide_all(ax)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return ax


    # ------------------------------------------------------------------ frozen sources (unchanged)
    A5 = rd("FIG5_A_feature_universe_coverage.csv").set_index("BTB_program").loc[BTB]
    B5 = rd("FIG5_B_gate_failure_decomposition.csv").set_index("absence_class")["n"].to_dict()
    C5 = rd("FIG5_C_biotype_composition.csv")
    D5 = rd("FIG5_D_primary_vs_PC.csv")
    E5 = rd("FIG5_E_seven_sensitivity_pairs.csv")
    # ARB-03 item 2: the concept strip must keep reading the frozen schematic table (V2's read set),
    # and must print that table's `label` column verbatim.
    SCHEM = rd("FIG5_F_interpretive_schematic.csv").sort_values("step")

    # ================================================================== PANEL A — coverage shift
    axA = canvas("a")
    S.head(fig, axA, FIG, "a", "Two BBB feature universes")
    AX0, AX1 = S.box_mm(FIG, "a")[0], S.box_mm(FIG, "a")[2]
    AY0, AY1 = S.box_mm(FIG, "a")[1], S.box_mm(FIG, "a")[3]
    S.annot(axA, 1.0, 1.0 - (S.HEAD_RESERVE_MM - 2.0) / (AY1 - AY0),
            "open, GSE256493 universe, %d/%d evaluable   \u00b7   filled, GSE163577 universe, "
            "%d/%d evaluable" % (int(A5["evaluable_GSE256493"].sum()), len(BTB),
                                 int(A5["evaluable_GSE163577"].sum()), len(BTB)),
            color=S.COL["INK2"], ha="right", va="center", size="AXIS")

    XA0, XA1 = AX0 + 25.0, AX0 + 150.0
    A_GATE = 0.70
    A_ROWS = [AY0 + 10.0 + 6.0 * i for i in range(6)]
    A_AXIS_Y = A_ROWS[-1] + 2.6


    def axx(mm):
        return (mm - AX0) / (AX1 - AX0)


    def axy(mm):
        return 1.0 - (mm - AY0) / (AY1 - AY0)


    def XA(v):
        return XA0 + (float(v) - 0.0) / 1.0 * (XA1 - XA0)


    S.gate(axA, axx(XA(A_GATE)), axy(A_AXIS_Y), axy(A_ROWS[0] - 3.0), label="0.70 gate",
           label_dx=0.004, label_dy=0.010)
    for i, f in enumerate(BTB):
        r = A5.loc[f]
        y_mm = A_ROWS[i]
        # ARB-02 item 1: exactly one label per drawn dumbbell, on its own y, evenly pitched
        S.annot(axA, 0.0, axy(y_mm), BSH[f], color=S.COL["BTB"], weight="bold",
                ha="left", va="center")
        S.dumbbell(axA, axy(y_mm), axx(XA(r.coverage_GSE256493)), axx(XA(r.coverage_GSE163577)),
                   S.COL["BTB"], S.COL["SUPPORTED"])
        # two printed values in total, for the one evaluable family
        if f == BTB[-1]:
            S.annot(axA, axx(XA(r.coverage_GSE256493) - 2.0), axy(y_mm),
                    "%.3f" % float(r.coverage_GSE256493), color=S.COL["INK2"], ha="right",
                    va="center", size="AXIS")
            S.annot(axA, axx(XA(r.coverage_GSE163577) + 2.0), axy(y_mm),
                    "%.3f" % float(r.coverage_GSE163577), color=S.COL["INK2"], ha="left",
                    va="center")
    S.rule(axA, axx(XA0), axx(XA1), axy(A_AXIS_Y), color=S.COL["RULE_STRONG"])
    for xv in (0.00, 0.70, 1.00):
        S.annot(axA, axx(XA(xv)), axy(A_AXIS_Y + 1.2), "%.2f" % xv, color=S.COL["INK2"],
                ha="center", va="top")

    # ================================================================== PANEL B — gate failures
    axB = canvas("b")
    S.head(fig, axB, FIG, "b", "Why coverage failed")
    BX0, BX1 = S.box_mm(FIG, "b")[0], S.box_mm(FIG, "b")[2]
    BY0, BY1 = S.box_mm(FIG, "b")[1], S.box_mm(FIG, "b")[3]

    n349 = int(B5["ABSENT_FROM_GSE256493_FEATURE_UNIVERSE"])
    n119 = int(B5["ABSENT_FROM_BOTH_BBB_FEATURE_UNIVERSES"])
    n2 = int(B5["PRESENT_BUT_MAPPING_AMBIGUOUS"])
    fail = n349 + n119 + n2
    pool = C5.groupby("mapped_status")[["lncRNA", "n_rows"]].sum()
    ln_u = 100.0 * float(pool.loc["UNMAPPED", "lncRNA"]) / float(pool.loc["UNMAPPED", "n_rows"])
    PCT_RECOVERABLE = 100.0 * n349 / fail
    # ARB-12 item 1: the brief's small achromatic proportional bar, restored arithmetically WITHOUT
    # the amber fill that FIGSTYLE_V3 section 8 forbids in 5b ("no amber appears anywhere in 5b").
    # The 470 gate failures are drawn at true proportion on a 60 x 1.3 mm strip: 349 recoverable in
    # the wider universe (RULE_STRONG), 119 absent from both universes (INK2) and the 2
    # PRESENT_BUT_MAPPING_AMBIGUOUS rows (INK) — the class that reconciles 349 + 119 with the
    # panel's own 470 base and that the locked legend leaves unstated.  One 1-2-word label per
    # segment, no stacked legend, no colour key, no amber.  78 mm2 of achromatic fill, i.e. thinner
    # and smaller than the Art-Director-mandated 95 x 1.2 mm / 114 mm2 bar in Fig2d, so it cannot
    # become the set's largest achromatic block.  Both display percentages and both captions are
    # unchanged.
    BAR_BX0, BAR_MM = BX0 + 6.0, 60.0
    BAR_BY, BAR_BH = BY0 + 6.0, 1.3
    BAR_SEGS = ((n349, S.COL["RULE_STRONG"], "recoverable"),
                (n119, S.COL["INK2"], "absent both"),
                (n2, S.COL["INK"], None))
    _x = BAR_BX0
    for _n, _col, _lab in BAR_SEGS:
        _w = BAR_MM * _n / float(fail)
        axB.add_patch(plt.Rectangle(((_x - BX0) / (BX1 - BX0),
                                     1.0 - (BAR_BY + BAR_BH - BY0) / (BY1 - BY0)),
                                    _w / (BX1 - BX0), BAR_BH / (BY1 - BY0), facecolor=_col,
                                    edgecolor="none", lw=0, zorder=S.Z["FILL"]))
        if _lab is not None:
            S.annot(axB, (_x + _w / 2.0 - BX0) / (BX1 - BX0), 1.0 - 9.0 / (BY1 - BY0), _lab,
                    color=S.COL["INK2"], ha="center", va="center", size="AXIS")
        _x += _w
    # the 2-row class is 0.26 mm wide at true scale, so it is named through an L-leader rather than
    # a label that could not fit over it: the class is handled explicitly, never dropped
    SEG3_X = BAR_BX0 + BAR_MM * (n349 + n119) / float(fail)
    axB.plot([(SEG3_X + 0.13 - BX0) / (BX1 - BX0), (SEG3_X + 0.13 - BX0) / (BX1 - BX0),
              (SEG3_X + 1.70 - BX0) / (BX1 - BX0)],
             [1.0 - (BAR_BY + BAR_BH - BY0) / (BY1 - BY0), 1.0 - 9.0 / (BY1 - BY0),
              1.0 - 9.0 / (BY1 - BY0)],
             color=S.COL["INK2"], lw=S.STROKE["TICK"], solid_capstyle="butt", zorder=S.Z["RULE"])
    S.annot(axB, (SEG3_X + 2.00 - BX0) / (BX1 - BX0), 1.0 - 9.0 / (BY1 - BY0),
            "%d mapping-ambiguous" % n2, color=S.COL["INK2"], ha="left", va="center", size="AXIS")
    # ARB-10 N6: 74.3 % needs its base on the artwork — "recoverable in a wider universe" alone does
    # not say what it is a percentage OF.  The base is FIG5_B's value; the composition denominators
    # (349 / 119 / 25.3 % / 34.0 %) stay in the caption per the brief.  ARB-12 item 2: the number
    # block moves from 9.5 to 12.0 and its rule from 14.0 to 15.0 mm so that every vertical gap the
    # new bar introduces is below the 3 mm dead band.
    for cx_mm, val, cap in ((BX0 + 42.0, PCT_RECOVERABLE,
                             "of the %d gate failures, recoverable in a wider universe" % fail),
                            (BX0 + 124.0, ln_u, "of unmapped rows are lncRNA")):
        S.number(axB, (cx_mm - BX0) / (BX1 - BX0), 1.0 - 12.0 / (BY1 - BY0),
                 "%.1f%%" % val, size="BIG_NUMBER", color=S.COL["INK"])
        S.rule(axB, (cx_mm - 17.0 - BX0) / (BX1 - BX0), (cx_mm + 17.0 - BX0) / (BX1 - BX0),
               1.0 - 15.0 / (BY1 - BY0), color=S.COL["RULE"], lw=S.STROKE["RULE"])
        S.annot(axB, (cx_mm - BX0) / (BX1 - BX0), 1.0 - 16.0 / (BY1 - BY0), cap,
                color=S.COL["INK2"], ha="center", va="top", size="AXIS")

    # ================================================================== PANEL C — the anchor
    axC = canvas("c")
    S.head(fig, axC, FIG, "c", "Two feature representations")
    CX0, CX1 = S.box_mm(FIG, "c")[0], S.box_mm(FIG, "c")[2]
    CY0, CY1 = S.box_mm(FIG, "c")[1], S.box_mm(FIG, "c")[3]


    def cxx(mm):
        return (mm - CX0) / (CX1 - CX0)


    def cxy(mm):
        return 1.0 - (mm - CY0) / (CY1 - CY0)


    # Both matrices need their own row identity (the ARB-01 lesson from Fig4d), so the pair is
    # shifted 8 mm right of the art-direction coordinates to open a 7 mm row-label gutter on each
    # matrix.  The matrices themselves are still 55 mm wide with the same cell pitch to 0.1 mm.
    MAT_W = 55.0
    MAT_L = CX0 + 8.0                # 11.0 -> 66.0 mm; row labels right-aligned at 10.0 mm
    MAT_R = CX0 + 72.0               # 75.0 -> 130.0 mm; row labels right-aligned at 74.0 mm
    CELL_W = MAT_W / 6.0
    # ARB-02 item 2: the amber rule must sit immediately under the POST-FREEZE SENSITIVITY heading
    # and well clear of the C01...C10 label row, so the header block is given its own vertical band.
    ROW_H = 5.4
    MAT_TOP = CY0 + 11.4
    BAND_Y = CY0 + 5.6               # PRESPECIFIED PRIMARY / POST-FREEZE SENSITIVITY
    AMBER_RULE_Y = CY0 + 7.6         # 0.6 mm below the heading's descender box
    HEAD_Y = CY0 + 9.8               # C01 ... C10, separated from the rule above

    for j, p in enumerate(PROG):
        for mx in (MAT_L, MAT_R):
            S.annot(axC, cxx(mx + CELL_W * (j + 0.5)), cxy(HEAD_Y), SH[p],
                    color=S.COL["BBB"], weight="bold", ha="center", va="center")
    for i, f in enumerate(BTB):
        y_mm = MAT_TOP + ROW_H * (i + 0.5)
        for lx in (MAT_L - 1.0, MAT_R - 1.0):
            S.annot(axC, cxx(lx), cxy(y_mm), BSH[f], color=S.COL["BTB"], weight="bold",
                    ha="right", va="center")
    S.annot(axC, cxx(MAT_L + MAT_W / 2), cxy(BAND_Y), "PRESPECIFIED PRIMARY",
            color=S.COL["INK"], ha="center", va="center", size="PANEL_TITLE")
    S.annot(axC, cxx(MAT_R + MAT_W / 2), cxy(BAND_Y), "POST-FREEZE SENSITIVITY",
            color=S.COL["SENSITIVITY_TEXT"], ha="center", va="center", size="PANEL_TITLE")
    # the 12 mm amber rule under the right heading only; the matrices themselves have no base rule
    S.rule(axC, cxx(MAT_R + MAT_W / 2 - 6.0), cxx(MAT_R + MAT_W / 2 + 6.0), cxy(AMBER_RULE_Y),
           color=S.COL["SENSITIVITY"], lw=S.STROKE["SECONDARY"])

    mSp = D5.pivot(index="BTB_program", columns="BBB_program", values="band_primary").loc[BTB, PROG]
    mSt = D5.pivot(index="BTB_program", columns="BBB_program", values="band_sensitivity").loc[BTB, PROG]
    mCp = D5.pivot(index="BTB_program", columns="BBB_program", values="convergent_PC").loc[BTB, PROG]


    def matrix(mx, mstate, mconv):
        inset = 0.95                    # cells are delimited by whitespace alone, never a border
        for i, f in enumerate(BTB):
            y_mm = MAT_TOP + ROW_H * (i + 0.5)
            for j, p in enumerate(PROG):
                x_mm = mx + CELL_W * j
                st = mstate.loc[f, p]
                if st == "NOT_EVALUABLE":
                    S.cell_not_evaluable(axC, cxx(x_mm + inset), cxy(y_mm + ROW_H / 2 - inset),
                                         (CELL_W - 2 * inset) / (CX1 - CX0),
                                         (ROW_H - 2 * inset) / (CY1 - CY0))
                else:
                    S.cell_plain(axC, cxx(x_mm + inset), cxy(y_mm + ROW_H / 2 - inset),
                                 (CELL_W - 2 * inset) / (CX1 - CX0),
                                 (ROW_H - 2 * inset) / (CY1 - CY0))
                    if bool(mconv.loc[f, p]):
                        S.filled_marker(axC, cxx(x_mm + CELL_W / 2), cxy(y_mm),
                                        S.COL["SUPPORTED"], s=18)
                    else:
                        S.open_marker(axC, cxx(x_mm + CELL_W / 2), cxy(y_mm), s=18,
                                      ec=S.COL["NOT_SUPPORTED"])


    matrix(MAT_L, mSp, pd.DataFrame(False, index=BTB, columns=PROG))
    matrix(MAT_R, mSt, mCp)

    N_LEFT_EVAL = int((mSp != "NOT_EVALUABLE").to_numpy().sum())
    N_LEFT_CONV = int(mSp.eq("CONVERGENT").to_numpy().sum())
    N_RIGHT_EVAL = int((mSt != "NOT_EVALUABLE").to_numpy().sum())
    N_RIGHT_POS = int(mCp.to_numpy().sum())
    BIG_Y = CY0 + 46.3          # ARB-12 item 2: 47.9 -> 46.3 mm, so the 3.5 mm dead band between
                                # the matrices' last cell row and the display numerals is 1.8 mm
    SUB_Y = CY0 + 51.2
    for mx, big, sub in ((MAT_L + MAT_W / 2, "%d / 36" % N_LEFT_EVAL,
                          "evaluable   \u00b7   %d convergent signals" % N_LEFT_CONV),
                         (MAT_R + MAT_W / 2, "%d / 36" % N_RIGHT_EVAL,
                          "evaluable   \u00b7   %d sensitivity-positive" % N_RIGHT_POS)):
        S.number(axC, cxx(mx), cxy(BIG_Y), big, size="BIG_NUMBER", color=S.COL["INK"])
        S.annot(axC, cxx(mx), cxy(SUB_Y), sub, color=S.COL["INK2"], ha="center", va="center", size="AXIS")
    # ARB-09 item 11: the sensitivity matrix carries its own qualifier
    S.annot(axC, cxx(MAT_R + MAT_W / 2), cxy(CY0 + 54.2),
            "sensitivity only, not a corrected primary result", color=S.COL["INK2"], ha="center",
            va="center", size="AXIS")
    # one state legend, inside panel c, in the width the two 55 mm matrices leave free
    SX_LEG = MAT_R + MAT_W + 4.0
    for k, line in enumerate(("hatched, not evaluable", "open, evaluable",
                              "filled, sensitivity-positive")):
        S.annot(axC, cxx(SX_LEG), cxy(CY0 + 22.0 + 3.0 * k), line,
                color=S.COL["INK2"], ha="left", va="center", size="AXIS")

    # ================================================================== PANEL D — seven effects
    axD = canvas("d")
    S.head(fig, axD, FIG, "d", "Seven sensitivity-positive effects")
    DX0, DX1 = S.box_mm(FIG, "d")[0], S.box_mm(FIG, "d")[2]
    DY0, DY1 = S.box_mm(FIG, "d")[1], S.box_mm(FIG, "d")[3]
    DLO, DHI = 0.0, 0.018
    DX_A0, DX_A1 = DX0 + 30.0, DX0 + 72.0    # full-length axis: the withdrawn area cap is not a
                                             # reason to destroy the encoding's resolution
    D_ROWS = [DY0 + 8.0 + 5.7 * i for i in range(7)]
    D_AXIS_Y = D_ROWS[-1] + 1.8   # ARB-12 item 2: 3.4 -> 1.8 mm (axis and tick labels rise 1.6 mm),
                                  # so the page's closing gap is 5.4 mm and no longer a 3.8 mm band
    RHO_X = DX0 + 82.0                       # dedicated gutter for the magnitude column (ARB-08 P1)
    # ARB-18: the seven Spearman rho values (0.0263-0.1452) all lie OUTSIDE the panel's 0.000-0.018
    # delta-cosine axis, by 2.46x to 16.49x.  Printing them as a column of numbers beside that axis
    # invited reading them on it.  The numbers are therefore replaced by a fixed-size square
    # magnitude glyph coded by FILL STATE alone, in its own column with no axis and no values.  The
    # three levels are cut on the measured gaps in FIG5_E and the 3 / 2 / 2 split is asserted, so a
    # data change fails here rather than silently relabelling a glyph.
    RHO_CUTS = (0.060, 0.105)
    RHO_VALUES = [float(v) for v in E5["observed_spearman_PC"].tolist()]
    RHO_LEVEL = [0 if v < RHO_CUTS[0] else (1 if v < RHO_CUTS[1] else 2) for v in RHO_VALUES]
    assert [RHO_LEVEL.count(k) for k in (0, 1, 2)] == [3, 2, 2], RHO_LEVEL
    RHO_FILLSTYLE = ("none", "bottom", "full")
    RHO_GLYPH_X = RHO_X + 1.1                # flush-left in the gutter: the square's own half-width


    def dxx(mm):
        return (mm - DX0) / (DX1 - DX0)


    def dxy(mm):
        return 1.0 - (mm - DY0) / (DY1 - DY0)


    def XD(v):
        return DX_A0 + (float(v) - DLO) / (DHI - DLO) * (DX_A1 - DX_A0)


    S.rule(axD, dxx(DX_A0), dxx(DX_A1), dxy(D_AXIS_Y), color=S.COL["RULE_STRONG"])
    S.vrule(axD, dxx(DX_A0), dxy(D_AXIS_Y), dxy(D_ROWS[0] - 3.0), color=S.COL["RULE_STRONG"],
            lw=S.STROKE["SECONDARY"])
    for xv in (DLO, DHI):
        S.annot(axD, dxx(XD(xv)), dxy(D_AXIS_Y + 1.2), "%.3f" % xv, color=S.COL["INK2"],
                ha="center", va="top")
    # ARB-08 P1: the value slot beside each bar carries DELTA COSINE for all seven rows, on the
    # panel's own 0-0.018 scale — never a mixture.  ARB-18: the Spearman magnitudes no longer appear
    # as numbers anywhere; their column is the fill-coded square glyph below, with no axis.
    S.vrule(axD, dxx(RHO_X - 4.0), dxy(D_AXIS_Y), dxy(D_ROWS[0] - 3.4),
            color=S.COL["RULE"], lw=S.STROKE["RULE"])
    S.annot(axD, dxx(RHO_X), dxy(DY0 + 4.4), "rho magnitude", color=S.COL["INK"], ha="left",
            va="center")
    for i, r in enumerate(E5.itertuples()):
        y_mm = D_ROWS[i]
        S.body(axD, 0.0, dxy(y_mm), "%s \u00b7 %s" % (BSH[r.BTB_program], SH[r.BBB_program]),
               color=S.COL["INK"], ha="left", va="center")
        S.lollipop(axD, dxy(y_mm), dxx(XD(0.0)), dxx(XD(r.delta_PC)), S.COL["SENSITIVITY"],
                   ms=S.MARKER["data_marker"])
        S.annot(axD, dxx(XD(r.delta_PC) + 2.0), dxy(y_mm), "+%.4f" % float(r.delta_PC),
                color=S.COL["INK2"], ha="left", va="center", size="AXIS")
        S.rho_glyph(axD, dxx(RHO_GLYPH_X), dxy(y_mm), RHO_FILLSTYLE[RHO_LEVEL[i]])
    # ARB-18: the three-item magnitude key, directly beneath the column — a magnitude legend, not
    # the stacked state legend the brief banned from 5b.  Same fixed square, same fill coding.
    for k, lab in enumerate(("low", "mid", "high")):
        _kx = DX0 + 79.0 + 6.6 * k
        S.rho_glyph(axD, dxx(_kx + 1.1), dxy(188.8), RHO_FILLSTYLE[k])
        S.annot(axD, dxx(_kx + 3.1), dxy(188.8), lab, color=S.COL["INK2"], va="center")

    # ================================================================== PANEL E — concept strip
    axE = canvas("e")
    S.head(fig, axE, FIG, "e", "Representation and inference")
    EX0, EX1 = S.box_mm(FIG, "e")[0], S.box_mm(FIG, "e")[2]
    EY0, EY1 = S.box_mm(FIG, "e")[1], S.box_mm(FIG, "e")[3]
    # verbatim from FIG5_F_interpretive_schematic.csv: Feature representation -> Evaluability ->
    # Inference strength.  Wrapped on two lines because the 2.80 mm single line is ~78 mm and the
    # panel box is 66 mm wide; the wrap is accepted, the shortened label is not.
    STEP_LABELS = [str(v) for v in SCHEM["label"].tolist()]
    S.subtitle(axE, 0.0, 1.0 - 20.0 / (EY1 - EY0), "%s \u2192" % STEP_LABELS[0],
               color=S.COL["INK"], ha="left", va="center")
    S.subtitle(axE, 0.0, 1.0 - 24.0 / (EY1 - EY0),
               "%s \u2192 %s" % (STEP_LABELS[1], STEP_LABELS[2]),
               color=S.COL["INK"], ha="left", va="center")
    S.rule(axE, 0.0, 1.0, 1.0 - 27.0 / (EY1 - EY0), color=S.COL["RULE"])
    S.annot(axE, 0.0, 1.0 - 30.0 / (EY1 - EY0),
            "Representation conditions cross-tissue inference.", color=S.COL["INK2"], va="center", size="AXIS")
    # ARB-09 item 12: the qualifying half of the concept, restored
    S.annot(axE, 0.0, 1.0 - 34.0 / (EY1 - EY0),
            "The primary endpoint stands;", color=S.COL["INK2"], va="center", size="AXIS")
    S.annot(axE, 0.0, 1.0 - 37.2 / (EY1 - EY0),
            "the sensitivity qualifies rather than replaces it.", color=S.COL["INK2"], va="center", size="AXIS")

    # ------------------------------------------------------------------ export + QC
    paths = S.finalize(fig, C.FIGS_MAIN, C.STEM_V3[FIG])
    rec = S.measure(fig)
    rec.update(
        figure=C.STEM_V3[FIG],
        panel_boxes_mm={k: list(v) for k, v in S.PAGE_BOXES[FIG].items() if k != "page_h"},
        visual_anchor=S.ANCHOR[FIG],
        core_message=("Feature representation determines both whether cross-tissue convergence is "
                      "testable and how strongly it is inferred."),
        panels=["a feature-universe coverage", "b gate failures: two facts",
                "c primary vs post-freeze matrices (anchor)", "d the seven sensitivity-positive "
                "effects", "e concept strip"],
        design_source=["FIGSTYLE_V3.json (AMD-01, AMD-02)", "FIGSTYLE_V3.md",
                       "FIGURE_V3_ART_DIRECTION.md section 5 Fig 5"],
        files={k: os.path.relpath(v, C.ROOT).replace("\\", "/") for k, v in paths.items()},
        source_tables=["FIG5_A_feature_universe_coverage.csv",
                       "FIG5_B_gate_failure_decomposition.csv", "FIG5_C_biotype_composition.csv",
                       "FIG5_D_primary_vs_PC.csv", "FIG5_E_seven_sensitivity_pairs.csv"],
        derived_in_canvas=dict(recoverable_pct=round(PCT_RECOVERABLE, 1), lncrna_unmapped_pct=round(ln_u, 1),
                               left_evaluable=N_LEFT_EVAL, left_convergent=N_LEFT_CONV,
                               right_evaluable=N_RIGHT_EVAL, right_sensitivity_positive=N_RIGHT_POS),
    )
    os.makedirs(C.LOGS_V3, exist_ok=True)
    json.dump(rec, open(os.path.join(C.LOGS_V3, "figure_5_render.json"), "w", encoding="utf-8"),
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
