# Paper — *Large Language Models for Software Requirements Classification: Cross-Dataset Generalization and Cost-Efficiency*

An IEEE-format conference paper built directly from the seven-stage pipeline in
the repository root. Every number in the paper is read back from a stored
artefact; nothing is transcribed by hand.

## Build

```bash
pdflatex main.tex && pdflatex main.tex && pdflatex main.tex   # 3 passes for cross-refs
```

Requires `IEEEtran`, `booktabs`, `tikz`, `pifont`, `balance`, `microtype`
(TeX Live: `texlive-latex-extra`, `texlive-publishers`).

## Layout

| Path | What it is |
|---|---|
| `main.tex` | the paper; the only hand-written file |
| `figures/fig_architecture.tex` | Fig. 1, the system-architecture diagram, pure TikZ |
| `figures/fig_inversion.pdf` | Fig. 3, the regime reversal (grouped bars incl. the prompted models + verdict bars) |
| `figures/fig_prior_shift.pdf` | Fig. 4, the shared failure mode (three panels) |
| `figures/fig_cost.pdf` | Fig. 5, Pareto frontier and break-even |
| `tables/tab_main.tex` | the single results table: 12 configurations × 6 cells × every regime |
| `tables/tab_loss.tex` | encoder relative loss under shift |
| `tables/tab_prompt.tex` | phrasing sub-study, incl. the best-of-three oracle gain |
| `tables/tab_cost.tex` | cost and latency by access tier, with the pricing basis |
| `scripts/make_figs.py` | regenerates the three data figures |
| `scripts/make_tables.py` | regenerates the numeric table bodies and the `*_stats.json` files the prose quotes |

Fig. 2 (the prompt template) is set inline in `main.tex`.

## Regenerating the numbers

The scripts expect the unzipped stage outputs under `../artefacts/`:

```
artefacts/
  results_Stage4_analysis/         tab0..tab11b  (metrics, McNemar, few-shot, per-project)
  results_Stage5_cost/             cost1..cost5  (per-model cost, Pareto, break-even)
  results_stage1_data_pipeline/    unified corpus + splits + manifest
  results_stage2_finetuned_baselines/  predictions_finetuned.parquet
  repair/                          predictions_llm_repaired.parquet,
                                   predictions_subtype_repaired.parquet
```

Unzip the `results *.zip` archives in the repository root into that directory
(`paper/artefacts/`, or a symlink to it), then:

```bash
cd scripts && python3 make_tables.py && python3 make_figs.py
```

Both scripts need `pandas`, `pyarrow`, `numpy`, `matplotlib`.

## Two conventions worth knowing before editing

* **Table fragments carry their own `tabular`.** `\input` of a bare row block
  inside an alignment confuses TeX's optional-argument lookahead at the file
  boundary, so each fragment in `tables/` opens and closes its own `tabular` and
  is `\input` at table-body level.
* **Figure canvases are sized so the tight bounding box lands near
  `\columnwidth`.** All three data figures then scale by ≈1.0, which keeps their
  type sizes consistent with each other and with the body text.

## Palette

Figures use the Okabe–Ito-derived four-colour categorical set
`#0072B2 / #009E73 / #E69F00 / #CC79A7` (fine-tuned encoder / hosted open-weight /
local open-weight / commercial). It passes the lightness-band, chroma, CVD-separation
and normal-vision checks, and every tier additionally carries a marker shape or hatch
so the figures stay readable in greyscale.
