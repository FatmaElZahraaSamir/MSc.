# Paper — *Large Language Models for Software Requirements Classification: Cross-Dataset Generalisation and Cost-Efficiency*

An 8-page IEEE conference paper (ICCI 2026) built directly from the seven-stage
pipeline in the repository root. **No number in the paper is typed by hand.**
`scripts/make_numbers.py` reads every reported quantity back out of the stored
stage artefacts and writes it as a LaTeX macro, so any figure in the text can be
traced to the artefact column it came from.

## Build

```bash
cd scripts && python3 make_numbers.py && python3 make_figs.py   # numbers, tables, figures
cd .. && pdflatex main.tex && pdflatex main.tex && pdflatex main.tex
cd scripts && python3 make_docx.py                              # optional Word copy
```

Requires `IEEEtran`, `booktabs`, `tikz`, `pifont`, `balance`, `microtype`
(TeX Live: `texlive-latex-extra`, `texlive-publishers`); Python needs `pandas`,
`pyarrow`, `numpy`, `matplotlib`, and `python-docx` for the Word export.

## Layout

| Path | What it is |
|---|---|
| `main.tex` | the paper; the only hand-written file |
| `figures/fig_architecture.tex` | Fig. 1, how the experiment is put together, pure TikZ |
| `figures/fig_inversion.pdf` | Fig. 2, the regime inversion (bars + verdict counts) |
| `figures/fig_prior.pdf` | Fig. 3, the shared failure mode (two panels) |
| `figures/fig_cost.pdf` | Fig. 4, price per 1,000 and the break-even crossing |
| `tables/numbers.tex` | every reported number, as `\n<Name>` macros |
| `tables/numbers.json` | the same values in plain JSON, for checking |
| `tables/tab_main.tex` | Table III, the single results table |
| `scripts/make_numbers.py` | generates `numbers.tex`, `numbers.json`, `tab_main.tex` |
| `scripts/make_figs.py` | regenerates the three data figures |
| `scripts/make_docx.py` | renders the same content as `paper.docx` |
| `paper.docx` | Word copy, generated from `main.tex` |

Tables I and II are small and set inline in `main.tex`; the prompt template is
set inline too.

## Regenerating the numbers

The scripts expect the unzipped stage outputs under `../../artefacts/`
(relative to `scripts/`, i.e. `artefacts/` at the repository root):

```
artefacts/
  results_Stage4_analysis/             tab0..tab11b (metrics, McNemar, few-shot, per-project)
  results_Stage5_cost/                 cost1..cost5 (per-model cost, Pareto, break-even)
  results_stage1_data_pipeline/        unified corpus + splits + manifest
  results_stage2_finetuned_baselines/  predictions_finetuned.parquet
  repair/                              predictions_llm_repaired.parquet,
                                       predictions_subtype_repaired.parquet
```

Unzip the `results *.zip` archives in the repository root into that directory
(it is git-ignored, since the archives are what is tracked):

```bash
mkdir -p artefacts && cd artefacts
unzip -q "../results Stage4 analysis.zip"          -d results_Stage4_analysis
unzip -q "../results Stage5 cost.zip"              -d results_Stage5_cost
unzip -q "../results stage1_data_pipeline.zip"     -d results_stage1_data_pipeline
unzip -q "../results stage2_finetuned_baselines.zip" -d results_stage2_finetuned_baselines
unzip -q "../results Stage3b repair.zip"           -d repair
```

## Three conventions worth knowing before editing

* **Numbers come from macros, never from the keyboard.** Write `\nDropXDmax\%`,
  not `42.8\%`. If a quantity has no macro yet, add it to `make_numbers.py`
  rather than typing the value.
* **Table fragments carry their own `tabular`.** `\input` of a bare row block
  inside an alignment confuses TeX's optional-argument lookahead at the file
  boundary, so `tab_main.tex` opens and closes its own `tabular` and is
  `\input` at table-body level.
* **Figure canvases are sized so the tight bounding box lands near
  `\columnwidth`.** All three data figures then scale by ≈1.0, which keeps their
  type sizes consistent with each other and with the body text.

## Palette

Figures use the Okabe–Ito-derived four-colour categorical set
`#0072B2 / #009E73 / #E69F00 / #CC79A7` (fine-tuned encoder / hosted open-weight /
local open-weight / commercial). It passes the lightness-band, chroma,
CVD-separation and normal-vision checks, and the prompted-model marks also carry
a hatch so the figures stay readable in greyscale.
