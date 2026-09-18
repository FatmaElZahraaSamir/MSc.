# Supervisor references — 16 Sep 2026

Four references sent by Dr. Lamia, with three remarks attached to them. This note
records what each reference is, what the remark behind it is asking of our paper
(*Fine-Tuned Encoders or Prompted LLMs for Requirements Classification? The
Verdict Inverts Under Distribution Shift*), and what we should do about it.

| # | Reference | Dr. Lamia's remark | Read from |
|---|---|---|---|
| 1 | Tamale, Tuape & Kasurinen, *Application of LLMs in Requirements Classification: A Literature Survey with perspective from Uganda's Software Practitioners*, SEiGS '26 (`10.1145/3786176.3788340`) | "the structure of the requirement also differs — user story vs app review; user story with acceptance criteria vs ambiguous requirement" | full PDF |
| 2 | Femmer, Houdek, Unterbusch & Vogelsang, *QuRE*, arXiv:2508.08868 | (same structural remark) | full text |
| 3 | van Can, Aydemir & Dalpiaz, *One Size Does Not Fit All: On the Role of Batch Size in Classifying Requirements with LLMs*, AIRE '25 (IEEE 11190244) | "the size of the number of requirements to classify in the prompt may vary the results" | abstract + programme only |
| 4 | *LLM for Requirements Classification: An Ensemble Approach*, Procedia CS / KES '25 (`S1877050925031631`) | "encoder transformers can be improved" | abstract only |

The three remarks are not three unrelated comments. They all say the same thing
about our experimental design: **we vary model family × task × regime, and hold
three other factors constant without testing them** — the *structure* of the
requirement text, the *number of requirements per prompt*, and the *strength of
the encoder baseline*. Each is a possible alternative explanation, or a boundary
condition, for our headline claim.

---

## 1. The SEiGS '26 survey (ref. 1)

7-page survey at the Symposium on Software Engineering in the Global South
(Rio, April 2026): 31 primary studies retrieved from four libraries, plus
semi-structured interviews with five Ugandan practitioners. Two RQs — which LLM
approaches are used for requirements classification and how they perform, and
what blocks their adoption in the Global South.

**Read it for what the field believes, not for its numbers.** Its Table 1
compresses the whole literature into four rows: fine-tuning (BERT, RoBERTa;
PROMISE/NFR datasets) at 85–92 % accuracy; prompt engineering (GPT-4, GPT-3.5;
custom RE datasets and user stories) at F1 0.85–0.90; hybrid BERT + rules at
precision 0.88–0.91; transfer learning (T5, LLaMA) at recall 0.83–0.89. No row
records an evaluation regime, and cost appears nowhere. The paper itself is not
strong — five purposively sampled interviewees, RQ numbering that contradicts
itself between §1 and §5, performance quoted as aggregate ranges with no
per-study detail — so we should not quote a number from it. What it *is* good
for is evidence of consensus, and it is useful to us in three ways.

**(a) It is the 2026 witness for our opening claim.** Our Introduction asserts
that the field's headline is "the task is essentially solved". A survey published
this year that summarises 31 studies as 85–92 % accuracy, with no transfer arm
and no cost axis anywhere in its synthesis, is a stronger citation for that
sentence than any single primary study — and it is a survey, so it speaks for the
field rather than for one team.

**(b) Its practitioners report exactly the failure we measure.** The generalisation
complaint is the interviewees' own, not the authors': Participant C asks for
models that "handle these different descriptions a lot better because sometimes
if you bring in new projects it might not be able to capture everything based on
the previous projects if they are really completely different", and the same
participant reports poor "generalizability across dissimilar projects". The
survey also relays a BERT security-NFR framework at 92 % on extended PROMISE with
"poor generalizability" off-domain. So: the literature reports 85–92 % in
distribution; the practitioners' number-one complaint is that it does not survive
a new project. **That gap is our paper's entire contribution**, and this gives us
a field-side citation for it instead of asserting it ourselves. It belongs in the
Introduction as motivation.

**(c) It makes our cost result an adoption result.** The survey's challenge table
lists infrastructure constraints (unreliable internet and power ruling out
cloud LLMs) and cost barriers, with "offline SLMs, lightweight models" as the
mitigation practitioners themselves propose. Our RQ3 shows a fine-tuned 110 M
encoder is 9–47× cheaper, breaks even after 46–552 items, and runs on one
free-tier GPU. We currently present that as an economics result; it is also an
*equity* result, and one sentence in the Discussion would say so.

**Where Dr. Lamia's structural remark comes from.** Look at what the survey's
rows are actually built on: PROMISE specification sentences for the fine-tuning
row, "custom RE datasets **and user stories**" for the prompting row, and in the
interviews, project descriptions (Participant C), user stories drawn from
interview transcripts (Participant E), and transcribed multilingual speech
(Participant A). Four structurally different artefacts, one 85–92 % range. That
range is not comparable across them, and "structured prompts reduce
misclassification of **ambiguous requirements**" is the survey's own admission
that form changes the result. Hence the remark: *user story vs app review*,
*user story with acceptance criteria vs ambiguous requirement*.

That criticism lands on us too, in a smaller way. Both our corpora are
specification-style statements, so our result is scoped to one artefact form —
which we never say. We should say it (§Corpus, one clause), and then measure it.

---

## 2. Requirement structure as a held-constant factor (refs. 1, 2)

**Where we stand.** Our cross-dataset arm attributes the inversion to an
uncalibrated class prior: security is 12.9 % of PROMISE_exp and 39.9 % of SecReq,
and the transferred encoder reproduces its training prior (44.2 % predicted vs.
12.9 % true). §Threats already concedes *definitional* shift. Artefact form is a
third axis we never name.

**QuRE (ref. 2) — Femmer, Houdek, Unterbusch & Vogelsang, arXiv:2508.08868.**
2,111 industrial requirements from Mercedes-Benz specifications, labelled through
a review process used contractually for ~5 years; ~30 % carry a defect across 23
"weak word" categories. The contribution that matters to us is not the data but
the **comparative analysis**: it profiles requirement corpora on

* lexical complexity — vocabulary richness, lexical diversity, lexical density
* syntactic complexity — sentence length, clause count, dependency-parse depth
* readability — Flesch–Kincaid grade level

across PURE, PROMISE, a 445-item security set, a 1,673-item user-story set,
GPT-4-generated synthetic requirements, and the Brown corpus as a generic-English
floor. Findings: real industrial requirements are syntactically far more complex
than synthetic ones; real corpora cluster at lexical diversity ≈ 0.11–0.15 while
GPT-4-generated ones sit at 0.18–0.28; QuRE reads at ~grade 11 vs. grade 6–8 for
synthetic text.

**This is an opportunity, not just a threat.** We already show the failure is
*not* unfamiliar vocabulary. If the two corpora are also *structurally*
comparable while differing three-fold in prior, the causal story gets much
stronger: it is the prior, not the prose. QuRE hands us the instrument to say
that with measurements instead of assertion, and without running a single model.

**Caveat.** QuRE's labels are *quality defects*, not FR/NFR or security. It is
**not** a drop-in third corpus for our three tasks. Its uses are: (i) the metric
protocol above, applied to our corpora; (ii) a citable industrial-provenance
argument for our contamination threat and against the field's reliance on two
ageing public corpora; (iii) a possible new task — requirement quality /
ambiguity detection — which is the "user story with acceptance criteria vs.
ambiguous requirement" contrast made operational.

**Action (P0, no GPU).** Compute QuRE's metric set on PROMISE_exp and SecReq and
report it in §Corpus beside the prevalence contrast. Both outcomes are useful:
structurally similar → the prior explanation is isolated; structurally different
→ we report a co-varying factor honestly and pre-empt the reviewer who would
have raised it.

**Action (P2, next study).** Make structure a *manipulated* variable: the same
label set over (a) formal `shall` specifications, (b) user stories with
acceptance criteria, (c) app-store reviews, (d) ambiguous industrial text. That
is the thesis' second study, and ref. 1 supplies its motivation — practitioners
feeding LLMs four different artefact forms and getting one undifferentiated
accuracy claim back from the literature.

---

## 3. Batch size in the prompt (ref. 3)

**Reference.** *One Size Does Not Fit All: On the Role of Batch Size in
Classifying Requirements with LLMs* — van Can, Aydemir & Dalpiaz, AIRE '25.
Three locally-deployable decoder LLMs (Llama-3.1-8B-Instruct, Gemma-3-12B,
DeepSeek-R1-Distill-Qwen-14B) × four requirement datasets × seven batch sizes
(1, 2, 4, 8, 16, 32, 64), classifying functional vs. quality requirements.
Reported: batch size materially affects performance, no single batch size is best
across models and datasets, and quality requirements are harder than functional
ones. *(Abstract and workshop programme only — the full PDF sits behind a blocked
domain; per-dataset numbers must be checked before we cite specifics.)*

**It hits us twice.**

1. *Accuracy.* §Prompting fixes one requirement per call — "sent as a single user
   message", greedy decoding, ≤ 12 new tokens. Batch size is therefore silently
   pinned at 1 across all eight prompted configurations. Our two sub-studies vary
   phrasing and shot count; this is a third factor of the same kind, on an arm we
   already show to be highly sensitive to such factors (re-wording alone moves
   macro-F1 by up to 0.485).
2. *Cost — the sharper one.* RQ3 is the paper's differentiator, and `Stage5`
   prices local inference as wall-clock seconds × hourly rate, with the code
   comment stating it "assumes sequential unbatched inference". Batching
   amortises the instruction block across items, so per-item input tokens and
   per-item wall-clock both fall. The 9–47× encoder advantage and
   N\* = 46–552 items are therefore computed against the *worst case* for the
   prompted arm. A reviewer holding this paper will ask whether batching closes
   the gap; better that we answer first.

**A hypothesis worth testing.** Our diagnosis is that prompted models mis-set the
class prior from the wording of the question. In a batch the model sees several
requirements at once, so the batch's own class mix becomes visible context.
Batching may therefore *partially self-calibrate* the prior — or push the model
to spread labels across the batch. Either result is a finding, and it joins our
calibration story to their batching story. Nobody has run it.

**Action (P0).** Cite the paper, state batch = 1 as a scope decision in
§Prompting, add the cost consequence to §Threats (Construct).
**Action (P1).** Sub-study: b ∈ {1, 4, 16, 32} on two local models plus the
commercial model, FR/NFR + security, measuring macro-F1 **and** $/item, plus
predicted-prior drift per batch size. Contained, reuses the existing harness and
scorer, and defends RQ3 on its own ground.

---

## 4. "Encoder transformers can be improved" (ref. 4)

**Reference.** *Large Language Model for Requirements Classification: An Ensemble
Approach*, Procedia Computer Science (KES 2025). Seven encoders — BERT,
DistilBERT, DistilRoBERTa, ELECTRA, DeBERTaV3, RoBERTa, XLNet — on binary
requirements classification over a newly collected dataset, then combined by
ensemble learning; the ensemble outperformed every individual model.
*(Abstract only — `sciencedirect.com` is blocked; dataset and per-model F1 need
reading before we cite numbers.)*

**Where it hits us.** Our encoder tier is `bert-base-uncased` and `roberta-base`,
weighted and unweighted — four variants, both ~110–125 M parameters, both 2019
checkpoints. The obvious objection to "encoders win in-domain, lose across
corpora" is: *your encoder simply was not the best encoder.*

**Answer with a prediction, not a defence.** We diagnose the cross-dataset
failure as an inherited class prior, not as insufficient capacity. An ensemble
trained on the *same* corpus inherits the *same* prior, so it should improve
in-domain and **still** invert under transfer. Falsifiable, and cheap — encoders
are small and Stage 2 already trains them.

**Action (P1a).** Add DeBERTaV3-base (optionally ELECTRA) plus a soft-vote
ensemble over the tier; run all three regimes. If the prediction holds, the
"weak baseline" objection dies permanently.
**Action (P1b), the companion.** We cite Saerens et al. (2002) on prior
adjustment but never apply it. Apply prior correction / threshold re-tuning to
the transferred encoder and report how much of the 42.8 % macro-F1 loss it
recovers. That turns the diagnosis into a remedy — *the fix is calibration, not
capacity* — and is the strongest single addition available to us.

---

## Priority

| | Work | Cost | Why |
|---|---|---|---|
| **P0** | Cite ref. 1 in §Intro (field consensus + practitioner-reported generalisation failure) and §Discussion (cost as adoption/equity); cite refs 2–4; state batch = 1 in §Prompting and the batching caveat in §Threats; state that both corpora are specification-style artefacts in §Corpus; add the QuRE metric profile of our two corpora | hours, no GPU | closes four reviewer objections and strengthens the prior-vs-prose argument |
| **P1a** | DeBERTaV3 + soft-vote ensemble across all three regimes | ~1 free-tier GPU day | kills the "weak encoder baseline" objection |
| **P1b** | Saerens prior correction on the transferred encoder | hours | turns the diagnosis into a remedy |
| **P1c** | Batch-size × cost sub-study, b ∈ {1, 4, 16, 32} | ~1 GPU day + quota | defends RQ3; tests batching as prior self-calibration |
| **P2** | Structure as a manipulated variable: shall-statements / user stories + acceptance criteria / app reviews / ambiguous industrial text | new study | the thesis' second paper |

## Open items

* Refs 3 and 4 were read from abstracts and secondary sources only — IEEE Xplore
  and ScienceDirect are blocked by this session's egress policy. Any number we
  quote from them must be checked against the published PDFs first.
* Ref. 1 should be cited for the field's claims and its practitioner evidence,
  never for its own performance figures.
