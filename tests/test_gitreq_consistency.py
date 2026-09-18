"""Every number the hand-off files state must equal what the code computes, and
adding GitReq must leave the committed run untouched.

Run:  GITREQ_ARCHIVE=/path/to/31669477.zip \
      [STAGE1_LOCAL_MIRROR=/dir/with/PROMISE_exp.arff+ePurse.csv+CPN.csv+GPS.csv] \
      python3 tests/test_gitreq_consistency.py

Without STAGE1_LOCAL_MIRROR (or network access to the two original sources) the
end-to-end section is skipped and says so; everything else still runs.
"""
import io, json, logging, os, subprocess, sys, tempfile, zipfile
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbcode import load_notebook_module, notebook_source, ROOT

ARC = os.environ.get("GITREQ_ARCHIVE")
if not ARC or not Path(ARC).exists():
    sys.exit(f"set GITREQ_ARCHIVE to the GitReq figshare archive; got {ARC!r}")

logging.disable(logging.WARNING)
S1 = load_notebook_module("stage1-data-pipeline")
NB = notebook_source("stage1-data-pipeline")
NOTES = (ROOT / "paper/notes/2026-09-16-supervisor-references.md").read_text()
PASS = FAIL = SKIP = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else:    FAIL += 1; print(f"  FAIL  {name}  {detail}")


cfg = dict(S1.CONFIG); cfg["gitreq_path"] = ARC; cfg["lowercase"] = False
man = {}
df = S1.load_gitreq(cfg, man)

fr = df.label_fr_nfr.eq("FR")
marker = df.text.str.contains(S1.GITREQ_FORMAL_MARKER)
n_fr, n_nfr = int(fr.sum()), int((~fr).sum())
fr_mark, nfr_mark = int((fr & marker).sum()), int((~fr & marker).sum())
nfr_pct = round(100 * nfr_mark / n_nfr, 1)
sec_pct = round(100 * df.label_security.eq("security").mean(), 1)
vc = df.project.value_counts()
n_dedup = df.text.nunique()

# marker-only baseline, recomputed
tp, fp = fr_mark, nfr_mark
fn, tn = n_fr - tp, n_nfr - fp
def f1(a, b, c):
    p = a / (a + b) if a + b else 0.0
    r = a / (a + c) if a + c else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0
macro = round((f1(tp, fp, fn) + f1(tn, fn, fp)) / 2, 4)

print("\n== computed from the archive ==")
print(f"  {man['gitreq']['raw_rows']} published -> {len(df)} cleaned -> {n_dedup} after internal dedup")
print(f"  security {int(df.label_security.eq('security').sum())} ({sec_pct}%)")
print(f"  marker FR {fr_mark}/{n_fr}, NFR {nfr_mark}/{n_nfr} ({nfr_pct}%), marker-only macro-F1 {macro}")
print(f"  repositories {len(vc)}, >=5 items {int((vc >= 5).sum())}, largest {int(vc.iloc[0])}")

print("\n== the notebook's own comments ==")
for label, text in [("6,302 published", "6,302 requirements"), ("531 FR", "531 FR items"),
                    ("17.9 % quality", "17.9% of the quality"), ("macro-F1 0.7048", "0.7048"),
                    ("26.1 % security", "26.1%"), ("4,079 repositories", "4,079 source repositories"),
                    ("147 hold five or more", "147 hold five or more"),
                    ("6,300 rows", "6,300 rows"), ("the 9,926 look-alike", "9,926")]:
    check(f"notebook states {label}", text in NB)
check("notebook 531/531 == computed", (fr_mark, n_fr) == (531, 531), (fr_mark, n_fr))
check("notebook 17.9% == computed", nfr_pct == 17.9, nfr_pct)
check("notebook 0.7048 == computed", macro == 0.7048, macro)
check("notebook 26.1% == computed", sec_pct == 26.1, sec_pct)
check("notebook 4,079 == computed", len(vc) == 4079, len(vc))
check("notebook 147 == computed", int((vc >= 5).sum()) == 147)
check("notebook 6,300 == computed", n_dedup == 6300, n_dedup)
check("notebook 6,302 == computed", man["gitreq"]["raw_rows"] == 6302)

print("\n== the notes agree with the notebook ==")
for label, text in [("6,301 cleaned", "**6,301**"), ("6,300 deduped", "**6,300**"),
                    ("531 of 531", "**531 of 531**"), ("1,030 of 5,770", "**1,030 of 5,770**"),
                    ("17.9 %", "17.9 %"), ("0.7048", "0.7048"), ("0.8365", "0.8365"),
                    ("26.1 %", "26.1 %"), ("298 NFRs", "298 NFRs"),
                    ("4,079 repositories", "4,079 repositories")]:
    check(f"notes state {label}", text in NOTES)
check("notes 1,030/5,770 == computed", (nfr_mark, n_nfr) == (1030, 5770), (nfr_mark, n_nfr))
check("notes and notebook use the same word for the class", "operational" in NB and "operational" in NOTES)
check("no stale marker numbers survive", "16.4" not in NB and "16.4 % of the 5,771" not in NOTES)

z = zipfile.ZipFile(ROOT / "results stage1_data_pipeline.zip")
old_u = pd.read_csv(io.BytesIO(z.read("data_processed/unified.csv")))
old_s = json.loads(z.read("data_processed/splits.json"))
p = old_u[old_u.source_dataset == "promise"]
support7 = int(p.label_nfr_subtype.isin(S1.SUBTYPE_SHARED7).sum())
check("notes' 298 == the committed artefact", support7 == 298, support7)
check("notes' 12.9 % == the committed artefact",
      round(100 * p.label_security.eq("security").mean(), 1) == 12.9)

print("\n== end to end: the committed run must survive the third corpus ==")
mirror = os.environ.get("STAGE1_LOCAL_MIRROR")
if not mirror or not Path(mirror).is_dir():
    SKIP += 1
    print("  SKIP  no STAGE1_LOCAL_MIRROR; set it to a directory holding "
          "PROMISE_exp.arff, ePurse.csv, CPN.csv, GPS.csv to run this section")
else:
    tmp = Path(tempfile.mkdtemp())
    (tmp / "frozen.json").write_bytes(z.read("data_processed/splits.json"))
    script = tmp / "stage1.py"; script.write_text(NB)
    env = dict(os.environ, STAGE1_LOCAL_MIRROR=mirror, STAGE1_OUT_DIR=str(tmp / "out"),
               STAGE1_GITREQ=ARC, STAGE1_FREEZE_SPLITS=str(tmp / "frozen.json"))
    r = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True)
    check("Stage 1 runs to completion", r.returncode == 0, r.stderr[-400:])
    if r.returncode == 0:
        new_u = pd.read_csv(tmp / "out/unified.csv")
        new_s = json.load(open(tmp / "out/splits.json"))
        a = old_u.set_index("id")["text"].sort_index()
        b = new_u[new_u.source_dataset.isin(["promise", "secreq"])].set_index("id")["text"].sort_index()
        check("every committed id still maps to the same sentence", a.equals(b))
        oldf = {e["fold"]: (tuple(e["train_ids"]), tuple(e["test_ids"]))
                for v in old_s.values() for e in v}
        newf = {e["fold"]: (tuple(e["train_ids"]), tuple(e["test_ids"]))
                for v in new_s.values() for e in v}
        check(f"all {len(oldf)} committed folds are present",
              not (set(oldf) - set(newf)), sorted(set(oldf) - set(newf))[:3])
        check("not one of them changed contents",
              not [f for f in oldf if f in newf and oldf[f] != newf[f]])
        check("new folds were added", len(set(newf) - set(oldf)) > 0,
              len(set(newf) - set(oldf)))
        check("no cross-corpus duplicate text (no leakage)",
              "0 appear in BOTH corpora" in r.stdout + r.stderr)
        check("coverage reaches 15 of 18 cells", "15 of 18 cells covered" in r.stdout)
        check("the marker sidecar is written", (tmp / "out/gitreq_marker_flags.csv").exists())
        man2 = json.load(open(tmp / "out/stage1_manifest.json"))
        check("the manifest records the freeze",
              len(man2["frozen_splits"]["folds_frozen"]) == len(oldf),
              len(man2["frozen_splits"]["folds_frozen"]))

print(f"\n{'=' * 52}\n  {PASS} passed, {FAIL} failed, {SKIP} skipped\n{'=' * 52}")
sys.exit(1 if FAIL else 0)
