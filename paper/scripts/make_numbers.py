"""Read every number the paper reports back out of the stored artefacts.

Nothing in main.tex is typed by hand: this script writes

  tables/numbers.tex   one LaTeX macro per reported quantity
  tables/tab_main.tex  the single results table (Table III)
  tables/numbers.json  the same values, for checking

so that a reader (or a reviewer) can point at any figure in the text and find
the artefact column it came from.  Run from paper/scripts/ with the stage
outputs unzipped under ../../artefacts/.
"""
import json
import numpy as np
import pandas as pd

Z = '../../artefacts/'
T = '../tables/'

# ---------------------------------------------------------------- artefacts
ev   = pd.read_csv(Z+'results_Stage4_analysis/tab9_evaluability.csv')
mc   = pd.read_csv(Z+'results_Stage4_analysis/tab4_mcnemar.csv')
gap  = pd.read_csv(Z+'results_Stage4_analysis/tab3_generalisation_gap.csv')
pc   = pd.read_csv(Z+'results_Stage4_analysis/tab6_perclass.csv')
fs   = pd.read_csv(Z+'results_Stage4_analysis/tab7_fewshot.csv')
ps   = pd.read_csv(Z+'results_Stage4_analysis/tab8_prompt_sensitivity.csv')
ll   = pd.read_csv(Z+'results_Stage4_analysis/tab10_like_for_like.csv')
pp   = pd.read_csv(Z+'results_Stage4_analysis/tab11b_per_project_spread.csv')
dum  = pd.read_csv(Z+'results_Stage4_analysis/tab0_baselines.csv')
c1   = pd.read_csv(Z+'results_Stage5_cost/cost1_per_model.csv')
be   = pd.read_csv(Z+'results_Stage5_cost/cost3_breakeven.csv')
pa   = pd.read_csv(Z+'results_Stage5_cost/cost2_pareto.csv')
sc   = pd.read_csv(Z+'results_Stage5_cost/cost5_scaling.csv')
prov = json.load(open(Z+'results_Stage5_cost/stage5_provenance.json'))
mani = json.load(open(Z+'results_stage1_data_pipeline/data_processed/stage1_manifest.json'))
spl  = mani['splits']
uni  = pd.read_csv(Z+'results_stage1_data_pipeline/data_processed/unified.csv')
fin  = pd.read_parquet(Z+'results_stage2_finetuned_baselines/predictions_finetuned.parquet')
lpr  = pd.read_parquet(Z+'repair/predictions_llm_repaired.parquet')
spr  = pd.read_parquet(Z+'repair/predictions_subtype_repaired.parquet')

N = {}   # macro name -> already-formatted string
J = {}   # macro name -> raw value


def put(k, v, fmt='{}'):
    out = fmt.format(v)
    if isinstance(v, (int, float)) and out.startswith('-'):
        out = '$-$' + out[1:]      # a real minus sign, not a hyphen
    N[k] = out
    J[k] = v
    return v


def spearman(x, y):
    return float(np.corrcoef(pd.Series(x).rank(), pd.Series(y).rank())[0, 1])


# ================================================================ 1. corpus
put('NpromiseRaw', mani['promise']['raw_rows'], '{:,}')
put('NsecreqRaw',  mani['secreq']['raw_rows'], '{:,}')
put('Ndup',        mani['deduplication']['duplicate_texts_removed'])
put('Ntotal',      mani['deduplication']['rows_after'], '{:,}')
put('Npromise',    mani['deduplication']['final_by_source']['promise'])
put('Nsecreq',     mani['deduplication']['final_by_source']['secreq'])
put('Nshared',     mani['deduplication']['texts_appearing_in_BOTH_corpora'])
put('NpromiseProj', mani['promise']['projects'])
put('NsecreqProj',  uni[uni.source_dataset == 'secreq'].project.nunique())
put('Ngroups',      uni.groupby(['source_dataset', 'project']).ngroups)

prom = uni[uni.source_dataset == 'promise']
put('PrevPromise', 100*(prom.label_security == 'security').mean(), '{:.1f}')
put('PrevSecreq',  100*(uni[uni.source_dataset == 'secreq'].label_security == 'security').mean(), '{:.1f}')
put('NsecPromise', int((prom.label_security == 'security').sum()))
put('NsecSecreq',  int((uni[uni.source_dataset == 'secreq'].label_security == 'security').sum()))
put('NnfrPromise', int((prom.label_fr_nfr == 'NFR').sum()))
put('NfrPromise',  int((prom.label_fr_nfr == 'FR').sum()))
put('ShareNFR',    100*(prom.label_fr_nfr == 'NFR').mean(), '{:.1f}')

st = prom[prom.label_nfr_subtype.notna() & (prom.label_nfr_subtype != '')]
put('Nsubtypeall', len(st))
vc = st.label_nfr_subtype.value_counts()
put('Nsubtypesix',  int(vc.head(6).sum()))
put('Nsubtypefour', int(vc.head(4).sum()))
put('Nsplitfam', len(spl))
put('Nfolds', sum(v['n_folds'] for v in spl.values()))
put('Npred', len(fin)+len(lpr)+len(spr), '{:,}')
put('NpredEnc', len(fin), '{:,}')
put('NpredLLM', len(lpr)+len(spr), '{:,}')

# ============================================================ 2. gate/tests
put('Ncells',     len(ev))
put('Ncellsrep',  int(ev.reportable.sum()))
put('Ncellsdrop', int((~ev.reportable).sum()))
put('Ntests',   len(mc))
put('SigRaw',   int(mc.sig_raw.sum()))
put('SigBH',    int(mc.sig_bh.sum()))
put('SigHolm',  int(mc.sig_holm.sum()))

for reg, tag in [('in_domain', 'ID'), ('cross_dataset', 'XD')]:
    d = mc[mc.encoder_regime == reg]
    put('Win'+tag,  int((d.verdict == 'Encoder wins').sum()))
    put('Tie'+tag,  int((d.verdict == 'n.s.').sum()))
    put('Loss'+tag, int((d.verdict == 'LLM wins').sum()))
    put('Ntest'+tag, len(d))
d = mc[mc.encoder_regime.str.startswith('cross_project')]
put('WinXP',  int((d.verdict == 'Encoder wins').sum()))
put('TieXP',  int((d.verdict == 'n.s.').sum()))
put('LossXP', int((d.verdict == 'LLM wins').sum()))
put('NtestXP', len(d))
put('AheadXP', int((d.verdict != 'LLM wins').sum()))

gm = mc[mc.llm == 'Gemini-3.1-Flash-Lite']
put('NtestGemini', len(gm))
put('TieGemini', int((gm.verdict == 'n.s.').sum()))
put('NGemini', int(gm.n_paired.median()))

# ============================================================== 3. transfer
def gapof(model, task, ds):
    r = gap[(gap.model == model) & (gap.task == task) & (gap.evaluated_on == ds)]
    return r


g = gap[(gap.oos_regime == 'cross_dataset')].sort_values('relative_drop_pct')
put('DropXDmax',   g.relative_drop_pct.max(), '{:.1f}')
put('DropXDmin',   g.relative_drop_pct.min(), '{:.1f}')
worst = g.iloc[-1]
put('XDrefF',   worst.reference_f1, '{:.3f}')
put('XDtransF', worst.transfer_f1, '{:.3f}')
for m, k in [('RoBERTa (weighted)', 'Rw'), ('BERT (unweighted)', 'Bu'), ('RoBERTa (unweighted)', 'Ru')]:
    r = g[(g.model == m) & (g.evaluated_on == 'promise')]
    put('DropXD'+k, r.relative_drop_pct.iloc[0], '{:.1f}')
rev = g[g.evaluated_on == 'secreq']
put('DropXDrevMin', rev.relative_drop_pct.min(), '{:.1f}')
put('DropXDrevMax', rev.relative_drop_pct.max(), '{:.1f}')

gp = gap[gap.oos_regime.str.startswith('cross_project')]
put('DropXPmax', gp.relative_drop_pct.max(), '{:.1f}')
gpp = gp[gp.evaluated_on == 'promise']
put('DropXPpromMin', gpp.relative_drop_pct.min(), '{:.1f}')
put('DropXPpromMax', gpp.relative_drop_pct.max(), '{:.1f}')

# ===================================================== 4. predicted priors
sec = fin[fin.task == 'security']


def share(tag, ds, reg):
    d = sec[(sec.model_tag == tag) & (sec.dataset == ds) & (sec.eval_regime == reg)]
    return 100*(d.y_pred == 'security').mean()


put('ShareBertXD',   share('bert-base-uncased-weighted', 'promise', 'cross_dataset'), '{:.1f}')
put('ShareBertID',   share('bert-base-uncased-weighted', 'promise', 'in_domain'), '{:.1f}')
put('ShareRobXD',    share('roberta-base-weighted', 'promise', 'cross_dataset'), '{:.1f}')
put('ShareBertRev',  share('bert-base-uncased-weighted', 'secreq', 'cross_dataset'), '{:.1f}')
put('ShareRobRev',   share('roberta-base-weighted', 'secreq', 'cross_dataset'), '{:.1f}')

q = pc[(pc.model == 'BERT (weighted)') & (pc.task == 'security') &
       (pc.dataset == 'promise') & (pc.category == 'security')]
for reg, k in [('in_domain', 'ID'), ('cross_dataset', 'XD')]:
    r = q[q.eval_regime == reg].iloc[0]
    put('Prec'+k, r.precision, '{:.3f}')
    put('Rec'+k,  r.recall, '{:.3f}')

L = lpr[(lpr.task == 'fr_nfr') & (lpr.dataset == 'promise') &
        (lpr.shot_k == 0) & (lpr.prompt_id == 'base')]
rows = []
for tag, gg in L.groupby('model_tag'):
    if 'nemotron' in tag:
        continue
    rows.append((tag, (gg.y_pred_strict == 'NFR').mean(),
                 (gg.y_pred_strict == gg.y_true).mean()))
D = pd.DataFrame(rows, columns=['m', 'pred', 'acc'])
put('LLMnfrMin', 100*D.pred.min(), '{:.1f}')
put('LLMnfrMax', 100*D.pred.max(), '{:.1f}')
put('LLMnfrMinModel', 'Qwen2.5-3B' if 'qwen2.5-3b' in D.loc[D.pred.idxmin(), 'm'] else D.loc[D.pred.idxmin(), 'm'])
put('RhoPrior', spearman(D.pred, D.acc), '{:.2f}')
put('NLLMprior', len(D))

# ============================================================== 5. prompts
put('SpreadMed', ps.spread.median(), '{:.3f}')
put('SpreadMax', ps.spread.max(), '{:.3f}')
put('NpsCells',  len(ps))
ps = ps.copy()
ps['oracle'] = ps[['f1_base', 'f1_terse', 'f1_verbose']].max(axis=1) - ps.f1_base
put('OracleMed', ps.oracle.median(), '{:.3f}')
put('OracleMax', ps.oracle.max(), '{:.3f}')

allp = pd.concat([lpr, spr], ignore_index=True)
sel = allp[allp.model_tag.isin(['gemma-2-2b-it', 'qwen2.5-7b-instruct']) & (allp.shot_k == 0)]
put('NpsRows', len(sel), '{:,}')
put('PsParse', 100*sel.parse_ok_v2.mean(), '{:.2f}')
gt = allp[(allp.model_tag == 'gemma-2-2b-it') & (allp.task == 'security') &
          (allp.dataset == 'secreq') & (allp.prompt_id == 'terse') & (allp.shot_k == 0)]
put('TerseShare', 100*(gt.y_pred_strict == 'security').mean(), '{:.1f}')
put('TerseTrue',  100*(gt.y_true == 'security').mean(), '{:.1f}')

put('NfsTests', len(fs))
put('FsMed', fs.gain.median(), '{:+.3f}')
b = fs[fs.task.isin(['fr_nfr', 'security'])]
s = fs[fs.task.str.startswith('subtype')]
put('FsBinN', len(b)); put('FsBinMean', b.gain.mean(), '{:+.3f}')
put('FsSubN', len(s)); put('FsSubMean', s.gain.mean(), '{:+.3f}')

# ========================================================== 6. per project
q = pp[(pp.task == 'fr_nfr') & (pp.spread_comparable)]
enc = q[q.tier == 'finetuned']; loc = q[q.tier == 'open_local']
put('NppProj', int(q.n_projects.max()))
put('PpEncMed', enc.acc_median.max(), '{:.3f}')
put('PpEncSdMin', enc.acc_std.min(), '{:.3f}')
put('PpEncSdMax', enc.acc_std.max(), '{:.3f}')
put('PpLocMedMin', loc.acc_median.min(), '{:.3f}')
put('PpLocMedMax', loc.acc_median.max(), '{:.3f}')
put('PpLocSdMin', loc.acc_std.min(), '{:.3f}')
put('PpLocSdMax', loc.acc_std.max(), '{:.3f}')

# ================================================================= 7. cost
med = c1.groupby(['model', 'tier'], dropna=False).agg(
    params=('params_b', 'median'), cpk=('inference_usd_per_1k', 'median'),
    lat=('latency_s_median', 'median')).reset_index()
encc = float(med[med.tier == 'finetuned'].cpk.median())
pm = med[med.tier != 'finetuned']
put('CostEnc', encc, '{:.4f}')
put('CostLLMmin', pm.cpk.min(), '{:.4f}')
put('CostLLMmax', pm.cpk.max(), '{:.4f}')
put('RatioMin', pm.cpk.min()/encc, '{:.0f}')
put('RatioMax', pm.cpk.max()/encc, '{:.0f}')
put('RatioMed', pm.cpk.median()/encc, '{:.0f}')
loc10 = med[med.tier.isin(['finetuned', 'open_local'])].dropna(subset=['params'])
put('NlocalCfg', len(loc10))
put('RhoSize', spearman(loc10.params, loc10.cpk), '{:.2f}')

tr = c1[c1.one_off_training_usd > 0].groupby('model').one_off_training_usd.median()
put('TrainMed', tr.median(), '{:.4f}')
put('TrainSec', c1[c1.train_time_s_all_folds > 0].groupby('model').train_time_s_all_folds.median().median(), '{:.0f}')
put('NBE', len(be))
put('BEmin', int(be.breakeven_n_items.min()))
put('BEmax', int(be.breakeven_n_items.max()))
put('BEmed', int(be.breakeven_n_items.median()))
put('NPareto', len(pa))
put('NParetoEnc', int((pa.tier == 'finetuned').sum()))
pfront = pa[pa.tier != 'finetuned'].iloc[0]
encsame = pa[(pa.task == pfront.task) & (pa.dataset == pfront.dataset) & (pa.tier == 'finetuned')]
put('ParetoLLM', pfront.model)
put('ParetoGain', float(pfront.macro_f1) - float(encsame.macro_f1.max()), '{:.3f}')
put('ParetoRatio', float(pfront.inference_usd_per_1k)/encc, '{:.0f}')

lt = c1.groupby('tier').latency_s_median.median()
put('LatEnc', lt['finetuned'], '{:.3f}')
put('LatHost', lt['open_hosted'], '{:.3f}')
put('LatCom', lt['commercial'], '{:.3f}')
lloc = c1[c1.tier == 'open_local'].groupby('model').latency_s_median.median()
put('LatLocMin', lloc.min(), '{:.3f}'); put('LatLocMax', lloc.max(), '{:.3f}')

put('GpuOnDemand', prov['gpu_price_usd_per_hour']['on_demand'], '{:.4f}')
put('GpuSpot',     prov['gpu_price_usd_per_hour']['spot'], '{:.4f}')
put('GpuSource',   prov['gpu_price_source'])
pr = lpr[lpr.price_in_per_mtok > 0].groupby('model_tag')[['price_in_per_mtok', 'price_out_per_mtok']].first()
put('PriceGemIn',  pr.loc['gemini-3.1-flash-lite', 'price_in_per_mtok'], '{:.2f}')
put('PriceGemOut', pr.loc['gemini-3.1-flash-lite', 'price_out_per_mtok'], '{:.2f}')
put('PriceLlaIn',  pr.loc['groq-llama-3.3-70b-versatile', 'price_in_per_mtok'], '{:.2f}')
put('PriceLlaOut', pr.loc['groq-llama-3.3-70b-versatile', 'price_out_per_mtok'], '{:.2f}')

# worked example: total USD to classify 10,000 requirements
w = sc[sc.n_requirements == 10000]
def tot(m):
    return float(w[w.model == m].total_usd.median())
put('TenkEnc',  tot('BERT (weighted)'), '{:.2f}')
put('TenkQwen', tot('Qwen2.5-3B'), '{:.2f}')
put('TenkGem',  tot('Gemini-3.1-Flash-Lite'), '{:.2f}')
put('TenkLla',  tot('Llama-3.3-70B (Groq)'), '{:.2f}')

# ============================================ 8. the single results table
SHORT = {
    'BERT (weighted)': r'BERT\textsubscript{w}',
    'BERT (unweighted)': r'BERT\textsubscript{u}',
    'RoBERTa (weighted)': r'RoBERTa\textsubscript{w}',
    'RoBERTa (unweighted)': r'RoBERTa\textsubscript{u}',
    'Gemini-3.1-Flash-Lite': 'Gemini 3.1 Flash-Lite',
    'Llama-3.3-70B (Groq)': 'Llama-3.3-70B',
    'Qwen2.5-7B': 'Qwen2.5-7B', 'Llama-3.1-8B': 'Llama-3.1-8B',
    'Gemma-2-2B': 'Gemma-2-2B', 'Phi-4-mini': 'Phi-4-mini',
    'SmolLM3-3B': 'SmolLM3-3B', 'Qwen2.5-3B': 'Qwen2.5-3B',
}
ENC = ['BERT (weighted)', 'BERT (unweighted)',
       'RoBERTa (weighted)', 'RoBERTa (unweighted)']
LLM = ['Gemini-3.1-Flash-Lite', 'Llama-3.3-70B (Groq)', 'Qwen2.5-7B',
       'Llama-3.1-8B', 'Gemma-2-2B', 'Phi-4-mini', 'SmolLM3-3B', 'Qwen2.5-3B']
# (task, dataset, [regimes])
GROUPS = [('security', 'promise', ['in_domain', 'cross_project', 'cross_dataset']),
          ('security', 'secreq',  ['in_domain', 'cross_project', 'cross_dataset']),
          ('fr_nfr',   'promise', ['in_domain', 'cross_project']),
          ('subtype_top4', 'promise', ['in_domain', 'cross_project']),
          ('subtype_top6', 'promise', ['in_domain', 'cross_project']),
          ('subtype_all',  'promise', ['in_domain', 'cross_project'])]


def score(model, task, ds, regime):
    r = ev[(ev.model == model) & (ev.task == task) & (ev.dataset == ds) &
           (ev.eval_regime == regime) & (ev.reportable)]
    return float(r.macro_f1.iloc[0]) if len(r) else None


best = {}
for task, ds, regs in GROUPS:
    for reg in regs:
        vals = [score(m, task, ds, reg) for m in ENC]
        vals += [score(m, task, ds, 'prompted') for m in LLM]
        vals = [v for v in vals if v is not None]
        best[(task, ds, reg)] = max(vals) if vals else None

lines = []
for m in ENC:
    cells = []
    for task, ds, regs in GROUPS:
        for reg in regs:
            v = score(m, task, ds, reg)
            if v is None:
                cells.append('--')
            else:
                s = f'{v:.3f}'
                cells.append(r'\bfseries '+s if abs(v-best[(task, ds, reg)]) < 1e-9 else s)
    lines.append(SHORT[m] + ' & ' + ' & '.join(cells) + r' \\')
lines.append(r'\addlinespace[2pt]')
for m in LLM:
    cells = []
    for task, ds, regs in GROUPS:
        v = score(m, task, ds, 'prompted')
        k = len(regs)
        if v is None:
            cells.append(r'\multicolumn{%d}{c}{--}' % k)
        else:
            s = f'{v:.3f}'
            if abs(v-(best[(task, ds, regs[0])] or -1)) < 1e-9:
                s = r'\bfseries '+s
            cells.append(r'\multicolumn{%d}{c}{%s}' % (k, s))
    lines.append(SHORT[m] + ' & ' + ' & '.join(cells) + r' \\')
lines.append(r'\midrule')
cells = []
for task, ds, regs in GROUPS:
    d = dum[(dum.task == task) & (dum.dataset == ds)]
    cells.append(r'\multicolumn{%d}{c}{%s}' % (len(regs), f'{float(d.macro_f1.iloc[0]):.3f}'))
lines.append(r'\itshape majority-class baseline & ' + ' & '.join(cells) + r' \\')
# The fragment ships its own complete tabular: \input of a bare row block
# inside an alignment confuses TeX's lookahead at the file boundary.
HEAD = (r'''\setlength{\tabcolsep}{3.0pt}
\renewcommand{\arraystretch}{1.02}
\scriptsize
\begin{tabular}{@{}l*{14}{c}@{}}
\toprule
& \multicolumn{3}{c}{\textbf{Security --- \pex{}}}
& \multicolumn{3}{c}{\textbf{Security --- SecReq}}
& \multicolumn{2}{c}{\textbf{FR/NFR --- \pex{}}}
& \multicolumn{2}{c}{\textbf{Sub-types top-4}}
& \multicolumn{2}{c}{\textbf{Sub-types top-6}}
& \multicolumn{2}{c}{\textbf{Sub-types all-11}} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-9}%
\cmidrule(lr){10-11}\cmidrule(lr){12-13}\cmidrule(l){14-15}
\textbf{Configuration}
& ID & XP & XD & ID & XP & XD & ID & XP & ID & XP & ID & XP & ID & XP \\
\midrule
''')
open(T+'tab_main.tex', 'w').write(
    HEAD + '\n'.join(lines) + '\n\\bottomrule\n\\end{tabular}\n')

# item counts behind each group, for the table note
ns = []
for task, ds, regs in GROUPS:
    r = ev[(ev.task == task) & (ev.dataset == ds) & (ev.eval_regime == 'in_domain')]
    ns.append(int(r.n.max()))
put('NcellItems', '/'.join(str(x) for x in ns))
pr_n = ev[(ev.eval_regime == 'prompted') & (ev.reportable)].n
put('NpromptMin', int(pr_n.min())); put('NpromptMax', int(pr_n.max()))

# in-domain leads the text quotes
put('SecreqBestLLM', score('Qwen2.5-7B', 'security', 'secreq', 'prompted'), '{:.3f}')
put('SecreqBestEnc', score('BERT (weighted)', 'security', 'secreq', 'in_domain'), '{:.3f}')
r = mc[(mc.task == 'security') & (mc.dataset == 'secreq') &
       (mc.encoder_regime == 'in_domain') & (mc.llm == 'Qwen2.5-7B') &
       (mc.encoder == 'BERT (weighted)')].iloc[0]
put('SecreqP', r.p_value, '{:.3f}')
put('SecreqPBH', r.p_bh, '{:.3f}')
for task, key in [('subtype_top4', 'Four'), ('subtype_all', 'All')]:
    e = max(score(m, task, 'promise', 'in_domain') or 0 for m in ENC)
    l = max(score(m, task, 'promise', 'prompted') or 0 for m in LLM)
    put('Lead'+key, e-l, '{:.3f}')
t4 = ll[ll.task == 'subtype_top4'].sort_values('macro_f1_common', ascending=False)
put('NcommonFour', int(t4.n_common.iloc[0]))
put('LeadFourCommon', float(t4.macro_f1_common.iloc[0]) - float(
    t4[t4.tier != 'finetuned'].macro_f1_common.max()), '{:.3f}')
put('GemmaSec', score('Gemma-2-2B', 'security', 'promise', 'prompted'), '{:.3f}')
put('LlamaSec', score('Llama-3.3-70B (Groq)', 'security', 'promise', 'prompted'), '{:.3f}')

# ----------------------------------------------------------------- write
with open(T+'numbers.tex', 'w') as f:
    f.write('%% Generated by scripts/make_numbers.py -- do not edit by hand.\n')
    for k in sorted(N):
        f.write('\\newcommand{\\n%s}{%s}\n' % (k, N[k]))
json.dump(J, open(T+'numbers.json', 'w'), indent=1, default=str)
print(f'{len(N)} macros -> {T}numbers.tex')
for k in sorted(N):
    print(f'  {k:18s} {N[k]}')
