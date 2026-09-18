"""
STAGE 1 ADD-ON - GitReq loader (third corpus).

WHY THIS EXISTS
    Stage 1's own header records the limit this closes: "SecReq carries neither
    FR/NFR nor sub-type annotation, so there is no second corpus to transfer
    those tasks to. Closing them needs a third labelled corpus." GitReq is that
    corpus. It carries a Functional class AND seven ISO/IEC 25010-aligned
    quality classes, so it opens the two cross-dataset arms that are empty today
    and adds a third point to the security prior axis (PROMISE_exp 12.9 % ->
    GitReq 26.1 % -> SecReq 39.9 %).

SOURCE
    F. Kamal, M. H. Kabir and M. R. Islam, "GitReq: A Gold Standard Dataset for
    Software Quality Requirements", arXiv:2606.21810 (2026).
    Data: figshare 10.6084/m9.figshare.31669477, CC BY 4.0.
    6,302 expert-validated requirements mined from GitHub issues over 4,080
    repositories; Fleiss' kappa 0.72.

READ THIS BEFORE POINTING IT AT A FILE
    The figshare item contains SEVERAL csv files, and one file circulating under
    the name GitReq.csv is NOT the published corpus: it has 9,926 rows, mixed
    label casing, and a class histogram that matches nothing in the paper
    (performance 3,973, security 2,802 ...). Its texts are disjoint from the
    published 6,302 - exactly one string overlaps. Loading it would have
    silently replaced the dataset with something else, so this loader builds
    from GitReq_FR.csv + GitReq_NFR.csv, which additionally carry the `url`
    column the published GitReq.csv lacks, and REFUSES anything whose class
    histogram does not match the paper.

WHAT IT PRODUCES
    A frame in Stage 1's own schema - text, label_fr_nfr, label_nfr_subtype,
    label_security, project, source_dataset - so build_unified() can consume it
    beside promise_df and secreq_df with no other change.

    `project` is the GitHub repository (owner/name), parsed from `url`. Note the
    grouping is weak: 4,080 repositories hold 6,302 items, and only 147 repos
    hold five or more, so a grouped fold over GitReq prevents same-repo leakage
    but is close to an item-level split. That is a property of the corpus, not a
    bug, and belongs in the write-up rather than in a fold-count claim.

THE ONE THING THE WRITE-UP MUST SAY
    GitReq's FR and NFR classes come from different pipelines: the NFR side is
    semantic, the FR side first requires a formal-language score built on
    shall / must / will / user-story / users-can markers. Measured on the
    published corpus: 100.0 % of the 531 functional items carry such a marker
    against 16.4 % of the 5,771 quality items, and a five-token regex that
    predicts FR iff a marker is present scores macro-F1 0.720 (accuracy 0.850)
    on that task. The FR/NFR cross-dataset arm is therefore partly a surface-form
    probe and must be reported as one, with the error analysis conditioned on
    marker presence. `write_marker_sidecar()` emits the per-item flags for that.
    The security arm and the sub-type arm are drawn from the NFR pipeline only
    and do not carry this artefact.

WIRING IT INTO STAGE 1 - four edits, none of them to the split functions
    1. SUBTYPE_LABELSETS["shared7"] = SUBTYPE_SHARED7
       Needed because macro-F1 is scored over a variant's FULL declared label
       set: transferring on "all" or "top6" would charge a model for legal,
       look_and_feel, operational and usability, which GitReq cannot contain.
    2. build_unified(promise_df, secreq_df, manifest) takes exactly two frames.
       Generalise it to a list - `for src, df in frames:` - and pass
       [("promise", promise_df), ("secreq", secreq_df), ("gitreq", gitreq_df)].
       Its de-duplication, id assignment and post-dedup counting already work
       per source and need no other change.
    3. CROSS_PROJECT_PLAN: add the GitReq arms if wanted, e.g.
          ("gitreq", "security", "label_security", None, "xproj_security_gitreq")
          ("gitreq", "subtype_shared7", "label_nfr_subtype", SUBTYPE_SHARED7,
           "xproj_subtype_shared7_gitreq")
       with the caveat above about 4,080 groups over 6,302 items.
    4. Nothing in cross_dataset_splits(). It already emits every ordered pair of
       corpora that share a task, so GitReq's arrival creates
       promise<->gitreq and secreq<->gitreq automatically - which is exactly
       what its docstring promised a third corpus would do.

    Adding GitReq fills the two empty cells in Stage 1's own table:
        fr_nfr           in_domain  cross_project  cross_dataset  <- opens
        security         in_domain  cross_project  cross_dataset  <- third prior
        subtype_shared7  in_domain  cross_project  cross_dataset  <- opens
    and re-running Stages 2, 3 and 3b is required: the splits file changes, and
    the existing prediction stores are keyed on the old folds.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("stage1.gitreq")

csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))

# =============================================================================
# configuration
# =============================================================================
GITREQ_CONFIG = {
    # The figshare item is an archive; the article-level download URL follows
    # figshare's usual pattern but has NOT been verified from this environment,
    # so treat the local mirror as the primary path and the URL as provenance.
    # On Kaggle (Internet = ON) fetch it once, store it, and pin the hash below.
    "doi": "10.6084/m9.figshare.31669477",
    "archive_url": "https://figshare.com/ndownloader/articles/31669477/versions/1",
    "archive_name": "31669477.zip",

    # sha256 of the archive and of the two member files this loader reads, as
    # downloaded on 2026-09-18. Stage 1 pins its other sources the same way.
    "expected_sha256": {
        "31669477.zip":
            "80cabf7837aa54c941c15a4a322a85a30ca1a30fe7c366fa83c58bf536638ab8",
        "GitReq_FR.csv":
            "9f5ee7490981803e8908890c7459bb63a20b591c956395b29741ed082bb560da",
        "GitReq_NFR.csv":
            "8c9927bd648d41d6288ca40bcfd96e8e1e8cfb20d2b6eae1824c1057405bb90f",
    },
}

# The published composition (paper Table I). The loader refuses any file whose
# histogram differs, which is what catches the 9,926-row impostor.
GITREQ_EXPECTED_COUNTS = {
    "Security": 1646, "Performance": 1509, "Portability": 1284,
    "Availability": 738, "Functional": 531, "Fault-tolerance": 293,
    "Scalability": 157, "Maintainability": 144,
}
GITREQ_EXPECTED_TOTAL = 6302

# GitReq class -> Stage 1's sub-type vocabulary (PROMISE_SUBTYPE_MAP values).
# Seven classes are shared with PROMISE_exp. GitReq has no legal,
# look_and_feel, operational or usability class; PROMISE_exp has no class
# outside this map that GitReq carries. `Functional` is not a sub-type and maps
# to NaN, exactly as PROMISE's "F" does.
GITREQ_SUBTYPE_MAP = {
    "Availability":     "availability",
    "Fault-tolerance":  "fault_tolerance",
    "Maintainability":  "maintainability",
    "Performance":      "performance",
    "Portability":      "portability",
    "Scalability":      "scalability",
    "Security":         "security",
}

# The label set for the cross-dataset sub-type arm. Stage 1 scores macro-F1 over
# the FULL declared label set of a variant, so transferring on "all"/"top6"
# would charge a model for classes the target corpus cannot contain. Declare
# this variant and use it for the PROMISE_exp <-> GitReq pair.
#   SUBTYPE_LABELSETS["shared7"] = SUBTYPE_SHARED7
SUBTYPE_SHARED7 = sorted(GITREQ_SUBTYPE_MAP.values())

GITREQ_SECURITY_CLASS = "Security"

# Excel writes these into text cells when a formula fails; one row carries
# "#NAME?" as its entire text. Dropped and counted, never silently kept.
_SPREADSHEET_ERRORS = {"#NAME?", "#REF!", "#VALUE!", "#N/A", "#DIV/0!", "#NULL!"}

_REPO = re.compile(r"github\.com/([^/\s]+/[^/\s#?]+)", re.I)

# The five formal markers GitReq's FR pipeline scores on, as the paper names
# them. Used only for the diagnostic sidecar - never as a feature.
FORMAL_MARKER = re.compile(
    r"\b(?:shall|must|will|as an?\s+[a-z][a-z ]{0,20}?i\s+want|users?\s+can)\b",
    re.I)

_WS = re.compile(r"\s+")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _normalize_text(s, lowercase=False):
    """Mirror of Stage 1's normalize_text: minimal by design. If Stage 1's
    version changes, change this with it - a corpus normalised differently from
    its neighbours would confound every cross-dataset comparison in the study."""
    if s is None:
        return ""
    s = _CTRL.sub(" ", str(s))
    s = _WS.sub(" ", s).strip()
    return s.lower() if lowercase else s


def _sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _check_hash(name: str, blob: bytes, manifest_slot: dict) -> None:
    want = GITREQ_CONFIG["expected_sha256"].get(name)
    got = _sha256(blob)
    manifest_slot[name] = got
    if want and got != want:
        raise RuntimeError(
            f"{name} sha256 {got} does not match the pinned {want}. The source "
            f"changed, or this is a different file. If the change is wanted, "
            f"update GITREQ_CONFIG['expected_sha256'] and re-run Stages 2, 3 "
            f"and 3b from scratch - the existing stores cannot be carried "
            f"across it.")


def _read_member(source: Path, member: str, hashes: dict) -> list[dict]:
    """Read one csv either from the figshare archive or from a directory of
    already-extracted files."""
    if source.is_dir():
        path = source / member
        if not path.is_file():
            raise FileNotFoundError(f"{path} not found.")
        blob = path.read_bytes()
    else:
        with zipfile.ZipFile(source) as z:
            names = {Path(n).name: n for n in z.namelist()}
            if member not in names:
                raise FileNotFoundError(
                    f"{member} not in {source}; archive holds {sorted(names)}")
            blob = z.read(names[member])
    _check_hash(member, blob, hashes)
    text = blob.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


# =============================================================================
# loader
# =============================================================================
def load_gitreq(source, manifest=None, lowercase=False):
    """Build the GitReq frame in Stage 1's unified schema.

    `source` is the figshare archive (31669477.zip) or a directory holding its
    extracted csv files. Returns a DataFrame with the same columns the PROMISE
    and SecReq loaders return, minus `id`, which build_unified() assigns.
    """
    source = Path(source)
    manifest = {} if manifest is None else manifest
    hashes: dict[str, str] = {}

    fr_rows = _read_member(source, "GitReq_FR.csv", hashes)
    nfr_rows = _read_member(source, "GitReq_NFR.csv", hashes)
    raw = fr_rows + nfr_rows
    log.info("GitReq: read %d FR + %d NFR = %d raw rows.",
             len(fr_rows), len(nfr_rows), len(raw))

    # ---- integrity gate -----------------------------------------------------
    # This is what rejects the 9,926-row file circulating as "GitReq.csv".
    hist: dict[str, int] = {}
    for r in raw:
        hist[r["class_label"]] = hist.get(r["class_label"], 0) + 1
    if len(raw) != GITREQ_EXPECTED_TOTAL or hist != GITREQ_EXPECTED_COUNTS:
        raise RuntimeError(
            "GitReq composition does not match the published corpus.\n"
            f"  expected {GITREQ_EXPECTED_TOTAL} rows {GITREQ_EXPECTED_COUNTS}\n"
            f"  got      {len(raw)} rows {dict(sorted(hist.items()))}\n"
            "A 9,926-row file with lower-cased labels circulates under the name "
            "GitReq.csv and is NOT the published dataset - its texts are "
            "disjoint from it. Use GitReq_FR.csv and GitReq_NFR.csv from the "
            "figshare archive.")

    rows, dropped_err, no_repo = [], 0, 0
    for r in raw:
        cls = r["class_label"]
        text = _normalize_text(r.get("RequirementText"), lowercase)
        if not text or text.strip() in _SPREADSHEET_ERRORS:
            dropped_err += 1
            continue

        m = _REPO.search(r.get("url") or "")
        if m:
            project = m.group(1).lower()
        else:
            # Never invent a group: an unparseable url becomes its own singleton
            # group, which is the conservative choice for a grouped split.
            project = f"gitreq_unknown_{len(rows):05d}"
            no_repo += 1

        rows.append({
            "text": text,
            "label_fr_nfr": "FR" if cls == "Functional" else "NFR",
            "label_nfr_subtype": GITREQ_SUBTYPE_MAP.get(cls, np.nan),
            "label_security": int(cls == GITREQ_SECURITY_CLASS),
            "project": project,
            "source_dataset": "gitreq",
        })

    out = pd.DataFrame(rows, columns=["text", "label_fr_nfr",
                                      "label_nfr_subtype", "label_security",
                                      "project", "source_dataset"])

    n_marker_fr = int(out[out.label_fr_nfr.eq("FR")].text
                      .str.contains(FORMAL_MARKER).sum())
    n_marker_nfr = int(out[out.label_fr_nfr.eq("NFR")].text
                       .str.contains(FORMAL_MARKER).sum())
    n_fr = int(out.label_fr_nfr.eq("FR").sum())
    n_nfr = int(out.label_fr_nfr.eq("NFR").sum())

    manifest["gitreq"] = {
        "doi": GITREQ_CONFIG["doi"],
        "archive_url": GITREQ_CONFIG["archive_url"],
        "source_path": str(source),
        "sha256": hashes,
        "raw_rows": len(raw),
        "rows": int(len(out)),
        "dropped_spreadsheet_errors": dropped_err,
        "rows_without_parseable_repo": no_repo,
        "class_histogram": dict(sorted(hist.items())),
        "projects": int(out["project"].nunique()),
        "security_prevalence": round(float(out["label_security"].mean()), 4),
        "subtype_map": GITREQ_SUBTYPE_MAP,
        "shared7_labelset": SUBTYPE_SHARED7,
        # the surface-form artefact, recorded as data so the claim in the paper
        # is read back from an artefact rather than retyped
        "formal_marker": {
            "fr_with_marker": n_marker_fr, "fr_total": n_fr,
            "nfr_with_marker": n_marker_nfr, "nfr_total": n_nfr,
            "fr_rate": round(n_marker_fr / n_fr, 4) if n_fr else None,
            "nfr_rate": round(n_marker_nfr / n_nfr, 4) if n_nfr else None,
        },
    }

    log.info("GitReq: %d rows, %d repositories, security prevalence %.1f%% "
             "(dropped %d spreadsheet-error rows, %d rows had no parseable "
             "repo).", len(out), out["project"].nunique(),
             100 * out["label_security"].mean(), dropped_err, no_repo)
    log.info("GitReq: formal marker in %d/%d FR (%.1f%%) vs %d/%d NFR (%.1f%%) "
             "- the FR/NFR arm is a surface-form probe, report it as one.",
             n_marker_fr, n_fr, 100 * n_marker_fr / max(n_fr, 1),
             n_marker_nfr, n_nfr, 100 * n_marker_nfr / max(n_nfr, 1))
    return out


def write_marker_sidecar(uni, out_dir):
    """Per-item formal-marker flags for the FR/NFR error analysis, keyed by the
    unified id. Kept OUT of unified.parquet so UNIFIED_COLUMNS and every
    downstream stage's schema stay untouched."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    side = uni.loc[uni.source_dataset.eq("gitreq"), ["id", "text"]].copy()
    side["has_formal_marker"] = side["text"].str.contains(FORMAL_MARKER)
    side = side.drop(columns=["text"])
    path = out_dir / "gitreq_marker_flags.csv"
    side.to_csv(path, index=False)
    log.info("wrote %s (%d rows, %d with a marker).",
             path, len(side), int(side.has_formal_marker.sum()))
    return path


# =============================================================================
# self-test
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    if len(sys.argv) != 2:
        sys.exit("usage: python stage1_gitreq.py <31669477.zip | extracted-dir>")

    man: dict = {}
    df = load_gitreq(sys.argv[1], man)
    print("\ncolumns:", list(df.columns))
    print("\nlabel_fr_nfr:\n", df.label_fr_nfr.value_counts().to_string())
    print("\nlabel_nfr_subtype:\n",
          df.label_nfr_subtype.value_counts(dropna=False).to_string())
    print("\nlabel_security: %d positive / %d total (%.1f%%)"
          % (df.label_security.sum(), len(df), 100 * df.label_security.mean()))
    print("\nprojects: %d  (largest %d items)"
          % (df.project.nunique(), df.project.value_counts().iloc[0]))
    print("\nshared-7 label set:", SUBTYPE_SHARED7)
    print("\nmanifest['gitreq']['formal_marker']:", man["gitreq"]["formal_marker"])
