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
CELLS = [('fr_nfr', 'promise'), ('security', 'promise'), ('security', 'secreq'),
         ('subtype_top4', 'promise'), ('subtype_top6', 'promise'), ('subtype_all', 'promise')]


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
    order = [('security', 'promise', r'Security --- PROMISE\_exp'),
             ('security', 'secreq', r'Security --- SecReq'),
             ('fr_nfr', 'promise', r'FR/NFR --- PROMISE\_exp'),
             ('subtype_top4', 'promise', r'NFR sub-types, top-4'),
             ('subtype_top6', 'promise', r'NFR sub-types, top-6'),
             ('subtype_all', 'promise', r'NFR sub-types, all-11')]
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
HEADERS = {
 'tab_in_domain.tex': (
   "\\setlength{\\tabcolsep}{7pt}\n\\renewcommand{\\arraystretch}{1.05}\n"
   "\\begin{tabular}{@{}lcccccc@{}}\n\\toprule\n"
   "& \\textbf{FR/NFR} & \\multicolumn{2}{c}{\\textbf{Security}} "
   "& \\multicolumn{3}{c}{\\textbf{NFR sub-types (\\pex{})}} \\\\\n"
   "\\cmidrule(lr){2-2}\\cmidrule(lr){3-4}\\cmidrule(l){5-7}\n"
   "\\textbf{Configuration} & \\pex{} & \\pex{} & SecReq & top-4 & top-6 & all-11 \\\\\n"
   "\\midrule\n"),
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
