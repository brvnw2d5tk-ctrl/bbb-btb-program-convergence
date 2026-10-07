"""Portable paths and input checks for the figure renderers."""
from __future__ import annotations
import os
import sys
DATA_ROOT_ENV_VAR = "BBB_BTB_DATA_ROOT"
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_ROOT_OVERRIDE = None
class DataRootNotConfigured(RuntimeError):
    pass
class DataSourceMissing(FileNotFoundError):
    pass
def resolve_data_root(explicit=None, argv=None):
    if explicit: return os.path.abspath(os.path.expanduser(explicit))
    args = sys.argv if argv is None else argv
    for i, arg in enumerate(args):
        if arg == "--data-root" and i + 1 < len(args): return os.path.abspath(os.path.expanduser(args[i + 1]))
        if arg.startswith("--data-root="): return os.path.abspath(os.path.expanduser(arg.split("=", 1)[1]))
    env = os.environ.get(DATA_ROOT_ENV_VAR)
    if env: return os.path.abspath(os.path.expanduser(env))
    local = os.path.join(PACKAGE_ROOT, "data")
    return local if os.path.isdir(local) else None
def set_data_root(path):
    global _DATA_ROOT_OVERRIDE
    _DATA_ROOT_OVERRIDE = os.path.abspath(os.path.expanduser(path)) if path else None
def require_data_root(what="the requested operation"):
    root = _DATA_ROOT_OVERRIDE or resolve_data_root()
    if not root: raise DataRootNotConfigured(f"Data root is not configured for {what}. Set {DATA_ROOT_ENV_VAR} or pass --data-root DIR.")
    return root
def check_sources(required=()):
    root = _DATA_ROOT_OVERRIDE or resolve_data_root()
    missing = [p for p in required if not root or not os.path.isfile(os.path.join(root, p))]
    present = [p for p in required if root and os.path.isfile(os.path.join(root, p))]
    return {"package_root": PACKAGE_ROOT, "data_root": root, "data_root_source": _source(), "required": list(required), "present": present, "missing": missing}
def _source():
    if _DATA_ROOT_OVERRIDE: return "command_line"
    if os.environ.get(DATA_ROOT_ENV_VAR): return "environment"
    if os.path.isdir(os.path.join(PACKAGE_ROOT, "data")): return "local_data_directory"
    return None
def require_files(rels, what="the requested operation"):
    root = require_data_root(what)
    missing = [p for p in rels if not os.path.isfile(os.path.join(root, p))]
    if missing: raise DataSourceMissing(f"Missing {len(missing)} required input file(s) for {what} under {root}: " + ", ".join(missing))
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path
def __getattr__(name):
    root = _DATA_ROOT_OVERRIDE or resolve_data_root()
    if name in {"DATA_ROOT", "ROOT"}: return root
    if name == "SRC": return os.path.join(require_data_root(), "figure_source_data")
    if name == "FIGS_MAIN": return os.path.join(require_data_root(), "figures", "main")
    if name == "FIGS_EXT": return os.path.join(require_data_root(), "figures", "extended")
    if name == "DELIV": return os.path.join(require_data_root(), "deliverables")
    raise AttributeError(name)
