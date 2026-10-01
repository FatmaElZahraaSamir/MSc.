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
| 2 | `stage2-finetuned-baselines` | GPU **T4 x2** (it trains on one; the second idles), Internet ON | Stage 1 output, `resume-stage2` | ~14 h → **two sessions** (measured: 10.5 h + ~3 h) |
| 3 | `stage3-llm-harnes` | GPU **T4 x2**, Internet ON, `HF_TOKEN` | Stage 1 output, `resume-stage3` | ~3–6 h |
| 4 | `stage3b-subtype-harness` | GPU **T4 x2**, Internet ON, `HF_TOKEN` | Stage 1 output, `resume-stage3b` | ~2–5 h |
| 5 | `stage3b-repair` | no GPU | Stage 3 + Stage 3b outputs | minutes |
| 6 | `stage4-analysis` | no GPU, Internet **OFF** | Stage 1 + final Stage 2 + repair outputs | minutes |
| 7 | `stage5-cost` | no GPU, Internet **OFF** | final Stage 2 + repair + Stage 4 outputs | minutes |

### Where the run stands, and what may run at the same time

Stage 1 and Stage 2 session 1 have both been run. Confirmed from their logs:

| stage | state | output it produced |
|---|---|---|
| 1 `stage1-data-pipeline` | **done** | `data_processed/` - `unified.parquet` (7,712 rows), `splits.json` (22 families, 155 folds), 15 of 18 RQ2 cells covered |
| 2 `stage2-finetuned-baselines` | **85 of 112 new runs** | `predictions_finetuned.parquet` (146,329 rows; complete at 208,336) |
| 3, 3b, repair, 4, 5 | not started | - |

The 340-run plan reconstructs exactly: 2 models x 155 folds = 310 weighted, plus
2 x (10 `cross_dataset` + 5 `in_domain_security_promise`) = 30 unweighted. 228
were already committed, 85 ran in session 1, so **27 remain**. Priced at the
per-run times session 1 itself measured, session 2 is **3.2 h**, and five
`xproj_subtype_shared7_gitreq` folds are 5,187 s of that - 10 epochs on ~4,600
training rows is simply the expensive corner of the plan.

**Stages 2, 3 and 3b are independent of one another and may run concurrently.**
Not a guess - each one's `glob("/kaggle/input/**/<name>")` calls were read, and
none of the three reads an artefact another produces:

```
stage 1 ── unified.parquet + splits.json
             │
             ├─→ stage 2   (+ its own predictions_finetuned resume)   ─┐
             ├─→ stage 3   (+ its own predictions_llm resume)         ─┤ any order,
             └─→ stage 3b  (+ its own predictions_subtype resume)     ─┘ or together
                                  │
                   stage 3 + stage 3b ─→ stage 3b-repair
                                              │
       stage 1 + final stage 2 + repair ─→ stage 4 ─→ (tab9) ─→ stage 5
```

So the three long GPU jobs can be started in any order, or in parallel if Kaggle
grants a second GPU session; what cannot move is that **repair waits for both 3
and 3b**, **stage 4 waits for the FINAL stage 2 and repair**, and **stage 5 waits
for stage 4's `tab9_evaluability.csv`**. Stages repair, 4 and 5 need no GPU.

Remaining GPU cost is about 3.2 h (stage 2 session 2) + 3-6 h (stage 3) + 2-5 h
(stage 3b) = **9-15 h**, inside one week of Kaggle's ~30 GPU-h allowance.

**Resume is verified, not assumed.** Against the frozen splits, Stage 2's two
resume guards pass (stored fold contents and epoch budgets both match), 228 of
its 340 planned runs are reused and 112 are new, and not one old fold is
retrained. Every pre-existing prompted evaluation cell — frame and core sample,
same ids in the same order — is identical, so Stages 3 and 3b generate only the
GitReq cells.

### The API tier changed under us: Groq retired Llama-3.3-70B

On **16 August 2026** Groq moved `llama-3.3-70b-versatile` and
`llama-3.1-8b-instant` to enterprise-only. A free or developer key now gets
`model not available` for both, which is exactly what the 24 September probe
reported. The paper's `open_hosted` tier was that Llama, with **870 committed
rows**.

What the notebooks now do about it:

* Both harnesses probe **`qwen/qwen3.8-27b` first** (then `qwen3.6-27b`,
  `gpt-oss-120b`, `gpt-oss-20b`), all at their published list prices. The order
  is pinned rather than cheapest-first so Stage 3 and Stage 3b cannot resolve to
  two different hosted models and put their tables in contradiction.
* The 870 Llama rows are **kept, not replaced**: the substitute gets its own
  `model_tag` (`groq-qwen3.8-27b`), so nothing overwrites anything. Report
  Llama-3.3-70B at the coverage it has, and say the provider retired it
  mid-study.
* `report_retired_api_models()` now **prints** any committed API model the run
  cannot reach, with its row count, and records it in `stage3_manifest.json`
  under `api_models_retired_since_committed_run`. Previously this was silent.
* An OpenRouter `:free` route is priced 0.0/0.0 **by rule**, so it is no longer
  reported as an estimate — a free route's rate is a fact, not a guess.
* `price_override_for()` resolves an id written either way (`qwen/qwen3.8-27b`
  or `qwen3.8-27b`), and declines to guess if two providers share a short name
  at different rates.

> **Attach the resume store, or lose the Llama rows.** Without
> `predictions_llm.parquet` under `/kaggle/input`, Stage 3 starts from scratch
> and `groq-llama-3.3-70b-versatile` simply will not exist in the results — no
> re-run can recreate it, because Groq will not serve the model. The notebook
> now says so in a banner instead of a one-line log message.

**No session is lost to Kaggle's 12-hour limit.** Stage 2 stops itself at
10.5 h with the store flushed; Stages 3 and 3b check a 10 h budget before each
model and each API provider, so phase 1 — the core comparison — completes for
every model before phase 2 is cut. Attach a stopped session's output as the next
session's input and it resumes. Stage 2's store is complete at exactly
**208,336 rows**; the new runs take about 14 GPU-hours, so it needs two sessions.

Session 1 has now been run and confirms it. It stopped itself on the budget
after **85 of the 112 new runs**, flushed the store at **146,329 rows**, and
printed the resume instruction — the designed behaviour, not a failure. What is
left is 27 runs, dominated by five `xproj_subtype_shared7_gitreq` folds at
~1,050 s each (10 epochs on ~4,600 training rows); at the per-run times session
1 measured, session 2 is roughly **2.5-3.5 h**, well inside one sitting.

**Session 2, step by step.** Create a NEW notebook from the current
`stage2-finetuned-baselines.ipynb` (Create -> New Notebook -> File -> Import
Notebook) rather than re-running the session-1 page: the session-1 version stays
untouched as the record of what produced the first 146,329 rows, and nothing
depends on Kaggle letting a notebook mount its own output. Attach exactly two
inputs - Stage 1's output and **session 1's output** - and not `resume-stage2`
(or `stage2-outputs`): two files called `predictions_finetuned.parquet` trip the
`DUPLICATE` guard rather than being picked between. The preflight should read
`146,329 rows ... -> this is a PARTIAL GitReq store - resume Stage 2 from it`,
then `Plan: 340 runs total, 27 remaining`. It is finished at `(208336 rows)`,
and **that notebook's output is "the final Stage 2" for Stages 4 and 5**.

Updating Stage 2's code between the sessions changes no number: the two
changes are the epochs log line and the preflight messages. The preflight now
also refuses a partial store (24,280 < n < 208,336) in Stages 4 and 5, and the
two-corpus store beside the GitReq corpus; before, both ran and would have
scored half the encoder cells.

**A missing input now stops every stage in its first seconds.** Stage 2
session 2's first attempt ran with nothing attached: the check printed
`(not attached)` for every file, then `No duplicates. Running the stage now.`,
and the stage died 30 s later in a traceback. Only Stage 5 treated a missing
file it reads as a hard stop; Stages 2, repair and 4 now carry the same rule,
word for word. It matters most for Stage 2, where Stage 1 attached without the
resume store did not fail at all - it retrained the whole 340-run plan from
zero (~18 GPU-hours), and the 228 published runs would have come back with
different numbers, GPU training not being bit-reproducible. Stages 3 and 3b
likewise stop when their store is missing, unless `allow_fresh_start` is set
for a deliberate rebuild, and every stage refuses a store that is attached but
unreadable instead of starting over. **Before Save Version, check that the
editor's Input panel lists every input** - an empty panel is exactly the
failure above.

**Stages 3 and 3b must be run from the current files.** Each maps every
evaluation cell to a fine-tuned comparator label (`COMPARABLE_FT_FOLD`), and
the map named only the two original corpora: `fr_nfr/gitreq`, `security/gitreq`,
`subtype_shared7/gitreq` and `subtype_shared7/promise` would have been written
as `unmapped`, and each harness's final gate fails the run over one such row -
after the full 3-6 h. The four labels are added (the three committed ones per
harness are unchanged, and no later stage reads the label), and a check now
stops the harness before any model loads if a frame is ever unmapped again.

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
