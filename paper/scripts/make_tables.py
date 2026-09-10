"""Emit the paper's numeric tables straight from the Stage-4/5 artefacts.

Every value written here is read back from a stored CSV; nothing is typed in by
hand. The table bodies are complete `tabular` environments so that main.tex can
`\input` them at table-body level.
"""
import pandas as pd, numpy as np, json, io

Z = '../artefacts/'
T = '../tables/'

ev  = pd.read_csv(Z+'results_Stage4_analysis/tab9_evaluability.csv')
gap = pd.read_csv(Z+'results_Stage4_analysis/tab3_generalisation_gap.csv')
c1  = pd.read_csv(Z+'results_Stage5_cost/cost1_per_model.csv')
be  = pd.read_csv(Z+'results_Stage5_cost/cost3_breakeven.csv')
dum = pd.read_csv(Z+'results_Stage4_analysis/tab0_baselines.csv')
snr = pd.read_csv(Z+'results_Stage4_analysis/tab8_prompt_sensitivity.csv')

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
ENCODERS = ['BERT (weighted)', 'BERT (unweighted)',
            'RoBERTa (weighted)', 'RoBERTa (unweighted)']
PROMPTED = ['Gemini-3.1-Flash-Lite', 'Llama-3.3-70B (Groq)',
            'Qwen2.5-7B', 'Llama-3.1-8B', 'Gemma-2-2B', 'Phi-4-mini',
            'SmolLM3-3B', 'Qwen2.5-3B']
ORDER = ENCODERS + PROMPTED

# Each column group: (task, dataset, regimes shown). The security task is the
# only one both corpora annotate, so it is the only one with a cross-dataset
# column; every other task is confined to PROMISE_exp.
GROUPS = [('security', 'promise', ['in_domain', 'cross_project', 'cross_dataset']),
          ('security', 'secreq',  ['in_domain', 'cross_project', 'cross_dataset']),
          ('fr_nfr',   'promise', ['in_domain', 'cross_project']),
          ('subtype_top4', 'promise', ['in_domain', 'cross_project']),
          ('subtype_top6', 'promise', ['in_domain', 'cross_project']),
          ('subtype_all',  'promise', ['in_domain', 'cross_project'])]


def get(model, task, ds, regime):
    r = ev[(ev.model == model) & (ev.task == task) & (ev.dataset == ds) &
           (ev.eval_regime == regime) & (ev.reportable)]
    return float(r.macro_f1.iloc[0]) if len(r) else None


def get_n(model, task, ds, regime):
    r = ev[(ev.model == model) & (ev.task == task) & (ev.dataset == ds) &
           (ev.eval_regime == regime) & (ev.reportable)]
    return int(r.n.iloc[0]) if len(r) else None


# ------------------------------------------------------- Table: the one table
# One table for the whole comparison. Encoders carry a score per regime because
# they are re-fitted at each one; a prompted model consumes no training data, so
# its score cannot move with the regime and is written once across the span.
def tab_main():
    cols = []                       # (task, ds, regime) in print order
    for task, ds, regs in GROUPS:
        cols += [(task, ds, r) for r in regs]

    best = {}
    for key in cols:
        vals = []
        for m in ORDER:
            v = get(m, *key) if m in ENCODERS else get(m, key[0], key[1], 'prompted')
            if v is not None:
                vals.append(v)
        best[key] = max(vals) if vals else None

    def fmt(v, key):
        if v is None:
            return '--'
        s = f'{v:.3f}'
        return r'\textbf{'+s+'}' if best[key] is not None and abs(v-best[key]) < 1e-9 else s

    lines = []
    for m in ENCODERS:
        cells = [fmt(get(m, *k), k) for k in cols]
        lines.append(f'{SHORT[m]} & ' + ' & '.join(cells) + r' \\')
    lines.append(r'\addlinespace[1.5pt]')
    for m in PROMPTED:
        cells = []
        for task, ds, regs in GROUPS:
            v = get(m, task, ds, 'prompted')
            key = (task, ds, regs[0])
            body = fmt(v, key)
            cells.append(r'\multicolumn{%d}{c}{%s}' % (len(regs), body))
        lines.append(f'{SHORT[m]} & ' + ' & '.join(cells) + r' \\')
        if m == 'Llama-3.3-70B (Groq)':
            lines.append(r'\addlinespace[1.5pt]')

    dummy = []
    for task, ds, regs in GROUPS:
        d = dum[(dum.task == task) & (dum.dataset == ds)]
        dummy.append(r'\multicolumn{%d}{c}{%.3f}' % (len(regs), float(d.macro_f1.iloc[0])))
    body = '\n'.join(lines) + '\n\\midrule\n' + \
        r'\textit{majority-class baseline} & ' + ' & '.join(dummy) + r' \\'
    open(T+'tab_main.tex', 'w').write(body + '\n')

    # item counts per column group, for the caption
    n = {}
    for task, ds, regs in GROUPS:
        n[(task, ds)] = (get_n('BERT (weighted)', task, ds, 'in_domain')
                         or get_n('BERT (weighted)', task, ds, 'cross_dataset'),
                         [get_n(m, task, ds, 'prompted') for m in PROMPTED])
    stats = {}
    for (task, ds), (ne, npr) in n.items():
        npr = [x for x in npr if x]
        stats[f'{task}_{ds}'] = dict(n_enc=ne, n_llm_min=min(npr), n_llm_max=max(npr))
    json.dump(stats, open(T+'main_stats.json', 'w'), indent=1)
    print('tab_main.tex ', {k: v['n_enc'] for k, v in stats.items()})


# ------------------------------------------- Table: relative loss under shift
# The companion to tab_main: the same encoder scores expressed as the fraction
# of in-domain macro-F1 that survives each regime, which is the quantity the
# text quotes. Prompted models have no in-domain reference of their own to lose,
# so the column simply does not apply to them and the table says so.
def tab_loss():
    out = []
    for j, (task, ds, regs) in enumerate(GROUPS):
        label = {'security': 'Security', 'fr_nfr': 'FR/NFR',
                 'subtype_top4': 'NFR sub-types, top-4',
                 'subtype_top6': 'NFR sub-types, top-6',
                 'subtype_all': 'NFR sub-types, all-11'}[task]
        if task == 'security':
            label += ' --- ' + (r'PROMISE\_exp' if ds == 'promise' else 'SecReq')
        if j:
            out.append(r'\addlinespace[2pt]')
        out.append(r'\multicolumn{6}{@{}l}{\itshape ' + label + r'} \\')
        for m in ENCODERS:
            idm = get(m, task, ds, 'in_domain')
            if idm is None:
                continue

            def pair(v):
                if v is None:
                    return '--', '--'
                return f'{v:.3f}', r'$-$' + f'{100*(idm-v)/idm:.0f}'
            a, da = pair(get(m, task, ds, 'cross_project'))
            b, db = pair(get(m, task, ds, 'cross_dataset'))
            out.append(f'\\quad {SHORT[m]} & {idm:.3f} & {a} & {da} & {b} & {db} ' + r'\\')
    open(T+'tab_loss.tex', 'w').write('\n'.join(out) + '\n')

    # the two loss figures the text quotes, so prose and table cannot drift
    xp, xd = [], []
    for task, ds, regs in GROUPS:
        for m in ENCODERS:
            idm = get(m, task, ds, 'in_domain')
            if idm is None:
                continue
            for reg, acc in (('cross_project', xp), ('cross_dataset', xd)):
                v = get(m, task, ds, reg)
                if v is not None:
                    acc.append(100*(idm-v)/idm)
    json.dump(dict(xp_max=max(xp), xp_min=min(xp), xd_max=max(xd), xd_min=min(xd)),
              open(T+'loss_stats.json', 'w'), indent=1)
    print('tab_loss.tex  worst cross-project %.1f%%  worst cross-dataset %.1f%%'
          % (max(xp), max(xd)))


# ------------------------------------------------ Table: what a wording buys
# Answers the obvious objection to a fixed prompt: how much of the result is the
# particular wording? Reported as the gain a target-labelled oracle would get by
# picking the best of the three wordings per cell.
def tab_prompt():
    s = snr.copy()
    s['best'] = s[['f1_base', 'f1_terse', 'f1_verbose']].max(axis=1)
    s['which'] = s[['f1_base', 'f1_terse', 'f1_verbose']].idxmax(axis=1).str.replace('f1_', '')
    s['gain'] = s.best - s.f1_base
    TASK = {'fr_nfr': 'FR/NFR', 'security': 'sec.',
            'subtype_all': 'sub-11', 'subtype_top4': 'sub-4',
            'subtype_top6': 'sub-6'}
    DS = {'promise': 'PR', 'secreq': 'SR'}
    rows = []
    for _, r in s.iterrows():
        rows.append(f'{SHORT[r.model]} & {TASK[r.task]}/{DS[r.dataset]} & '
                    f'{r.f1_base:.3f} & {r.f1_terse:.3f} & {r.f1_verbose:.3f} & '
                    f'{r.spread:.3f} & $+${r.gain:.3f} ' + r'\\')
    open(T+'tab_prompt.tex', 'w').write('\n'.join(rows) + '\n')
    json.dump(dict(n_cells=len(s), gain_med=float(s.gain.median()),
                   gain_max=float(s.gain.max()), gain_mean=float(s.gain.mean()),
                   spread_med=float(s.spread.median()),
                   spread_max=float(s.spread.max()),
                   n_terse_collapse=int((s.spread > 0.2).sum()),
                   spread_med_excl=float(s[s.spread <= 0.2].spread.median()),
                   spread_max_excl=float(s[s.spread <= 0.2].spread.max()),
                   n_base_best=int((s.which == 'base').sum())),
              open(T+'prompt_stats.json', 'w'), indent=1)
    print('tab_prompt.tex  best-of-three gain: median %.3f max %.3f'
          % (s.gain.median(), s.gain.max()))


# ------------------------------------------------------------ Table: the cost
# Split by what the price actually is: metered compute for anything that runs on
# our own GPU (the encoders and every open-weight local model, all of which are
# free to download), metered tokens for anything behind an API.
def tab_cost():
    rows = []
    for tier, label, basis in [
            ('finetuned', 'Fine-tuned encoder', 'GPU time'),
            ('open_local', 'Open-weight, local', 'GPU time'),
            ('open_hosted', 'Open-weight, hosted', 'tokens'),
            ('commercial', 'Commercial API', 'tokens')]:
        d = c1[c1.tier == tier]
        per = d.groupby('model').inference_usd_per_1k.median()
        lat = d.groupby('model').latency_s_median.median()
        sz = d.groupby('model').params_b.first().dropna()
        if not len(sz):
            szs = 'n/a'
        elif abs(sz.min() - sz.max()) < 1e-9:
            szs = f'{sz.min():.2f}'
        else:
            szs = f'{sz.min():.2f}--{sz.max():.2f}'
        tr = d[d.one_off_training_usd > 0].one_off_training_usd
        trs = f'{tr.median():.4f}' if len(tr) else '--'
        rows.append((label, len(per), szs, basis, f'{per.min():.4f}--{per.max():.4f}',
                     f'{lat.min():.3f}--{lat.max():.3f}', trs))
    with open(T+'tab_cost.tex', 'w') as f:
        for label, k, sz, basis, per, lat, tr in rows:
            per = per.split('--')[0] if per.split('--')[0] == per.split('--')[-1] else per
            lat = lat.split('--')[0] if lat.split('--')[0] == lat.split('--')[-1] else lat
            f.write(f'{label} & {k} & {sz} & {basis} & {per} & {lat} & {tr} ' + r'\\' + '\n')

    med = c1.groupby(['model', 'tier']).inference_usd_per_1k.median().reset_index()
    enc_med = float(med[med.tier == 'finetuned'].inference_usd_per_1k.median())
    pr = med[med.tier != 'finetuned'].inference_usd_per_1k
    loc = c1[c1.tier.isin(['finetuned', 'open_local'])]
    per_model = loc.groupby('model').agg(
        params_b=('params_b', 'first'),
        usd=('inference_usd_per_1k', 'median'),
        tok_out=('tokens_out', 'median')).dropna(subset=['params_b'])
    rho = per_model.params_b.rank().corr(per_model.usd.rank())
    stats = dict(
        be_min=int(be.breakeven_n_items.min()), be_max=int(be.breakeven_n_items.max()),
        be_med=int(be.breakeven_n_items.median()), be_pairs=len(be),
        be_all=int(be.encoder_cheaper_at_100k.sum()),
        enc_med=enc_med,
        pr_min=float(pr.min()), pr_max=float(pr.max()), pr_med=float(pr.median()),
        ratio_min=float(pr.min()/enc_med), ratio_max=float(pr.max()/enc_med),
        ratio_med=float(pr.median()/enc_med),
        train_med=float(c1[c1.one_off_training_usd > 0].one_off_training_usd.median()),
        size_cost_rho=float(rho),
    )
    json.dump(stats, open(T+'cost_stats.json', 'w'), indent=1)
    print('tab_cost.tex', stats)


tab_main(); tab_loss(); tab_prompt(); tab_cost()

# --- complete tabulars ------------------------------------------------------
# \input of a bare row block inside an alignment confuses TeX's lookahead at the
# file boundary, so each fragment ships the whole tabular and is \input at
# table-body level instead.
HEADERS = {
 'tab_main.tex': (
   "\\setlength{\\tabcolsep}{3.0pt}\n\\renewcommand{\\arraystretch}{1.05}\n"
   "\\begin{tabular}{@{}l*{14}{c}@{}}\n\\toprule\n"
   "& \\multicolumn{6}{c}{\\textbf{Security}} "
   "& \\multicolumn{2}{c}{\\textbf{FR/NFR}} "
   "& \\multicolumn{6}{c}{\\textbf{NFR sub-types} (\\pex{})} \\\\\n"
   "\\cmidrule(lr){2-7}\\cmidrule(lr){8-9}\\cmidrule(l){10-15}\n"
   "& \\multicolumn{3}{c}{\\pex{}} & \\multicolumn{3}{c}{SecReq} "
   "& \\multicolumn{2}{c}{\\pex{}} & \\multicolumn{2}{c}{top-4} "
   "& \\multicolumn{2}{c}{top-6} & \\multicolumn{2}{c}{all-11} \\\\\n"
   "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(lr){8-9}"
   "\\cmidrule(lr){10-11}\\cmidrule(lr){12-13}\\cmidrule(l){14-15}\n"
   "\\textbf{Configuration} & \\ID & \\XP & \\XD & \\ID & \\XP & \\XD "
   "& \\ID & \\XP & \\ID & \\XP & \\ID & \\XP & \\ID & \\XP \\\\\n"
   "\\midrule\n"),
 'tab_loss.tex': (
   "\\setlength{\\tabcolsep}{3.6pt}\n\\renewcommand{\\arraystretch}{1.06}\n"
   "\\begin{tabular}{@{}lccccc@{}}\n\\toprule\n"
   "& \\textbf{In-dom.} & \\multicolumn{2}{c}{\\textbf{Cross-project}} "
   "& \\multicolumn{2}{c}{\\textbf{Cross-dataset}} \\\\\n"
   "\\cmidrule(lr){2-2}\\cmidrule(lr){3-4}\\cmidrule(l){5-6}\n"
   "\\textbf{Fine-tuned encoder} & \\Fm{} & \\Fm{} & $\\Delta$\\% & \\Fm{} & $\\Delta$\\% \\\\\n"
   "\\midrule\n"),
 'tab_prompt.tex': (
   "\\setlength{\\tabcolsep}{2.6pt}\n\\renewcommand{\\arraystretch}{1.05}\n"
   "\\scriptsize\n\\begin{tabular}{@{}llccccc@{}}\n\\toprule\n"
   "\\textbf{Model} & \\textbf{Cell} & \\textbf{base} & \\textbf{terse} "
   "& \\textbf{verb.} & \\textbf{spread} & \\textbf{oracle} \\\\\n\\midrule\n"),
 'tab_cost.tex': (
   "\\setlength{\\tabcolsep}{2.0pt}\n\\renewcommand{\\arraystretch}{1.05}\n"
   "\\scriptsize\n\\begin{tabular}{@{}lcccccc@{}}\n\\toprule\n"
   "\\textbf{Tier} & \\textbf{Mod.} & \\textbf{B} & \\textbf{Basis} "
   "& \\textbf{USD/1k} & \\textbf{Latency (s)} "
   "& \\textbf{Train} \\\\\n\\midrule\n"),
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
