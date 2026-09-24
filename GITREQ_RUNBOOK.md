# Adding GitReq: what changed, and how to run it

GitReq (arXiv:2606.21810; figshare `10.6084/m9.figshare.31669477`, CC BY 4.0) is
the third corpus. It closes the two cells Stage 1 used to report as permanent
data limits — FR/NFR and NFR sub-type had no cross-dataset arm, because SecReq
carries neither label — and adds a third point to the security prior axis.

| task | in-domain | cross-project | cross-dataset |
|---|---|---|---|
| FR/NFR | ✓ | ✓ | **opened** |
| security | ✓ | ✓ | ✓ → **6 ordered pairs** (was 2) |
| NFR sub-type (shared-7) | ✓ | ✓ | **opened** |
| NFR sub-type (all / top-6 / top-4) | ✓ | ✓ | deliberately empty — see below |

Coverage goes from 11 of 15 cells to 15 of 18. Corpus: 1,412 → 7,712 rows
(promise 968, secreq 444, gitreq 6,300).

## Two decisions worth knowing before you read the diff

**Nothing already computed moves.** GitReq is appended last, ids are positional
and de-duplication keeps the first occurrence, so every `promise_*` and
`secreq_*` id still maps to the sentence the committed prediction stores were
built against. `STAGE1_FREEZE_SPLITS` then reuses a previous `splits.json`
*fold by fold*, so the 107 folds those stores are keyed on are reused
byte-identical and only the 48 new GitReq folds are generated. Use it: measured
across two scikit-learn versions on this corpus, eight of the fourteen families
reproduce exactly and five grouped ones do not, so regenerating them would
invalidate the stores in silence.

**The all-11 / top-6 / top-4 sub-type transfers stay empty on purpose.**
macro-F1 is scored over a variant's full declared label set, and GitReq
structurally cannot contain `legal`, `look_and_feel`, `operational` or
`usability`. Transferring on those label sets would measure the taxonomy
mismatch, not the model. A corpus now qualifies for a label set only if it can
produce every class in it, and each exclusion is logged by name — an arm rigged
by a taxonomy mismatch is not coverage.

## Run order

Every stage reads the previous stage's output, and **no code edit is needed on
Kaggle**: Stage 1 finds GitReq and the frozen `splits.json` under
`/kaggle/input` on its own, recognising the archive by its contents rather than
its name, and refusing either if attached twice.

Five small Kaggle Datasets carry the inputs that are not notebook outputs:
`gitreq` (the figshare archive), `stage1-frozen-splits` (the committed
`splits.json`), and three resume stores — `predictions_finetuned.parquet`
(24,280 rows), `predictions_llm.parquet` (35,049) and
`predictions_subtype.parquet` (16,786) — so that nothing already computed is
recomputed.

| # | notebook | Kaggle settings | attach | time |
|---|---|---|---|---|
| 1 | `stage1-data-pipeline` | Internet **ON**, no GPU | `gitreq`, `stage1-frozen-splits` | ~1 min |
| 2 | `stage2-finetuned-baselines` | GPU **T4**, Internet ON | Stage 1 output, `resume-stage2` | ~14 h → **two sessions** |
| 3 | `stage3-llm-harnes` | GPU **T4 x2**, Internet ON, `HF_TOKEN` | Stage 1 output, `resume-stage3` | ~3–6 h |
| 4 | `stage3b-subtype-harness` | GPU **T4 x2**, Internet ON, `HF_TOKEN` | Stage 1 output, `resume-stage3b` | ~2–5 h |
| 5 | `stage3b-repair` | no GPU | Stage 3 + Stage 3b outputs | minutes |
| 6 | `stage4-analysis` | no GPU, Internet **OFF** | Stage 1 + final Stage 2 + repair outputs | minutes |
| 7 | `stage5-cost` | no GPU, Internet **OFF** | final Stage 2 + repair + Stage 4 outputs | minutes |

**Resume is verified, not assumed.** Against the frozen splits, Stage 2's two
resume guards pass (stored fold contents and epoch budgets both match), 228 of
its 340 planned runs are reused and 112 are new, and not one old fold is
retrained. Every pre-existing prompted evaluation cell — frame and core sample,
same ids in the same order — is identical, so Stages 3 and 3b generate only the
GitReq cells.

**No session is lost to Kaggle's 12-hour limit.** Stage 2 stops itself at
10.5 h with the store flushed; Stages 3 and 3b check a 10 h budget before each
model and each API provider, so phase 1 — the core comparison — completes for
every model before phase 2 is cut. Attach a stopped session's output as the next
session's input and it resumes. Stage 2's store is complete at exactly
**208,336 rows**; the new runs take about 14 GPU-hours, measured from the
committed store's own training times, so it needs two sessions.

## What changed per stage

* **Stage 1** — the GitReq loader (with the integrity gate that refuses the
  9,926-row look-alike circulating under the same name), `subtype_shared7`,
  GitReq's in-domain and cross-project arms, the label-set coverage rule, the
  fold-level split freeze, and `gitreq_marker_flags.csv`.
* **Stage 2** — `subtype_shared7` gets the 10-epoch sub-type budget; the
  preflight accepts both corpus shapes. The family list is derived from
  `splits.json`, so the new families arrive on their own.
* **Stage 3** — GitReq gets its own FR/NFR and security cells, so the prompted
  tier gains the arm the encoders gain and RQ1 stays like-for-like. A
  `full_set_cap` of 1,000 bounds the local-only full sets; the largest
  pre-existing frame is 968, so no existing cell is touched.
* **Stage 3b** — sub-type frames are keyed by the corpus they came from. They
  used to be filed under `"promise"` with no source filter, which was safe only
  while PROMISE was the sole sub-typed corpus; with GitReq that would have
  published its 5,769 NFRs as PROMISE results. `full_set_cap` 600, again above
  every PROMISE frame.
* **Stage 4** — `transfer_source` joins the cell key. A cross-dataset fold is
  tagged with its *test* corpus, so `secreq_to_promise` and `gitreq_to_promise`
  would have landed in one cell, scoring every item twice and blending two
  source corpora under a caption naming one.
* **Stage 5** — preflight only.
* **paper/scripts** — `get()` takes the transfer source and raises on an
  ambiguous lookup instead of silently taking the first row; GitReq cells are
  added only when three-corpus artefacts are present.

## Final review — are cross-project and cross-dataset achieved?

**In the code: yes, and verified end to end.** A synthetic three-corpus run —
the committed stores plus plausible rows for every new fold and cell
(`tests/three_corpus_fixture.py`) — was carried through Stage 3b-repair, Stage 4
and Stage 5. Every new arm reaches the result tables with the right `n` and no
double counting:

* **cross-dataset**: 10 transfers (was 2) — FR/NFR ×2, security ×6 (every
  ordered pair of three corpora), shared-7 ×2 — each with `n` equal to its
  target corpus, each named by its source in `tab2`, one gap row per source in
  `tab3`, and paired McNemar tests per source in `tab4`.
* **cross-project**: GitReq FR/NFR, security and shared-7, plus shared-7 on
  PROMISE_exp, alongside every original arm.

**In the results: not yet.** No model has been trained or prompted on a GitReq
fold until Stages 2, 3 and 3b run. The synthetic run proves the pipeline carries
the new arms; it says nothing about their numbers.

**Caveats the write-up must carry.** GitReq's grouping key is the repository —
4,079 of them over 6,300 rows — so its cross-project arm is close to an
item-level split, not the cross-document test SecReq's three specifications
give. And its FR/NFR arm is partly a surface-form probe (`gitreq_marker_flags.csv`).

**What the review found and fixed** — each reproduced first, then verified:

1. Stage 1's locator searched the working directory before `/kaggle/input` and
   picked up a modified `GitReq_NFR.csv`; the hash pin refused it, but it should
   never have been offered. Now `/kaggle/input` only, and never twice.
2. Stage 1 needed an environment variable Kaggle cannot set; the frozen
   `splits.json` is now discovered like GitReq.
3. Stage 3b-repair had no `subtype_shared7` label set — a KeyError on the first
   shared-7 row, so the harness's GitReq sub-type output would never have
   reached Stage 4.
4. Stage 4's transfer table would have crashed on its own assertion: two
   transfers into one corpus land in one column.
5. Stage 4's gap table took the max of two transfer sources.
6. Stage 4's McNemar tests kept whichever source Stage 2 wrote first.
7. Stage 4's sub-type table pooled PROMISE_exp and GitReq for shared-7.
8. Stage 5 and Stage 2's summary had no shared-7 label set, and would have
   scored it over the labels observed rather than the ones declared.
9. Stage 5's break-even figure picked a regime across all encoders and applied
   it to one — a latent IndexError in the original code, which the two-corpus
   rows happened to avoid.
10. The long stages had no session budget (above).

After all of it, the committed two-corpus run still reproduces exactly: all 17
Stage 4 tables (four gain one identifying column: `transfer_source`,
`encoder_source`, or `dataset`), all 5 Stage 5 tables, and both Stage 3b-repair
stores, byte-for-byte in every value.

## Not done yet, on purpose

`paper/main.tex` and `make_figs.py` still describe the two-corpus study, because
the three-corpus numbers do not exist until the runs above finish. The figures
encode a two-corpus narrative (SecReq → PROMISE prior shift) and need redesign,
not a search-and-replace, once there are results.

## Tests

```bash
GITREQ_ARCHIVE=/path/to/31669477.zip python3 tests/test_stage1_gitreq.py
GITREQ_ARCHIVE=... STAGE1_LOCAL_MIRROR=/dir/with/the/four/source/files \
    python3 tests/test_gitreq_consistency.py
THREE_CORPUS_UNIFIED=/path/to/unified.parquet python3 tests/test_downstream_gitreq.py
```

107 checks in total. They import the notebooks themselves rather than a copy, so
what is tested is what runs.

Verified while writing this: Stage 1 reproduces the committed corpus exactly and
all 107 committed folds survive unchanged; Stage 4 reproduces all 17 committed
tables byte-for-byte on the two-corpus stores; Stage 5 reproduces all 5; and the
paper's tables regenerate identically.
