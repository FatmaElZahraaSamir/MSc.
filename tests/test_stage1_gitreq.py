"""Adversarial battery for the GitReq loader that lives in Stage 1.

Run:  GITREQ_ARCHIVE=/path/to/31669477.zip python3 tests/test_stage1_gitreq.py

The archive is figshare 10.6084/m9.figshare.31669477 (CC BY 4.0); it is not
committed, because this repository ships code and artefacts, not third-party
data. The tests import the NOTEBOOK, not a copy of it.
"""
import csv, io, logging, os, shutil, sys, tempfile, zipfile
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbcode import load_notebook_module

ARC = os.environ.get("GITREQ_ARCHIVE")
if not ARC or not Path(ARC).exists():
    sys.exit(f"set GITREQ_ARCHIVE to the GitReq figshare archive; got {ARC!r}")
ARC = Path(ARC)
# The 9,926-row look-alike, if available; synthesised otherwise.
LOOKALIKE = os.environ.get("GITREQ_LOOKALIKE")

logging.disable(logging.WARNING)
S1 = load_notebook_module("stage1-data-pipeline")
PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else:    FAIL += 1; print(f"  FAIL  {name}  {detail}")


def expect_raise(name, fn, must_contain=None):
    try:
        fn(); check(name, False, "no exception raised")
    except Exception as e:
        ok = must_contain is None or must_contain.lower() in str(e).lower()
        check(name, ok, f"message was: {str(e)[:160]}")


def cfg(path, lowercase=False):
    c = dict(S1.CONFIG)
    c["gitreq_path"] = str(path)
    c["lowercase"] = lowercase
    return c


def load(path, lowercase=False, manifest=None):
    return S1.load_gitreq(cfg(path, lowercase), {} if manifest is None else manifest)


def members():
    with zipfile.ZipFile(ARC) as z:
        return {m: z.read(S1._gitreq_resolve_zip_member(z, m))
                for m in S1.GITREQ_MEMBERS}


def unpin(*keys):
    saved = dict(S1.CONFIG["expected_sha256"])
    for k in keys:
        S1.CONFIG["expected_sha256"].pop(k, None)
    return saved


def repin(saved):
    S1.CONFIG["expected_sha256"] = saved


tmp = Path(tempfile.mkdtemp())
M = members()

print("\n== 1. happy path, pinned archive ==")
man = {}
df = load(ARC, manifest=man)
check("6301 rows", len(df) == 6301, len(df))
check("label_security uses Stage 1's string pair",
      set(df.label_security) == {"security", "non-security"}, set(df.label_security))
check("label_fr_nfr is FR/NFR", set(df.label_fr_nfr) == {"FR", "NFR"})
check("1646 security rows", int(df.label_security.eq("security").sum()) == 1646)
check("sub-type is NaN exactly for the 531 FR items",
      int(df.label_nfr_subtype.isna().sum()) == int(df.label_fr_nfr.eq("FR").sum()) == 531)
check("sub-types are the seven shared classes",
      sorted(df.label_nfr_subtype.dropna().unique()) == S1.SUBTYPE_SHARED7)
check("every sub-type is in Stage 1's own vocabulary",
      set(df.label_nfr_subtype.dropna()) <= set(S1.PROMISE_SUBTYPE_MAP.values()))
check("columns match the other loaders",
      list(df.columns) == ["text", "label_fr_nfr", "label_nfr_subtype",
                           "label_security", "project", "source_dataset"])
check("manifest records the composition",
      man["gitreq"]["raw_rows"] == 6302 and man["gitreq"]["projects"] == 4079, man["gitreq"]["projects"])

print("\n== 2. the 9,926-row look-alike is refused ==")
if LOOKALIKE and Path(LOOKALIKE).exists():
    imp = Path(LOOKALIKE).read_bytes()
else:
    rows = ["ID,RequirementText,class_label,url"]
    for i in range(9926):
        rows.append(f'{i},"synthetic {i}",{"performance" if i % 2 else "security"},'
                    f'https://github.com/o/r/issues/{i}')
    imp = "\n".join(rows).encode()
d = tmp / "lookalike"; d.mkdir()
for m in S1.GITREQ_MEMBERS: (d / m).write_bytes(imp)
sv = unpin(*S1.GITREQ_MEMBERS)
expect_raise("refused, naming the look-alike", lambda: load(d),
             "does not match the published corpus")
repin(sv)

print("\n== 3. UTF-8 BOM, both column orders ==")
for tag, reorder in [("original order", False), ("text column second", True)]:
    d = tmp / f"bom_{tag.split()[0]}"; d.mkdir()
    for m, blob in M.items():
        text = blob.decode("utf-8")
        if reorder:
            rws = list(csv.DictReader(io.StringIO(text)))
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=["class_label", "RequirementText", "url"],
                               extrasaction="ignore")
            w.writeheader(); w.writerows(rws); text = buf.getvalue()
        (d / m).write_bytes(b"\xef\xbb\xbf" + text.encode())
    sv = unpin(*S1.GITREQ_MEMBERS)
    try:
        check(f"BOM tolerated ({tag})", len(load(d)) == 6301)
    except Exception as e:
        check(f"BOM tolerated ({tag})", False, str(e)[:140])
    repin(sv)

print("\n== 4. lowercase=True still drops the '#NAME?' row ==")
low = load(ARC, lowercase=True)
check("same row count", len(low) == 6301, len(low))
check("no spreadsheet-error text survives",
      not low.text.str.upper().isin(S1._SPREADSHEET_ERRORS).any())
check("text is lower-cased", low.text.str.islower().mean() > 0.9)

print("\n== 5. a renamed text column fails loudly ==")
d = tmp / "renamed"; d.mkdir()
for m, blob in M.items():
    head, _, rest = blob.decode("utf-8").partition("\n")
    (d / m).write_text(head.replace("RequirementText", "Requirement_Text") + "\n" + rest)
sv = unpin(*S1.GITREQ_MEMBERS)
expect_raise("missing column raises", lambda: load(d), "missing required column")
repin(sv)

print("\n== 6. archive member ambiguity ==")
def build(path, extra):
    with zipfile.ZipFile(path, "w") as z:
        for n, b in M.items(): z.writestr(n, b)
        for n, b in extra: z.writestr(n, b)
z1 = tmp / "shadow.zip"; build(z1, [("__MACOSX/GitReq_FR.csv", b"junk")])
check("__MACOSX shadow ignored", len(load(z1)) == 6301)
z2 = tmp / "dup.zip"; build(z2, [("v1/GitReq_FR.csv", M["GitReq_FR.csv"])])
expect_raise("duplicate member refused", lambda: load(z2), "files named")

print("\n== 7. an extracted directory behaves like the archive ==")
d = tmp / "extracted"; (d / "GitReq").mkdir(parents=True)
for m, b in M.items(): (d / "GitReq" / m).write_bytes(b)
check("nested extraction loads", len(load(d)) == 6301)
d2 = tmp / "split"; (d2 / "a").mkdir(parents=True); (d2 / "b").mkdir(parents=True)
(d2 / "a" / "GitReq_FR.csv").write_bytes(M["GitReq_FR.csv"])
(d2 / "b" / "GitReq_NFR.csv").write_bytes(M["GitReq_NFR.csv"])
expect_raise("members from different directories refused",
             lambda: load(d2), "different directories")

print("\n== 8. a ragged row is diagnosed, not a TypeError ==")
d = tmp / "ragged"; d.mkdir()
for m, b in M.items(): (d / m).write_bytes(b + b'\n9999,"orphan, no label"')
sv = unpin(*S1.GITREQ_MEMBERS)
try:
    load(d); check("ragged row raises", False, "no exception")
except TypeError as e:
    check("ragged row raises", False, f"TypeError leaked: {e}")
except RuntimeError as e:
    check("ragged row raises RuntimeError", "<missing>" in str(e) or "does not match" in str(e),
          str(e)[:160])
repin(sv)

print("\n== 9. a tampered file fails the pin ==")
d = tmp / "tampered"; d.mkdir()
(d / "GitReq_FR.csv").write_bytes(M["GitReq_FR.csv"] + b"\n")
(d / "GitReq_NFR.csv").write_bytes(M["GitReq_NFR.csv"])
expect_raise("hash mismatch refused", lambda: load(d), "changed upstream")

print("\n== 10. missing GitReq is an instruction, not a crash ==")
expect_raise("absent path explained", lambda: load(tmp / "nope"), "does not exist")

print("\n== 11. it composes with the other loaders ==")
# A PROMISE stand-in carrying ALL eleven sub-types, so the label-set coverage
# rule is exercised for the reason it exists rather than by accident.
sub_classes = sorted(S1.PROMISE_SUBTYPE_MAP.values())
rows = []
for i, c in enumerate(sub_classes * 3):
    rows.append({"text": f"promise nfr {c} {i}", "label_fr_nfr": "NFR",
                 "label_nfr_subtype": c,
                 "label_security": "security" if c == "security" else "non-security",
                 "project": f"p{i % 4}", "source_dataset": "promise"})
for i in range(12):
    rows.append({"text": f"promise fr {i}", "label_fr_nfr": "FR",
                 "label_nfr_subtype": np.nan, "label_security": "non-security",
                 "project": f"p{i % 4}", "source_dataset": "promise"})
promise = pd.DataFrame(rows)
secreq = pd.DataFrame([{"text": f"secreq {i}", "label_fr_nfr": np.nan,
                        "label_nfr_subtype": np.nan,
                        "label_security": "security" if i % 2 else "non-security",
                        "project": ["CEPS", "CPN", "GPS"][i % 3],
                        "source_dataset": "secreq"} for i in range(30)])

uni = S1.build_unified([("promise", promise), ("secreq", secreq), ("gitreq", df)], {})
check("build_unified accepts three corpora",
      len(uni) == len(promise) + len(secreq) + df.text.nunique(), len(uni))
check("unified.parquet writes", (lambda: (uni.to_parquet(tmp / "u.parquet"), True)[1])())
check("ids stay prefixed by their corpus",
      {i.split("_")[0] for i in uni.id} == {"promise", "secreq", "gitreq"})

xd = list(S1.cross_dataset_splits(uni))
tasks = {e["task"] for e in xd}
check("cross-dataset now covers fr_nfr and subtype_shared7",
      {"fr_nfr", "security", "subtype_shared7"} <= tasks, sorted(tasks))
check("it does NOT invent all/top6/top4 transfers GitReq cannot support",
      not ({"subtype_all", "subtype_top6", "subtype_top4"} & tasks), sorted(tasks))
check("security now has all six ordered pairs",
      sum(e["task"] == "security" for e in xd) == 6,
      sum(e["task"] == "security" for e in xd))
check("every cross-dataset fold is train-on-one, test-on-another",
      all(uni.set_index("id").loc[list(e["train_ids"]), "source_dataset"].nunique() == 1
          and uni.set_index("id").loc[list(e["test_ids"]), "source_dataset"].nunique() == 1
          for e in xd))

shutil.rmtree(tmp, ignore_errors=True)
print(f"\n{'=' * 52}\n  {PASS} passed, {FAIL} failed\n{'=' * 52}")
sys.exit(1 if FAIL else 0)
