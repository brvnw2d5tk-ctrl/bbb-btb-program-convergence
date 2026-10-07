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
from matplotlib.patches import Circle

import figure_style as S
import figure_common as C



import argparse

# Added so the released renderer (a) imports without executing a render, (b) answers
# --help, (c) fails gracefully when the data root is absent, and (d) supports --dry-run.
# The frozen render body inside main() is unchanged, statement for statement; see
FIG_NAME = 'Fig1'
REQUIRED_SOURCE_TABLES = (
    "FIG1_A_concept.csv",
    "FIG1_B_btb_discovery.csv",
    "FIG1_C_bbb_discovery.csv",
    "FIG1_D_freeze_flow.csv",
    "FIG1_E_evidence_ladder.csv",
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
    """Released entry point for Fig1.  Renders nothing unless the frozen inputs are present."""
    args = _cli(argv)
    if args.dry_run:
        print(json.dumps(_dry_run_report(args), indent=1, ensure_ascii=False))
        return 0
    try:
        C.require_files(_REQUIRED_RELS, what="the Fig1 render")
        C.ensure_output_dirs()
    except (C.DataRootNotConfigured, C.DataSourceMissing) as exc:
        sys.stderr.write("\n" + os.path.basename(__file__) + ": cannot render Fig1.\n")
        sys.stderr.write(str(exc) + "\n")
        return 2

    SD = C.SRC
    rd = lambda n: pd.read_csv(os.path.join(SD, n))

    FIG = "Fig1"
    PAGE_H_MM = S.page_h(FIG)
    W = S.FULL_W
    fig = plt.figure(figsize=(W, PAGE_H_MM * S.MM))


    def canvas(panel):
        x0, y0, x1, y1 = S.box_mm(FIG, panel)
        ax = fig.add_axes([x0 / S.FULL_W_MM, (PAGE_H_MM - y1) / PAGE_H_MM,
                           (x1 - x0) / S.FULL_W_MM, (y1 - y0) / PAGE_H_MM])
        S.hide_all(ax)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return ax


    # ------------------------------------------------------------------ frozen sources (unchanged)
    T1A = rd("FIG1_A_concept.csv")
    T1B = rd("FIG1_B_btb_discovery.csv").set_index("item")["value"].to_dict()
    T1C = rd("FIG1_C_bbb_discovery.csv").set_index("item")["value"].to_dict()
    T1D = rd("FIG1_D_freeze_flow.csv")
    T1E = rd("FIG1_E_evidence_ladder.csv")

    # ================================================================== PANEL A — conceptual biology
    axA = canvas("a")
    S.head(fig, axA, FIG, "a", "Two organs, one barrier function")
    AX0, AY0, AX1, AY1 = S.box_mm(FIG, "a")


    def axx(mm):
        return (mm - AX0) / (AX1 - AX0)


    def axy(mm):
        return 1.0 - (mm - AY0) / (AY1 - AY0)


    CIRC_D_MM = 22.0
    CIRC_CY = 27.0
    ROWS_A = {str(r.side): r for r in T1A.itertuples()}


    def organ_symbol(cx_mm, kind, col):
        """One 22 mm vector symbol.  Both organ sides share the two-circle construction so the pair is
    comparable, but each carries ONE structural cue that names its anatomy (ARB-05 item 3):
    the BTB side its dashed Sertoli-junction boundary, the BBB side a double-walled endothelium.
    The V2 amber pericyte arc is deleted: Fig1 carries no amber."""
        d = CIRC_D_MM / (AX1 - AX0)
        iax = axA.inset_axes([axx(cx_mm) - d / 2.0,
                              1.0 - (CIRC_CY + CIRC_D_MM / 2.0 - AY0) / (AY1 - AY0), d,
                              CIRC_D_MM / (AY1 - AY0)])
        iax.set_xlim(-1.15, 1.15)
        iax.set_ylim(-1.15, 1.15)
        iax.set_aspect("equal")
        S.hide_all(iax)
        if kind == "BTB":
            iax.add_patch(Circle((0, 0), 1.0, facecolor="none", edgecolor=col,
                                 lw=S.STROKE["AXIS_FRAME"], zorder=3))
            iax.add_patch(Circle((0, 0), 0.62, facecolor="none", edgecolor=S.COL["INK2"],
                                 lw=S.STROKE["DATA_MAIN"], ls=(0, (2.2, 1.5)), zorder=3))
            iax.add_patch(Circle((0, 0), 0.22, facecolor="none", edgecolor=col,
                                 lw=S.STROKE["AXIS_FRAME"], zorder=3))
        else:
            iax.add_patch(Circle((0, 0), 1.0, facecolor="none", edgecolor=col,
                                 lw=S.STROKE["AXIS_FRAME"], zorder=3))
            iax.add_patch(Circle((0, 0), 0.90, facecolor="none", edgecolor=col,
                                 lw=S.STROKE["AXIS_FRAME"], zorder=3))
            iax.add_patch(Circle((0, 0), 0.45, facecolor="none", edgecolor=S.COL["INK2"],
                                 lw=S.STROKE["DATA_MAIN"], zorder=3))


    organ_symbol(48.0, "BTB", S.COL["BTB"])
    organ_symbol(130.0, "BBB", S.COL["BBB"])
    S.annot(axA, axx(48.0), axy(44.5), str(ROWS_A["left"].barrier), color=S.COL["BTB"],
            ha="center", va="center")
    S.annot(axA, axx(130.0), axy(44.5), str(ROWS_A["right"].barrier), color=S.COL["BBB"],
            ha="center", va="center")
    # the one structural cue per side, named (ARB-05 item 3); two anatomical labels per figure side,
    # which keeps the schematic inside the brief's 2-4 label budget
    S.annot(axA, axx(33.0), axy(23.0), "Sertoli junction", color=S.COL["INK2"], ha="right",
            va="center")
    S.annot(axA, axx(145.0), axy(23.0), "Endothelium", color=S.COL["INK2"], ha="left", va="center")
    S.body(axA, axx(89.0), axy(27.0), "Analogous barrier function", color=S.COL["INK"], ha="center",
           va="center", size="PANEL_TITLE", weight="semibold")
    S.rule(axA, axx(74.0), axx(104.0), axy(30.0), color=S.COL["RULE"])
    # ARB-05 item 1: the brief-mandated premise question, restored at annotation size
    S.annot(axA, axx(89.0), axy(35.0), "Do analogous barriers share molecular programs?",
            color=S.COL["INK"], ha="center", va="center", size="AXIS")

    # ================================================================== PANEL B — discovery arms
    axB = canvas("b")
    S.head(fig, axB, FIG, "b", "Two independent discovery arms")
    BX0, BY0, BX1, BY1 = S.box_mm(FIG, "b")


    def bxx(mm):
        return (mm - BX0) / (BX1 - BX0)


    def bxy(mm):
        return 1.0 - (mm - BY0) / (BY1 - BY0)


    ARMS = [(44.0, S.COL["BTB"], format(int(T1B["global_cell_n"]), ","),
             "working Sertoli-like cells",
             "%s stable program families" % T1B["stable_program_families"], None,
             "%s \u00b7 %s" % (T1B["dataset"], T1B["lock"])),
            (134.0, S.COL["BBB"], format(int(T1C["capillary_cell_n"]), ","),
             "Capillary nuclei", "%s stable Capillary families" % T1C["stable_capillary_families"],
             "%s primary-eligible" % T1C["primary_eligible_capillary_families"],
             "%s \u00b7 %s" % (T1C["dataset"], T1C["lock"]))]
    # ARB-18 (addition): the two discovery datasets and their freeze locks are restored, one LEGEND
    # line per arm, read from the frozen tables (FIG1_B / FIG1_C `dataset` and `lock`) rather than
    # typed.  The locked legend's panel-b sentence already states all four identifiers, and this is
    # the only content added to Fig1.  The whole number block is re-spaced across the band so it
    # reads as a composed panel instead of two figures floating in a full-width band.
    for cx, col, big, unit, fam, elig, acc in ARMS:
        S.number(axB, bxx(cx), bxy(66.9), str(big), size="BIG_NUMBER", color=col)
        S.annot(axB, bxx(cx), bxy(70.4), unit, color=S.COL["INK2"], ha="center", va="center",
                size="AXIS")
        S.arrow(axB, bxx(cx), bxy(73.0), bxx(cx), bxy(75.8), color=S.COL["INK2"],
                lw=S.STROKE["CONNECTOR"], head=False)
        S.annot(axB, bxx(cx), bxy(79.0), fam, color=S.COL["INK"], ha="center", va="center",
                size="AXIS")
        if elig:
            S.annot(axB, bxx(cx), bxy(82.5), elig, color=S.COL["INK"], ha="center", va="center",
                    size="AXIS")
        S.annot(axB, bxx(cx), bxy(86.4), acc, color=S.COL["INK2"], ha="center", va="center")
    S.vrule(axB, (bxx(89.0)), bxy(88.8), bxy(62.8), color=S.COL["RULE"], lw=S.STROKE["RULE"])

    # ================================================================== PANEL C — freeze-first chain
    axC = canvas("c")
    S.head(fig, axC, FIG, "c", "Freeze-first design")
    CX0, CY0, CX1, CY1 = S.box_mm(FIG, "c")
    C_STAGES = [str(x) for x in T1D.sort_values("step").stage]
    C_SHORT = {"External structural replication": "External structural replication",
               "Cross-barrier convergence (prespecified)": "Cross-organ test (prespecified)",
               "Disease expression / human genetics": "Disease expression"}
    C_LINE_Y = 119.5
    C_STATION_X = [20.0, 52.0, 84.0, 116.0, 148.0]


    def cxx(mm):
        return (mm - CX0) / (CX1 - CX0)


    def cxy(mm):
        return 1.0 - (mm - CY0) / (CY1 - CY0)


    S.rule(axC, cxx(10.0), cxx(167.0), cxy(C_LINE_Y), color=S.COL["INK2"],
           lw=S.STROKE["DATA_MAIN"])
    # ARB-05 item 4: one small open chevron makes the one-way direction explicit, at baseline weight
    # and with no filled head
    axC.plot([cxx(167.5), cxx(171.0), cxx(167.5)],
             [cxy(C_LINE_Y - 2.2), cxy(C_LINE_Y), cxy(C_LINE_Y + 2.2)],
             color=S.COL["INK2"], lw=S.STROKE["SECONDARY"], solid_capstyle="butt",
             zorder=S.Z["RULE"])
    for x_mm, name in zip(C_STATION_X, C_STAGES[:5]):
        lab = C_SHORT.get(name, name)
        frozen = (name == "Freeze")
        # the anchor carries the figure's structural ink: one station node per station plus the
        # station names at the panel-heading token (the anchor must out-weigh the text tables, which
        # ARB-09's restored keys made heavier)
        S.filled_marker(axC, cxx(x_mm), cxy(C_LINE_Y), S.COL["INK"], s=64)
        S.annot(axC, cxx(x_mm), cxy(C_LINE_Y - 1.8), lab, color=S.COL["INK"], ha="center",
                va="bottom", size="PANEL_TITLE",
                weight="semibold" if frozen else "normal")
    # the stage gate: one 0.60 pt tick, no block and no background
    S.vrule(axC, cxx(48.0), cxy(C_LINE_Y + 5.0), cxy(C_LINE_Y - 5.0), color=S.COL["INK2"],
            lw=S.STROKE["DATA_MAIN"])
    S.annot(axC, cxx(48.0), cxy(C_LINE_Y - 6.5), "stage gate", color=S.COL["INK2"], ha="center",
            va="top", size="SUBSECTION")
    # downstream branches (step 6) after the chain, so the frozen step order is preserved
    S.vrule(axC, cxx(166.0), cxy(C_LINE_Y), cxy(C_LINE_Y + 9.5), color=S.COL["RULE"],
            lw=S.STROKE["RULE"])
    # ARB-12 item 2: the two downstream-branch labels move 1.5 mm down (9.0 -> 10.5 and
    # 12.6 -> 13.5) so the 4.0 mm run between the chain and this block becomes a legal 5.4 mm gap
    # while the two labels and the struck-through rule stay inside the 3 mm leading band.
    S.annot(axC, cxx(166.0), cxy(C_LINE_Y + 10.5), "Disease expression", color=S.COL["INK2"],
            ha="right", va="top", size="AXIS")
    S.annot(axC, cxx(166.0), cxy(C_LINE_Y + 13.5), "human genetics", color=S.COL["INK2"],
            ha="right", va="top", size="AXIS")
    # the prohibited direction: ONE dashed rule, ONE slash, ONE label
    S.struck_through(axC, cxx(60.0), cxx(144.0), cxy(137.0), slash_half=1.8 / (CX1 - CX0))
    S.annot(axC, cxx(173.0), cxy(137.0), "no backward information flow", color=S.COL["INK2"],
            ha="right", va="center", size="SUBSECTION")

    # ================================================================== PANEL D — evidence ladder
    axD = canvas("d")
    S.head(fig, axD, FIG, "d", "Evidence layers and their frozen status")
    DX0, DY0, DX1, DY1 = S.box_mm(FIG, "d")
    # ARB-12 item 2: the six-row pitch drops from 5.6 to 4.6 mm and the glyph key rises from
    # DY1-2.4 to DY1-5.5 mm, so all four 3.0-3.8 mm dead bands inside panel d close to 2.3-2.8 mm
    # and the panel keeps its 40 mm box and its ceiling.
    D_ROWS = [152.6 + 4.6 * i for i in range(6)]
    #: one short value string per row, retained verbatim from V2 (same digits, same formatting)
    CLAIM = {
        # ARB-13: the scope of the two stability counts is now on the plate.  Panel b's "11 stable
        # families" is the Capillary arm (FIG1_C); panel d's "14/14 BBB stable" is all fourteen BBB
        # series (11 Capillary + 3 Pericyte, FIG1_E).  Both numbers are frozen and unchanged; only
        # the compartment/scope words are added, so the two can no longer read as contradictory.
        "Within-organ stability": "5/6 BTB, 14/14 BBB stable",
        "External structural replication": "2/6 cosine, 1/6 Spearman",
        "Cell-type specificity": "1/6 capillary, 6/6 warning",
        "Cross-organ convergence": "6/36 evaluable, 0 convergent",
        "Disease expression": "not evaluable (P3 tiers)",
        "Human common-variant genetics": "no primary anchor (0/6, 0/42)",
    }


    def dxx(mm):
        return (mm - DX0) / (DX1 - DX0)


    def dxy(mm):
        return 1.0 - (mm - DY0) / (DY1 - DY0)


    for i, r in enumerate(T1E.itertuples()):
        y = D_ROWS[i]
        S.annot(axD, 0.0, dxy(y), str(r.layer), color=S.COL["INK"], ha="left", va="center")
        S.annot(axD, 0.300, dxy(y), CLAIM.get(str(r.layer), ""), color=S.COL["INK2"], va="center", )
        st = str(r.status)
        if st == "SUPPORTED":
            S.filled_marker(axD, 0.955, dxy(y), S.COL["SUPPORTED"], s=19)
        elif st == "PARTIAL":
            # ARB-08 P4: a genuine thick ring, larger than the open marker, so partial and
            # not-supported are distinguishable in greyscale
            S.partial_ring(axD, 0.955, dxy(y), color=S.COL["INK2"], s=40, lw=1.9)
        elif st == "NOT_EVALUABLE":
            S.not_evaluable_swatch(axD, 0.955 - 0.008, dxy(y), w=0.016, h=3.4 / (DY1 - DY0))
        else:
            S.open_marker(axD, 0.955, dxy(y), s=19, ec=S.COL["NOT_SUPPORTED"])
    # ARB-09 item 1: the one-line glyph key.  Without it the four encodings are undecodable, and it
    # is what makes the greyscale reading of ring vs open unambiguous.
    S.annot(axD, 0.0, dxy(DY1 - 7.6),
            "filled, supported   \u00b7   ring, partial   \u00b7   open, not supported   \u00b7   "
            "hatched, not evaluable", color=S.COL["INK2"], va="center", size="AXIS")

    # ------------------------------------------------------------------ export + QC
    paths = S.finalize(fig, C.FIGS_MAIN, C.STEM_V3[FIG])
    rec = S.measure(fig)
    rec.update(
        figure=C.STEM_V3[FIG],
        panel_boxes_mm={k: list(v) for k, v in S.PAGE_BOXES[FIG].items() if k != "page_h"},
        visual_anchor=S.ANCHOR[FIG],
        core_message=("A falsifiable cross-organ barrier hypothesis was tested using independently "
                      "learned and frozen expression programs with no backward information flow."),
        panels=["a conceptual biology", "b two independent discovery arms",
                "c freeze-first design (anchor)", "d evidence layers and frozen status"],
        amber_elements=0,
        design_source=["FIGSTYLE_V3.json (AMD-01/02/03)", "FIGSTYLE_V3.md",
                       "FIGURE_V3_ART_DIRECTION.md section 5 Fig 1"],
        files={k: os.path.relpath(v, C.ROOT).replace("\\", "/") for k, v in paths.items()},
        source_tables=["FIG1_A_concept.csv", "FIG1_B_btb_discovery.csv",
                       "FIG1_C_bbb_discovery.csv", "FIG1_D_freeze_flow.csv",
                       "FIG1_E_evidence_ladder.csv"],
    )
    os.makedirs(C.LOGS_V3, exist_ok=True)
    json.dump(rec, open(os.path.join(C.LOGS_V3, "figure_1_render.json"), "w", encoding="utf-8"),
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
