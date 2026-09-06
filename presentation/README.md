# Defense presentation

Two decks built from the paper (`../paper/main.tex`), 43 slides each:

| File | What it is |
|---|---|
| `Presentation.pptx` | slides only (English) |
| `Presentation_with_Arabic_notes.pptx` | same slides + Egyptian-Arabic speaker notes under every slide |
| `deck.json` | the slide content and notes (source of truth; every number traced to `main.tex` line ranges in `sources`) |
| `render.js` | pptxgenjs renderer: `node render.js deck.json out.pptx [--notes]` |
| `build.sh` | builds both decks and validates them |
| `figs/` | the paper's figures (fig_inversion, fig_prior_shift, fig_cost) as PNG |

Rebuild: `npm install pptxgenjs && bash build.sh`.
