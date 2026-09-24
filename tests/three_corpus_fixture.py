"""Committed stores + plausible rows for EVERY new three-corpus fold and cell.

This is how the three-corpus pipeline was exercised end to end before any real
GitReq prediction existed. Run it from a working directory holding
  s3in/data_processed/unified.parquet   the 7,712-row Stage 1 corpus
  final_out/splits.json                  the frozen three-corpus splits
and it writes syn_in/ with the four inputs Stage 3b-repair and Stages 4-5 read.
Then point /kaggle/input at syn_in (repair), and at repair's output plus
syn_in (Stages 4 and 5). Verified this way: every new cross-dataset transfer
reaches tab9 with n equal to its target corpus - never doubled - and flows into
tab2, tab3, tab4 and tab5; Stage 5 completes.

Predictions are the gold label with 25% flipped to another class, so metrics
are finite and non-trivial. The point is not the numbers but the SHAPES: every
code path in Stages 3b-repair, 4 and 5 sees exactly the rows a real
three-corpus run would write.
"""
import ast, io, json, os, sys, zipfile
import numpy as np, pandas as pd
R = os.environ.get("MSC_REPO", str(__import__("pathlib").Path(__file__).resolve().parent.parent))
rng = np.random.default_rng(7)
uni = pd.read_parquet("s3in/data_processed/unified.parquet").set_index("id")
splits = json.load(open("final_out/splits.json"))

def lift(nb, funcs, names):
    d = json.load(open(f"{R}/{nb}.ipynb"))
    src = "\n".join(l for c in d["cells"] if c["cell_type"] == "code"
                    for l in "".join(c["source"]).splitlines() if not l.startswith(("!", "%")))
    keep = [n for n in ast.parse(src).body
            if (isinstance(n, ast.FunctionDef) and n.name in funcs)
            or (isinstance(n, ast.Assign) and {t.id for t in n.targets if isinstance(t, ast.Name)} & names)]
    ns = {"np": np, "pd": pd, "os": os}
    exec(compile(ast.fix_missing_locations(ast.Module(body=keep, type_ignores=[])), "<l>", "exec"), ns)
    return ns

def noisy(y, labels, p=0.25):
    out = []
    for v in y:
        if rng.random() < p and len(labels) > 1:
            out.append(rng.choice([l for l in labels if l != v]))
        else:
            out.append(v)
    return out

# ---------------------------------------------------------------- encoders
s2 = lift("stage2-finetuned-baselines", {"build_plan", "epochs_for"}, {"CONFIG", "CATEGORIES_ALL", "TOP4", "TOP6", "LABELSETS", "BINARY_LABELSETS"})
cfg = s2["CONFIG"]; cfg["quick_mode"] = False; cfg["families"] = list(splits)
ft = pd.read_parquet(io.BytesIO(zipfile.ZipFile(f"{R}/results stage2_finetuned_baselines.zip").read("predictions_finetuned.parquet")))
done = set(zip(ft.model_tag, ft.fold))
todo = [p for p in s2["build_plan"](splits, cfg) if (p[0], p[4]["fold"]) not in done]
tmpl = {t: g.iloc[0] for t, g in ft.groupby("model_tag")}
new = []
for tag, base, weighting, fam, e in todo:
    ids = list(map(str, e["test_ids"]))
    labelset = e.get("labelset") or s2["BINARY_LABELSETS"][e["task"]]
    y = uni.loc[ids, e["label_col"]].astype(str).tolist()
    ds = uni.loc[ids, "source_dataset"].unique()
    t = tmpl[tag]
    new.append(pd.DataFrame({**{c: t[c] for c in ft.columns},
        "task": e["task"], "dataset": ds[0] if len(ds) == 1 else "mixed",
        "eval_regime": e["eval_regime"], "family": fam, "fold": e["fold"],
        "id": ids, "y_true": y, "y_pred": noisy(y, labelset), "parse_ok": True,
        "train_epochs": s2["epochs_for"](fam, e["task"], cfg)}))
ft3 = pd.concat([ft] + new, ignore_index=True)
print(f"encoder store: {len(ft)} committed + {len(ft3) - len(ft)} synthetic = {len(ft3)}")

# ---------------------------------------------------------------- prompted
def extend(store, nb, cells, like_cell):
    n = lift(nb, {"build_frames", "stratified"}, {"CONFIG", "LABELSETS", "CATEGORIES_ALL", "TOP4", "TOP6", "SHARED7", "SEED"})
    F = n["build_frames"](uni.reset_index())
    core = {k: set(n["stratified"](F[k], n["CONFIG"]["core_eval_n"]).id) for k in cells}
    full = {k: set(n["stratified"](F[k], n["CONFIG"]["full_set_cap"]).id) for k in cells}
    rows = []
    like = store[(store.task == like_cell[0]) & (store.dataset == like_cell[1])]
    for (tag, split, pid, k), g in like.groupby(["model_tag", "split", "prompt_id", "shot_k"]):
        t = g.iloc[0]
        frac = g.id.nunique() / max(1, len(core.get(like_cell, [])) or 1)
        for cell in cells:
            task, ds = cell
            if split == "zero_shot" and pid == "base" and k == 0 and len(g) > 300:
                ids = sorted(core[cell] | full[cell])            # local model: core + capped full
            else:
                ids = sorted(core[cell])[: max(1, min(len(core[cell]), g.id.nunique()))]
            labels = n["LABELSETS"][task]
            col = "label_nfr_subtype" if task.startswith("subtype") else f"label_{task}"
            y = uni.loc[ids, col].astype(str).tolist()
            yp = noisy(y, labels)
            rows.append(pd.DataFrame({**{c: t[c] for c in store.columns},
                "task": task, "dataset": ds, "id": ids, "y_true": y, "y_pred": yp,
                "raw_output": yp, "parse_ok": True, "split": split, "prompt_id": pid, "shot_k": k}))
    out = pd.concat([store] + rows, ignore_index=True)
    print(f"{nb}: {len(store)} committed + {len(out) - len(store)} synthetic = {len(out)}")
    return out

llm = pd.read_parquet(io.BytesIO(zipfile.ZipFile(f"{R}/results Stage3 llm harness.zip").read("predictions_llm.parquet")))
sub = pd.read_parquet(io.BytesIO(zipfile.ZipFile(f"{R}/results Stage3b subtype harness.zip").read("predictions_subtype.parquet")))
llm3 = extend(llm, "stage3-llm-harnes", [("fr_nfr", "gitreq"), ("security", "gitreq")], ("security", "promise"))
sub3 = extend(sub, "stage3b-subtype-harness", [("subtype_shared7", "promise"), ("subtype_shared7", "gitreq")], ("subtype_all", "promise"))

os.makedirs("syn_in/data_processed", exist_ok=True)
uni.reset_index().to_parquet("syn_in/data_processed/unified.parquet", index=False)
json.dump(splits, open("syn_in/data_processed/splits.json", "w"))
ft3.to_parquet("syn_in/predictions_finetuned.parquet", index=False)
llm3.to_parquet("syn_in/predictions_llm.parquet", index=False)
sub3.to_parquet("syn_in/predictions_subtype.parquet", index=False)
print("written to syn_in/")
