"""Emit the paper's numeric tables straight from the Stage-4/5 artefacts."""
import pandas as pd, numpy as np, json, io

Z = '../artefacts/'
T = '../tables/'

ev  = pd.read_csv(Z+'results_Stage4_analysis/tab9_evaluability.csv')
gap = pd.read_csv(Z+'results_Stage4_analysis/tab3_generalisation_gap.csv')
c1  = pd.read_csv(Z+'results_Stage5_cost/cost1_per_model.csv')
be  = pd.read_csv(Z+'results_Stage5_cost/cost3_breakeven.csv')
dum = pd.read_csv(Z+'results_Stage4_analysis/tab0_baselines.csv')

SHORT = {
    'BERT (weighted)': r'BERT\textsubscript{w}',
    'BERT (unweighted)': r'BERT\textsubscript{u}',
    'RoBERTa (weighted)': r'RoBERTa\textsubscript{w}',
    'RoBERTa (unweighted)': r'RoBERTa\textsubscript{u}',
    'Gemini-3.1-Flash-Lite': 'Gemini 3.1 Flash-Lite',
    'Llama-3.3-70B (Groq)': 'Llama-3.3-70B',
    'Gemma-2-2B': 'Gemma-2-2B', 'Llama-3.1-8B': 'Llama-3.1-8B',
    'Phi-4-mini': 'Phi-4-mini', 'Qwen2.5-3B': 'Qwen2.5-3B',
    'Qwen2.5-7B': 'Qwen2.5-7B', 'SmolLM3-3B': 'SmolLM3-3B',
}
ORDER = ['BERT (weighted)', 'BERT (unweighted)', 'RoBERTa (weighted)', 'RoBERTa (unweighted)',
         'Gemini-3.1-Flash-Lite', 'Llama-3.3-70B (Groq)',
         'Qwen2.5-7B', 'Llama-3.1-8B', 'Gemma-2-2B', 'Phi-4-mini', 'SmolLM3-3B', 'Qwen2.5-3B']
# ---------------------------------------------------------------------------
# WHICH (task, corpus) CELLS THE TABLES SHOW - read off the artefacts.
#
# This was a six-entry literal, and so were the tabular headers further down.
# Both were right for a two-corpus study and wrong the moment a third corpus was
# added: PURE exists to give FR/NFR the cross-dataset arm it never had, and a
# hand-written cell list would have left its column out of every paper table
# with no error - the LaTeX would compile, the numbers would be missing, and
# nothing would say so.
#
# A cell appears when the evaluability gate passed an in-domain result for it.
# On the current artefacts that reproduces the original six, in the original
# order, byte for byte; a re-run carrying PURE widens the tables instead.
# ---------------------------------------------------------------------------
TASK_ORDER = ['fr_nfr', 'security', 'subtype_top4', 'subtype_top6', 'subtype_all']
CORPUS_ORDER = ['promise', 'secreq']       # historic; anything newer is appended
CORPUS_TEX = {'promise': r'\pex{}', 'secreq': 'SecReq', 'pure': 'PURE'}
CORPUS_TEX_LONG = {'promise': r'PROMISE\_exp', 'secreq': 'SecReq', 'pure': 'PURE'}
TASK_TEX = {'fr_nfr': 'FR/NFR', 'security': 'Security'}
SUBTYPE_TEX = {'subtype_top4': 'top-4', 'subtype_top6': 'top-6',
               'subtype_all': 'all-11'}


def _tex(corpus, long=False):
    d = CORPUS_TEX_LONG if long else CORPUS_TEX
    return d.get(corpus, corpus.upper())


def corpora_for(task, regime='in_domain'):
    seen = set(ev[(ev.task == task) & (ev.eval_regime == regime) &
                  (ev.reportable)].dataset.astype(str))
    return ([c for c in CORPUS_ORDER if c in seen]
            + sorted(seen - set(CORPUS_ORDER)))


CELLS = [(t, ds) for t in TASK_ORDER for ds in corpora_for(t)]
print('cells:', CELLS)


def get(model, task, ds, regime):
    r = ev[(ev.model == model) & (ev.task == task) & (ev.dataset == ds) &
           (ev.eval_regime == regime) & (ev.reportable)]
    return float(r.macro_f1.iloc[0]) if len(r) else None


# ---------------------------------------------------------------- Table IV
def tab_in_domain():
    lines = []
    best = {}
    for task, ds in CELLS:
        vals = [(m, get(m, task, ds, 'in_domain' if m in ORDER[:4] else 'prompted'))
                for m in ORDER]
        vals = [(m, v) for m, v in vals if v is not None]
        best[(task, ds)] = max(v for _, v in vals)
    for m in ORDER:
        reg = 'in_domain' if m in ORDER[:4] else 'prompted'
        cells = []
        for task, ds in CELLS:
            v = get(m, task, ds, reg)
            if v is None:
                cells.append('--')
            else:
                s = f'{v:.3f}'
                cells.append(r'\textbf{'+s+'}' if abs(v-best[(task, ds)]) < 1e-9 else s)
        lines.append(f'{SHORT[m]} & ' + ' & '.join(cells) + r' \\')
    dummy = []
    for task, ds in CELLS:
        d = dum[(dum.task == task) & (dum.dataset == ds)]
        dummy.append(f'{float(d.macro_f1.iloc[0]):.3f}')
    body = '\n'.join(lines[:4]) + '\n\\addlinespace[1.5pt]\n' + \
           '\n'.join(lines[4:6]) + '\n\\addlinespace[1.5pt]\n' + '\n'.join(lines[6:])
    n = []
    for task, ds in CELLS:
        r = ev[(ev.task == task) & (ev.dataset == ds) & (ev.eval_regime.isin(['in_domain']))]
        n.append(int(r.n.max()))
    open(T+'tab_in_domain.tex', 'w').write(body + '\n\\midrule\n' +
        r'\textit{majority-class baseline} & ' + ' & '.join(dummy) + r' \\' + '\n')
    open(T+'tab_in_domain_n.tex', 'w').write(' & '.join(str(x) for x in n))
    print('tab_in_domain.tex  encoder n per cell:', n)


# ---------------------------------------------------------------- Table V
def tab_transfer():
    # Security leads because it is the task with the longest-standing
    # cross-dataset evidence; everything else follows TASK_ORDER. The corpus is
    # named for the binary tasks, and for the sub-type rows only when more than
    # one corpus annotates them - naming it unconditionally would add a column
    # of noise to a table whose sub-type rows are all one corpus today.
    order = []
    for task in ['security'] + [t for t in TASK_ORDER if t != 'security']:
        corpora = corpora_for(task)
        for ds in corpora:
            if task in SUBTYPE_TEX:
                label = 'NFR sub-types, ' + SUBTYPE_TEX[task]
                if len(corpora) > 1:
                    label += ' --- ' + _tex(ds, long=True)
            else:
                label = TASK_TEX.get(task, task) + ' --- ' + _tex(ds, long=True)
            order.append((task, ds, label))
    out = []
    for j, (task, ds, label) in enumerate(order):
        if j:
            out.append(r'\addlinespace[2pt]')
        out.append(r'\multicolumn{6}{@{}l}{\itshape ' + label + r'} \\')
        for m in ORDER[:4]:
            idm = get(m, task, ds, 'in_domain')
            if idm is None:
                continue
            xp = get(m, task, ds, 'cross_project')
            xd = get(m, task, ds, 'cross_dataset')
            def pair(v):
                if v is None:
                    return '--', '--'
                return f'{v:.3f}', r'$-$' + f'{100*(idm-v)/idm:.0f}'
            a, da = pair(xp); b, db = pair(xd)
            out.append(f'\\quad {SHORT[m]} & {idm:.3f} & {a} & {da} & {b} & {db} ' + r'\\')
    open(T+'tab_transfer.tex', 'w').write('\n'.join(out) + '\n')
    print('tab_transfer.tex written')


# ---------------------------------------------------------------- Table VI
def tab_cost():
    rows = []
    for tier, label in [('finetuned', 'Fine-tuned encoder'),
                        ('open_local', 'Open-weight, local (4-bit)'),
                        ('open_hosted', 'Open-weight, hosted API'),
                        ('commercial', 'Commercial API')]:
        d = c1[c1.tier == tier]
        per = d.groupby('model').inference_usd_per_1k.median()
        lat = d.groupby('model').latency_s_median.median()
        tr = d[d.one_off_training_usd > 0].one_off_training_usd
        trs = f'{tr.median():.4f}' if len(tr) else '--'
        rows.append((label, len(per), f'{per.min():.4f}--{per.max():.4f}',
                     f'{lat.min():.3f}--{lat.max():.3f}', trs))
    with open(T+'tab_cost.tex', 'w') as f:
        for label, k, per, lat, tr in rows:
            f.write(f'{label} & {k} & {per} & {lat} & {tr} ' + r'\\' + '\n')
    stats = dict(
        be_min=int(be.breakeven_n_items.min()), be_max=int(be.breakeven_n_items.max()),
        be_med=int(be.breakeven_n_items.median()), be_pairs=len(be),
        be_all=int(be.encoder_cheaper_at_100k.sum()),
        enc_med=float(c1[c1.tier == 'finetuned'].inference_usd_per_1k.median()),
        pr_min=float(c1[c1.tier != 'finetuned'].inference_usd_per_1k.min()),
        pr_max=float(c1[c1.tier != 'finetuned'].inference_usd_per_1k.max()),
        pr_med=float(c1[c1.tier != 'finetuned'].inference_usd_per_1k.median()),
        train_med=float(c1[c1.one_off_training_usd > 0].one_off_training_usd.median()),
    )
    json.dump(stats, open(T+'cost_stats.json', 'w'), indent=1)
    print('tab_cost.tex', stats)


tab_in_domain(); tab_transfer(); tab_cost()

# --- complete tabulars ------------------------------------------------------
# \input of a bare row block inside an alignment confuses TeX's lookahead at the
# file boundary, so each fragment ships the whole tabular and is \input at
# table-body level instead.
def in_domain_header():
    """The header that matches CELLS, built rather than typed.

    Three things vary with the corpora present and all three used to be frozen
    into the string below: the column spec (one 'c' per cell), the group spans,
    and whether the sub-type group can be annotated with a single corpus name.
    The last one is the subtle one - "NFR sub-types (\\pex{})" is only true
    while PROMISE is the only corpus annotating sub-types, and a second one
    would have made the printed header quietly false.
    """
    groups = [('FR/NFR', ['fr_nfr']), ('Security', ['security']),
              ('NFR sub-types', ['subtype_top4', 'subtype_top6', 'subtype_all'])]
    titles, labels, spans, col = [], [], [], 2
    for title, tasks in groups:
        cells = [(t, ds) for t in tasks for ds in corpora_for(t)]
        if not cells:
            continue
        corpora = {ds for _, ds in cells}
        if tasks[0].startswith('subtype'):
            if len(corpora) == 1:
                title += f' ({_tex(next(iter(corpora)))})'
                labels += [SUBTYPE_TEX[t] for t, _ in cells]
            else:
                labels += [f'{SUBTYPE_TEX[t]} {_tex(ds)}' for t, ds in cells]
        else:
            labels += [_tex(ds) for _, ds in cells]
        titles.append((title, len(cells)))
        spans.append((col, col + len(cells) - 1))
        col += len(cells)

    head = ' & '.join(
        (r'\textbf{' + t + '}') if n == 1
        else (r'\multicolumn{' + str(n) + r'}{c}{\textbf{' + t + '}}')
        for t, n in titles)
    rules = ''.join(
        (r'\cmidrule(l){' if i == len(spans) - 1 else r'\cmidrule(lr){')
        + f'{a}-{b}' + '}' for i, (a, b) in enumerate(spans))
    return (
        "\\setlength{\\tabcolsep}{7pt}\n\\renewcommand{\\arraystretch}{1.05}\n"
        "\\begin{tabular}{@{}l" + 'c' * len(CELLS) + "@{}}\n\\toprule\n"
        "& " + head + " \\\\\n" + rules + "\n"
        "\\textbf{Configuration} & " + ' & '.join(labels) + " \\\\\n\\midrule\n")


HEADERS = {
 'tab_in_domain.tex': in_domain_header(),
 'tab_transfer.tex': (
   "\\setlength{\\tabcolsep}{3.6pt}\n\\renewcommand{\\arraystretch}{1.06}\n"
   "\\begin{tabular}{@{}lccccc@{}}\n\\toprule\n"
   "& \\textbf{In-dom.} & \\multicolumn{2}{c}{\\textbf{Cross-project}} "
   "& \\multicolumn{2}{c}{\\textbf{Cross-dataset}} \\\\\n"
   "\\cmidrule(lr){2-2}\\cmidrule(lr){3-4}\\cmidrule(l){5-6}\n"
   "\\textbf{Configuration} & \\Fm{} & \\Fm{} & $\\Delta$\\% & \\Fm{} & $\\Delta$\\% \\\\\n"
   "\\midrule\n"),
 'tab_cost.tex': (
   "\\setlength{\\tabcolsep}{3.4pt}\n\\renewcommand{\\arraystretch}{1.06}\n"
   "\\begin{tabular}{@{}lcccc@{}}\n\\toprule\n"
   "\\textbf{Tier} & \\textbf{Models} & \\textbf{USD/1k} & \\textbf{Latency (s)} "
   "& \\textbf{Training} \\\\\n\\midrule\n"),
}
for _f, _hdr in HEADERS.items():
    _p = T + _f
    _t = open(_p).read().rstrip()
    if _t.startswith('\\setlength'):
        continue
    if _t.endswith('\\bottomrule'):
        _t = _t[:-len('\\bottomrule')].rstrip()
    if not _t.endswith('\\\\'):
        _t += ' \\\\'
    open(_p, 'w').write(_hdr + _t + '\n\\bottomrule\n\\end{tabular}\n')
print('fragments are now complete tabulars')
