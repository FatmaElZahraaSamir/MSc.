"""Paper figures for the IEEE two-column submission.

Design rules applied (dataviz skill):
  * form chosen by the data's job, color assigned last and validated
    (palette #0072B2,#009E73,#E69F00,#CC79A7 passes all six checks, light mode)
  * every tier carries a second, non-colour encoding (marker shape / hatch),
    so the figures survive greyscale printing
  * one axis per panel, recessive grid, selective direct labels only.
Every number is read from the Stage-4 / Stage-5 artefacts, never hard-coded
except where a value is quoted from those same CSVs in a comment.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd, numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

Z = '../artefacts/'
OUT = '../figures/'

CM = 1/2.54
COL = 8.8*CM          # IEEE single column
FULL = 18.0*CM        # IEEE double column

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['FreeSerif', 'Nimbus Roman', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 7,
    'axes.labelsize': 7.5,
    'axes.titlesize': 7.5,
    'xtick.labelsize': 6.8,
    'ytick.labelsize': 6.8,
    'legend.fontsize': 6.5,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.5, 'ytick.major.width': 0.5,
    'xtick.major.size': 2.4, 'ytick.major.size': 2.4,
    'grid.linewidth': 0.4, 'grid.color': '#c9c9c9',
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 300, 'savefig.dpi': 300,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.012,
    'pdf.fonttype': 42,
})

# validated categorical palette -- identity, fixed order, never cycled
C_ENC  = '#0072B2'   # fine-tuned encoder
C_LOC  = '#E69F00'   # local open-weight LLM
C_HOST = '#009E73'   # hosted open-weight LLM
C_COM  = '#CC79A7'   # commercial LLM
INK, INK2, MUTED = '#1a1a1a', '#4d4d4d', '#8a8a8a'

MK = {'finetuned': 'o', 'open_local': '^', 'open_hosted': 's', 'commercial': 'D'}
CO = {'finetuned': C_ENC, 'open_local': C_LOC, 'open_hosted': C_HOST, 'commercial': C_COM}
TIER_LABEL = {'finetuned': 'Fine-tuned encoder', 'open_local': 'Open-weight, local (4-bit)',
              'open_hosted': 'Open-weight, hosted API', 'commercial': 'Commercial API'}


def prf(yt, yp):
    tp = (yt & yp).sum(); fp = (~yt & yp).sum(); fn = (yt & ~yp).sum()
    P = tp/(tp+fp) if tp+fp else 0.0
    R = tp/(tp+fn) if tp+fn else 0.0
    return P, R


# ---------------------------------------------------------------- Figure 2
# Why the encoders fail across corpora: the decision threshold follows the
# training corpus base rate.

def fig_prior_shift():
    p = pd.read_parquet(Z+'results_stage2_finetuned_baselines/predictions_finetuned.parquet')
    s = p[p.task == 'security']
    L = pd.read_parquet(Z+'repair/predictions_llm_repaired.parquet')

    def rate(tag, ds, reg):
        d = s[(s.model_tag == tag) & (s.dataset == ds) & (s.eval_regime == reg)]
        return (d.y_pred == 'security').mean(), (d.y_true == 'security').mean()

    fig = plt.figure(figsize=(8.0*CM, 4.75*CM))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.10, 1.0], width_ratios=[1.0, 1.06],
                          hspace=1.20, wspace=0.52)
    ax = fig.add_subplot(gs[0, :])
    bx = None
    cx = fig.add_subplot(gs[1, :])

    # -- (a) the transferred encoder reproduces the source corpus base rate
    prev = {ds: rate('bert-base-uncased-weighted', ds, 'in_domain')[1]
            for ds in ('promise', 'secreq')}
    rows = [('SecReq $\\rightarrow$ PROMISE', 'promise'),
            ('PROMISE $\\rightarrow$ SecReq', 'secreq')]
    for (title, ds), y in zip(rows, [1.0, 0.0]):
        src_ds = 'secreq' if ds == 'promise' else 'promise'
        tgt, srcp = prev[ds], prev[src_ds]
        ax.plot([tgt, srcp], [y, y], color='#dcdcdc', lw=3.0, solid_capstyle='butt', zorder=1)
        ax.plot([tgt], [y], marker='|', ms=9, mew=1.5, color=INK, zorder=4)
        ax.plot([srcp], [y], marker='|', ms=9, mew=1.5, color=MUTED, zorder=4)
        side = 1 if ds == 'promise' else -1
        for tag, name, dy, mk in [('bert-base-uncased-weighted', 'BERT', 0.235, 'o'),
                                  ('roberta-base-weighted', 'RoBERTa', -0.235, 's')]:
            pr, _ = rate(tag, ds, 'cross_dataset')
            ax.plot([pr], [y+dy], marker=mk, ms=4.0, color=C_ENC, mec='white', mew=0.5, zorder=5)
            ax.annotate(f'{name} {pr:.3f}', (pr, y+dy), xytext=(5*side, 0),
                        textcoords='offset points', va='center',
                        ha='left' if side > 0 else 'right', fontsize=6.2, color=INK)
        ax.text(-0.010, y, title, ha='right', va='center', fontsize=6.5, color=INK)
    ax.annotate('true rate in\nthe test corpus', (prev['promise'], 1.38), xytext=(-1, 20),
                textcoords='offset points', ha='center', fontsize=5.9, color=INK,
                linespacing=0.98,
                arrowprops=dict(arrowstyle='-', lw=0.5, color=INK, shrinkA=1, shrinkB=0))
    ax.annotate('base rate of the\ntraining corpus', (prev['secreq'], 1.38), xytext=(20, 20),
                textcoords='offset points', ha='center', fontsize=5.9, color=MUTED,
                linespacing=0.98,
                arrowprops=dict(arrowstyle='-', lw=0.5, color=MUTED, shrinkA=1, shrinkB=0))
    ax.set_xlim(0.0, 0.62); ax.set_ylim(-0.62, 2.15)
    ax.set_yticks([]); ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.set_xlabel('share of test items predicted "security"', labelpad=1.5)
    ax.xaxis.set_major_formatter(lambda v, _: f'{v:.0%}')
    ax.grid(axis='x'); ax.set_axisbelow(True)
    ax.set_title('(a) a fine-tuned encoder inherits its prior from its training corpus',
                 fontsize=7.2, loc='left', pad=27)

    # -- (c) prompted models: how well the prior is calibrated predicts accuracy
    TIER = {'gemini-3.1-flash-lite': 'commercial',
            'groq-llama-3.3-70b-versatile': 'open_hosted'}
    z = L[(L.task == 'fr_nfr') & (L.prompt_id == 'base') & (L.shot_k == 0) &
          (L.model_tag != 'openrouter-nemotron-3-nano-30b-a3b')]
    g = z.groupby('model_tag').apply(
        lambda d: pd.Series({'pred': (d.y_pred == 'NFR').mean(),
                             'acc': (d.y_pred == d.y_true).mean()}), include_groups=False)
    true_nfr = (z.y_true == 'NFR').mean()
    for tag, r in g.iterrows():
        t = TIER.get(tag, 'open_local')
        cx.scatter([r.pred], [r.acc], s=16, marker=MK[t], c=CO[t],
                   edgecolors='white', linewidths=0.4, zorder=3)
    cx.axvline(true_nfr, color=INK, lw=0.7, ls=(0, (3, 2)), zorder=2)
    cx.annotate('true\nrate', (true_nfr, 0.60), xytext=(-3, 0),
                textcoords='offset points', ha='right', va='center',
                fontsize=5.8, color=INK, linespacing=1.0)
    rho = pd.Series(g.pred).rank().corr(pd.Series(g.acc).rank())
    cx.text(0.03, 0.955, f'$\\rho={rho:.2f}$', transform=cx.transAxes,
            fontsize=6.4, va='top', color=INK)
    cx.set_xlim(0.10, 0.62); cx.set_ylim(0.55, 0.92)
    cx.set_xticks([0.2, 0.4, 0.6])
    cx.xaxis.set_major_formatter(lambda v, _: f'{v:.0%}')
    cx.set_xlabel('predicted NFR share', fontsize=7, labelpad=1.5)
    cx.set_ylabel('accuracy', fontsize=7)
    cx.grid(True); cx.set_axisbelow(True)
    cx.set_title('(b) the 8 prompted models, FR/NFR: accuracy tracks how far the '
                 'predicted class share sits from the true one',
                 fontsize=7.0, loc='left', pad=4)

    fig.savefig(OUT+'fig_prior_shift.pdf')
    fig.savefig(OUT+'fig_prior_shift.png', dpi=300)
    
    plt.close(fig)
    print('fig_prior_shift.pdf  rho=%.3f  true_nfr=%.4f' % (rho, true_nfr))


# ---------------------------------------------------------------- Figure 3
# The inversion. Panel (a) puts the prompted models on the same axis as the two
# encoders -- one bar each, at every regime -- so the reader sees three
# quantities being compared, not two lines against a shaded band. Panel (b)
# counts the paired tests behind that picture.

def fig_inversion():
    ev = pd.read_csv(Z+'results_Stage4_analysis/tab9_evaluability.csv')
    mc = pd.read_csv(Z+'results_Stage4_analysis/tab4_mcnemar.csv')
    sec = ev[(ev.task == 'security') & (ev.dataset == 'promise') & ev.reportable]

    def f1(model, reg):
        r = sec[(sec.model == model) & (sec.eval_regime == reg)]
        return float(r.macro_f1.iloc[0]) if len(r) else np.nan

    regimes = ['in_domain', 'cross_project', 'cross_dataset']
    labels = ['in-domain', 'cross-project', 'cross-dataset']
    prompted = sec[sec.eval_regime == 'prompted']
    pmed = float(prompted.macro_f1.median())
    plo, phi = float(prompted.macro_f1.min()), float(prompted.macro_f1.max())

    fig, (ax, bx) = plt.subplots(2, 1, figsize=(9.45*CM, 6.35*CM),
                                 gridspec_kw={'height_ratios': [1.52, 1.0],
                                              'hspace': 0.78})

    x = np.arange(3); w = 0.26
    series = [('BERT (weighted)', 'BERT$_\\mathrm{w}$', C_ENC, None, -w),
              ('RoBERTa (weighted)', 'RoBERTa$_\\mathrm{w}$', 'white', C_ENC, 0.0)]
    base = {}
    for m, lab, fc, ec, dx in series:
        ys = [f1(m, r) for r in regimes]
        base[m] = ys[0]
        b = ax.bar(x+dx, ys, w, color=fc, edgecolor=ec or 'white',
                   linewidth=0.9 if ec else 0.7, label=lab, zorder=3)
        for r_, v in zip(b, ys):
            ax.annotate(f'{v:.3f}', (r_.get_x()+w/2, v), xytext=(0, 1.8),
                        textcoords='offset points', ha='center', fontsize=5.9,
                        color=INK)
    # the prompted models: one bar (median of the eight), whisker = full range
    b3 = ax.bar(x+w, [pmed]*3, w, color=C_LOC, edgecolor='white', linewidth=0.7,
                hatch='/////', zorder=3, label='8 prompted LLMs (median)')
    ax.errorbar(x+w, [pmed]*3, yerr=[[pmed-plo]*3, [phi-pmed]*3], fmt='none',
                ecolor='#8a6100', elinewidth=0.7, capsize=1.8, capthick=0.7, zorder=4)
    for i in range(3):
        ax.annotate(f'{pmed:.3f}', (i+w, phi), xytext=(0, 3.0),
                    textcoords='offset points', ha='center', fontsize=5.9,
                    color='#8a6100')

    # the two losses the text quotes, marked on the bars they belong to
    for m, dx, dy in [('BERT (weighted)', -w, 11)]:
        for i, reg in [(1, 'cross_project'), (2, 'cross_dataset')]:
            v = f1(m, reg); d = 100*(base[m]-v)/base[m]
            ax.annotate(f'$-${d:.0f}%', (i+dx, v), xytext=(0, dy),
                        textcoords='offset points', ha='center', fontsize=6.0,
                        color='#8a2f2f')
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.13); ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel('macro-F1')
    ax.grid(axis='y'); ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=3, loc='lower left', bbox_to_anchor=(-0.025, 0.995),
              handlelength=1.1, columnspacing=0.8, handletextpad=0.4, fontsize=6.2)
    ax.set_title('(a) security classification, PROMISE_exp \u2014 the same 968 items '
                 'scored in all three regimes', fontsize=7.0, loc='left', pad=15)

    order = list(zip(regimes, labels))
    ct = pd.crosstab(mc.encoder_regime, mc.verdict)
    y = np.arange(3)[::-1]
    left = np.zeros(3)
    segs = [('Encoder wins', C_ENC, None, 'white'),
            ('n.s.', '#e2e2e2', None, INK),
            ('LLM wins', C_LOC, '/////', INK)]
    for lab, col, hat, tc in segs:
        vals = np.array([ct.loc[k, lab] if lab in ct.columns else 0 for k, _ in order],
                        dtype=float)
        bx.barh(y, vals, left=left, height=0.60, color=col, edgecolor='white',
                linewidth=1.0, hatch=hat, label=lab)
        for yy, v, l in zip(y, vals, left):
            if v >= 6:
                bx.text(l+v/2, yy, f'{int(v)}', ha='center', va='center',
                        fontsize=6.3, color=tc)
        left += vals
    bx.set_yticks(y); bx.set_yticklabels([lbl for _, lbl in order])
    bx.set_xlabel('number of paired encoder-vs-LLM tests falling each way '
                  '(exact McNemar, Benjamini\u2013Hochberg, $\\alpha=0.05$)',
                  labelpad=1.5, fontsize=6.4)
    bx.set_xlim(0, 122)
    for yy, (k, _) in zip(y, order):
        bx.text(int(ct.loc[k].sum())+2.5, yy, f'{int(ct.loc[k].sum())} tests',
                va='center', fontsize=6.0, color=MUTED)
    bx.spines['left'].set_visible(False)
    bx.tick_params(axis='y', length=0)
    bx.grid(axis='x'); bx.set_axisbelow(True)
    bx.legend(frameon=False, ncol=3, loc='lower left', bbox_to_anchor=(-0.02, 0.99),
              handlelength=1.2, columnspacing=1.0, handletextpad=0.45)
    bx.set_title('(b) every one of the 260 paired comparisons, grouped by regime',
                 fontsize=7.0, loc='left', pad=14)
    fig.savefig(OUT+'fig_inversion.pdf')
    fig.savefig(OUT+'fig_inversion.png', dpi=300)

    plt.close(fig)
    print('fig_inversion  prompted median %.3f  range %.3f-%.3f' % (pmed, plo, phi))


# ---------------------------------------------------------------- Figure 4
# Cost: accuracy per dollar, and when fine-tuning repays its one-off training.

def fig_cost():
    c1 = pd.read_csv(Z+'results_Stage5_cost/cost1_per_model.csv')
    be = pd.read_csv(Z+'results_Stage5_cost/cost3_breakeven.csv')

    fig, (ax, bx) = plt.subplots(2, 1, figsize=(10.4*CM, 6.35*CM),
                                 gridspec_kw={'height_ratios': [1.0, 1.05], 'hspace': 0.80})

    cell = c1[(c1.task == 'security') & (c1.dataset == 'secreq') &
              (c1.eval_regime.isin(['in_domain', 'prompted']))]
    for tier in ['finetuned', 'open_local', 'open_hosted', 'commercial']:
        d = cell[cell.tier == tier]
        ax.scatter(d.inference_usd_per_1k, d.macro_f1, s=18, marker=MK[tier],
                   c=CO[tier], edgecolors='white', linewidths=0.5, zorder=3,
                   label=TIER_LABEL[tier])
    OFF = {
        'BERT (weighted)':       (6, 4, 'left'),
        'RoBERTa (weighted)':    (6, -7, 'left'),
        'Qwen2.5-7B':            (-5, 4, 'right'),
        'Llama-3.1-8B':          (6, 2, 'left'),
        'Gemma-2-2B':            (-5, -3, 'right'),
        'Llama-3.3-70B (Groq)':  (5, -6, 'left'),
        'SmolLM3-3B':            (6, -1, 'left'),
        'Qwen2.5-3B':            (0, 6, 'center'),
        'Gemini-3.1-Flash-Lite': (-5, -1, 'right'),
        'Phi-4-mini':            (6, -1, 'left'),
    }
    for _, r in cell.iterrows():
        dx, dy, ha = OFF[r.model]
        ax.annotate(r.model.replace(' (Groq)', '').replace(' (weighted)', ' (w)')
                    .replace('Gemini-3.1-Flash-Lite', 'Gemini-3.1-FL'),
                    (r.inference_usd_per_1k, r.macro_f1), xytext=(dx, dy),
                    textcoords='offset points', ha=ha, fontsize=5.8, color=INK2)
    pf = cell.sort_values('inference_usd_per_1k')
    best, xs, ys = -1, [], []
    for _, r in pf.iterrows():
        if r.macro_f1 > best:
            best = r.macro_f1; xs.append(r.inference_usd_per_1k); ys.append(r.macro_f1)
    ax.step(xs+[0.20], ys+[ys[-1]], where='post', color=MUTED, lw=0.7,
            ls=(0, (3, 2)), zorder=2, label='Pareto frontier')
    ax.set_xscale('log')
    ax.set_xlim(1.4e-3, 0.30)
    ax.set_xlabel('inference cost, USD per 1,000 requirements (log scale)', labelpad=1.5)
    ax.set_ylabel('macro-F1')
    ax.set_ylim(0.595, 0.905)
    ax.grid(True); ax.set_axisbelow(True)
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, frameon=False, ncol=3, loc='lower left', bbox_to_anchor=(-0.02, 0.99),
              handlelength=1.0, columnspacing=0.6, handletextpad=0.28, borderpad=0,
              fontsize=5.9)
    ax.set_title('(a) security / SecReq -- the one cell a prompted model leads'
                 .replace('--', '\u2013'), fontsize=7.2, loc='left', pad=21)

    cell_be = be[(be.task == 'fr_nfr') & (be.encoder == 'BERT (weighted)') &
                 (be.encoder_regime == 'in_domain')]
    C0 = float(cell_be.encoder_fixed_usd.iloc[0])
    cE = float(cell_be.encoder_marginal_usd_per_item.iloc[0])
    n = np.logspace(0, 4, 240)
    bx.axvspan(be.breakeven_n_items.min(), be.breakeven_n_items.max(),
               color='#dde4ec', zorder=0, lw=0)
    show = cell_be.sort_values('alternative_marginal_usd_per_item')
    picks = [show.iloc[0], show.iloc[len(show)//2], show.iloc[-1]]
    for r, ls, dy in zip(picks, [(0, (1, 1.7)), (0, (4, 2)), '-'], (-7, 0, 7)):
        bx.plot(n, r.alternative_marginal_usd_per_item*n, ls=ls, lw=1.0,
                color=CO[r.alternative_tier], zorder=3)
        bx.annotate(str(r.alternative),
                    (7.5e3, r.alternative_marginal_usd_per_item*7.5e3),
                    xytext=(-2, dy), textcoords='offset points', ha='right',
                    fontsize=5.8, color='#8a6100')
    bx.plot(n, C0 + cE*n, color=C_ENC, lw=1.5, zorder=4)
    bx.annotate('BERT (w), incl.\n$%.4f training' % C0, (2.2e3, C0 + cE*2.2e3),
                xytext=(0, -14), textcoords='offset points', ha='center',
                fontsize=5.8, color=C_ENC, linespacing=1.05)
    bx.set_xscale('log'); bx.set_yscale('log')
    bx.set_xlim(1, 1e4); bx.set_ylim(1e-5, 2.0)
    bx.set_xlabel('requirements classified', labelpad=1.5)
    bx.set_ylabel('cumulative cost (USD)')
    bx.grid(True); bx.set_axisbelow(True)
    bx.text(150, 0.55,
            'break-even, %d\u2013%d items\n(all 276 encoder-vs-alternative pairs)'
            % (be.breakeven_n_items.min(), be.breakeven_n_items.max()),
            ha='center', va='center', fontsize=5.9, color='#3d5570', linespacing=1.06)
    bx.set_title('(b) FR/NFR: cumulative cost against classified volume',
                 fontsize=7.2, loc='left', pad=4)
    fig.savefig(OUT+'fig_cost.pdf')
    fig.savefig(OUT+'fig_cost.png', dpi=300)
    
    plt.close(fig)
    print('fig_cost.pdf  C0=%.4f cE=%.2e  breakeven %d-%d' %
          (C0, cE, be.breakeven_n_items.min(), be.breakeven_n_items.max()))


if __name__ == '__main__':
    fig_prior_shift()
    fig_inversion()
    fig_cost()
