# Corrections applied to the thesis chapters and slide decks

Every claim in Chapter 3 and in the Methodology deck was re-derived from the
pipeline artefacts (the Stage-1 manifest, the Stage-4/5 tables and the raw
prediction stores). The corpus and dataset figures in Chapter 2 all reproduced
exactly. The items below did not, and are now fixed in the four files in this
directory.

## Wrong as written

| # | Where | Was | Now | Why |
|---|---|---|---|---|
| 1 | §3.9 · deck s11 | encoder margin on the shared subset `+0.044 (0.9660 against 0.9216)` | `+0.036 (0.9660 against Llama-3.3-70B's 0.9298)` | On the 59 items every model answered, the best prompted model is **Llama-3.3-70B at 0.9298**, not Gemini at 0.9216 (`tab10_like_for_like.csv`). |
| 2 | §3.6 · deck s8 | exemplars "selected … from the **training folds only**" | exemplars "**carved out of the corpus** before the evaluation frames are formed" | Stage 3 has no folds. Exemplars are sampled from the same (task, dataset) frame and then removed from it. The conclusion — no test item ever appears in a prompt — still holds. |
| 3 | §3.1 · deck s4 | "every stage writes a versioned, **content-hashed** artefact" | "every stage writes a **versioned** artefact" | Only Stage 1 hashes anything, and it hashes the four *source files*. Stages 2–5 write no digests. |
| 4 | §3.5 · deck s6, s9 | splits "keyed by requirement identifiers **pinned to the SHA-256** of the source files" | "keyed by **stable requirement identifiers over source files that the manifest pins by SHA-256**" | `splits.json` contains zero hashes; the ids are ordinal (`promise_00000`). The SHA-256 pins are on the source files in the manifest. |
| 5 | deck s9 | "Every statistic was additionally re-derived … against scikit-learn / SciPy / **statsmodels** reference implementations (Δ = 0)." | "Metrics from scikit-learn; paired tests from SciPy's exact binomial; Holm and Benjamini–Hochberg computed in-notebook over the stored p-values." | **`statsmodels` appears in none of the seven notebooks**, and no Δ = 0 re-derivation block exists. The original sentence would not survive an examiner asking to see that check. |

## Right but imprecise

| # | Where | Correction |
|---|---|---|
| 6 | §3.4 | The unweighted control runs on the security task's **in-domain PROMISE_exp and cross-dataset families**, not on the whole task (3 of its cells). |
| 7 | §3.4 | "linear schedule" → "**linear decay with no warmup**" (`num_warmup_steps = 0`). |
| 8 | §3.5 | The prompted sample is a **300-item core per binary cell and 200 per sub-type cell (218 for all-11), floor of ten per class**. Only the six local models complete those cores; the rate-limited hosted and commercial arms complete less, which is why prompted cell sizes span **59–960**. |
| 9 | §3.6 · deck s8 | The three phrasings are a **two-model sub-study** (Gemma-2-2B, Qwen2.5-7B). The **hosted and commercial models ran zero-shot, base phrasing only**. Decoding is greedy (temperature 0, ≤ 12 new tokens). |
| 10 | §3.12 · deck s18 | Pareto frontier holds **10 cells** (not configurations — the same encoder appears at more than one regime); prompted models cost **9–47×** more per 1k, not 9–49× (0.1132 / 0.0024 = 47.2). |
| 11 | Table 3.4 | Added: the three regime rows are **not the same test population** — the 64 cross-dataset tests are the security task alone, the 106 in-domain tests span all five task variants. |
| 12 | §3.13 | Added: **N⁎ is a pure cost crossover computed regardless of the accuracy gap**, and the ×1/×8/×32 batching grid is **assumed, not measured**. |
| 13 | §2.8, §2.9 · LR deck s12 | The cross-dataset arm is possible **only for the security task**, the one task both corpora annotate — SecReq carries no FR/NFR or sub-type labels. RQ2 now says so. |

## Checked and correct — no change needed

PROMISE_exp 969 raw (444 FR / 525 NFR), SecReq 510 raw (187 security / 323
non-security), 67 duplicates removed, 968 + 444 = 1,412 in 50 project groups,
the eleven sub-type class counts, 14 split families / 107 folds, 76,115
predictions (24,280 + 35,049 + 16,786), 81 of 87 cells reportable, 260 McNemar
tests (175 raw / 170 BH / 131 Holm significant), the 67–39–0 and 3–13–48 verdict
splits, 76 of 90 cross-project, the 2.7–10.1 and 24.7-point gaps, 42.8% / 22.7% /
17.4% relative drops, the prior-shift per-class numbers (0.847 → 0.210 precision,
0.888 → 0.720 recall, 44.2% predicted vs 12.9% true), every few-shot and
prompt-sensitivity figure, $0.0024 per 1k, $0.0093 median training, 277 GPU-s,
break-even 46–552 (median 215) over 276 pairs.

The claims in Chapter 2 about the ten reviewed papers were **not** verifiable
from this repository — they describe other authors' work. Worth re-reading the
characterisation of Binkhonain & Alfayaz in particular, since the research gap
rests on it.
