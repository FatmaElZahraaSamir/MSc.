# MSc.

Fine-tuned encoders vs. prompted LLMs for requirements classification, across
in-domain, cross-project and cross-dataset evaluation. Stages 1–5 are Kaggle
notebooks; `paper/` builds the write-up from their stored artefacts.

## Attaching the PURE corpus

PURE is the study's **third corpus** and the one that gives FR/NFR a
cross-dataset arm. It is optional: with no PURE file attached every stage runs
exactly as before and Stage 1 reproduces its previous `splits.json` byte for
byte.

1. Attach a requirement-level **FR/NFR-labelled PURE export** to the Stage 1
   notebook as a Kaggle dataset. Stage 1 finds it automatically when `pure`
   appears in the dataset folder or the file name; `.csv`, `.tsv`, `.xlsx`,
   `.json` and `.arff` are all read. Set `STAGE1_PURE_PATH` (or
   `CONFIG["pure_path"]`) to name the file explicitly.
2. Run Stage 1. The log prints the columns it read, the corpus overlap with
   PROMISE and SecReq, and the file's `sha256`.
3. Copy that `sha256` into `CONFIG["expected_sha256"]` under the file's
   basename, so later runs are pinned the way the three fetched sources are.
4. Re-run Stages 2, 3, 3b, 4 and 5. Nothing downstream needs editing — the new
   `promise_to_pure_fr_nfr` / `pure_to_promise_fr_nfr` folds, the evaluation
   cells, the tables and the figures are all enumerated from the data.

What Stage 1 will **not** do: guess a numeric label (set
`CONFIG["pure_label_map"]`, e.g. `{"0": "FR", "1": "NFR"}`), invent a
`label_security` for an FR/NFR-only export, or invent a document column —
without one PURE is a single pseudo-project and gets a cross-dataset arm but no
cross-project arm. Each refusal is logged.

The published PURE release (Ferrari et al., RE'17; Zenodo
`10.5281/zenodo.1414117`) is 79 unannotated requirements *documents*, so the
FR/NFR labels come from whichever export is attached. `stage1_manifest.json`
records its name, digest and columns; the write-up must cite both and note that
PURE's labels and PROMISE's were produced by different annotators.

## Layout

| Path | What it is |
|---|---|
| `stage1-data-pipeline.ipynb` | unified corpus + every evaluation split |
| `stage2-finetuned-baselines.ipynb` | BERT/RoBERTa over every split family |
| `stage3-llm-harnes.ipynb` | prompted LLMs, binary tasks |
| `stage3b-subtype-harness.ipynb` | prompted LLMs, NFR sub-types |
| `stage3b-repair.ipynb` | parse repair for the stored LLM outputs |
| `stage4-analysis.ipynb` | metrics, significance tests, figures |
| `stage5-cost.ipynb` | cost, latency and break-even analysis |
| `results *.zip` | the stored outputs each stage produced |
| `paper/` | the IEEE paper, built from those artefacts |
