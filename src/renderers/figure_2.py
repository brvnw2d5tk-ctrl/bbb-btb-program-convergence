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
FIG_NAME = 'Fig2'
REQUIRED_SOURCE_TABLES = (
    "FIG2_A_btb_stability.csv",
    "FIG2_A_btb_family_K_membership.csv",
    "FIG2_B_bbb_stability.csv",
    "FIG2_B_bbb_family_K_membership.csv",
    "FIG2_C_bbb_eligibility.csv",
    "FIG2_D_external_replication.csv",
    "FIG2_E_mapping_route.csv",
    "FIG2_E_harmonization_route_counts.csv",
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
    """Released entry point for Fig2.  Renders nothing unless the frozen inputs are present."""
    args = _cli(argv)
    if args.dry_run:
        print(json.dumps(_dry_run_report(args), indent=1, ensure_ascii=False))
        return 0
    try:
        C.require_files(_REQUIRED_RELS, what="the Fig2 render")
        C.ensure_output_dirs()
    except (C.DataRootNotConfigured, C.DataSourceMissing) as exc:
        sys.stderr.write("\n" + os.path.basename(__file__) + ": cannot render Fig2.\n")
        sys.stderr.write(str(exc) + "\n")
        return 2

    SD = C.SRC
    rd = lambda n: pd.read_csv(os.path.join(SD, n))

    FIG = "Fig2"
    PAGE_H_MM = S.page_h(FIG)
    W = S.FULL_W
    fig = plt.figure(figsize=(W, PAGE_H_MM * S.MM))

    CAP = list(C.BBB_CAP)                       # C01 C03 C04 C07 C09 C10
    SH = {p: "C%02d" % int(p[-3:]) for p in C.BBB_CAP_ALL}
    BSH = {p: "F%03d" % int(p[-3:]) for p in C.BTB_FAM}


    def canvas(panel):
        x0, y0, x1, y1 = S.box_mm(FIG, panel)
        ax = fig.add_axes([x0 / S.FULL_W_MM, (PAGE_H_MM - y1) / PAGE_H_MM,
                           (x1 - x0) / S.FULL_W_MM, (y1 - y0) / PAGE_H_MM])
        S.hide_all(ax)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return ax


    # ------------------------------------------------------------------ frozen sources (unchanged)
    A = rd("FIG2_A_btb_stability.csv")
    MA = rd("FIG2_A_btb_family_K_membership.csv")
    B = rd("FIG2_B_bbb_stability.csv")
    MB = rd("FIG2_B_bbb_family_K_membership.csv")     # ARB-04 item 5: frozen-read set restored
    E = rd("FIG2_C_bbb_eligibility.csv")
    D = rd("FIG2_D_external_replication.csv")
    MR = rd("FIG2_E_mapping_route.csv")
    RC = rd("FIG2_E_harmonization_route_counts.csv")

    CAPB = B[B.branch == "Capillary"].reset_index(drop=True)
    ELIG = E.set_index("program_id")
    MEM_A = {p: sorted(MA[MA.program_id == p].K.astype(int)) for p in A.program_id}
    # K extents for panel b come from FIG2_B_bbb_family_K_membership.csv, exactly as V2 did; the
    # stability table carries the same extents and the equality is asserted, not assumed.
    MEM_B = {r.program_id: (int(r.K_min), int(r.K_max)) for r in MB.itertuples()}
    assert all(MEM_B[r.program_id] == (int(r.K_min), int(r.K_max)) for r in CAPB.itertuples()), \
        "FIG2_B family K extents disagree with FIG2_B_bbb_family_K_membership.csv"

    # ================================================================== PANEL A — BTB stability
    axA = canvas("a")
    S.head(fig, axA, FIG, "a", "Stability across K")
    AX0, AX1 = S.box_mm(FIG, "a")[0], S.box_mm(FIG, "a")[2]
    AY0, AY1 = S.box_mm(FIG, "a")[1], S.box_mm(FIG, "a")[3]
    KA0, KA1 = 2, 12
    A_TRK0, A_TRK1 = AX0 + 9.0, AX0 + 51.0
    A_COS0, A_COS1 = AX0 + 55.0, AX0 + 69.0     # shared median-cosine scale (ARB-08 P2)
    A_CLO, A_CHI = 0.985, 1.0001                # V2's cosine scale, unchanged
    A_GLYPH = AX0 + 75.5
    A_ROWS = [11.8 + 14.30 * i for i in range(6)]   # ARB-14: exactly twice panel b's 7.15 mm pitch,
                                                    # so the arms keep first row (11.8) and last row
                                                    # (83.3) aligned inside the taller 5-92 mm band
    A_AXIS_Y = 84.7
    A_HEAD_Y = 9.6
    A_NOTE_Y = (88.4, 91.0)   # ARB-15: re-wrapped at the AXIS token


    def axx(mm):
        return (mm - AX0) / (AX1 - AX0)


    def axy(mm):
        return 1.0 - (mm - AY0) / (AY1 - AY0)


    def KX(v):
        return A_TRK0 + (float(v) - KA0) / (KA1 - KA0) * (A_TRK1 - A_TRK0)


    def AXK(v):
        return (KX(v) - AX0) / (AX1 - AX0)


    S.rule(axA, axx(A_TRK0), axx(A_TRK1), axy(A_AXIS_Y), color=S.COL["RULE_STRONG"])
    for kv in (2, 6, 12):
        S.annot(axA, axx(KX(kv)), axy(A_AXIS_Y + 0.35), "%d" % kv, color=S.COL["INK2"],
                ha="center", va="top")
    for i, r in enumerate(A.itertuples()):
        y_mm = A_ROWS[i]
        S.annot(axA, 0.0, axy(y_mm), BSH[r.program_id], color=S.COL["BTB"], weight="bold",
                ha="left", va="center")
        ks = MEM_A[r.program_id]
        axA.plot([axx(KX(ks[0])), axx(KX(ks[-1]))], [axy(y_mm), axy(y_mm)], color=S.COL["BTB"],
                 lw=S.STROKE["HAIR"], solid_capstyle="butt", zorder=S.Z["FILL"])
        S.rule(axA, axx(A_COS0), axx(A_COS1), axy(y_mm), color=S.COL["RULE_STRONG"],
               lw=S.STROKE["RULE"])
        # ARB-08 P2: the median pairwise cosine the frozen legend says is drawn.  A filled SQUARE in
        # slate, against the stability column's filled CIRCLE / open AMBER DIAMOND, so the two
        # statistics stay distinguishable with zero chroma (shape, not colour).
        t = min(1.0, max(0.0, (float(r.median_pairwise_cosine) - A_CLO) / (A_CHI - A_CLO)))
        S.filled_marker(axA, axx(A_COS0 + (A_COS1 - A_COS0) * t), axy(y_mm), S.COL["BTB"],
                        marker="s", s=9)
        if bool(r.stable_at_both):
            S.filled_marker(axA, axx(A_GLYPH), axy(y_mm), S.COL["SUPPORTED"], s=20)
        else:                                  # BTB_FAM_006: 0.65-ambiguous, open amber diamond
            S.open_diamond(axA, axx(A_GLYPH), axy(y_mm), s=21)
    for x_mm, lab in ((A_TRK0 + (A_TRK1 - A_TRK0) / 2.0, "K coverage"),
                      (A_COS0 + (A_COS1 - A_COS0) / 2.0, "median cosine"),
                      (A_GLYPH, "stable")):
        S.annot(axA, axx(x_mm), axy(A_HEAD_Y), lab, color=S.COL["INK2"], weight="bold", size="AXIS",
                ha="center", va="center")
    # ARB-15: the ARB-13 merged footer measured x 3.0-91.3 mm inside panel a's 81 mm box once the
    # sanctioned remedy): the decode-critical count keeps AXIS on its own line and the amber
    # convention key stays a separate LEGEND line.  Same words, same numbers, one line break more.
    S.annot(axA, 0.0, axy(A_NOTE_Y[0]),
            "%d / %d stable at 0.65 and 0.80   \u00b7   all %d primary-eligible"
            % (int(A.stable_at_both.sum()), len(A), int(A.primary_eligible.sum())),
            color=S.COL["INK"], weight="semibold", va="center", size="AXIS")
    S.annot(axA, 0.0, axy(A_NOTE_Y[1]), "amber diamond, 0.65-ambiguous", color=S.COL["INK2"],
            va="center")

    # ================================================================== PANEL B — eleven families
    axB = canvas("b")
    S.head(fig, axB, FIG, "b", "Eleven Capillary families")
    BX0, BX1 = S.box_mm(FIG, "b")[0], S.box_mm(FIG, "b")[2]
    BY0, BY1 = S.box_mm(FIG, "b")[1], S.box_mm(FIG, "b")[3]
    KB0 = int(CAPB.K_min.min())
    KB1 = int(CAPB.K_max.max())
    B_TRK0, B_TRK1 = BX0 + 9.0, BX0 + 51.0
    B_TICK_X = BX0 + 7.0
    B_COS0, B_COS1 = BX0 + 55.0, BX0 + 69.0     # shared median-cosine scale (ARB-08 P2)
    B_CLO, B_CHI = 0.965, 1.0001                # V2's cosine scale, unchanged
    B_GLYPH = BX0 + 75.0
    # ARB-14: panel b's row pitch takes the height the a/b band gained from panel d's bottom slack.
    # 6.24 -> 7.15 mm is above the 6.64 mm a legal >=5 mm run needs for the measured 1.64-2.04 mm
    # row ink, so all ten inter-row runs clear the 3-5 mm band.  Panel a is doubled to 14.30 mm, so
    # row 1 (11.8) and row 11 (83.3) still align across the two arms.
    B_ROWS = [11.8 + 7.15 * i for i in range(11)]
    B_AXIS_Y = 84.7
    B_HEAD_Y = 9.6
    B_KEY_Y = (87.7, 90.7)   # ARB-16: 3.00 mm baseline pitch


    def bxx(mm):
        return (mm - BX0) / (BX1 - BX0)


    def bxy(mm):
        return 1.0 - (mm - BY0) / (BY1 - BY0)


    def KBX(v):
        return B_TRK0 + (float(v) - KB0) / (KB1 - KB0) * (B_TRK1 - B_TRK0)


    S.rule(axB, bxx(B_TRK0), bxx(B_TRK1), bxy(B_AXIS_Y), color=S.COL["RULE_STRONG"])
    for kv in (2, 8, 15):
        S.annot(axB, bxx(KBX(kv)), bxy(B_AXIS_Y + 0.35), "%d" % kv, color=S.COL["INK2"],
                ha="center", va="top")
    for i, r in enumerate(CAPB.itertuples()):
        y_mm = B_ROWS[i]
        S.annot(axB, 0.0, bxy(y_mm), SH[r.program_id], color=S.COL["BBB"], weight="bold",
                ha="left", va="center")
        k0, k1 = MEM_B[r.program_id]
        axB.plot([bxx(KBX(k0)), bxx(KBX(k1))], [bxy(y_mm), bxy(y_mm)],
                 color=S.COL["BBB"], lw=S.STROKE["HAIR"], solid_capstyle="butt", zorder=S.Z["FILL"])
        S.rule(axB, bxx(B_COS0), bxx(B_COS1), bxy(y_mm), color=S.COL["RULE_STRONG"],
               lw=S.STROKE["RULE"])
        # ARB-08 P2: the median pairwise cosine restored, as a filled slate SQUARE on a shared scale
        t = min(1.0, max(0.0, (float(r.median_pairwise_cosine) - B_CLO) / (B_CHI - B_CLO)))
        S.filled_marker(axB, bxx(B_COS0 + (B_COS1 - B_COS0) * t), bxy(y_mm), S.COL["BTB"],
                        marker="s", s=9)
        if bool(r.primary_eligible):
            S.filled_marker(axB, bxx(B_GLYPH), bxy(y_mm), S.COL["BBB"], s=20)
        else:
            S.open_marker(axB, bxx(B_GLYPH), bxy(y_mm), s=20, ec=S.COL["RULE_STRONG"],
                          lw=S.STROKE["GLYPH"])
        if int(ELIG.loc[r.program_id, "sample_dominated_members"]) > 0:
            # the five caption-mandated exclusion ticks: data-bearing amber, <= 0.60 pt, open stroke
            axB.plot([bxx(B_TICK_X), bxx(B_TICK_X)], [bxy(y_mm) - 0.9 / (BY1 - BY0),
                                                      bxy(y_mm) + 0.9 / (BY1 - BY0)],
                     color=S.COL["SENSITIVITY"], lw=S.STROKE["DATA_MAIN"],
                     solid_capstyle="butt", zorder=S.Z["GLYPH"])
    for x_mm, lab in ((B_TRK0 + (B_TRK1 - B_TRK0) / 2.0, "K coverage"),
                      (B_COS0 + (B_COS1 - B_COS0) / 2.0, "median cosine"),
                      (B_GLYPH, "eligible")):
        S.annot(axB, bxx(x_mm), bxy(B_HEAD_Y), lab, color=S.COL["INK2"], weight="bold",
                ha="center", va="center", size="AXIS")
    N_STABLE_B = int(sum(str(a).startswith("STABLE") and str(b).startswith("STABLE")
                         for a, b in zip(CAPB.edge065, CAPB.edge080)))
    N_ELIG_B = int(CAPB.primary_eligible.sum())
    # ARB-13: panel b's three key lines become two.  The two marker conventions share one line;
    # every element and every clause survives, only the line break goes.
    S.annot(axB, 0.0, bxy(B_KEY_Y[0]),
            "%d / %d stable at 0.65 and 0.80" % (N_STABLE_B, len(CAPB)),
            color=S.COL["INK"], weight="semibold", va="center", size="AXIS")
    S.annot(axB, 0.0, bxy(B_KEY_Y[1]),
            "filled, primary-eligible   \u00b7   open, stable   \u00b7   "
            "amber tick, sample-dominated exclusion", color=S.COL["INK2"], va="center", size="AXIS")

    # ================================================================== PANEL C — the anchor
    axC = canvas("c")
    S.head(fig, axC, FIG, "c", "External structural replication")
    # ARB-09 item 3: the matched-null definition the frozen legend states
    S.annot(axC, 1.0, 1.0 - 3.5 / 48.0,
            "marker, observed   \u00b7   tick, null median   \u00b7   bar, null median\u2013q95",
            color=S.COL["INK2"], ha="right", va="center", size="AXIS")
    CX0, CX1 = S.box_mm(FIG, "c")[0], S.box_mm(FIG, "c")[2]
    CY0, CY1 = S.box_mm(FIG, "c")[1], S.box_mm(FIG, "c")[3]
    GUT = 6.0
    BAND_W = (CX1 - CX0 - GUT) / 2.0
    C_L0, C_L1 = CX0, CX0 + BAND_W                 # 3.0 - 86.0 mm
    C_R0, C_R1 = C_L1 + GUT, CX1                   # 92.0 - 175.0 mm
    C_BAND_LBL_Y = CY0 + 7.0
    C_RULE_Y = CY0 + 8.6
    # ARB-12 item 2: the whole lower block of the anchor (six program rows, their axis, the tick
    # labels and the two display numerators) rises 2.0 mm, so the 3.4 mm dead band between the band
    # rule and the first row becomes 2.2 mm while the row leading (4.4 mm pitch) and the axis gaps
    # stay below the 3 mm band.  No content, order or value moves.
    C_ROWS = [CY0 + 11.6 + 4.4 * i for i in range(6)]
    C_AXIS_Y = CY0 + 36.6
    # ARB-14: the anchor's two display numerators move 42.6 -> 44.0 mm, so panel c's foot lands on
    # its box floor and the c -> d band measures 7.6 mm instead of a 10.1 mm accidental gap.
    C_BIG_Y = CY0 + 44.0
    LIM_PRIMARY = (0.705, 0.810)
    LIM_SENS = (-0.05, 0.43)


    def cxx(mm):
        return (mm - CX0) / (CX1 - CX0)


    def cxy(mm):
        return 1.0 - (mm - CY0) / (CY1 - CY0)


    def band_axis(b0, b1, lim):
        lbl, trk0, trk1 = b0 + 11.0, b0 + 12.5, b1 - 2.0

        def X(v):
            return trk0 + (float(v) - lim[0]) / (lim[1] - lim[0]) * (trk1 - trk0)
        return lbl, trk0, trk1, X


    for band, (b0, b1), lim, ticks, label, lcol, kind in (
            ("PRESPECIFIED PRIMARY", (C_L0, C_L1), LIM_PRIMARY, (0.70, 0.80),
             "PRESPECIFIED PRIMARY", S.COL["INK"], "primary"),
            ("POST-FREEZE SENSITIVITY", (C_R0, C_R1), LIM_SENS, (0.07, 0.42),
             "POST-FREEZE SENSITIVITY", S.COL["SENSITIVITY_TEXT"], "sensitivity")):
        sub = D[D.band == band].set_index("program_id")
        lbl, trk0, trk1, X = band_axis(b0, b1, lim)
        mid = (trk0 + trk1) / 2.0
        S.annot(axC, cxx(mid), cxy(C_BAND_LBL_Y), label, color=lcol, ha="center", va="center",
                size="PANEL_TITLE")
        # two 0.45 pt rules of EQUAL length; the sensitivity one is Fig2's single amber rule
        S.rule(axC, cxx(mid - 6.0), cxx(mid + 6.0), cxy(C_RULE_Y),
               color=S.COL["SENSITIVITY"] if kind == "sensitivity" else S.COL["RULE_STRONG"])
        for i, p in enumerate(CAP):
            r = sub.loc[p]
            y_mm = C_ROWS[i]
            S.annot(axC, cxx(lbl), cxy(y_mm), SH[p], color=S.COL["BBB"], weight="bold",
                    ha="right", va="center")
            # one light guide rule per program row, across both bands, so the six rows read as
            # aligned pairs and the anchor carries the figure's ink instead of the support rails
            S.rule(axC, cxx(trk0), cxx(trk1), cxy(y_mm), color=S.COL["RULE_STRONG"],
                   lw=S.STROKE["RULE"])
            axC.plot([cxx(X(r.null_median)), cxx(X(r.null_q95))], [cxy(y_mm), cxy(y_mm)],
                     color=S.COL["INK2"], lw=S.STROKE["SECONDARY"], solid_capstyle="butt",
                     zorder=S.Z["FILL"])
            # the frozen legend words the reference as "the tick the matched-null median and the bar
            # the matched-null median-to-q95 reference": bar plus a distinct short median tick
            axC.plot([cxx(X(r.null_median)), cxx(X(r.null_median))],
                     [cxy(y_mm) - S.TICK_HALF_MM / 48.0, cxy(y_mm) + S.TICK_HALF_MM / 48.0],
                     color=S.COL["INK2"], lw=S.STROKE["DATA_MAIN"], solid_capstyle="butt",
                     zorder=S.Z["FILL"] + 0.1)
            ec = (S.COL["SENSITIVITY"] if kind == "sensitivity" else S.COL["SUPPORTED"]) \
                if bool(r.replicated) else S.COL["NOT_SUPPORTED"]
            S.open_marker(axC, cxx(X(r.observed)), cxy(y_mm), s=17, ec=ec)
        S.rule(axC, cxx(trk0), cxx(trk1), cxy(C_AXIS_Y), color=S.COL["RULE_STRONG"])
        for xv in ticks:
            S.annot(axC, cxx(X(xv)), cxy(C_AXIS_Y + 1.1), "%.2f" % xv, color=S.COL["INK2"],
                    ha="center", va="top")
        n_rep = int(sub["replicated"].sum())
        S.number(axC, cxx(mid) - 0.012, cxy(C_BIG_Y), "%d" % n_rep, size="BIG_NUMBER",
                 color=S.COL["INK"])
        S.annot(axC, cxx(mid) + 0.012, cxy(C_BIG_Y + 0.4), "/ 6", color=S.COL["INK"],
                ha="left", va="center", size="PANEL_TITLE")

    # ================================================================== PANEL D — mapping route
    axD = canvas("d")
    S.head(fig, axD, FIG, "d", "Mapping-route limitation")
    DX0, DX1 = S.box_mm(FIG, "d")[0], S.box_mm(FIG, "d")[2]
    DY0, DY1 = S.box_mm(FIG, "d")[1], S.box_mm(FIG, "d")[3]
    tot = int(round(float(RC[RC.mapping_route == "LEVEL1_ENSEMBL_EXACT"].n_features.iloc[0])
                    + float(RC[RC.mapping_route == "LEVEL2_UNIQUE_CANONICAL_SYMBOL"].n_features.iloc[0])))
    ex = int(RC[RC.mapping_route == "LEVEL1_ENSEMBL_EXACT"].n_features.iloc[0])
    fbk = int(RC[RC.mapping_route == "LEVEL2_UNIQUE_CANONICAL_SYMBOL"].n_features.iloc[0])
    n_evaluable = int((~MR["evaluable"].astype(bool)).sum())
    gate = float(MR["coverage_gate"].iloc[0])
    BAR_X0, BAR_X1 = DX0 + 3.0, DX0 + 98.0            # 95 mm, not full page width (ARB-07)
    # ARB-14: d's box is 41 mm instead of 49 (the 8 mm went to a/b).  The same six strings are
    # re-spaced inside it with every gap on the 5-9 mm scale, and the closing dead band falls from
    # 19.1 to 8.1 mm.
    BAR_Y, BAR_H = 19.0, 1.2


    def dxx(mm):
        return (mm - DX0) / (DX1 - DX0)


    def dxy(mm):
        return 1.0 - (mm - DY0) / (DY1 - DY0)


    # ARB-12 item 2: this block's three text lines close up (9.0 -> 7.6 mm for the header line,
    # +8.4 -> +7.6 and +14.0 -> +11.6 mm for the two footer lines), turning the 4.1 / 3.3 / 3.9 mm
    # dead bands into 2.6-2.7 mm leading.  Every string and every number is unchanged.
    S.annot(axD, dxx(BAR_X0), dxy(DY0 + 11.0), "%s shared genes used by the replication test"
            % format(tot, ","), color=S.COL["INK"], va="center", )
    # ARB-07: a 95 x 1.2 mm proportional bar in RULE_STRONG, NOT a full-page-width ground.  The
    # earlier 165 x 5 mm #EAECED block was 824 mm2 = 2.37 % of the page, the heaviest object in the
    # figure by 5x, and at full width the 99.7 % segment covered the whole bar so the proportion it
    # exists to show was invisible.  The 64-gene Ensembl-exact segment is a 1.0 mm INK block at the
    # left end; both value strings are one line beneath the bar.
    axD.add_patch(plt.Rectangle((dxx(BAR_X0), dxy(DY0 + BAR_Y + BAR_H)),
                                dxx(BAR_X1) - dxx(BAR_X0), BAR_H / (DY1 - DY0),
                                facecolor=S.COL["RULE_STRONG"], edgecolor="none", lw=0,
                                zorder=S.Z["FILL"]))
    # ARB-08 P5: the Ensembl-exact segment is drawn at its true proportion — 0.3 % of the bar width
    # (0.285 mm on a 95 mm bar), with a 0.25 mm floor so it never vanishes at 300 dpi.
    SEG_MM = max(0.25, (ex / float(tot)) * (BAR_X1 - BAR_X0))
    axD.add_patch(plt.Rectangle((dxx(BAR_X0), dxy(DY0 + BAR_Y + BAR_H)),
                                SEG_MM / (DX1 - DX0), BAR_H / (DY1 - DY0),
                                facecolor=S.COL["INK"], edgecolor="none", lw=0,
                                zorder=S.Z["FILL"] + 0.1))
    # ARB-13: panel d's three footer lines become two, with the register split kept — one grey
    # detail line and one INK conclusion line that now carries the evaluability clause as well.
    # Every clause and every number survives; the block is also pushed down the panel, which takes
    # the closing dead band from 21.3 to 19.3 mm.  Gaps: bar -> line 1 = 5.6 mm, line 1 -> line 2 =
    # 6.1 mm, both legal.
    S.annot(axD, dxx(BAR_X0), dxy(DY0 + BAR_Y + BAR_H + 7.8),
            "%d genes (%.1f%%) matched at the Ensembl-exact level   \u00b7   %s (%.1f%%) required "
            "the canonical-symbol fallback" % (ex, 100.0 * ex / tot, format(fbk, ","),
                                               100.0 * fbk / tot),
            color=S.COL["INK2"], va="center", )
    S.annot(axD, dxx(BAR_X0), dxy(DY0 + BAR_Y + BAR_H + 16.0),
            "%d / %d evaluable on the Ensembl-exact-only route   \u00b7   unchanged %.2f gate   "
            "\u00b7   an evaluability limit, not a negative result" % (n_evaluable, len(MR), gate),
            color=S.COL["INK"], va="center", )

    # ------------------------------------------------------------------ export + QC
    paths = S.finalize(fig, C.FIGS_MAIN, C.STEM_V3[FIG])
    rec = S.measure(fig)
    rec.update(
        figure=C.STEM_V3[FIG],
        panel_boxes_mm={k: list(v) for k, v in S.PAGE_BOXES[FIG].items() if k != "page_h"},
        visual_anchor=S.ANCHOR[FIG],
        core_message=("Stable within-organ transcriptional structure can be recovered, but BBB "
                      "external replication is only partial and statistic/mapping sensitive."),
        panels=["a BTB stability across K", "b eleven Capillary families",
                "c external structural replication (anchor)", "d mapping-route limitation"],
        design_source=["FIGSTYLE_V3.json (AMD-01/02/03)", "FIGSTYLE_V3.md",
                       "FIGURE_V3_ART_DIRECTION.md section 5 Fig 2"],
        v2_defect_fixed=("V2 Fig2 panels a and b had overlapping axes rectangles (84 x 55 mm = "
                         "13.2 % of the page) and axes_2's white background painted over axes_1, so "
                         "panel a's median-cosine column and stability glyph column never rendered "
                         "and the F001-F004 K-bands were truncated at x = 91.0 mm. The V3 boxes "
                         "a = 3-84 mm and b = 90-175 mm do not overlap."),
        files={k: os.path.relpath(v, C.ROOT).replace("\\", "/") for k, v in paths.items()},
        source_tables=["FIG2_A_btb_stability.csv", "FIG2_A_btb_family_K_membership.csv",
                       "FIG2_B_bbb_stability.csv", "FIG2_C_bbb_eligibility.csv",
                       "FIG2_D_external_replication.csv", "FIG2_E_mapping_route.csv",
                       "FIG2_E_harmonization_route_counts.csv"],
        derived_in_canvas=dict(primary_replicated=int(D[D.band == "PRESPECIFIED PRIMARY"]
                                                      ["replicated"].sum()),
                               sensitivity_replicated=int(D[D.band == "POST-FREEZE SENSITIVITY"]
                                                          ["replicated"].sum()),
                               shared_genes=tot, ensembl_exact=ex, canonical_fallback=fbk,
                               ensembl_route_evaluable=n_evaluable, gate=gate),
    )
    os.makedirs(C.LOGS_V3, exist_ok=True)
    json.dump(rec, open(os.path.join(C.LOGS_V3, "figure_2_render.json"), "w", encoding="utf-8"),
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
