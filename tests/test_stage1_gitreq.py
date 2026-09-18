"""Adversarial test battery for stage1_gitreq.load_gitreq.

Run:  GITREQ_ARCHIVE=/path/to/31669477.zip python3 tests/test_stage1_gitreq.py

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
import csv, io, logging, shutil, sys, tempfile, zipfile
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import stage1_gitreq as G

logging.disable(logging.WARNING)
ARC = Path(ARC)
# The 9,926-row look-alike, if available. Set GITREQ_LOOKALIKE to exercise the
# refusal against the real file; otherwise that case is synthesised.
IMPOSTOR = os.environ.get("GITREQ_LOOKALIKE")
PASS = FAIL = 0

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else:    FAIL += 1; print(f"  FAIL  {name}  {detail}")

def expect_raise(name, fn, must_contain=None):
    try:
        fn(); check(name, False, "no exception raised")
    except Exception as e:
        ok = (must_contain is None) or (must_contain.lower() in str(e).lower())
        check(name, ok, f"message was: {str(e)[:150]}")

def members(arc=ARC):
    with zipfile.ZipFile(arc) as z:
        return {m: z.read(G._resolve_zip_member(z, m)) for m in G.MEMBERS}

def build_zip(path, mapping, extra=()):
    with zipfile.ZipFile(path, "w") as z:
        for name, blob in mapping.items(): z.writestr(name, blob)
        for name, blob in extra: z.writestr(name, blob)

def unpin(*keys):
    saved = dict(G.GITREQ_CONFIG["expected_sha256"])
    for k in keys: G.GITREQ_CONFIG["expected_sha256"].pop(k, None)
    return saved

def repin(saved):
    G.GITREQ_CONFIG["expected_sha256"] = saved

tmp = Path(tempfile.mkdtemp())
M = members()

print("\n== 1. happy path, pinned archive ==")
man = {}
df = G.load_gitreq(ARC, man)
check("6301 rows", len(df) == 6301, len(df))
check("label_security is Stage 1's string pair",
      set(df.label_security) == {"security", "non-security"}, set(df.label_security))
check("label_fr_nfr is FR/NFR", set(df.label_fr_nfr) == {"FR", "NFR"})
check("security count 1646", int(df.label_security.eq("security").sum()) == 1646)
check("subtype NaN exactly for FR",
      int(df.label_nfr_subtype.isna().sum()) == int(df.label_fr_nfr.eq("FR").sum()) == 531)
check("archive sha recorded", man["gitreq"]["sha256"].get("__archive__", "").startswith("80cabf78"))
check("prevalence key names pre-dedup",
      "security_prevalence_before_global_dedup" in man["gitreq"]
      and "security_prevalence" not in man["gitreq"])
b = G.marker_only_baseline(df)
check("baseline matches docstring 0.7048/0.8365",
      (b["macro_f1"], b["accuracy"]) == (0.7048, 0.8365), b)

print("\n== 2. the 9,926-row look-alike is refused ==")
if IMPOSTOR and Path(IMPOSTOR).exists():
    imp = Path(IMPOSTOR).read_bytes()
else:
    # same shape, wrong composition: lower-cased labels and the wrong total
    rows = ["ID,RequirementText,class_label"]
    for i in range(9926):
        rows.append(f"{i},\"synthetic row {i}\",{'performance' if i % 2 else 'security'}")
    imp = ("\n".join(rows)).encode("utf-8")
d_imp = tmp / "impostor"; d_imp.mkdir()
(d_imp / "GitReq_FR.csv").write_bytes(imp); (d_imp / "GitReq_NFR.csv").write_bytes(imp)
sv = unpin("GitReq_FR.csv", "GitReq_NFR.csv")
expect_raise("refuses look-alike with a diagnostic",
             lambda: G.load_gitreq(d_imp), "does not match the published corpus")
repin(sv)

print("\n== 3. UTF-8 BOM, both column orders ==")
for order, tag in [(None, "original order"), ("reorder", "text column second")]:
    d = tmp / f"bom_{tag.replace(' ','_')}"; d.mkdir()
    for m, blob in M.items():
        text = blob.decode("utf-8")
        if order == "reorder":
            rows = list(csv.DictReader(io.StringIO(text)))
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=["class_label", "RequirementText", "url"],
                               extrasaction="ignore")
            w.writeheader(); w.writerows(rows); text = buf.getvalue()
        (d / m).write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    sv = unpin("GitReq_FR.csv", "GitReq_NFR.csv")
    try:
        got = len(G.load_gitreq(d))
        check(f"BOM tolerated ({tag})", got == 6301, got)
    except Exception as e:
        check(f"BOM tolerated ({tag})", False, str(e)[:120])
    repin(sv)

print("\n== 4. lowercase=True still drops the '#NAME?' row ==")
low = G.load_gitreq(ARC, {}, lowercase=True)
check("same row count under lowercase", len(low) == 6301, len(low))
check("no spreadsheet-error text survives",
      not low.text.str.upper().isin(G._SPREADSHEET_ERRORS).any())
check("text really is lower-cased", low.text.str.islower().mean() > 0.9)

print("\n== 5. renamed text column fails loudly (not silently empty) ==")
d = tmp / "renamed"; d.mkdir()
for m, blob in M.items():
    t = blob.decode("utf-8").split("\n", 1)
    (d / m).write_text(t[0].replace("RequirementText", "Requirement_Text") + "\n" + t[1])
sv = unpin("GitReq_FR.csv", "GitReq_NFR.csv")
expect_raise("missing column raises", lambda: G.load_gitreq(d), "missing required column")
repin(sv)

print("\n== 6. zip member ambiguity is refused, __MACOSX ignored ==")
z1 = tmp / "shadow.zip"
build_zip(z1, M, extra=[("__MACOSX/GitReq_FR.csv", b"junk")])
sv = unpin("__archive__")
got = len(G.load_gitreq(z1))
check("__MACOSX shadow ignored", got == 6301, got)
z2 = tmp / "dup.zip"
build_zip(z2, M, extra=[("v1/GitReq_FR.csv", M["GitReq_FR.csv"])])
expect_raise("duplicate member refused", lambda: G.load_gitreq(z2), "files named")
repin(sv)

print("\n== 7. extracted directory == archive (nested) ==")
d = tmp / "extracted"; (d / "GitReq").mkdir(parents=True)
for m, blob in M.items(): (d / "GitReq" / m).write_bytes(blob)
check("nested extraction loads", len(G.load_gitreq(d)) == 6301)

print("\n== 7b. members from different directories are refused ==")
d = tmp / "mixed"; (d / "a").mkdir(parents=True); (d / "b").mkdir(parents=True)
(d / "a" / "GitReq_FR.csv").write_bytes(M["GitReq_FR.csv"])
(d / "b" / "GitReq_NFR.csv").write_bytes(M["GitReq_NFR.csv"])
expect_raise("split directories refused", lambda: G.load_gitreq(d), "different directories")

print("\n== 8. ragged row gives a diagnostic, not a TypeError ==")
d = tmp / "ragged"; d.mkdir()
for m, blob in M.items():
    (d / m).write_bytes(blob + b"\n9999,\"orphan text with no label\"")
sv = unpin("GitReq_FR.csv", "GitReq_NFR.csv")
try:
    G.load_gitreq(d); check("ragged row raises", False, "no exception")
except TypeError as e:
    check("ragged row raises", False, f"TypeError leaked: {e}")
except RuntimeError as e:
    check("ragged row raises RuntimeError with histogram", "<missing>" in str(e) or "does not match" in str(e),
          str(e)[:160])
repin(sv)

print("\n== 9. csv field-size limit restored ==")
before = csv.field_size_limit(); G.load_gitreq(ARC, {})
check("field_size_limit restored", csv.field_size_limit() == before,
      f"{before} -> {csv.field_size_limit()}")

print("\n== 10. tampered file fails the hash pin ==")
d = tmp / "tampered"; d.mkdir()
(d / "GitReq_FR.csv").write_bytes(M["GitReq_FR.csv"] + b"\n")
(d / "GitReq_NFR.csv").write_bytes(M["GitReq_NFR.csv"])
expect_raise("hash mismatch refused", lambda: G.load_gitreq(d), "sha256")

print("\n== 11. downstream compatibility ==")
promise = pd.DataFrame({
    "text": ["the system shall encrypt data", "response within 2 seconds"],
    "label_fr_nfr": ["FR", "NFR"], "label_nfr_subtype": [np.nan, "performance"],
    "label_security": ["non-security", "non-security"],
    "project": ["p1", "p2"], "source_dataset": ["promise", "promise"]})
secreq = pd.DataFrame({
    "text": ["access shall be authenticated"], "label_fr_nfr": [np.nan],
    "label_nfr_subtype": [np.nan], "label_security": ["security"],
    "project": ["CEPS"], "source_dataset": ["secreq"]})
frames = []
for src, d_ in [("promise", promise), ("secreq", secreq), ("gitreq", df)]:
    x = d_.copy().reset_index(drop=True)
    x["id"] = [f"{src}_{i:05d}" for i in range(len(x))]
    frames.append(x)
uni = pd.concat(frames, ignore_index=True)
uni = uni.drop_duplicates(subset=["text"]).reset_index(drop=True)
uni = uni[["id", "text", "label_fr_nfr", "label_nfr_subtype", "label_security",
           "project", "source_dataset"]]
try:
    uni.to_parquet(tmp / "unified.parquet"); check("unified.parquet writes", True)
except Exception as e:
    check("unified.parquet writes", False, str(e)[:120])
check("label_security has one dtype",
      sorted(pd.unique(uni.label_security)) == ["non-security", "security"])
STAGE2_SECURITY = ["non-security", "security"]
STAGE2_CATEGORIES_ALL = ["availability", "fault_tolerance", "legal", "look_and_feel",
                         "maintainability", "operational", "performance",
                         "portability", "scalability", "security", "usability"]
kept = uni[uni.label_security.astype(str).isin(STAGE2_SECURITY)]
check("Stage 2 security filter keeps every GitReq row",
      int((kept.source_dataset == "gitreq").sum())
      == int((uni.source_dataset == "gitreq").sum()))
check("every GitReq sub-type is in Stage 2's CATEGORIES_ALL",
      set(df.label_nfr_subtype.dropna()) <= set(STAGE2_CATEGORIES_ALL))
check("shared7 subset of CATEGORIES_ALL",
      set(G.SUBTYPE_SHARED7) <= set(STAGE2_CATEGORIES_ALL))
N_DEDUP = df.text.nunique()          # GitReq holds one internal duplicate pair
check("loader reports the internal duplicate",
      man["gitreq"]["internal_duplicate_texts"] == len(df) - N_DEDUP
      and man["gitreq"]["rows_after_internal_dedup"] == N_DEDUP,
      man["gitreq"]["internal_duplicate_texts"])
rep = G.gitreq_post_dedup_report(uni)
check("post-dedup report matches the deduped frame",
      rep["rows"] == N_DEDUP and 0 < rep["security_prevalence"] < 1, rep["rows"])
path = G.write_marker_sidecar(uni, tmp / "out")
check("sidecar rows == deduped gitreq rows", len(pd.read_csv(path)) == N_DEDUP)
sid = pd.read_csv(path)
check("sidecar agrees with post-dedup report",
      int(sid.has_formal_marker.sum()) == rep["fr_with_marker"] + rep["nfr_with_marker"])

shutil.rmtree(tmp, ignore_errors=True)
print(f"\n{'='*52}\n  {PASS} passed, {FAIL} failed\n{'='*52}")
sys.exit(1 if FAIL else 0)
