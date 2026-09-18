# Supervisor references — 16 Sep 2026

Four references sent by Dr. Lamia, with three remarks attached to them. This note
records what each reference is, what the remark behind it is asking of our paper
(*Fine-Tuned Encoders or Prompted LLMs for Requirements Classification? The
Verdict Inverts Under Distribution Shift*), and what we should do about it.

| # | Reference | Dr. Lamia's remark | Status |
|---|---|---|---|
| 1 | ACM `10.1145/3786176.3788340` | "the structure of the requirement also differs — user story vs app review; user story with acceptance criteria vs ambiguous requirement" | **not retrieved** — `dl.acm.org` is blocked by the session's egress policy; title needed |
| 2 | arXiv 2508.08868 — *QuRE* | (same structural remark) | read (arXiv full text) |
| 3 | IEEE `11190244` — *One Size Does Not Fit All* | "the size of the number of requirements to classify in the prompt may vary the results" | identified; abstract + programme only (`ieeexplore.ieee.org` blocked) |
| 4 | Procedia CS `S1877050925031631` — ensemble | "encoder transformers can be improved" | identified; abstract only (`sciencedirect.com` blocked) |

The three remarks are not three unrelated comments. They all say the same thing
about our experimental design: **we vary model family × task × regime, and hold
three other factors constant without testing them** — the *structure* of the
requirement text, the *number of requirements per prompt*, and the *strength of
the encoder baseline*. Each is a possible alternative explanation, or a boundary
condition, for our headline claim.

---

## 1. Requirement structure as a held-constant factor (remark + ref. 1, 2)

**What the remark means for us.** Our cross-dataset arm attributes the inversion
to an uncalibrated class prior: security is 12.9 % of PROMISE_exp and 39.9 % of
SecReq, and the transferred encoder reproduces its training prior (44.2 %
predicted vs. 12.9 % true). §Threats already concedes *definitional* shift
(PROMISE_exp's security label derives from the `SE` sub-class; SecReq annotates
any security-relevant sentence). Dr. Lamia is pointing at a third axis we never
name: the two corpora also differ in **artefact form**. A `shall`-style
specification sentence, a user story with acceptance criteria, and a free-text
app review are different objects, and a classifier that transfers badly may be
failing on form, not only on prior.

**Why this is an opportunity, not just a threat.** We already show the failure is
*not* unfamiliar vocabulary. If we can also show the two corpora are
*structurally* comparable while differing three-fold in prior, the causal story
gets much stronger: it is the prior, not the prose. QuRE gives us the instrument
to do this without running a single model.

**QuRE (ref. 2) — Femmer, Houdek, Unterbusch & Vogelsang, arXiv:2508.08868.**
2,111 industrial requirements from Mercedes-Benz specifications, labelled through
a real review process used contractually for ~5 years; ~30 % carry a defect, over
23 "weak word" categories. The paper's contribution that matters to us is not the
data but the **comparative analysis**: it profiles requirement corpora on

* lexical complexity — vocabulary richness, lexical diversity, lexical density
* syntactic complexity — sentence length, clause count, dependency-parse depth
* readability — Flesch–Kincaid grade level

across PURE, PROMISE, a 445-item security set, a 1,673-item user-story set,
GPT-4-generated synthetic requirements, and the Brown corpus as a generic-English
floor. Findings: real industrial requirements are syntactically far more complex
than synthetic ones; real corpora cluster at lexical diversity ≈ 0.11–0.15 while
GPT-4-generated ones sit at 0.18–0.28; QuRE reads at ~grade 11 vs. grade 6–8 for
synthetic text.

**Caveat.** QuRE's labels are *quality defects*, not FR/NFR or security. It is
**not** a drop-in third corpus for our three tasks. Its three uses for us are:
(i) the metric protocol above, applied to our own corpora; (ii) a citable,
industrial-provenance argument for our contamination threat (§Discussion) and
against the field's reliance on two ageing public corpora; (iii) a possible new
task — requirement quality / ambiguity detection — which is exactly the
"user story with acceptance criteria vs. ambiguous requirement" contrast.

**Action (P0, no GPU).** Compute QuRE's metric set on PROMISE_exp and SecReq and
report it in §Corpus, next to the prevalence contrast. Two outcomes, both good:
structurally similar → the prior explanation is isolated and the paper is
stronger; structurally different → we report it as a co-varying factor, which is
honest and pre-empts the reviewer who would have raised it.

**Action (P2, next study).** Turn structure into a *manipulated* variable rather
than a confound: the same label set over (a) formal `shall` specifications,
(b) user stories with acceptance criteria, (c) app-store reviews, (d) ambiguous
industrial text. That is the natural second study of the thesis, and reference 1
is presumably where the taxonomy should come from — **its title is still needed**.

---

## 2. Batch size in the prompt (remark + ref. 3)

**Reference.** *One Size Does Not Fit All: On the Role of Batch Size in
Classifying Requirements with LLMs* — van Can, Aydemir & Dalpiaz, AIRE'25
(IEEE Xplore 11190244). Three locally-deployable decoder LLMs
(Llama-3.1-8B-Instruct, Gemma-3-12B, DeepSeek-R1-Distill-Qwen-14B) × four
requirement datasets × seven batch sizes (1, 2, 4, 8, 16, 32, 64), classifying
functional vs. quality requirements. Reported findings: batch size materially
affects performance, no single batch size is best across models/datasets, and
quality requirements are harder than functional ones. *(Abstract and workshop
programme only — the full PDF is behind a blocked domain; the per-dataset numbers
must be checked against the paper before we cite specifics.)*

**Where this hits us — twice.**

1. *Accuracy.* §Prompting fixes one requirement per call: "sent as a single user
   message", greedy decoding, ≤ 12 new tokens. Batch size is therefore silently
   pinned at 1 across all eight prompted configurations. Our two sub-studies vary
   phrasing and shot count — this is a third factor of the same kind, and we
   already show the prompted arm is highly sensitive to such factors (re-wording
   alone moves macro-F1 by up to 0.485).
2. *Cost — and this is the sharper one.* Our RQ3 is the paper's differentiator,
   and `Stage5` prices local inference as "wall-clock seconds × hourly rate",
   with the code comment explicitly stating it "assumes sequential unbatched
   inference". Batching amortises the instruction block across items, so
   per-item input tokens and per-item wall-clock both fall. The encoders'
   9–47× cost advantage and the break-even range N\* = 46–552 items are computed
   against the *worst case* for the prompted arm. A reviewer holding this paper
   will ask whether batching closes the gap. Better we answer it than they do.

**A hypothesis worth testing, not just a threat.** Our diagnosis is that the
prompted models mis-set the class prior from the wording of the question. In a
batch, the model sees several requirements at once, so the batch's own class mix
becomes visible context. Batching could therefore *partially self-calibrate* the
prior — or push the model towards spreading labels across the batch. Either
result is a genuine finding, and it links our prior-calibration story to ref. 3's
batching story. No one has run that.

**Action (P0).** Cite the paper, state batch = 1 as a scope decision in
§Prompting, and add the cost consequence to §Threats (Construct).
**Action (P1).** Sub-study: b ∈ {1, 4, 16, 32} on two local models plus the
commercial model, FR/NFR + security, measuring macro-F1 **and** $/item, plus
predicted-prior drift per batch size. Contained, reuses the existing harness and
scorer, and defends RQ3 on its own ground.

---

## 3. "Encoder transformers can be improved" (remark + ref. 4)

**Reference.** *Large Language Model for Requirements Classification: An Ensemble
Approach* — Procedia Computer Science (KES 2025), `S1877050925031631`. Seven
encoders — BERT, DistilBERT, DistilRoBERTa, ELECTRA, DeBERTaV3, RoBERTa, XLNet —
evaluated on binary requirements classification over a newly collected dataset,
then combined by ensemble learning; the ensemble outperformed every individual
model. *(Abstract only — `sciencedirect.com` is blocked; the dataset and the
per-model F1 figures need to be read before citing numbers.)*

**Where this hits us.** Our encoder tier is `bert-base-uncased` and
`roberta-base`, weighted and unweighted — four variants, both 110–125 M
parameters, both 2019 checkpoints. The obvious reviewer objection to "encoders
win in-domain, lose across corpora" is: *your encoder was simply not the best
encoder — try DeBERTaV3, or an ensemble.*

**Our answer should be a prediction, not a defence.** We diagnose the
cross-dataset failure as an inherited class prior, not as insufficient capacity.
An ensemble of encoders trained on the *same* corpus inherits the *same* prior,
so it should improve in-domain accuracy and **still** invert under cross-dataset
transfer. That is falsifiable and cheap to test — encoders are small, and the
Stage-2 pipeline already trains them.

**Action (P1a).** Add DeBERTaV3-base (and optionally ELECTRA) to the encoder tier
and a soft-vote ensemble over the tier; run the same three regimes. If the
prediction holds, the "weak baseline" objection dies permanently.
**Action (P1b), the natural companion.** We already cite Saerens et al. (2002) on
prior adjustment but never apply it. Apply prior correction / threshold
re-tuning to the transferred encoder and report how much of the 42.8 % macro-F1
loss it recovers. That converts the paper's diagnosis into a remedy —
*the fix is calibration, not capacity* — and is the strongest single addition
available to us.

---

## Priority

| | Work | Cost | Why |
|---|---|---|---|
| **P0** | Cite refs 2–4; state batch = 1 in §Prompting; batching caveat in §Threats (Construct); QuRE metric profile of our two corpora in §Corpus | hours, no GPU | closes three reviewer objections; strengthens the prior-vs-prose argument |
| **P1a** | DeBERTaV3 + soft-vote ensemble through all three regimes | ~1 free-tier GPU day | kills the "weak encoder baseline" objection |
| **P1b** | Saerens prior correction on the transferred encoder | hours | turns the diagnosis into a remedy |
| **P1c** | Batch-size × cost sub-study, b ∈ {1,4,16,32} | ~1 GPU day + quota | defends RQ3, and tests batch-as-prior-calibration |
| **P2** | Structure as a manipulated variable: shall-statements / user stories + acceptance criteria / app reviews / ambiguous industrial text | new study | the thesis' second paper |

## Open items

* **Reference 1 is unidentified.** `dl.acm.org` is blocked by this session's
  egress policy, so `10.1145/3786176.3788340` could not be resolved to a title,
  and it should not be guessed. Needed: the title, or the PDF.
* Refs 3 and 4 were read from abstracts and secondary sources only. Any number we
  quote from them must be checked against the published PDFs first.
