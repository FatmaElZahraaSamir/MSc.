"""Load a notebook's code as an importable module.

The pipeline's loaders live in the notebooks, because each notebook has to run
standalone on Kaggle. Tests therefore exercise the notebook itself rather than a
copy of it: a second copy of `load_gitreq` in a .py beside the notebook is
exactly the drift this project cannot afford.
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def notebook_source(name):
    """Concatenated source of every code cell in <repo>/<name>.ipynb."""
    nb = json.loads((ROOT / f"{name}.ipynb").read_text())
    return "\n".join("".join(c["source"]) for c in nb["cells"]
                     if c["cell_type"] == "code")


def load_notebook_module(name, modname=None):
    """Import that source as a module. The notebooks guard their driver with
    `if __name__ == "__main__"`, so importing defines the functions without
    running the stage."""
    modname = modname or name.replace("-", "_")
    src = notebook_source(name)
    tmp = Path(tempfile.mkdtemp()) / f"{modname}.py"
    tmp.write_text(src)
    spec = importlib.util.spec_from_file_location(modname, tmp)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod
