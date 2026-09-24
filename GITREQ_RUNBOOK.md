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

Every stage reads the previous stage's output. Attach the GitReq archive as a
Kaggle Dataset; Stage 1 finds it under `/kaggle/input` on its own.

| # | notebook | Kaggle settings | attach |
|---|---|---|---|
| 1 | `stage1-data-pipeline` | Internet **ON**, no GPU | GitReq archive + the old `splits.json` |
| 2 | `stage2-finetuned-baselines` | GPU **T4**, Internet ON | Stage 1 output |
| 3 | `stage3-llm-harnes` | GPU **T4 x2**, Internet ON | Stage 1 output |
| 4 | `stage3b-subtype-harness` | GPU **T4 x2**, Internet ON | Stage 1 output |
| 5 | `stage3b-repair` | no GPU | Stage 3 + 3b output |
| 6 | `stage4-analysis` | no GPU, Internet **OFF** | everything above |
| 7 | `stage5-cost` | no GPU, Internet **OFF** | everything above |

### Attaching GitReq on Kaggle

*Add data* → upload the figshare item. The dataset can be named anything, and it
works whether Kaggle unpacks it or leaves it as a `.zip`: Stage 1 searches
`/kaggle/input` for the two member files, then for any archive that *contains*
them, so it is recognised by contents rather than by file name. If it still is
not found, the error lists everything attached under `/kaggle/input`, which is
usually enough to see what went wrong in one look.

Stage 1 environment variables:

```
STAGE1_GITREQ=/kaggle/input/<your-dataset>/31669477.zip   # or a directory
STAGE1_FREEZE_SPLITS=/kaggle/input/<old-stage1>/splits.json
STAGE1_REQUIRE_GITREQ=0                                   # reproduce the 2-corpus study
```

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
