"""Shared configuration for the five figure renderers."""
from __future__ import annotations
import os
import bbbtb_common as _B
DATA_ROOT_ENV_VAR = _B.DATA_ROOT_ENV_VAR
DataRootNotConfigured = _B.DataRootNotConfigured
DataSourceMissing = _B.DataSourceMissing
require_files = _B.require_files
set_data_root = _B.set_data_root
RUN_ID = "figure_render"
STEM_V3 = {"Fig1": "figure_1_study_design", "Fig2": "figure_2_program_stability", "Fig3": "figure_3_cell_specificity", "Fig4": "figure_4_cross_barrier_test", "Fig5": "figure_5_feature_representation"}
BBB_CAP = ["BBB_CAP_FAM_%03d" % i for i in (1, 3, 4, 7, 9, 10)]
BBB_CAP_ALL = ["BBB_CAP_FAM_%03d" % i for i in range(1, 12)]
BTB_FAM = ["BTB_FAM_%03d" % i for i in range(1, 7)]
def ensure_output_dirs():
    root = _B.require_data_root("figure output")
    for rel in ("figures/main", "runs/figure_render/logs"):
        _B.ensure_dir(os.path.join(root, *rel.split("/")))
def __getattr__(name):
    if name in {"ROOT", "DATA_ROOT", "SRC", "FIGS_MAIN", "FIGS_EXT", "DELIV"}: return getattr(_B, name)
    if name == "LOGS_V3": return os.path.join(_B.require_data_root(), "runs", RUN_ID, "logs")
    raise AttributeError(name)
