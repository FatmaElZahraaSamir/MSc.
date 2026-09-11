# Paper — *Large Language Models for Software Requirements Classification: Cross-Dataset Generalization and Cost-Efficiency*

An 8-page IEEE conference paper, formatted for **ICCI 2026** (7th International
Conference on Computing and Informatics, Future University in Egypt, Cairo,
19-20 December 2026), built directly from the seven-stage pipeline in the
repository root. Every number in the paper is read back from a stored
artefact; nothing is transcribed by hand.

The 8-page limit is tight and the layout is tuned to it: Tables I and II are set
at `\scriptsize`, float separation is reduced in the preamble, and the prompt
template sits inline in Section III-E rather than as a captioned float. Adding a
paragraph will usually push the last references onto a ninth page.

## Conference format

ICCI 2026 requires the standard IEEE conference template, and the template it
ships is the **A4** variant. Both deliverables follow it:

| | `main.tex` / `main.pdf` | `paper-revised.docx` |
|---|---|---|
| class / geometry | `IEEEtran` with `conference,a4paper` | the template's own A4 block: 54pt top, 45.35pt sides, 72pt bottom, two columns 18pt apart |
| keyword label | `\IEEEkeywordsname` set to `Keywords` | `Keywords—` |
| first-page footer | `\IEEEpubid` with the template placeholder | same, in a first-page footer |
| author block | names / dept. / organization / city, country / contact | same lines |

The two differ by about 2% in text width: `IEEEtran`'s A4 block is 516pt wide
with a 12pt column gap, the Word template's is 504.58pt with an 18pt gap. Both
are IEEE's own templates and either is accepted; the `.docx` is the exact one
ICCI distributed.

The copyright identifier (`XXX-X-XXXX-XXXX-X/XX/$XX.00 ©20XX IEEE`) is the
template's placeholder. IEEE assigns the real one at camera-ready.

All 26 fonts in `main.pdf` are embedded subsets, which is what IEEE PDF eXpress
checks.

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
| `figures/fig_inversion.pdf` | Fig. 2, the regime reversal (grouped bars incl. the prompted models + verdict bars) |
| `figures/fig_prior_shift.pdf` | Fig. 3, the shared failure mode (two panels) |
| `tables/tab_main.tex` | the single results table: 12 configurations × 6 cells × every regime |
| `tables/tab_loss.tex`, `tab_prompt.tex`, `tab_cost.tex` | generated, but folded into prose at 8 pages; `*_stats.json` holds the values the prose quotes |
| `scripts/make_figs.py` | regenerates the three data figures |
| `scripts/make_tables.py` | regenerates the numeric table bodies and the `*_stats.json` files the prose quotes |

The prompt template is set inline in `main.tex`, not as a numbered figure.

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

## Word version

`paper-revised.docx` is the same paper as a Word file, for review outside
LaTeX. It is generated, not hand-edited:

```bash
cd scripts
python3 tex2docx_content.py          # main.tex + tables/ -> scripts/paper.json
npm install docx                     # once
node build_docx.js ../paper-revised.docx
```

`tex2docx_content.py` understands only the constructs this paper uses and
resolves citation, section, table and figure numbers the way LaTeX does, so the
two versions carry the same numbering. Figure 1 is rendered from
`figures/fig_architecture.tex` via a `standalone` compile to
`figures/fig_architecture.png`; the other figures use the PNGs that
`make_figs.py` writes alongside the PDFs.

Regenerate the tables and figures before rebuilding the `.docx`, or it will
carry stale numbers.
