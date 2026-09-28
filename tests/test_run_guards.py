"""The guards that stop a Kaggle run before it spends hours on a wrong setup.

Run:  python3 tests/test_run_guards.py
      [THREE_CORPUS_UNIFIED=/path/to/unified.parquet]   # checks the real frames

Both guards are executed from the notebooks' own source, lifted by AST. The
preflight hard-codes /kaggle/input, so the lifted copy is pointed at a
temporary directory instead - the logic under test is unchanged.
"""
import ast, contextlib, io, os, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbcode import notebook_source

PASS = FAIL = SKIP = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else:    FAIL += 1; print(f"  FAIL  {name}  {detail}")


def skip(name, why):
    global SKIP
    SKIP += 1; print(f"  SKIP  {name}  ({why})")


def src_of(nb):
    return "".join(l for l in notebook_source(nb).splitlines(keepends=True)
                   if not l.startswith(("!", "%")))


def lift(nb, funcs, names):
    keep = [n for n in ast.parse(src_of(nb)).body
            if (isinstance(n, ast.FunctionDef) and n.name in funcs) or
               (isinstance(n, ast.Assign) and
                {t.id for t in n.targets if isinstance(t, ast.Name)} & names)]
    ns = {"np": np, "pd": pd, "os": os}
    exec(compile(ast.fix_missing_locations(ast.Module(body=keep, type_ignores=[])),
                 "<lifted>", "exec"), ns)
    return ns


HARNESSES = {
    "stage3-llm-harnes": {"CONFIG", "LABELSETS", "SEED", "COMPARABLE_FT_FOLD"},
    "stage3b-subtype-harness": {"CONFIG", "LABELSETS", "CATEGORIES_ALL", "TOP4",
                                "TOP6", "SHARED7", "SEED", "COMPARABLE_FT_FOLD"},
}

# =============================================================================
print("\n== 1. every evaluation frame names its fine-tuned comparator ==")
# Rows of a frame missing from COMPARABLE_FT_FOLD are written as "unmapped",
# and verify_stage3 fails the whole run over one such row - at the END.
COMMITTED = {  # labels the committed stores carry; they must never change
    "stage3-llm-harnes": {("security", "secreq"): "promise_to_secreq",
                          ("security", "promise"): "secreq_to_promise",
                          ("fr_nfr", "promise"): "LOPO_pooled"},
    "stage3b-subtype-harness": {("subtype_top4", "promise"): "indomain_subtype_top4_pooled",
                                ("subtype_top6", "promise"): "indomain_subtype_top6_pooled",
                                ("subtype_all", "promise"): "indomain_subtype_all_pooled"},
}
for nb, names in HARNESSES.items():
    m = lift(nb, set(), {"COMPARABLE_FT_FOLD"})["COMPARABLE_FT_FOLD"]
    check(f"{nb}: the committed labels are unchanged",
          all(m.get(k) == v for k, v in COMMITTED[nb].items()))
    lines = src_of(nb).splitlines()
    gi = next((i for i, l in enumerate(lines) if l.startswith("_unmapped = ")), None)
    ci = next(i for i, l in enumerate(lines) if l.startswith("FRAMES, POOL = carve_pool"))
    check(f"{nb}: the guard exists and runs before any model is loaded",
          gi is not None and gi < ci)

uni_path = os.environ.get("THREE_CORPUS_UNIFIED")
if not uni_path or not Path(uni_path).exists():
    skip("frames of the real corpus", "set THREE_CORPUS_UNIFIED to a 3-corpus unified.parquet")
else:
    uni = pd.read_parquet(uni_path)
    for nb, names in HARNESSES.items():
        ns = lift(nb, {"build_frames", "stratified"}, names)
        with contextlib.redirect_stdout(io.StringIO()):
            F = {k: v for k, v in ns["build_frames"](uni).items() if len(v) > 0}
        m = ns["COMPARABLE_FT_FOLD"]
        missing = sorted(k for k in F if k not in m)
        check(f"{nb}: all {len(F)} frames are mapped", not missing, missing)
        guard = [n for n in ast.parse(src_of(nb)).body
                 if isinstance(n, (ast.Assign, ast.If)) and "_unmapped" in ast.unparse(n)]
        code = compile(ast.Module(body=guard, type_ignores=[]), "<guard>", "exec")
        try:
            exec(code, {"_raw": F, "COMPARABLE_FT_FOLD": dict(m)}); quiet = True
        except RuntimeError:
            quiet = False
        check(f"{nb}: the guard is silent on the real map", quiet)
        try:
            exec(code, {"_raw": F, "COMPARABLE_FT_FOLD":
                        {k: v for k, v in m.items() if k[1] != "gitreq"}}); fired = False
        except RuntimeError:
            fired = True
        check(f"{nb}: the guard fires when a GitReq label is missing", fired)

# =============================================================================
print("\n== 2. the preflight tells a partial Stage 2 store from a complete one ==")
REPAIRED = {"predictions_llm_repaired.parquet": 35049,
            "predictions_subtype_repaired.parquet": 16786}


def preflight(nb, root):
    src = src_of(nb)
    fn = [n for n in ast.parse(src).body
          if isinstance(n, ast.FunctionDef) and n.name == "_check_kaggle_inputs"][0]
    code = ast.unparse(fn).replace("/kaggle/input", root)
    ns = {}
    exec(compile(code, "<preflight>", "exec"), ns)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            ns["_check_kaggle_inputs"]()
        return "RUN", out.getvalue()
    except SystemExit:
        return "STOP", out.getvalue()


def attach(root, files):
    for j, (fname, n) in enumerate(files.items()):
        d = Path(root) / f"in{j}"; d.mkdir(parents=True, exist_ok=True)
        if fname.endswith(".csv"):
            pd.DataFrame({"x": range(n)}).to_csv(d / fname, index=False)
        else:
            pd.DataFrame({"x": np.zeros(n, dtype="int8")}).to_parquet(d / fname)


CASES = [
    ("stage2-finetuned-baselines", {"unified.parquet": 7712, "predictions_finetuned.parquet": 146329},
     "RUN",  "", "Stage 2 resumes from its own partial store"),
    ("stage2-finetuned-baselines", {"unified.parquet": 7712, "predictions_finetuned.parquet": 24280},
     "RUN",  "", "Stage 2 starts the GitReq run from the two-corpus store"),
    ("stage4-analysis", dict(REPAIRED, **{"unified.parquet": 7712, "predictions_finetuned.parquet": 146329}),
     "STOP", "PARTIAL Stage 2 store", "Stage 4 refuses a partial store"),
    ("stage4-analysis", dict(REPAIRED, **{"unified.parquet": 7712, "predictions_finetuned.parquet": 24280}),
     "STOP", "TWO-corpus store", "Stage 4 refuses the two-corpus store beside the GitReq corpus"),
    ("stage4-analysis", dict(REPAIRED, **{"unified.parquet": 7712, "predictions_finetuned.parquet": 208336}),
     "RUN",  "", "Stage 4 accepts the complete GitReq store"),
    ("stage4-analysis", dict(REPAIRED, **{"unified.parquet": 1412, "predictions_finetuned.parquet": 24280}),
     "RUN",  "", "the two-corpus replay still runs"),
    ("stage5-cost", dict(REPAIRED, **{"predictions_finetuned.parquet": 146329, "tab9_evaluability.csv": 5}),
     "STOP", "PARTIAL Stage 2 store", "Stage 5 refuses a partial store"),
    ("stage5-cost", dict(REPAIRED, **{"predictions_finetuned.parquet": 208336, "tab9_evaluability.csv": 5}),
     "RUN",  "", "Stage 5 accepts the complete GitReq store"),
    ("stage3b-repair", {"predictions_finetuned.parquet": 146329},
     "RUN",  "", "repair does not consume the encoder store, so a partial one is only reported"),
]
for nb, files, want, reason, label in CASES:
    with tempfile.TemporaryDirectory() as root:
        attach(root, files)
        got, out = preflight(nb, root)
    check(f"{label}  ({nb})", got == want and (reason in out if reason else True),
          f"got {got}; output tail: {out[-300:]!r}")

for nb in ("stage2-finetuned-baselines", "stage3b-repair", "stage4-analysis", "stage5-cost"):
    s = src_of(nb)
    want = "RESUMES_FINETUNED = True" if nb.startswith("stage2") else "RESUMES_FINETUNED = False"
    check(f"{nb}: declares {want}", want in s)

print(f"\n{'=' * 60}\n  {PASS} passed, {FAIL} failed, {SKIP} skipped\n{'=' * 60}")
sys.exit(1 if FAIL else 0)
