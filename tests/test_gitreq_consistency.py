"""Cross-file numeric consistency: code, docstring and notes must agree.

Run:  GITREQ_ARCHIVE=/path/to/31669477.zip python3 tests/test_gitreq_consistency.py

The archive is the figshare item 10.6084/m9.figshare.31669477 (CC BY 4.0); it is
not committed, because the repository ships code and artefacts, not third-party
data. Every number asserted here is recomputed from that archive, so a silent
drift between the data, stage1_gitreq.py and the notes fails the run.
"""
import os, sys
_ARCHIVE_ENV = "GITREQ_ARCHIVE"
ARC = os.environ.get(_ARCHIVE_ENV)
if not ARC or not os.path.exists(ARC):
    sys.exit(f"set {_ARCHIVE_ENV} to the GitReq figshare archive (31669477.zip); "
             f"got {ARC!r}")
import io, logging, re, zipfile
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); logging.disable(logging.WARNING)
import stage1_gitreq as G

MOD = (ROOT / "stage1_gitreq.py").read_text()
NOTES = (ROOT / "paper/notes/2026-09-16-supervisor-references.md").read_text()
PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else:    FAIL += 1; print(f"  FAIL  {name}  {detail}")

man = {}
df = G.load_gitreq(ARC, man)
base = G.marker_only_baseline(df)
m = man["gitreq"]
vc = df.project.value_counts()
n_clean, n_dedup = len(df), df.text.nunique()
n_fr = int(df.label_fr_nfr.eq("FR").sum()); n_nfr = n_clean - n_fr
fr_mark = m["formal_marker_before_global_dedup"]["fr_with_marker"]
nfr_mark = m["formal_marker_before_global_dedup"]["nfr_with_marker"]
nfr_rate_pct = round(100 * nfr_mark / n_nfr, 1)

z = zipfile.ZipFile(ROOT / "results stage1_data_pipeline.zip")
uni = pd.read_csv(io.BytesIO(z.read("data_processed/unified.csv")))
p = uni[uni.source_dataset == "promise"]
SHARED7 = G.SUBTYPE_SHARED7
support7 = int(p.label_nfr_subtype.isin(SHARED7).sum())
prom_prev = round(100 * p.label_security.eq("security").mean(), 1)
sec = uni[uni.source_dataset == "secreq"]
sec_prev = round(100 * sec.label_security.eq("security").mean(), 1)

print("\n== computed ==")
print(f"  published {m['raw_rows']} -> clean {n_clean} -> dedup {n_dedup}")
print(f"  security {int(df.label_security.eq('security').sum())} "
      f"({100*df.label_security.eq('security').mean():.1f}%)")
print(f"  marker FR {fr_mark}/{n_fr}, NFR {nfr_mark}/{n_nfr} ({nfr_rate_pct}%)")
print(f"  marker-only macro-F1 {base['macro_f1']} acc {base['accuracy']}")
print(f"  repos {len(vc)}, >=5 items {int((vc>=5).sum())}, largest {int(vc.iloc[0])}")
print(f"  PROMISE_exp shared-7 support {support7}; prevalence {prom_prev}% / SecReq {sec_prev}%")

print("\n== the module's own docstring ==")
for label, text, doc in [
    ("6,302 published", "6,302", MOD), ("6,301 cleaned", "6,301", MOD),
    ("531 of 531", "531 of 531", MOD), ("1,030 of 5,770", "1,030 of 5,770", MOD),
    ("17.9 %", "17.9 %", MOD), ("macro-F1 0.7048", "0.7048", MOD),
    ("accuracy 0.8365", "0.8365", MOD), ("4,079 repositories", "4,079 repositories", MOD),
    ("147 hold five or more", "147\n    hold five or more", MOD),
]:
    check(f"module states {label}", text in doc)
check("module states the values it computes: raw", str(m["raw_rows"]) == "6302")
check("module docstring 0.7048 == computed", base["macro_f1"] == 0.7048, base)
check("module docstring 0.8365 == computed", base["accuracy"] == 0.8365, base)
check("module 531/531 == computed", (fr_mark, n_fr) == (531, 531))
check("module 1,030/5,770 == computed", (nfr_mark, n_nfr) == (1030, 5770))
check("module 17.9% == computed", nfr_rate_pct == 17.9, nfr_rate_pct)
check("module 4,079 repos == computed", len(vc) == 4079)
check("module 147 == computed", int((vc >= 5).sum()) == 147)
check("module 6,301 == computed", n_clean == 6301)

print("\n== the notes ==")
for label, text in [
    ("6,301 after #NAME?", "**6,301**"), ("6,300 after dedup", "**6,300**"),
    ("531 of 531", "**531 of 531**"), ("1,030 of 5,770", "**1,030 of 5,770**"),
    ("17.9 %", "17.9 %"), ("macro-F1 0.7048", "0.7048"), ("accuracy 0.8365", "0.8365"),
    ("4,079 repositories", "4,079 repositories"), ("147 with five or more", "147 with five or more"),
    ("298 NFRs", "298 NFRs"), ("26.1 %", "26.1 %"),
    ("one string in common", "exactly one text string is common"),
]:
    check(f"notes state {label}", text in NOTES)
check("notes 6,300 == computed dedup", n_dedup == 6300, n_dedup)
check("notes 298 == computed support", support7 == 298, support7)
check("notes 12.9%/39.9% == artefact", (prom_prev, sec_prev) == (12.9, 39.9), (prom_prev, sec_prev))

print("\n== no stale numbers survive anywhere ==")
for stale, where in [("0.720 ", "module"), ("0.850 ", "module"), ("16.4 %", "module"),
                     ("946 of", "module")]:
    check(f"module no longer says {stale.strip()}", stale not in MOD)
for stale in ["macro-F1 0.720 ", "accuracy 0.850)", "16.4 % of the 5,771", "299 NFRs", "operability"]:
    check(f"notes no longer say {stale!r}", stale not in NOTES)
check("notes and module agree on the vocabulary word 'operational'",
      ("operational" in NOTES) and ("operational" in MOD))

print(f"\n{'='*52}\n  {PASS} passed, {FAIL} failed\n{'='*52}")
sys.exit(1 if FAIL else 0)
