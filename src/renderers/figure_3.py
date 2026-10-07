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
FIG_NAME = 'Fig3'
REQUIRED_SOURCE_TABLES = (
    "FIG3_A_bbb_evidence_matrix.csv",
    "FIG3_B_bbb_subject_paired.csv",
    "FIG3_B_bbb_subject_specificity.csv",
    "FIG3_C_btb_evidence_matrix.csv",
    "FIG3_D_btb_sample_paired.csv",
    "FIG3_D_btb_sample_specificity.csv",
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
    """Released entry point for Fig3.  Renders nothing unless the frozen inputs are present."""
    args = _cli(argv)
    if args.dry_run:
        print(json.dumps(_dry_run_report(args), indent=1, ensure_ascii=False))
        return 0
    try:
        C.require_files(_REQUIRED_RELS, what="the Fig3 render")
        C.ensure_output_dirs()
    except (C.DataRootNotConfigured, C.DataSourceMissing) as exc:
        sys.stderr.write("\n" + os.path.basename(__file__) + ": cannot render Fig3.\n")
        sys.stderr.write(str(exc) + "\n")
        return 2

    SD = C.SRC
    rd = lambda n: pd.read_csv(os.path.join(SD, n))

    FIG = "Fig3"
    PAGE_H_MM = S.page_h(FIG)
    W = S.FULL_W
    fig = plt.figure(figsize=(W, PAGE_H_MM * S.MM))

    PROG = list(C.BBB_CAP)
    BTB = list(C.BTB_FAM)
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
    A3 = rd("FIG3_A_bbb_evidence_matrix.csv").set_index("program_id").loc[PROG]
    Bp = rd("FIG3_B_bbb_subject_paired.csv")          # ARB-04 item 1: frozen-read set restored
    Bs = rd("FIG3_B_bbb_subject_specificity.csv")
    C3 = rd("FIG3_C_btb_evidence_matrix.csv").set_index("program_id").loc[BTB]
    Dp = rd("FIG3_D_btb_sample_paired.csv")           # ARB-04 item 1: frozen-read set restored
    Ds = rd("FIG3_D_btb_sample_specificity.csv")

    # Provenance check (no recomputation is drawn): the per-subject / per-sample paired tables carry
    # exactly the median and IQR that the frozen specificity summary tables hold, to floating-point
    # rounding of the frozen CSV.  The render still draws the summary values, as V2 did.
    _prov = {"bbb_max_median_absdiff": 0.0, "bbb_max_iqr_absdiff": 0.0, "btb_max_median_absdiff": 0.0,
             "btb_max_iqr_absdiff": 0.0, "bbb_pairs": 0, "btb_rows": 0}
    for _r in Bs.itertuples():
        _g = Bp[(Bp.program_id == _r.program_id) & (Bp.comparison == _r.comparison)]["difference"]
        if not len(_g):
            continue
        _prov["bbb_pairs"] += 1
        _prov["bbb_max_median_absdiff"] = max(_prov["bbb_max_median_absdiff"],
                                              abs(float(np.median(_g)) - float(_r.median_paired_difference)))
        _q1, _q3 = np.percentile(_g, [25, 75])
        _prov["bbb_max_iqr_absdiff"] = max(_prov["bbb_max_iqr_absdiff"],
                                           abs(float(_q3 - _q1) - float(_r.iqr_paired_difference)))
    for _r in Ds.itertuples():
        _g = Dp[(Dp.program_id == _r.program_id) & (Dp.comparison == _r.comparison)]["difference"]
        if not len(_g) or pd.isna(_r.median_sample_level_difference):
            continue
        _prov["btb_rows"] += 1
        _prov["btb_max_median_absdiff"] = max(
            _prov["btb_max_median_absdiff"],
            abs(float(np.median(_g)) - float(_r.median_sample_level_difference)))
        _q1, _q3 = np.percentile(_g, [25, 75])
        _prov["btb_max_iqr_absdiff"] = max(
            _prov["btb_max_iqr_absdiff"],
            abs(float(_q3 - _q1) - float(_r.iqr_sample_level_difference)))
    for _k, _v in _prov.items():
        _prov[_k] = round(_v, 9) if isinstance(_v, float) else _v
    assert max(_prov["bbb_max_median_absdiff"], _prov["bbb_max_iqr_absdiff"],
               _prov["btb_max_median_absdiff"], _prov["btb_max_iqr_absdiff"]) < 1e-6, _prov


    def MK(ax, panel):
        """mm -> axes fraction helpers for one panel."""
        x0, y0, x1, y1 = S.box_mm(FIG, panel)
        return (lambda mm: (mm - x0) / (x1 - x0)), (lambda mm: 1.0 - (mm - y0) / (y1 - y0)), (x0, y0, x1, y1)


    # ================================================================== PANEL A — 6 x 3 glyph matrix
    axA = canvas("a")
    S.head(fig, axA, FIG, "a", "BBB programs: three properties")
    axx, axy, (AX0, AY0, AX1, AY1) = MK(axA, "a")
    COLS_A = [("Stable", 34.0), ("Replicated", 68.0), ("Specific", 102.0)]
    ROWS_A = [14.8 + 6.0 * i for i in range(6)]      # 6.0 mm pitch (glyph_row_pitch_min), which
                                                     # frees air below the matrix for the thesis line
    for name, cx in COLS_A:
        S.annot(axA, axx(cx), axy(11.4), name, color=S.COL["INK2"], weight="bold", ha="center",
                va="center", size="PANEL_TITLE")
    # ARB-04 item 3: the right-hand annotation column needs its own <= 2-word header
    S.annot(axA, axx(112.0), axy(11.4), "Expression program", color=S.COL["INK2"], weight="bold",
            ha="left", va="center", size="PANEL_TITLE")
    S.annot(axA, 1.0, axy(11.4), "amber ring, C01 Spearman sensitivity", color=S.COL["INK2"],
            ha="right", va="center")
    for i, p in enumerate(PROG):
        r = A3.loc[p]
        y = ROWS_A[i]
        S.annot(axA, axx(26.0), axy(y), SH[p], color=S.COL["BBB"], weight="bold", ha="right",
                va="center")
        S.filled_marker(axA, axx(34.0), axy(y), S.COL["BBB"], s=19)                 # stable: all six
        if str(r.external_replication) == "REPLICATED":
            S.filled_marker(axA, axx(68.0), axy(y), S.COL["SUPPORTED"], s=19)
        else:
            S.open_marker(axA, axx(68.0), axy(y), s=19, ec=S.COL["NOT_SUPPORTED"])
        if str(r.spearman_sensitivity) == "REPLICATED":        # exactly one: C01
            S.ring_outline(axA, axx(68.0), axy(y), color=S.COL["SENSITIVITY"], s=31)
        if str(r.capillary_specificity) == "SUPPORTED":
            S.filled_marker(axA, axx(102.0), axy(y), S.COL["NOT_SUPPORTED"], s=19)
        else:
            S.open_marker(axA, axx(102.0), axy(y), s=19, ec=S.COL["NOT_SUPPORTED"])
        S.annot(axA, axx(112.0), axy(y), str(r.generic_interpretation), color=S.COL["INK2"],
                ha="left", va="center", size="AXIS")
    # ARB-09 item 6 / ARB-10 N1: the panel's thesis sentence, now clear of the last matrix row
    # (rows end at 44.8 mm; the sentence sits at 48.6 mm with 1.9 mm of air above its cap)
    S.annot(axA, axx(85.0), axy(48.6), "no family is both replicated and specific",
            color=S.COL["INK"], weight="semibold", ha="center", va="center", size="PANEL_TITLE")

    # ================================================================== PANEL B — generality warning
    axB = canvas("b")
    S.head(fig, axB, FIG, "b", "BTB generality warning")
    bxx, bxy, (BX0, BY0, BX1, BY1) = MK(axB, "b")
    COLS_B = [("Stable", 30.0), ("Sample pattern", 58.0), ("Reference", 86.0),
              ("top200 coverage", 112.0), ("Warning", 140.0)]
    ROWS_B = [65.0 + 6.4 * i for i in range(6)]
    for name, cx in COLS_B:
        S.annot(axB, bxx(cx), bxy(62.4), name, color=S.COL["INK2"], weight="bold", ha="center",
                va="center", size="PANEL_TITLE")
    # The frozen legend states "The statistic drawn is the frozen top200 coverage proportion against
    # the unchanged 0.70 gate", so that statistic is drawn: one 24 mm 0-1 track per family with the
    # unchanged gate as a single 0.60 pt tick spanning the column.
    COV0, COV_W = 100.0, 24.0
    GATE_X = COV0 + COV_W * 0.70
    S.vrule(axB, bxx(GATE_X), bxy(ROWS_B[0] - 3.4), bxy(ROWS_B[-1] + 3.4), color=S.COL["INK2"],
            lw=S.STROKE["DATA_MAIN"])
    for i, p in enumerate(BTB):
        r = C3.loc[p]
        y = ROWS_B[i]
        S.annot(axB, bxx(26.0), bxy(y), BSH[p], color=S.COL["BTB"], weight="bold", ha="right",
                va="center")
        S.filled_marker(axB, bxx(30.0), bxy(y), S.COL["SUPPORTED"], s=19)
        if str(r.internal_sample_pattern).endswith("MIXED"):
            # ARB-08 P6: the mixed sub-state is named in the panel key below, and the glyph is the
            # same charcoal as its open-circle neighbours so the column reads as one syntax family
            S.open_diamond(axB, bxx(58.0), bxy(y), s=19, color=S.COL["NOT_SUPPORTED"])
        else:
            S.open_marker(axB, bxx(58.0), bxy(y), s=19, ec=S.COL["NOT_SUPPORTED"])
        S.not_evaluable_swatch(axB, bxx(86.0 - 3.0), bxy(y), w=6.0 / (BX1 - BX0),
                               h=3.4 / (BY1 - BY0))
        S.rule(axB, bxx(COV0), bxx(COV0 + COV_W), bxy(y), color=S.COL["RULE_STRONG"],
               lw=S.STROKE["RULE"])
        t = min(1.0, max(0.0, float(r.external_ST_coverage)))
        S.filled_marker(axB, bxx(COV0 + COV_W * t), bxy(y), S.COL["BTB"], marker="s", s=9)
        if str(r.gse142585_warning).startswith("SOMATIC_OR_VASCULAR"):   # six open amber diamonds
            S.open_diamond(axB, bxx(140.0), bxy(y), s=19)
    N_WARN = int(C3["gse142585_warning"].astype(str)
                 .str.startswith("SOMATIC_OR_VASCULAR").sum())
    S.annot(axB, bxx(152.0), bxy(81.0), "%d / %d generality warning" % (N_WARN, len(BTB)),
            color=S.COL["INK2"], ha="left", va="center", size="AXIS")
    # ARB-09 item 7 and ARB-08 P6: ONE glyph key for the panel, which panel c below also reads against
    S.annot(axB, 0.0, bxy(99.6),
            "sample pattern: open, not supported   \u00b7   diamond, mixed   \u00b7   "
            "hatched, not evaluable", color=S.COL["INK2"], va="center", size="AXIS")
    S.annot(axB, bxx(GATE_X), bxy(99.6), "0.70 gate", color=S.COL["INK2"], ha="center",
            va="center", size="AXIS")

    # ================================================================== PANEL C — specificity
    # c is ONE top-level panel with an internal left/right split: the two FIGSTYLE_V3 boxes
    # c_left (3-84) and c_right (90-175) are drawn as a single 3-175 mm panel with one letter, one
    # heading and one shared baseline rule.
    C_CBOX = (3.0, 107.0, 175.0, 186.0)
    axC = fig.add_axes([C_CBOX[0] / S.FULL_W_MM, (PAGE_H_MM - C_CBOX[3]) / PAGE_H_MM,
                        (C_CBOX[2] - C_CBOX[0]) / S.FULL_W_MM,
                        (C_CBOX[3] - C_CBOX[1]) / PAGE_H_MM])
    S.hide_all(axC)
    axC.set_xlim(0, 1)
    axC.set_ylim(0, 1)
    _cx0, _cy0, _cx1, _cy1 = C_CBOX


    def cxx(mm):
        return (mm - _cx0) / (_cx1 - _cx0)


    def cxy(mm):
        return 1.0 - (mm - _cy0) / (_cy1 - _cy0)


    _base = _cy0 + S.LETTER_DY_MM
    fig.text((_cx0 + S.LETTER_DX_MM) / S.FULL_W_MM,
             1.0 - (_base - S.CAP_RATIO * S.FONT_MM["PANEL_LETTER"]) / PAGE_H_MM, "c",
             fontsize=S.FS("PANEL_LETTER"), fontweight="bold", color=S.COL["INK"], ha="left",
             va="top")
    axC.text(S.HEADING_DX_MM / (_cx1 - _cx0),
             1.0 - (_base - S.CAP_RATIO * S.FONT_MM["PANEL_TITLE"] - _cy0) / (_cy1 - _cy0),
             "Subject and sample specificity", transform=axC.transAxes,
             fontsize=S.FS("PANEL_TITLE"), fontweight="semibold", color=S.COL["INK"], ha="left",
             va="top")

    C_ROWS = [126.0 + 9.0 * i for i in range(6)]     # 126 - 171 mm
    C_AXIS_Y = 174.0
    C_TOP_LBL_Y = 118.0                              # comparator group headers, above the zero rules
                                                     # (ARB-12 item 2: 119.0 -> 118.0 mm, so the
                                                     # 3.7 mm band under the two half-titles closes
                                                     # to 2.6 mm and the two-line labels still clear
                                                     # the first row by 2.5 mm)
    C_TICK_Y = 176.0
    C_QTY_Y = 179.4                                  # ARB-10 N2: the axis quantity, one token per half
    C_HEAD_Y = 182.6                                 # ARB-10 N3: the headline names the property
    CMPB = [("A_other_endothelial", "other\nendothelial"), ("B_mural", "mural"),
            ("C_fibroblast", "fibroblast"), ("D_nonvascular", "nonvascular")]
    CMPT = [("C1_germ_compartments", "germ"), ("C3_other_somatic", "other\nsomatic"),
            ("C2_leydig_interstitial", "Leydig")]

    # one shared zero/baseline rule across the full width of the c box
    S.rule(axC, cxx(C_CBOX[0]), cxx(C_CBOX[2]), cxy(C_AXIS_Y), color=S.COL["RULE_STRONG"],
           lw=S.STROKE["SECONDARY"])

    LEFT_X0, LEFT_X1 = 12.0, 82.0
    RIGHT_X0, RIGHT_X1 = 104.0, 172.0
    S.annot(axC, cxx((LEFT_X0 + LEFT_X1) / 2.0), cxy(114.0), "BBB capillary",
            color=S.COL["BBB"], ha="center", va="center", size="PANEL_TITLE")
    S.annot(axC, cxx((RIGHT_X0 + RIGHT_X1) / 2.0), cxy(114.0), "BTB Sertoli-like set",
            color=S.COL["BTB"], ha="center", va="center", size="PANEL_TITLE")


    def draw_half(rows, x0, x1, cmps, table, key_cmp, val_col, iqr_col, scale,
                  labels=None, filled_progs=()):
        gw = (x1 - x0) / len(cmps)
        for j, (key, lab) in enumerate(cmps):
            cx = x0 + gw * (j + 0.5)
            S.vrule(axC, cxx(cx), cxy(C_AXIS_Y), cxy(C_ROWS[0] - 2.0), color=S.COL["RULE_STRONG"],
                    lw=S.STROKE["DATA_MAIN"])
            S.annot(axC, cxx(cx), cxy(C_TOP_LBL_Y), lab, color=S.COL["INK2"], ha="center",
                    va="top", linespacing=1.25)
            if labels:
                # ARB-11 item 2: ONE shared comparator tick treatment — identical tick values and an
                # identical local scale in both halves, with a tick STROKE under every group and the
                # values labelled once per half (under the first group).  Strokes, not "|" text, so
                # the type count is untouched.
                for xv in labels:
                    S.vrule(axC, cxx(cx + xv * scale), cxy(C_AXIS_Y), cxy(C_AXIS_Y + 2.0),
                            color=S.COL["RULE_STRONG"], lw=S.STROKE["TICK"])
                    if j == 0:
                        S.annot(axC, cxx(cx + xv * scale), cxy(C_TICK_Y + 1.5), "%+.2f" % xv,
                                color=S.COL["INK2"], ha="center", va="top")
        for i, p in enumerate(rows):
            y = C_ROWS[i]
            S.annot(axC, cxx(x0 - 2.0), cxy(y), SH[p] if p in SH else BSH[p],
                    color=S.COL["BBB"] if p in SH else S.COL["BTB"], weight="bold", ha="right",
                    va="center")
            for j, (key, lab) in enumerate(cmps):
                cx = x0 + gw * (j + 0.5)
                srow = table[(table["program_id"] == p) & (table[key_cmp] == key)]
                if not len(srow):
                    continue
                v = float(srow.iloc[0][val_col])
                if not np.isfinite(v):
                    S.not_evaluable_swatch(axC, cxx(cx - 3.0), cxy(y),
                                           w=6.0 / (_cx1 - _cx0), h=3.4 / (_cy1 - _cy0))
                    continue
                h = float(srow.iloc[0][iqr_col]) / 2.0
                axC.plot([cxx(cx + (v - h) * scale), cxx(cx + (v + h) * scale)], [cxy(y), cxy(y)],
                         color=S.COL["INK2"], lw=S.STROKE["DATA_MAIN"], solid_capstyle="butt",
                         zorder=S.Z["FILL"])
                if p in filled_progs:
                    S.filled_marker(axC, cxx(cx + v * scale), cxy(y), S.COL["SUPPORTED"], s=16)
                else:
                    S.open_marker(axC, cxx(cx + v * scale), cxy(y), s=16,
                                  ec=S.COL["NOT_SUPPORTED"])


    # ARB-11 item 2: one shared comparator tick treatment — the SAME tick values and the SAME local
    # scale in both halves, so the two sub-panels read as one object
    draw_half(PROG, LEFT_X0, LEFT_X1, CMPB, Bs, "comparison", "median_paired_difference",
              "iqr_paired_difference", 60.0, labels=(-0.10, 0.10),
              filled_progs=("BBB_CAP_FAM_010",))
    draw_half(BTB, RIGHT_X0, RIGHT_X1, CMPT, Ds, "comparison", "median_sample_level_difference",
              "iqr_sample_level_difference", 60.0, labels=(-0.10, 0.10))

    # ARB-10 N2: the axis quantity, in the legend's own words, one token per sub-panel
    S.annot(axC, cxx((LEFT_X0 + LEFT_X1) / 2.0), cxy(C_QTY_Y),
            "median paired difference in capillary rank score (IQR bar)", color=S.COL["INK2"],
            ha="center", va="center", size="AXIS")
    S.annot(axC, cxx((RIGHT_X0 + RIGHT_X1) / 2.0), cxy(C_QTY_Y),
            "median sample-level difference (IQR bar)", color=S.COL["INK2"], ha="center",
            va="center", size="AXIS")
    # ARB-04 item 2 / ARB-10 N3: the headline names the property, computed from the frozen matrix
    N_NOT_SUPPORTED = int((A3["capillary_specificity"].astype(str) != "SUPPORTED").sum())
    S.annot(axC, cxx((LEFT_X0 + LEFT_X1) / 2.0), cxy(C_HEAD_Y),
            "%d / %d capillary specificity not supported" % (N_NOT_SUPPORTED, len(PROG)),
            color=S.COL["INK"], weight="semibold", ha="center", va="center", size="AXIS")

    # ------------------------------------------------------------------ export + QC
    paths = S.finalize(fig, C.FIGS_MAIN, C.STEM_V3[FIG])
    rec = S.measure(fig)
    rec.update(
        figure=C.STEM_V3[FIG],
        panel_boxes_mm={k: list(v) for k, v in S.PAGE_BOXES[FIG].items() if k != "page_h"},
        visual_anchor=S.ANCHOR[FIG],
        core_message=("Program stability, structural replication and target-cell specificity are "
                      "distinct properties."),
        panels=["a BBB three-property glyph matrix", "b BTB generality warning",
                "c subject- and sample-level specificity (anchor; internal c-left / c-right split)"],
        design_source=["FIGSTYLE_V3.json (AMD-01/02/03)", "FIGSTYLE_V3.md",
                       "FIGURE_V3_ART_DIRECTION.md section 5 Fig 3"],
        paired_table_provenance=_prov,
        files={k: os.path.relpath(v, C.ROOT).replace("\\", "/") for k, v in paths.items()},
        source_tables=["FIG3_A_bbb_evidence_matrix.csv", "FIG3_B_bbb_subject_specificity.csv",
                       "FIG3_B_bbb_subject_paired.csv", "FIG3_C_btb_evidence_matrix.csv",
                       "FIG3_D_btb_sample_specificity.csv", "FIG3_D_btb_sample_paired.csv"],
    )
    os.makedirs(C.LOGS_V3, exist_ok=True)
    json.dump(rec, open(os.path.join(C.LOGS_V3, "figure_3_render.json"), "w", encoding="utf-8"),
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
