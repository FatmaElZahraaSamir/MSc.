# Defense numbers sheet

Every figure below is read back from the stored stage artefacts, not transcribed
from the draft. They are internally consistent. What trips people up is that
several *different* quantities happen to look alike — those are listed first.

Sources are named per row: `tab*.csv` files live in `results Stage4 analysis.zip`,
`cost*.csv` in `results Stage5 cost.zip`, corpus figures in
`results stage1_data_pipeline.zip`.

---

## The one-sentence anchor

Twelve configurations — four fine-tuned encoders, eight prompted LLMs — classify
**1,412** requirements across three tasks and three regimes. **76,115**
predictions, one strict scorer, **260** paired McNemar tests corrected as a
single family. In-domain the encoders win **67** and lose **none**.
Cross-dataset the same comparisons flip: prompted models win **48 of 64**. The
cause is an uncalibrated class prior, and *both* families have it. Encoders are
still **9–47×** cheaper.

---

## 1. The look-alikes

### 444 appears twice, meaning two different things
| | |
|---|---|
| 444 | SecReq requirements after de-duplication (from 510 raw) |
| 444 | Functional requirements in PROMISE_exp (968 = 444 FR / 524 NFR) |

Coincidence, not an error. Name the corpus when you say it.

### 42.8% vs −43
Same number, two roundings: 0.9235 → 0.5279 is a 42.8% relative loss, shown as
`−43` in the transfer table. Never quote them as two findings.

### 0.908 / 0.923 / 0.936 — three different "best encoder"
| | |
|---|---|
| 0.908 | BERT-w, FR/NFR, PROMISE_exp, in-domain |
| 0.923 | BERT-w, **security**, PROMISE_exp, in-domain — *this* is the one that collapses to 0.528 |
| 0.936 | RoBERTa-w, NFR sub-types top-4 — the highest number in the study |

### 0.836 vs 0.846 — the one cell an LLM leads
BERT-w scores 0.836 on SecReq security; 4-bit Qwen2.5-7B scores 0.846. The lead
is **not significant** — exact McNemar p = 0.696, BH-adjusted 0.774. Say
"better point estimate, statistically a tie."

### Three verdict triples, one per regime
| Regime | Encoder wins – ties – losses | Tests |
|---|---|---|
| In-domain | 67 – 39 – 0 | 106 |
| Cross-project | 38 – 38 – 14 | 90 |
| Cross-dataset | 3 – 13 – 48 | 64 |

106 + 90 + 64 = 260. The paper's "ahead or tied in 76 of 90" is 38 + 38, not a
separate count.

### 1,412 / 76,115 / 47,663
| | |
|---|---|
| 1,412 | **Requirements** in the unified corpus |
| 76,115 | **Predictions** in the store: 24,280 encoder + 35,049 prompted binary + 16,786 prompted sub-type |
| 47,663 | Analysis head: 24,280 encoder + 23,383 prompted |

Requirements ≠ predictions. Each requirement is scored many times, by many
models, in many regimes.

### 12.9% / 39.9% / 44.2% / 21.4%
| | |
|---|---|
| 12.9% | **True** security prevalence in PROMISE_exp (125 of 968) |
| 39.9% | **True** security prevalence in SecReq |
| 44.2% | **Predicted** by the transferred BERT on PROMISE items |
| 21.4% | Prevalence in the merged corpus — descriptive only |

44.2% is the only one that is a model output. That is the whole mechanism.

### Precision collapses, recall holds — do not swap them
| | |
|---|---|
| 0.847 → 0.210 | Security-class **precision**, in-domain → cross-dataset |
| 0.888 → 0.720 | Security-class **recall**, same two cells |

"It still finds the security requirements, it just cannot stop finding them."
Reverse these two and the argument for prior shift disappears.

### 0.044 vs 0.485 — prompt wording
0.044 is the **median** macro-F1 spread across base/terse/verbose over nine
paired cells; 0.485 is the **extreme** (Gemma-2-2B on SecReq security:
0.827 / 0.343 / 0.828). Lead with the median, then give the extreme as mechanism.

### Two small ranges that swap easily
46–552 is a count of **items** (break-even volume). 9–47× is a **cost ratio**.

### 12 / 9 / 8 models
12 reported configurations = 4 encoder variants + 8 prompted LLMs. Nine prompted
models were run; the ninth (Nemotron 3 Nano 30B A3B) failed the reportability
gate and enters no table.

### 175 / 170 / 131 significant
Raw / after Benjamini–Hochberg / after Holm. **Verdicts key on BH.** All 260
corrected as one family, not per table.

### 36 vs 34 encoder cells
36 encoder cells are included in the main in-domain/transfer tables; 34 encoder
cells sit among the 81 reportable cells the cost stage reads. Different views,
both correct.

---

## 2. Every number, addressed

### Corpus and splits — Stage 1
| Value | What it is |
|---|---|
| 1,412 | Requirements in the unified corpus after de-duplication |
| 1,479 | Raw rows before de-duplication (969 + 510) |
| 67 | Exact duplicates removed; none shared between corpora |
| 969 → 968 | PROMISE_exp raw → final |
| 510 → 444 | SecReq raw → final |
| 444 / 524 | FR / NFR split in PROMISE_exp |
| 50 | Project groups (47 PROMISE projects + 3 SecReq specifications) |
| 12.9% / 39.9% / 21.4% | Security prevalence: PROMISE_exp / SecReq / merged |
| 54.2% | True NFR share on the FR/NFR task |
| 524 / 433 / 353 | Item counts for all-11 / top-6 / top-4 sub-type variants |
| 42 | Random seed — splits, bootstrap, everything |

### Store, gate and tests — Stages 3b–4
| Value | What it is |
|---|---|
| 76,115 | Total predictions scored under one strict rule |
| 24,280 / 35,049 / 16,786 | Encoder / prompted binary / prompted sub-type |
| 47,663 | Analysis head (24,280 encoder + 23,383 prompted) |
| 14 / 107 | Frozen split families / total folds |
| 87 → 81 | Cells total → reportable (6 fail the gate) |
| 260 | Exact McNemar tests, corrected as one family |
| 106 / 90 / 64 | Tests per regime |
| 175 / 170 / 131 | Significant raw / BH / Holm, α = 0.05 |
| 2,000 | Stratified bootstrap resamples, within each true class |
| 99.98% | Share of the 11,518 phrasing sub-study responses the parser accepted |

Gate: every class ≥ 5 test items, cell ≥ 40 items, parse rate ≥ 50%.

### RQ1 — in-domain macro-F1
| Value | What it is |
|---|---|
| 67 – 39 – 0 | In-domain verdicts over 106 tests |
| 0.908 | BERT-w, FR/NFR, PROMISE_exp |
| 0.923 | BERT-w, security, PROMISE_exp |
| 0.936 / 0.837 / 0.724 | RoBERTa-w, sub-types top-4 / top-6 / all-11 |
| 0.836 vs 0.846 | BERT-w vs Qwen2.5-7B, SecReq security (p = 0.696) |
| 0.900 vs 0.891 | Gemma-2-2B (2.6 B) beats the hosted 70 B on PROMISE security |
| 0.554 – 0.727 | Range of the six small open models on FR/NFR |
| +0.014 / +0.013 / +0.095 | Encoder advantage on top-4 / top-6 / all-11 |
| 0.966 vs 0.930 | Top-4 recomputed on the 59 items every model answered (+0.036) |
| 0.351 / 0.466 / 0.376 | Majority baselines: FR/NFR, PROMISE sec, SecReq sec |
| 0.131 / 0.075 / 0.035 | Majority baselines: sub-types top-4 / top-6 / all-11 |

### RQ2 — transfer
| Value | What it is |
|---|---|
| 3 – 13 – 48 | Cross-dataset verdicts over 64 tests — the inversion |
| 38 – 38 – 14 | Cross-project verdicts over 90 tests |
| 0.923 → 0.528 (−42.8%) | BERT-w, PROMISE security — the headline collapse |
| 0.902 → 0.698 (−23%) | RoBERTa-w, same transfer |
| 0.907 → 0.534 (−41%) | BERT unweighted — weighting is not the cause |
| 0.903 → 0.707 (−22%) | RoBERTa unweighted |
| −17% / −16% | Reverse direction (SecReq): BERT-w 0.836 → 0.690; RoBERTa-w 0.824 → 0.696 |
| −3% to −12% | Cross-project cost on PROMISE |
| −30% | Worst cross-project drop: BERT-w on SecReq, 0.836 → 0.588 |
| −0.034 to +0.163 | How far the prompted models move between corpora |
| 37 | Projects with comparable coverage in the LOPO arm |
| 0.000 / 1.000 | Every configuration has a project it scores 0 on and one it scores 1 on |
| 0.917 (sd 0.198) | Encoder per-project median accuracy on LOPO |
| 0.545 – 0.750 | Per-project medians, small open models (sd 0.213–0.301) |

### The mechanism — class prior
| Value | What it is |
|---|---|
| 44.2% vs 12.9% | Predicted vs true security rate after transfer |
| 0.847 → 0.210 | Security-class precision |
| 0.888 → 0.720 | Security-class recall |
| 19.7% | RoBERTa's predicted rate — carries less of the source prior |
| 33.6% / 29.1% | Reverse direction: both encoders predict *below* the 39.9% target |
| ρ = 0.95 | Spearman: prompted accuracy vs prior miscalibration, 8 models |
| 14.9% – 43.4% | How often prompted models answer NFR (true share 54.2%) |
| 0.044 / 0.485 | Median / extreme phrasing spread |
| 96.7% / 51.3% | Terse-wording security rate, Gemma-2-2B on SecReq / PROMISE (true 39.7% / 12.7%) |
| +0.024 | Median few-shot gain over 90 paired comparisons |
| −0.007 / +0.062 | Few-shot mean: binary (54) vs sub-types (36) |
| −0.027 / +0.114 | Mean of BH-significant few-shot effects: 30 binary, 14 sub-type |

### RQ3 — cost and latency
| Value | What it is |
|---|---|
| $0.0024 | Encoder inference per 1,000 classifications |
| $0.0216 – $0.1132 | Prompted inference per 1,000 (median $0.0439) |
| 9 – 47× | Cost multiplier (18× at the medians) |
| $0.0093 | Median one-off fine-tuning cost (~277 GPU-seconds over all folds) |
| 46 – 552 | Break-even in items; median 215; finite in all 276 pairings |
| 276 | Encoder-versus-alternative pairings |
| 10 / 9 | Pareto-frontier cells / how many are encoders |
| +0.011 for ≈19× | The single prompted frontier point (Qwen2.5-7B, SecReq security) |
| 0.016 s | Median encoder latency |
| 0.095 / 0.19–0.36 / 0.61 s | Median latency: hosted 70 B / local 4-bit / commercial |
| $0.5260/h | AWS g4dn.xlarge on-demand rate used to impute local GPU cost |
| $0.25 / $1.50 | Gemini 3.1 Flash-Lite per million input / output tokens |
| $0.59 / $0.79 | Llama-3.3-70B per million input / output tokens |

---

## 3. If they ask

**"Why does the ranking flip? Isn't that just noise?"**
260 *paired* tests on identical items with one scorer, corrected as a single
family. In-domain: 67 encoder wins, 0 losses. Cross-dataset: 48 losses, 3 wins.
Noise does not produce a clean sign reversal at that scale. One thing changes
between the regimes: how much distribution shift sits between training and test.

**"Isn't the collapse just unfamiliar vocabulary?"**
That was the competing hypothesis, and the per-class evidence separates them. If
it were vocabulary, precision and recall would fall together. Instead precision
goes 0.847 → 0.210 while recall only goes 0.888 → 0.720, and the model labels
44.2% of items security against a true 12.9% — close to the 39.9% prior of the
corpus it trained on. That is base-rate shift.

**"Your corpora are small, old and public. Isn't contamination fatal?"**
It cuts in our favour. Contamination inflates the *prompted* models in-domain,
which is exactly where we report the encoders winning, so the measured encoder
advantage is conservative. And it cannot manufacture the cross-dataset reversal,
because it would help the prompted models equally in both regimes.

**"Why is the commercial model 'never significantly beaten'? Small n?"**
Yes, and it is in Threats. That arm ran at n ≈ 60 per cell under free-tier quota,
and 23 of its 26 paired comparisons are inconclusive. Limited power, reported as
a limitation rather than a result.

**"Why strict parsing? Isn't that unfairly harsh on the LLMs?"**
Deliberately harsher than prior work — in deployment an unusable answer is not a
free pass. But it does not drive the result: the parser accepted 99.98% of the
sub-study's 11,518 responses, so the answers were well-formed and simply wrong.

**"Why not just fix the prior with threshold adjustment?"**
It would change the quantity being measured. The claim is about what the field's
current protocol reports. We name prior correction as the obvious next step and
cite the method; it needs no labels from the target corpus, which is what makes
the diagnosis encouraging.

**"Cross-dataset shift is also definitional, not just distributional."**
Agreed, and it is in Threats. PROMISE_exp's security label derives from the SE
sub-class and is non-functional by construction; SecReq annotates any
security-relevant sentence. A practitioner moving corpora meets exactly this
mixture, but the effect should not be read as purely distributional.

**"What should a practitioner actually do?"**
With a few hundred labelled requirements from the target domain and any
non-trivial volume: fine-tune a 110 M-parameter encoder — most accurate and by
far the cheapest, repaid within 46–552 items. Entering an unlabelled or shifting
domain: a mid-size quantised open model degrades more gracefully and runs free on
one consumer GPU. The worst option is the implicit default of recent work —
fine-tune on one corpus and assume it transfers.

**"What is the contribution, in one line?"**
The evaluation regime is part of the claim. Two protocols the field treats as
interchangeable return opposite rankings from the same data, the same items and
the same scorer.

---

## 4. When a number will not come

1. **Give the direction and the order of magnitude, never a guess.** "It loses
   roughly forty percent of its macro-F1" is defensible; a wrong third decimal
   is not.
2. **Name the address, then offer the table.** "That is the cross-dataset row
   for class-weighted BERT on PROMISE security — Table III."
3. **Never invent a second decimal under pressure.** If you have 0.92, say 0.92.
4. **Anchor everything to one sentence:** in-domain the encoders win,
   cross-dataset they lose, and the cause is a class prior neither family
   calibrates. Every number in the study is evidence for that one claim.
