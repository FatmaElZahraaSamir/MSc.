"""Stages 2-5 after GitReq: the new paths work, and the old ones do not move.

Run:  python3 tests/test_downstream_gitreq.py
      [THREE_CORPUS_UNIFIED=/path/to/unified.parquet]   # exercises the frames
      [RUN_STAGE4_REGRESSION=1]                         # replays Stage 4 (slow)

Nothing here needs a GPU. The frame builders are lifted out of each harness by
AST, verbatim, so the test runs the notebook's own code rather than a copy.
"""
import ast, json, os, sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbcode import notebook_source, ROOT

PASS = FAIL = SKIP = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else:    FAIL += 1; print(f"  FAIL  {name}  {detail}")


def skip(name, why):
    global SKIP
    SKIP += 1; print(f"  SKIP  {name}  ({why})")


def lift(nbname, funcs, names):
    """Execute only the named top-level defs and assignments of a notebook."""
    src = "".join(l for l in notebook_source(nbname).splitlines(keepends=True)
                  if not l.startswith(("!", "%")))
    keep = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name in funcs:
            keep.append(node)
        elif isinstance(node, ast.Assign):
            if {t.id for t in node.targets if isinstance(t, ast.Name)} & names:
                keep.append(node)
    ns = {"np": np, "pd": pd, "os": os}
    exec(compile(ast.fix_missing_locations(ast.Module(body=keep, type_ignores=[])),
                 "<lifted>", "exec"), ns)
    return ns


print("\n== 1. every notebook still parses ==")
for nb in ["stage1-data-pipeline", "stage2-finetuned-baselines", "stage3-llm-harnes",
           "stage3b-repair", "stage3b-subtype-harness", "stage4-analysis", "stage5-cost"]:
    src = "\n".join(l for l in notebook_source(nb).splitlines()
                    if not l.startswith(("!", "%")))
    try:
        ast.parse(src); check(f"{nb} parses", True)
    except SyntaxError as e:
        check(f"{nb} parses", False, f"line {e.lineno}: {e.msg}")

print("\n== 2. the preflight accepts both corpus shapes ==")
for nb in ["stage2-finetuned-baselines", "stage3b-repair", "stage4-analysis", "stage5-cost"]:
    s = notebook_source(nb)
    check(f"{nb}: unified.parquet 1,412 or 7,712", "{1412, 7712}" in s)
    check(f"{nb}: splits.json 14 or 22 families", "len(fams) in (14, 22)" in s)

print("\n== 3. Stage 2 gives the shared-7 variant the sub-type budget ==")
s2 = notebook_source("stage2-finetuned-baselines")
check("subtype_shared7 trains for 10 epochs like the other sub-type tasks",
      '"subtype_shared7": 10,' in s2)
check("families are still derived from splits.json, so GitReq's arrive on their own",
      '"families": None,' in s2)

print("\n== 4. Stage 3 / 3b frames ==")
uni_path = os.environ.get("THREE_CORPUS_UNIFIED")
if not uni_path or not Path(uni_path).exists():
    skip("frame construction", "set THREE_CORPUS_UNIFIED to a 3-corpus unified.parquet")
else:
    uni = pd.read_parquet(uni_path)
    check("the fixture really holds three corpora",
          set(uni.source_dataset) == {"promise", "secreq", "gitreq"}, set(uni.source_dataset))

    n3 = lift("stage3-llm-harnes", {"build_frames", "stratified"},
              {"CONFIG", "LABELSETS", "SEED"})
    F3 = n3["build_frames"](uni)
    check("Stage 3 gives GitReq its own FR/NFR cell", ("fr_nfr", "gitreq") in F3)
    check("Stage 3 gives GitReq its own security cell", ("security", "gitreq") in F3)
    check("Stage 3 keeps the two original corpora",
          {("fr_nfr", "promise"), ("security", "promise"), ("security", "secreq")} <= set(F3))
    cap3 = n3["CONFIG"]["full_set_cap"]
    check("the full-set cap is above every pre-existing frame, so none is touched",
          all(len(v) <= cap3 for k, v in F3.items() if k[1] != "gitreq"),
          {k: len(v) for k, v in F3.items() if k[1] != "gitreq"})
    check("and it does bound the GitReq frames",
          len(n3["stratified"](F3[("security", "gitreq")], cap3)) == cap3)

    n3b = lift("stage3b-subtype-harness", {"build_frames", "stratified"},
               {"CONFIG", "LABELSETS", "CATEGORIES_ALL", "TOP4", "TOP6", "SHARED7", "SEED"})
    F3b = n3b["build_frames"](uni)
    check("every sub-type frame is filed under the corpus it came from",
          all(k[1] in {"promise", "gitreq"} for k in F3b) and
          {k[1] for k in F3b} == {"promise", "gitreq"}, sorted({k[1] for k in F3b}))
    check("no GitReq row is filed as PROMISE",
          len(F3b[("subtype_shared7", "promise")]) == 298,
          len(F3b.get(("subtype_shared7", "promise"), [])))
    check("shared-7 exists for both corpora",
          {("subtype_shared7", "promise"), ("subtype_shared7", "gitreq")} <= set(F3b))
    check("GitReq is excluded from all/top6/top4, which it cannot label",
          not any(k[1] == "gitreq" and k[0] != "subtype_shared7" for k in F3b),
          sorted(k for k in F3b if k[1] == "gitreq"))
    cap3b = n3b["CONFIG"]["full_set_cap"]
    check("the 3b cap leaves every PROMISE frame untouched",
          all(len(v) <= cap3b for k, v in F3b.items() if k[1] != "gitreq"),
          {k: len(v) for k, v in F3b.items() if k[1] != "gitreq"})

print("\n== 5. Stage 4 keeps two transfers into one corpus apart ==")
s4 = notebook_source("stage4-analysis")
check("transfer_source is part of the cell key", '"transfer_source"]' in s4 and 'head["transfer_source"]' in s4)
check("subtype_shared7 has a label set, so its folds are not dropped",
      '"subtype_shared7": SHARED7' in s4)
store = ROOT / "results stage2_finetuned_baselines.zip"
if not store.exists():
    skip("separation on real rows", "stage 2 store not present")
else:
    import zipfile, io
    df = pd.read_parquet(io.BytesIO(zipfile.ZipFile(store).read("predictions_finetuned.parquet")))
    xd = df[(df.eval_regime == "cross_dataset") & (df.fold == "secreq_to_promise")].copy()
    fake = xd.copy(); fake["fold"] = "gitreq_to_promise"
    head = pd.concat([xd, fake], ignore_index=True)
    head["transfer_source"] = np.where(
        head["eval_regime"].astype(str).eq("cross_dataset"),
        head["fold"].astype(str).str.split("_to_").str[0], "")
    K = ["model_tag", "task", "dataset", "eval_regime"]
    old_n = head.groupby(K).size().unique()
    new_n = head.groupby(K + ["transfer_source"]).size().unique()
    check("without the key the cell would double-count",
          set(old_n) == {2 * len(xd) // len(head.groupby(K))} or old_n[0] == 2 * new_n[0],
          (old_n, new_n))
    check("with it each transfer keeps its own n", set(new_n) == {len(xd) // len(xd.groupby(K))},
          new_n)
    real = df.copy()
    real["transfer_source"] = np.where(
        real["eval_regime"].astype(str).eq("cross_dataset"),
        real["fold"].astype(str).str.split("_to_").str[0], "")
    check("and it is inert on the committed two-corpus store",
          len(real.groupby(K)) == len(real.groupby(K + ["transfer_source"])))

print("\n== 6. the paper scripts refuse to guess between two transfers ==")
mt = (ROOT / "paper/scripts/make_tables.py").read_text()
check("get() takes a source argument", "def get(model, task, ds, regime, source=None)" in mt)
check("an ambiguous lookup raises instead of taking the first row",
      "raise ValueError" in mt and "pass source=... to choose" in mt)
check("GitReq cells are added only when three-corpus artefacts are present",
      "if (ev.dataset == 'gitreq').any():" in mt)

print("\n== 7. the late stages carry the third corpus instead of dropping it ==")
rep = notebook_source("stage3b-repair")
check("3b-repair knows subtype_shared7 (a KeyError on its first row otherwise)",
      '"subtype_shared7": SHARED7}' in rep)
s5 = notebook_source("stage5-cost")
check("Stage 5 scores shared-7 over its declared label set, not over y_true",
      '"subtype_shared7": SHARED7,' in s5)
check("Stage 5's break-even figure picks the regime from the pinned encoder",
      "mine = sub[sub.encoder == enc]" in s5)
s4 = notebook_source("stage4-analysis")
check("tab2 names the SOURCE of each cross-dataset column once GitReq is present",
      '" from " + d.transfer_source' in s4)
check("tab2 appends, never drops, a column outside the canonical order",
      "piv = piv[order + extra]" in s4)
check("tab3 reports one gap per transfer source, not the max of two",
      'tra_all.groupby("transfer_source")' in s4)
check("tab4 pairs the encoder by (model, regime, source)",
      "for ftm, reg, src_name in fts:" in s4)
check("tab5 compares sub-types per corpus, not PROMISE and GitReq pooled",
      "for task, ds in [(t, d) for t in SUBTYPE_TASKS" in s4)
s1 = notebook_source("stage1-data-pipeline")
check("Stage 1 searches only /kaggle/input for GitReq", 'root = KAGGLE_INPUT' in s1
      and 'Path(".")' not in s1.split("def _gitreq_locate")[1].split("def ")[0])
check("Stage 1 discovers an attached splits.json - no environment variable needed",
      'KAGGLE_INPUT.glob("**/splits.json")' in s1)

print("\n== 8. no session is lost to Kaggle's 12-hour limit ==")
s2 = notebook_source("stage2-finetuned-baselines")
check("Stage 2 stops cleanly at 10.5 h with the store flushed",
      '"session_budget_hours": 10.5,' in s2 and "SESSION BUDGET of %.1f h reached" in s2)
check("Stage 2's summary scores shared-7 over its declared label set",
      '"subtype_shared7": SHARED7,' in s2)
for nb in ["stage3-llm-harnes", "stage3b-subtype-harness"]:
    s = notebook_source(nb)
    check(f"{nb} checks its 10 h budget before each model and each API provider",
          '"session_budget_hours": 10.0,' in s and 'over_budget(f"{mid} (phase {phase})")' in s
          and 'over_budget(f"provider {provider}")' in s)

print(f"\n{'=' * 56}\n  {PASS} passed, {FAIL} failed, {SKIP} skipped\n{'=' * 56}")
sys.exit(1 if FAIL else 0)
