"""
STAGE 1 ADD-ON - GitReq loader (third corpus).

WHY THIS EXISTS
    Stage 1's own header records the limit this closes: "SecReq carries neither
    FR/NFR nor sub-type annotation, so there is no second corpus to transfer
    those tasks to. Closing them needs a third labelled corpus." GitReq is that
    corpus: it carries a Functional class and seven ISO/IEC 25010-aligned
    quality classes, seven of which PROMISE_exp also carries.

    F. Kamal, M. H. Kabir and M. R. Islam, "GitReq: A Gold Standard Dataset for
    Software Quality Requirements", arXiv:2606.21810 (2026).
    Data: figshare 10.6084/m9.figshare.31669477, CC BY 4.0. 6,302 requirements
    mined from GitHub issues over 4,080 repositories; Fleiss' kappa 0.72.

STATUS - READ BEFORE USING
    This module is NOT wired into the pipeline, and it must not be wired in by
    the four-step note an earlier revision of this file carried: that note was
    wrong. Integrating GitReq requires edits to Stages 1, 2, 3, 3b, 4 and 5,
    each verified against the notebook source and listed under INTEGRATION
    below. Until they are all made, importing this module changes nothing,
    which is the intended safe state.

    On its own the loader is complete and tested: it parses the published
    archive, refuses the look-alike file described next, emits Stage 1's exact
    schema and label vocabulary, and records what it did in a manifest.

TWO DIFFERENT FILES ARE PUBLISHED UNDER THE NAME GitReq
    figshare carries two items by the same author - "GitReq" and "GitReq
    Artifacts" - and a csv named GitReq.csv circulates with 9,926 rows,
    lower-cased labels and a class histogram matching nothing in the paper
    (performance 3,973, security 2,802, ...). Measured against the published
    corpus, exactly one text string is common to both files: it is a different
    dataset, not a later version. Loading it would have replaced the study's
    corpus silently.

    This loader therefore builds from GitReq_FR.csv + GitReq_NFR.csv - which
    also carry the `url` column the archive's own GitReq.csv lacks - and
    refuses any input whose row count or class histogram differs from the
    published composition.

WHAT IT RETURNS
    A DataFrame in Stage 1's loader schema - text, label_fr_nfr,
    label_nfr_subtype, label_security, project, source_dataset - using Stage 1's
    label vocabulary exactly: "FR"/"NFR", the lower-case sub-type names of
    PROMISE_SUBTYPE_MAP, and "security"/"non-security" (NOT 0/1: Stages 2, 3,
    3b, 4 and 5 all pin the string pair, and a numeric column would be dropped
    by their label filters, leave the cross-dataset folds empty, and break
    unified.parquet's dtype).

    `project` is the GitHub repository (owner/name) parsed from `url`. The
    grouping is weak by nature: 4,079 repositories hold 6,301 rows and only 147
    hold five or more, so a grouped fold prevents same-repository leakage but is
    close to an item-level split. That is a property of the corpus and belongs
    in the write-up, not in a cross-project claim.

THE SURFACE-FORM ARTEFACT THE WRITE-UP MUST CARRY
    GitReq's FR and NFR classes are built by different pipelines: the NFR side
    is semantic, the FR side first requires a formal-language score over
    shall / must / will / user-story / users-can markers. FORMAL_MARKER below is
    this module's approximation of that rubric, not the authors' own code, so
    every figure here is what `marker_only_baseline()` computes from it on the
    cleaned 6,301-row frame - never a number typed by hand: 531 of 531
    functional items carry a marker (100.0 %) against 1,030 of 5,770 quality
    items (17.9 %), and the marker-only rule scores macro-F1 0.7048 at accuracy
    0.8365 on that task. All four are pre-global-de-duplication; quote
    gitreq_post_dedup_report(uni) in the write-up. The FR/NFR transfer arm is therefore partly
    a surface-form probe and has to be reported as one, with the error analysis
    conditioned on marker presence; `write_marker_sidecar()` emits the per-item
    flags for that, and `marker_only_baseline()` recomputes the numbers above
    from the frame rather than trusting this docstring.

    The sub-type arm does not carry the artefact: label_nfr_subtype is NaN for
    every FR-pipeline item. The security arm is drawn from the NFR pipeline for
    its positive class, but its negative class does include the 531 FR-pipeline
    items, so the artefact is present there in weaker form and must be named.

INTEGRATION - every edit verified against the notebook sources
    Stage 1
      1. Add "shared7" to the SUBTYPE_LABELSETS *literal*, above the plans:
             SUBTYPE_SHARED7 = sorted(GITREQ_SUBTYPE_MAP.values())
             SUBTYPE_LABELSETS = {"all": ..., "top6": ..., "top4": ...,
                                  "shared7": SUBTYPE_SHARED7}
         Assigning the key later does NOT work: CROSS_PROJECT_PLAN and
         CROSS_DATASET_TASKS are materialised by list comprehensions over
         SUBTYPE_LABELSETS.items() at definition time, so a later assignment
         reaches build_all_splits (which reads the dict at call time) but not
         the plans - producing an in-domain family for a task that has no
         cross-dataset arm, which Stage 4 then discards.
         The variant is needed because macro-F1 is scored over a variant's FULL
         declared label set: transferring on "all"/"top6"/"top4" charges the
         model for legal, look_and_feel, operational and usability, which GitReq
         structurally cannot contain.
      2. build_unified(promise_df, secreq_df, manifest) takes exactly two
         frames. Generalise it to a list of (name, frame) pairs and pass
         gitreq_df as a third. Its de-duplication, id assignment and post-dedup
         counting already work per source.
      3. Optional: add GitReq arms to CROSS_PROJECT_PLAN, with the grouping
         caveat above. Nothing in cross_dataset_splits() needs changing - it
         already enumerates every ordered pair that shares a task.
      4. Call write_marker_sidecar(uni, OUT_DIR) after build_unified.

    Stage 2  (stage2-finetuned-baselines)
      5. LABELSETS is a hard-coded dict: add "subtype_shared7": SUBTYPE_SHARED7.
         Without it, Stage 2 skips the arm GitReq was adopted for.
      6. Preflight EXPECTED["unified.parquet"] = ({1412}, "1,412") is a
         SystemExit, not a warning, and 1412 = 968 promise + 444 secreq. Update
         it to the new post-de-duplication total or Stage 2 refuses to run.

    Stage 3  (stage3-llm-harnes)
      7. build_frames pins is_p = source_dataset == "promise" and
         is_s == "secreq". GitReq needs its own branch, or the prompted tier
         gains no GitReq arm at all and RQ1's comparison extends on the encoder
         side only - which would not be a like-for-like comparison.

    Stage 3b  (stage3b-subtype-harness, stage3b-repair)
      8. build_frames selects label_nfr_subtype.notna() with NO source filter
         and keys every frame (task, "promise"). That is safe only while PROMISE
         is the only sub-typed corpus. With GitReq present, its 5,771 sub-typed
         NFRs would be published under dataset="promise" - 92-95 % of the frame.
         Key each frame by its actual source_dataset, and re-check the sampling
         budget: the frames grow by an order of magnitude.
      9. stage3b-repair carries the same 1412 preflight constant as Stage 2.

    Stage 4  (stage4-analysis)
     10. LABELSETS: add "subtype_shared7" (Stage 4 drops unknown tasks).
     11. Preflight 1412 constant, as above.
     12. KEYS = [model, model_tag, tier, task, dataset, eval_regime] and
         dataset_of() tags a fold by its TEST corpus, so with three corpora
         secreq_to_promise and gitreq_to_promise fall into ONE cell and every
         item is scored twice - a blend of two source corpora under a caption
         naming one, with bootstrap intervals narrowed by the duplication. Add
         the source corpus to KEYS (or de-duplicate on id inside cell()) BEFORE
         any three-corpus result is reported.

    Stage 5  (stage5-cost)
     13. Preflight 1412 constant, as above.

    Then re-run Stages 2, 3, 3b, 4 and 5: the splits file changes and the
    prediction stores are keyed on fold names.

    The paper needs the matching edits: main.tex still states "Cross-dataset
    applies only to the security task, the one task both corpora annotate", and
    paper/scripts/make_tables.py and make_figs.py enumerate promise/secreq only.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import re
import sys
import zipfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger("stage1.gitreq")

# =============================================================================
# configuration
# =============================================================================
GITREQ_CONFIG = {
    # The figshare item is an archive. The article-level download URL follows
    # figshare's usual pattern but has NOT been verified from this environment,
    # so the local mirror is the primary path and the URL is provenance only.
    "doi": "10.6084/m9.figshare.31669477",
    "archive_url": "https://figshare.com/ndownloader/articles/31669477/versions/1",

    # sha256 of the archive and of the two member files this loader reads, as
    # downloaded on 2026-09-18. Stage 1 pins its other sources the same way.
    # The archive entry is checked when `source` is an archive; the member
    # entries are checked on both the archive and the directory path.
    "expected_sha256": {
        "__archive__":
            "80cabf7837aa54c941c15a4a322a85a30ca1a30fe7c366fa83c58bf536638ab8",
        "GitReq_FR.csv":
            "9f5ee7490981803e8908890c7459bb63a20b591c956395b29741ed082bb560da",
        "GitReq_NFR.csv":
            "8c9927bd648d41d6288ca40bcfd96e8e1e8cfb20d2b6eae1824c1057405bb90f",
    },
}

MEMBERS = ("GitReq_FR.csv", "GitReq_NFR.csv")
# Checked before the composition gate, so a look-alike is identified by its
# histogram rather than by a missing column.
IDENTITY_COLUMNS = ("RequirementText", "class_label")
# `url` is checked after the gate: it carries the repository, i.e. the grouping
# key, so it is required - but only once we know which file we are holding.
REQUIRED_COLUMNS = IDENTITY_COLUMNS + ("url",)

# The published composition (paper Table I). Any deviation is refused: this is
# what catches the 9,926-row look-alike.
GITREQ_EXPECTED_COUNTS = {
    "Security": 1646, "Performance": 1509, "Portability": 1284,
    "Availability": 738, "Functional": 531, "Fault-tolerance": 293,
    "Scalability": 157, "Maintainability": 144,
}
GITREQ_EXPECTED_TOTAL = 6302
# Rows surviving the clean on the pinned files: the published total minus the
# one row whose entire text is the spreadsheet error "#NAME?".
GITREQ_EXPECTED_ROWS_AFTER_CLEAN = 6301

# GitReq class -> Stage 1's sub-type vocabulary (the values of
# PROMISE_SUBTYPE_MAP, which Stage 2 and Stage 4 pin as CATEGORIES_ALL).
# "Functional" is not a sub-type and maps to NaN, exactly as PROMISE's "F" does.
GITREQ_SUBTYPE_MAP = {
    "Availability":     "availability",
    "Fault-tolerance":  "fault_tolerance",
    "Maintainability":  "maintainability",
    "Performance":      "performance",
    "Portability":      "portability",
    "Scalability":      "scalability",
    "Security":         "security",
}
SUBTYPE_SHARED7 = sorted(GITREQ_SUBTYPE_MAP.values())

GITREQ_FUNCTIONAL_CLASS = "Functional"
GITREQ_SECURITY_CLASS = "Security"

# Stage 1's label vocabulary, restated so this file cannot drift from it
# silently. If Stage 1 changes these, this module must change with it.
LABEL_FR, LABEL_NFR = "FR", "NFR"
LABEL_SECURITY, LABEL_NON_SECURITY = "security", "non-security"

# Excel writes these into a cell when a formula fails; one published row carries
# "#NAME?" as its whole text. Compared case-insensitively, because the loader
# may be asked to lower-case.
_SPREADSHEET_ERRORS = {"#NAME?", "#REF!", "#VALUE!", "#N/A", "#DIV/0!",
                       "#NULL!", "#NUM!", "#GETTING_DATA"}

# github.com/<owner>/<repo>, anchored on the host and rejecting the path
# prefixes that are not repositories. Every url in the published files is
# https://github.com/<owner>/<repo>/issues/<n>; the guards are for robustness
# against a future version, and are verified not to change the published counts.
_REPO = re.compile(
    r"^https?://(?:www\.)?github\.com/(?!(?:repos|orgs|users|gist|topics|"
    r"search|settings|sponsors|apps|marketplace)/)([^/\s?#]+)/([^/\s?#]+)",
    re.I)

# The five formal markers GitReq's FR pipeline scores on, as the paper names
# them. Diagnostic only - never a feature.
FORMAL_MARKER = re.compile(
    r"\b(?:shall|must|will|users?\s+can)\b"
    r"|\bas\s+an?\b[^.!?\n]{0,60}?\bi\s+want\b",
    re.I)

_WS = re.compile(r"\s+")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# =============================================================================
# helpers
# =============================================================================
def _normalize_text(s, lowercase=False):
    """Byte-for-byte mirror of Stage 1's normalize_text. If Stage 1's version
    changes, change this with it: a corpus normalised differently from its
    neighbours would confound every cross-dataset comparison in the study."""
    if not isinstance(s, str):
        s = "" if pd.isna(s) else str(s)
    s = _CTRL.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s.lower() if lowercase else s


@contextmanager
def _csv_field_limit(limit=2 ** 27):
    """Raise csv's field-size guard for this read only. Leaving it raised
    process-wide would let a malformed quote elsewhere parse into one giant row
    instead of raising."""
    old = csv.field_size_limit()
    csv.field_size_limit(limit)
    try:
        yield
    finally:
        csv.field_size_limit(old)


def _check_hash(key: str, blob: bytes, recorded: dict) -> None:
    got = hashlib.sha256(blob).hexdigest()
    recorded[key] = got
    want = GITREQ_CONFIG["expected_sha256"].get(key)
    if want is None:
        log.warning("%s is not pinned in GITREQ_CONFIG['expected_sha256']; "
                    "its sha256 is %s. Pin it before any run whose predictions "
                    "will be reported.", key, got)
        return
    if got != want:
        raise RuntimeError(
            f"{key} sha256 {got} does not match the pinned {want}. The source "
            f"changed, or this is a different file. If the change is wanted, "
            f"update GITREQ_CONFIG['expected_sha256'] and re-run Stages 2, 3, "
            f"3b, 4 and 5 from scratch - the existing stores cannot be carried "
            f"across it.")


def _resolve_zip_member(z: zipfile.ZipFile, member: str) -> str:
    """Find exactly one real file named `member`. Ambiguity is refused rather
    than resolved: a __MACOSX shadow or a versioned duplicate silently
    overriding the real member is precisely the class of mistake this loader
    exists to prevent."""
    hits = [n for n in z.namelist()
            if Path(n).name == member
            and not n.endswith("/")
            and "__MACOSX" not in n.split("/")]
    if not hits:
        raise FileNotFoundError(
            f"{member} not found in the archive. It holds: "
            f"{sorted({Path(n).name for n in z.namelist() if not n.endswith('/')})}")
    if len(hits) > 1:
        raise RuntimeError(
            f"the archive holds {len(hits)} files named {member} ({sorted(hits)}). "
            f"Extract the one you mean into a directory and load that instead - "
            f"guessing here would pick a stale or shadow copy without saying so.")
    return hits[0]


def _resolve_dir_member(root: Path, member: str) -> Path:
    """Directory twin of _resolve_zip_member, searched recursively so an
    extracted archive (which nests its files one level down) loads exactly like
    the archive itself."""
    hits = [p for p in root.rglob(member)
            if p.is_file() and "__MACOSX" not in p.parts]
    if not hits:
        raise FileNotFoundError(f"{member} not found under {root}.")
    if len(hits) > 1:
        raise RuntimeError(
            f"{len(hits)} files named {member} under {root} ({sorted(map(str, hits))}). "
            f"Point the loader at the one directory that holds the published files.")
    return hits[0]


def _read_members(source: Path, recorded: dict) -> dict[str, list[dict]]:
    """Read both member csvs from an archive or a directory, with the same
    validation on either path."""
    blobs: dict[str, bytes] = {}
    if source.is_dir():
        found = {m: _resolve_dir_member(source, m) for m in MEMBERS}
        parents = {p.parent for p in found.values()}
        if len(parents) > 1:
            raise RuntimeError(
                f"the member files live in different directories "
                f"({sorted(map(str, parents))}). Loading one version's FR file "
                f"beside another's NFR file would pass every other check here, "
                f"so it is refused.")
        blobs = {m: p.read_bytes() for m, p in found.items()}
    else:
        _check_hash("__archive__", source.read_bytes(), recorded)
        with zipfile.ZipFile(source) as z:
            for m in MEMBERS:
                blobs[m] = z.read(_resolve_zip_member(z, m))

    out = {}
    for m, blob in blobs.items():
        _check_hash(m, blob, recorded)
        # utf-8-sig: these files are spreadsheet exports, and a BOM would
        # otherwise become part of the first column's name - which turns a
        # missing-column error into either a bare KeyError or, worse, a silently
        # empty corpus.
        text = blob.decode("utf-8-sig", errors="replace")
        n_replacement = text.count("�")
        if n_replacement:
            log.warning("%s: %d character(s) could not be decoded and became "
                        "U+FFFD. Stage 1 reports the equivalent damage for "
                        "PROMISE; record this in the threats section.",
                        m, n_replacement)
        recorded[f"{m}::undecodable_chars"] = n_replacement
        with _csv_field_limit():
            rows = list(csv.DictReader(io.StringIO(text)))
        if not rows:
            raise RuntimeError(f"{m} parsed to zero rows.")
        # Identity columns are required before anything else, so a file that
        # carries them reaches the composition gate below and is refused with
        # the diagnostic that names the 9,926-row look-alike, rather than with a
        # column complaint that hides which file was loaded.
        missing = [c for c in IDENTITY_COLUMNS if c not in rows[0]]
        if missing:
            raise RuntimeError(
                f"{m} is missing required column(s) {missing}; it has "
                f"{sorted(k for k in rows[0] if k is not None)}. This loader "
                f"reads the published GitReq_FR.csv / GitReq_NFR.csv, whose "
                f"columns are {list(REQUIRED_COLUMNS)}.")
        out[m] = rows
    return out


def _histogram(rows) -> dict:
    """Class histogram with unparseable rows made visible rather than sorted
    into a TypeError: a ragged csv row gives class_label the value None."""
    hist: dict[str, int] = {}
    for r in rows:
        key = r.get("class_label")
        key = "<missing>" if key is None else str(key)
        hist[key] = hist.get(key, 0) + 1
    return dict(sorted(hist.items()))


# =============================================================================
# loader
# =============================================================================
def load_gitreq(source, manifest=None, lowercase=False):
    """Build the GitReq frame in Stage 1's loader schema.

    `source` is the figshare archive or a directory holding its extracted files;
    both paths validate identically. `lowercase` must be passed CONFIG's value,
    as Stage 1 does for its own loaders.
    """
    source = Path(source)
    manifest = {} if manifest is None else manifest
    recorded: dict[str, object] = {}

    members = _read_members(source, recorded)
    raw = members["GitReq_FR.csv"] + members["GitReq_NFR.csv"]
    log.info("GitReq: read %d FR + %d NFR = %d raw rows from %s.",
             len(members["GitReq_FR.csv"]), len(members["GitReq_NFR.csv"]),
             len(raw), source)

    # ---- integrity gate, on the raw rows ------------------------------------
    hist = _histogram(raw)
    if len(raw) != GITREQ_EXPECTED_TOTAL or hist != GITREQ_EXPECTED_COUNTS:
        raise RuntimeError(
            "GitReq composition does not match the published corpus.\n"
            f"  expected {GITREQ_EXPECTED_TOTAL} rows {GITREQ_EXPECTED_COUNTS}\n"
            f"  got      {len(raw)} rows {hist}\n"
            "A 9,926-row file with lower-cased labels circulates under the name "
            "GitReq.csv and is NOT the published dataset - its texts are "
            "disjoint from it. Use GitReq_FR.csv and GitReq_NFR.csv from the "
            "figshare archive.")

    unknown = sorted(set(hist) - set(GITREQ_SUBTYPE_MAP) - {GITREQ_FUNCTIONAL_CLASS})
    if unknown:                                    # unreachable while the gate
        raise RuntimeError(f"unmapped class label(s): {unknown}")  # above holds

    for m, rws in members.items():
        if "url" not in rws[0]:
            raise RuntimeError(
                f"{m} has the published composition but no `url` column, so the "
                f"repository - the grouping key for every grouped split - cannot "
                f"be recovered. Load GitReq_FR.csv and GitReq_NFR.csv from the "
                f"figshare archive; the archive's own GitReq.csv omits it.")

    # ---- clean --------------------------------------------------------------
    rows, dropped_err, no_repo = [], 0, 0
    for r in raw:
        cls = r["class_label"]
        text = _normalize_text(r.get("RequirementText"), lowercase)
        # Tested BEFORE case is considered, so the drop cannot depend on the
        # lowercase flag.
        if not text or text.upper() in _SPREADSHEET_ERRORS:
            dropped_err += 1
            continue

        m = _REPO.match((r.get("url") or "").strip())
        if m:
            owner, repo = m.group(1), re.sub(r"\.git$", "", m.group(2), flags=re.I)
            project = f"{owner}/{repo}".lower()
        else:
            # Never invent a group: an unparseable url becomes its own singleton,
            # the conservative choice for a grouped split.
            project = f"gitreq_unknown_{len(rows):05d}"
            no_repo += 1

        is_fr = cls == GITREQ_FUNCTIONAL_CLASS
        rows.append({
            "text": text,
            "label_fr_nfr": LABEL_FR if is_fr else LABEL_NFR,
            "label_nfr_subtype": GITREQ_SUBTYPE_MAP.get(cls, np.nan),
            "label_security": (LABEL_SECURITY if cls == GITREQ_SECURITY_CLASS
                               else LABEL_NON_SECURITY),
            "project": project,
            "source_dataset": "gitreq",
        })

    out = pd.DataFrame(rows, columns=["text", "label_fr_nfr",
                                      "label_nfr_subtype", "label_security",
                                      "project", "source_dataset"])

    # ---- post-clean guard ---------------------------------------------------
    # The gate above validates the raw rows; without this, any loss during the
    # clean - a renamed text column, a re-encoded file - would be reported only
    # as a smaller number in a log line. Both sibling loaders carry the same
    # kind of check.
    if len(out) != GITREQ_EXPECTED_ROWS_AFTER_CLEAN:
        raise RuntimeError(
            f"GitReq: {len(out)} rows survived the clean, expected "
            f"{GITREQ_EXPECTED_ROWS_AFTER_CLEAN} "
            f"({GITREQ_EXPECTED_TOTAL} published minus the one '#NAME?' row). "
            f"{dropped_err} row(s) were dropped as empty or spreadsheet errors. "
            f"Do not use this frame until the difference is explained; if it is "
            f"expected, update GITREQ_EXPECTED_ROWS_AFTER_CLEAN.")

    # build_unified() de-duplicates ACROSS the whole corpus on `text`, so the
    # number of GitReq rows that survive into unified.parquet is smaller than
    # the number returned here. Recorded, because Stage 1 documents the same
    # figure for PROMISE and SecReq and the write-up quotes post-dedup counts.
    n_internal_dupes = int(out.text.duplicated().sum())
    if n_internal_dupes:
        log.info("GitReq: %d row(s) duplicate another GitReq row after "
                 "normalisation and will be dropped by build_unified's global "
                 "de-duplication, leaving %d.",
                 n_internal_dupes, len(out) - n_internal_dupes)

    fr = out.label_fr_nfr.eq(LABEL_FR)
    has_marker = out.text.str.contains(FORMAL_MARKER)
    n_fr, n_nfr = int(fr.sum()), int((~fr).sum())
    n_marker_fr = int((fr & has_marker).sum())
    n_marker_nfr = int((~fr & has_marker).sum())

    manifest["gitreq"] = {
        "doi": GITREQ_CONFIG["doi"],
        "archive_url": GITREQ_CONFIG["archive_url"],
        "source_path": str(source),
        "sha256": {k: v for k, v in recorded.items() if not k.endswith("_chars")},
        "undecodable_chars": {k.split("::")[0]: v for k, v in recorded.items()
                              if k.endswith("_chars")},
        "raw_rows": len(raw),
        "expected_rows_per_publication": GITREQ_EXPECTED_TOTAL,
        "rows": int(len(out)),
        "dropped_spreadsheet_errors": dropped_err,
        "rows_without_parseable_repo": no_repo,
        "internal_duplicate_texts": n_internal_dupes,
        "rows_after_internal_dedup": int(len(out) - n_internal_dupes),
        "class_histogram_raw": hist,
        "projects": int(out["project"].nunique()),
        # NAMED as pre-de-duplication on purpose. build_unified() de-duplicates
        # ACROSS corpora afterwards, and the 12.9 % / 39.9 % figures the paper
        # places beside this one are post-de-duplication. Quote
        # gitreq_post_dedup_report(uni) in the write-up, never this field.
        "security_prevalence_before_global_dedup":
            round(float(out.label_security.eq(LABEL_SECURITY).mean()), 4),
        "subtype_map": GITREQ_SUBTYPE_MAP,
        "shared7_labelset": SUBTYPE_SHARED7,
        "formal_marker_before_global_dedup": {
            "fr_with_marker": n_marker_fr, "fr_total": n_fr,
            "nfr_with_marker": n_marker_nfr, "nfr_total": n_nfr,
            "fr_rate": round(n_marker_fr / n_fr, 4) if n_fr else None,
            "nfr_rate": round(n_marker_nfr / n_nfr, 4) if n_nfr else None,
        },
    }

    log.info("GitReq: %d rows, %d repositories, security %.1f%% (pre-global-"
             "dedup); dropped %d spreadsheet-error row(s), %d row(s) had no "
             "parseable repository.", len(out), out["project"].nunique(),
             100 * out.label_security.eq(LABEL_SECURITY).mean(),
             dropped_err, no_repo)
    log.info("GitReq: formal marker in %d/%d FR (%.1f%%) vs %d/%d NFR (%.1f%%) "
             "- the FR/NFR arm is partly a surface-form probe, report it as one.",
             n_marker_fr, n_fr, 100 * n_marker_fr / max(n_fr, 1),
             n_marker_nfr, n_nfr, 100 * n_marker_nfr / max(n_nfr, 1))
    return out


# =============================================================================
# artefacts the write-up reads back
# =============================================================================
def marker_only_baseline(df):
    """macro-F1 and accuracy of 'has a formal marker -> FR' on a GitReq frame.

    Recomputed from data so the paper never quotes a number typed by hand. On
    the published corpus, cleaned, this returns macro_f1 0.7048, accuracy
    0.8365.
    """
    fr = df.label_fr_nfr.eq(LABEL_FR)
    pred_fr = df.text.str.contains(FORMAL_MARKER)
    tp = int((fr & pred_fr).sum()); fp = int((~fr & pred_fr).sum())
    fn = int((fr & ~pred_fr).sum()); tn = int((~fr & ~pred_fr).sum())

    def f1(tp_, fp_, fn_):
        p = tp_ / (tp_ + fp_) if tp_ + fp_ else 0.0
        r = tp_ / (tp_ + fn_) if tp_ + fn_ else 0.0
        return 2 * p * r / (p + r) if p + r else 0.0

    f_fr, f_nfr = f1(tp, fp, fn), f1(tn, fn, fp)
    n = len(df)
    return {"n": n, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "f1_fr": round(f_fr, 4), "f1_nfr": round(f_nfr, 4),
            "macro_f1": round((f_fr + f_nfr) / 2, 4),
            "accuracy": round((tp + tn) / n, 4) if n else None}


def gitreq_post_dedup_report(uni):
    """The GitReq figures the write-up must quote: measured on the unified frame
    AFTER build_unified's cross-corpus de-duplication, so they share a
    denominator with PROMISE_exp's 12.9 % and SecReq's 39.9 %."""
    g = uni[uni.source_dataset.eq("gitreq")]
    if g.empty:
        raise ValueError("no gitreq rows in the unified frame.")
    fr = g.label_fr_nfr.eq(LABEL_FR)
    has = g.text.str.contains(FORMAL_MARKER)
    return {
        "rows": int(len(g)),
        "projects": int(g.project.nunique()),
        "security_prevalence": round(
            float(g.label_security.eq(LABEL_SECURITY).mean()), 4),
        "fr": int(fr.sum()), "nfr": int((~fr).sum()),
        "fr_with_marker": int((fr & has).sum()),
        "nfr_with_marker": int((~fr & has).sum()),
        "subtype_support": {k: int(v) for k, v in
                            g.label_nfr_subtype.value_counts().items()},
        "marker_only_baseline": marker_only_baseline(g),
    }


def write_marker_sidecar(uni, out_dir):
    """Per-item formal-marker flags for the FR/NFR error analysis, keyed by the
    unified id. Kept OUT of unified.parquet so UNIFIED_COLUMNS and every
    downstream stage's schema stay untouched. Call it from Stage 1 after
    build_unified (INTEGRATION step 4) - otherwise the artefact the write-up
    depends on is never produced."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    side = uni.loc[uni.source_dataset.eq("gitreq"), ["id", "text"]].copy()
    if side.empty:
        raise ValueError("no gitreq rows in the unified frame.")
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
        sys.exit("usage: python stage1_gitreq.py <archive.zip | extracted-dir>")

    man: dict = {}
    df = load_gitreq(sys.argv[1], man)
    print("\ncolumns:", list(df.columns))
    print("\nlabel_fr_nfr:\n", df.label_fr_nfr.value_counts().to_string())
    print("\nlabel_security:\n", df.label_security.value_counts().to_string())
    print("\nlabel_nfr_subtype:\n",
          df.label_nfr_subtype.value_counts(dropna=False).to_string())
    print("\nprojects: %d (largest %d items)"
          % (df.project.nunique(), df.project.value_counts().iloc[0]))
    print("\nshared-7 label set:", SUBTYPE_SHARED7)
    print("\nmarker-only baseline:", marker_only_baseline(df))
