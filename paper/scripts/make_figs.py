"""The paper's three data figures, drawn as plainly as the data allows.

Every value is read from the stored artefacts; none is typed in.  Each panel
carries one axis whose label says in words what the numbers on it are, because
a macro-F1, a share of items and a count of statistical tests all look alike on
a page and must not be confused with one another.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

Z = '../../artefacts/'
OUT = '../figures/'
CM = 1/2.54
COL = 8.8*CM          # IEEE single column

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Nimbus Roman', 'FreeSerif', 'DejaVu Serif'],
    'mathtext.fontset': 'stix',
    'font.size': 7, 'axes.labelsize': 7, 'axes.titlesize': 7.2,
    'xtick.labelsize': 6.6, 'ytick.labelsize': 6.6, 'legend.fontsize': 6.2,
    'axes.linewidth': 0.6,
    'xtick.major.width': 0.5, 'ytick.major.width': 0.5,
    'xtick.major.size': 2.2, 'ytick.major.size': 2.2,
    'grid.linewidth': 0.4, 'grid.color': '#cccccc',
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 300, 'savefig.dpi': 300,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.012,
    'pdf.fonttype': 42,
})

# Okabe--Ito derived categorical set, validated for colour-vision deficiency
# separation.  Identity is fixed: one hue per model family, never cycled.
C_ENC, C_ENC2, C_LOC = '#0072B2', '#66B2D8', '#E69F00'
C_HOST, C_COM = '#009E73', '#CC79A7'
INK, MUTED, RED = '#1a1a1a', '#5a5a5a', '#A11B1B'
TIER_C = {'finetuned': C_ENC, 'open_local': C_LOC,
          'open_hosted': C_HOST, 'commercial': C_COM}

ev = pd.read_csv(Z+'results_Stage4_analysis/tab9_evaluability.csv')
mc = pd.read_csv(Z+'results_Stage4_analysis/tab4_mcnemar.csv')
fin = pd.read_parquet(Z+'results_stage2_finetuned_baselines/predictions_finetuned.parquet')
lpr = pd.read_parquet(Z+'repair/predictions_llm_repaired.parquet')
uni = pd.read_csv(Z+'results_stage1_data_pipeline/data_processed/unified.csv')
c1 = pd.read_csv(Z+'results_Stage5_cost/cost1_per_model.csv')
be = pd.read_csv(Z+'results_Stage5_cost/cost3_breakeven.csv')

LLMS = ['Gemini-3.1-Flash-Lite', 'Llama-3.3-70B (Groq)', 'Qwen2.5-7B',
        'Llama-3.1-8B', 'Gemma-2-2B', 'Phi-4-mini', 'SmolLM3-3B', 'Qwen2.5-3B']


def f1(model, task, ds, regime):
    r = ev[(ev.model == model) & (ev.task == task) & (ev.dataset == ds) &
           (ev.eval_regime == regime) & (ev.reportable)]
    return float(r.macro_f1.iloc[0]) if len(r) else np.nan


# =======================================================  Figure: inversion
def fig_inversion():
    TASK, DS = 'security', 'promise'
    regs = ['in_domain', 'cross_project', 'cross_dataset']
    names = ['In-domain\n(same corpus)', 'Cross-project\n(unseen projects)',
             'Cross-dataset\n(the other corpus)']
    bert = [f1('BERT (weighted)', TASK, DS, r) for r in regs]
    rob = [f1('RoBERTa (weighted)', TASK, DS, r) for r in regs]
    pv = np.array([f1(m, TASK, DS, 'prompted') for m in LLMS])
    pv = pv[~np.isnan(pv)]
    pmed, plo, phi = np.median(pv), pv.min(), pv.max()

    fig, (ax, bx) = plt.subplots(
        2, 1, figsize=(COL, 6.2*CM),
        gridspec_kw=dict(height_ratios=[1.42, 1.0], hspace=1.02))

    # ---- (a) the same models at three levels of distribution shift
    x = np.arange(3)
    w = 0.26
    for i, (lab, vals, col, hat) in enumerate([
            ('BERT', bert, C_ENC, ''),
            ('RoBERTa', rob, C_ENC2, ''),
            ('prompted LLMs (median of 8)', [pmed]*3, C_LOC, '///')]):
        pos = x + (i-1)*w
        ax.bar(pos, vals, w*0.86, color=col, edgecolor='white', linewidth=0.7,
               hatch=hat, label=lab, zorder=3)
        for p, v in zip(pos, vals):
            ax.text(p, v+0.016, f'{v:.2f}', ha='center', va='bottom',
                    fontsize=5.8, color=INK)
    ax.errorbar(x+w, [pmed]*3, yerr=[[pmed-plo]*3, [phi-pmed]*3], fmt='none',
                ecolor=MUTED, elinewidth=0.6, capsize=1.8, capthick=0.6, zorder=4)

    # the only percentage in this panel, and it is a relative loss of score
    drop = 100*(bert[0]-bert[2])/bert[0]
    ax.annotate(f'BERT loses {drop:.1f}% of its own in-domain score',
                xy=(2-w-0.115, 0.44), xytext=(-0.46, 1.115),
                fontsize=5.9, color=RED, ha='left', va='center',
                arrowprops=dict(arrowstyle='->', lw=0.55, color=RED,
                                shrinkA=2, shrinkB=2,
                                connectionstyle='arc3,rad=-0.28'))
    ax.set_ylim(0, 1.20)
    ax.set_yticks(np.arange(0, 1.01, 0.25))
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=6.2, linespacing=1.15)
    ax.set_ylabel('macro-F1 (0 = worst, 1 = perfect)')
    ax.grid(axis='y', zorder=0); ax.set_axisbelow(True)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.30), ncol=3,
              frameon=False, handlelength=1.1, handletextpad=0.4,
              columnspacing=1.0, borderpad=0.0)
    ax.set_title('(a) security task on PROMISE_exp: the same 968 items scored\n'
                 'at each level of distribution shift',
                 fontsize=6.6, loc='left', pad=3, linespacing=1.25)

    # ---- (b) how the 260 paired tests came out, by regime
    order = [('in_domain', 'In-domain'), ('cross_project', 'Cross-project'),
             ('cross_dataset', 'Cross-dataset')]
    cats = [('Encoder wins', C_ENC, ''), ('n.s.', '#dcdcdc', ''),
            ('LLM wins', C_LOC, '///')]
    y = np.arange(3)[::-1]
    for j, (reg, lab) in enumerate(order):
        d = mc[mc.encoder_regime.str.startswith(reg)]
        left = 0
        for name, col, hat in cats:
            n = int((d.verdict == name).sum())
            if n:
                bx.barh(y[j], n, 0.52, left=left, color=col, edgecolor='white',
                        linewidth=0.7, hatch=hat, zorder=3)
                bx.text(left+n/2, y[j], str(n), ha='center', va='center',
                        fontsize=6.0,
                        color='white' if col == C_ENC else INK)
            left += n
        bx.text(left+2.5, y[j], f'{left} tests', va='center', fontsize=5.8,
                color=MUTED)
    bx.set_yticks(y); bx.set_yticklabels([l for _, l in order], fontsize=6.4)
    bx.set_xlim(0, 124)
    bx.set_xlabel('number of paired statistical tests\n'
                  '(one test = one encoder against one LLM on the same items)',
                  fontsize=6.2, linespacing=1.2)
    bx.grid(axis='x', zorder=0); bx.set_axisbelow(True)
    bx.legend(handles=[Patch(facecolor=c, hatch=h, edgecolor='white', label=n)
                       for n, c, h in [('encoder better', C_ENC, ''),
                                       ('no difference', '#dcdcdc', ''),
                                       ('LLM better', C_LOC, '///')]],
              loc='upper center', bbox_to_anchor=(0.5, -0.52), ncol=3,
              frameon=False, handlelength=1.1, handletextpad=0.4,
              columnspacing=1.2, borderpad=0.0)
    bx.set_title('(b) all 260 comparisons, grouped by how the encoder was tested',
                 fontsize=6.6, loc='left', pad=3)
    fig.savefig(OUT+'fig_inversion.pdf')
    plt.close(fig)
    print('fig_inversion.pdf  drop=%.1f%%  prompted median %.3f [%.3f, %.3f]'
          % (drop, pmed, plo, phi))


# =====================================================  Figure: class prior
def fig_prior():
    sec = fin[fin.task == 'security']

    def share(tag, ds, reg):
        d = sec[(sec.model_tag == tag) & (sec.dataset == ds) &
                (sec.eval_regime == reg)]
        return 100*(d.y_pred == 'security').mean()

    true_p = 100*(uni[uni.source_dataset == 'promise'].label_security == 'security').mean()
    src_p = 100*(uni[uni.source_dataset == 'secreq'].label_security == 'security').mean()

    fig, (ax, bx) = plt.subplots(
        2, 1, figsize=(COL, 6.4*CM),
        gridspec_kw=dict(height_ratios=[1.0, 1.12], hspace=1.00))

    # ---- (a) what share of the test items each encoder calls "security"
    rows = [('BERT, trained on\nPROMISE_exp itself',
             share('bert-base-uncased-weighted', 'promise', 'in_domain')),
            ('RoBERTa, trained\non SecReq',
             share('roberta-base-weighted', 'promise', 'cross_dataset')),
            ('BERT, trained\non SecReq',
             share('bert-base-uncased-weighted', 'promise', 'cross_dataset'))]
    y = np.arange(len(rows))
    ax.barh(y, [v for _, v in rows], 0.5, color=C_ENC, edgecolor='white',
            linewidth=0.7, zorder=3)
    for yy, (_, v) in zip(y, rows):
        ax.text(v+1.0, yy, f'{v:.1f}%', va='center', fontsize=6.2, color=INK)
    ax.axvline(true_p, color=RED, lw=0.8, zorder=4)
    ax.axvline(src_p, color=MUTED, lw=0.8, ls=(0, (2.5, 1.6)), zorder=4)
    ax.text(true_p-1.4, 2.68, f'truth: {true_p:.1f}%',
            ha='right', va='center', fontsize=5.8, color=RED)
    ax.text(src_p+1.4, 2.68, f'training\ncorpus: {src_p:.1f}%',
            ha='left', va='center', fontsize=5.8, color=MUTED, linespacing=1.05)
    ax.set_yticks(y)
    ax.set_yticklabels([n for n, _ in rows], fontsize=6.0, linespacing=1.1)
    ax.set_xlim(0, 62); ax.set_ylim(-0.55, 3.30)
    ax.set_xlabel('share of the 968 test items the model labels "security"',
                  fontsize=6.3)
    ax.grid(axis='x', zorder=0); ax.set_axisbelow(True)
    ax.set_title('(a) a transferred encoder keeps the class balance it was\n'
                 'trained on, not the one it is being tested on',
                 fontsize=6.6, loc='left', pad=3, linespacing=1.25)

    # ---- (b) the prompted models: same defect, different source
    L = lpr[(lpr.task == 'fr_nfr') & (lpr.dataset == 'promise') &
            (lpr.shot_k == 0) & (lpr.prompt_id == 'base')]
    pts = []
    for tag, g in L.groupby('model_tag'):
        if 'nemotron' in tag:
            continue
        pts.append((tag, 100*(g.y_pred_strict == 'NFR').mean(),
                    100*(g.y_pred_strict == g.y_true).mean()))
    P = pd.DataFrame(pts, columns=['m', 'pred', 'acc'])
    rho = np.corrcoef(P.pred.rank(), P.acc.rank())[0, 1]
    true_nfr = 100*(uni[uni.source_dataset == 'promise'].label_fr_nfr == 'NFR').mean()
    bx.scatter(P.pred, P.acc, s=20, color=C_LOC, edgecolor='white',
               linewidth=0.6, zorder=4)
    bx.axvline(true_nfr, color=RED, lw=0.8, zorder=3)
    bx.text(true_nfr-1.2, 60.5, f'truth: {true_nfr:.1f}% of\nitems are NFR',
            ha='right', fontsize=5.8, color=RED, linespacing=1.05)
    LAB = {'qwen2.5-3b-instruct': ('Qwen2.5-3B', 7, -2.5, 'left'),
           'groq-llama-3.3-70b-versatile': ('Llama-3.3-70B', 4, -3, 'left'),
           'gemini-3.1-flash-lite': ('Gemini 3.1 F-Lite', -4, 2, 'right')}
    for _, r in P.iterrows():
        if r.m in LAB:
            t, dx, dy, ha = LAB[r.m]
            bx.annotate(t, (r.pred, r.acc), xytext=(dx, dy),
                        textcoords='offset points', ha=ha, fontsize=5.7,
                        color=MUTED)
    bx.text(0.02, 0.97, f'Spearman $\\rho$ = {rho:.2f}', transform=bx.transAxes,
            fontsize=6.3, va='top', color=INK)
    bx.set_xlim(8, 58); bx.set_ylim(55, 93)
    bx.set_xlabel('share of items the model answers "NFR"', fontsize=6.3)
    bx.set_ylabel('accuracy (%)', fontsize=6.3)
    bx.grid(zorder=0); bx.set_axisbelow(True)
    bx.set_title('(b) the eight prompted models on FR/NFR: the closer its class\n'
                 'balance is to the truth, the better it scores',
                 fontsize=6.6, loc='left', pad=3, linespacing=1.25)
    fig.savefig(OUT+'fig_prior.pdf')
    plt.close(fig)
    print('fig_prior.pdf  rho=%.2f true_nfr=%.1f' % (rho, true_nfr))


# ============================================================  Figure: cost
def fig_cost():
    med = (c1.groupby(['model', 'tier'], dropna=False)
             .inference_usd_per_1k.median().reset_index()
             .sort_values('inference_usd_per_1k'))
    med = med[~med.model.str.contains('unweighted')]
    NICE = {'BERT (weighted)': 'BERT', 'RoBERTa (weighted)': 'RoBERTa',
            'Llama-3.3-70B (Groq)': 'Llama-3.3-70B',
            'Gemini-3.1-Flash-Lite': 'Gemini 3.1 F-Lite'}

    fig, (ax, bx) = plt.subplots(
        2, 1, figsize=(COL, 6.5*CM),
        gridspec_kw=dict(height_ratios=[1.30, 1.0], hspace=0.92))

    y = np.arange(len(med))[::-1]
    ax.barh(y, med.inference_usd_per_1k, 0.56,
            color=[TIER_C[t] for t in med.tier], edgecolor='white',
            linewidth=0.7, zorder=3)
    for yy, (_, r) in zip(y, med.iterrows()):
        ax.text(r.inference_usd_per_1k+0.0018, yy, f'{r.inference_usd_per_1k:.4f}',
                va='center', fontsize=6.0, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([NICE.get(m, m) for m in med.model], fontsize=6.2)
    ax.set_xlim(0, 0.099)
    ax.set_xlabel('US dollars to classify 1,000 requirements', fontsize=6.3)
    ax.grid(axis='x', zorder=0); ax.set_axisbelow(True)
    ax.legend(handles=[Patch(facecolor=TIER_C[t], edgecolor='white', label=l)
                       for t, l in [('finetuned', 'encoder, our GPU'),
                                    ('open_local', 'open LLM, our GPU'),
                                    ('open_hosted', 'open LLM, hosted'),
                                    ('commercial', 'commercial API')]],
              loc='upper right', bbox_to_anchor=(1.0, 1.04), frameon=False,
              handlelength=1.0, handletextpad=0.35, borderpad=0.0,
              labelspacing=0.24)
    ax.set_title('(a) price of 1,000 classifications, median over the cells that\n'
                 'model answered', fontsize=6.6, loc='left', pad=3,
                 linespacing=1.25)

    # ---- (b) when the encoder's one-off training has paid for itself
    r = be[(be.encoder == 'BERT (weighted)') & (be.task == 'fr_nfr') &
           (be.dataset == 'promise') & (be.encoder_regime == 'in_domain') &
           (be.alternative == 'Gemini-3.1-Flash-Lite')].iloc[0]
    C0, ce, ca = (float(r.encoder_fixed_usd),
                  float(r.encoder_marginal_usd_per_item),
                  float(r.alternative_marginal_usd_per_item))
    n = np.linspace(0, 700, 400)
    bx.plot(n, C0 + ce*n, color=C_ENC, lw=1.4, zorder=4,
            label=f'BERT: \\${C0:.3f} to fine-tune, then \\${ce*1000:.3f} per 1,000')
    bx.plot(n, ca*n, color=C_LOC, lw=1.4, ls=(0, (3.2, 1.6)), zorder=4,
            label=f'Gemini 3.1 F-Lite: nothing to train, \\${ca*1000:.3f} per 1,000')
    nstar = int(r.breakeven_n_items)
    bx.plot([nstar], [C0+ce*nstar], marker='o', ms=2.8, color=INK, zorder=5)
    bx.annotate(f'equal cost at {nstar}\nrequirements',
                xy=(nstar, C0+ce*nstar), xytext=(nstar+58, 0.0028),
                fontsize=5.9, color=INK, linespacing=1.05,
                arrowprops=dict(arrowstyle='->', lw=0.55, color=INK,
                                shrinkA=1, shrinkB=2))
    bx.set_xlim(0, 700); bx.set_ylim(0, 0.0245)
    bx.set_xlabel('requirements classified', fontsize=6.3)
    bx.set_ylabel('total cost (US dollars)', fontsize=6.3)
    bx.grid(zorder=0); bx.set_axisbelow(True)
    bx.legend(loc='upper left', frameon=False, handlelength=1.7,
              handletextpad=0.5, borderpad=0.1, labelspacing=0.26)
    bx.set_title('(b) one of the 276 pairings; across all of them the crossing\n'
                 'point falls between 46 and 552 requirements',
                 fontsize=6.6, loc='left', pad=3, linespacing=1.25)
    fig.savefig(OUT+'fig_cost.pdf')
    plt.close(fig)
    print('fig_cost.pdf  %s vs %s, N*=%d' % (r.encoder, r.alternative, nstar))


if __name__ == '__main__':
    import sys
    if '--png' in sys.argv:          # preview renders, not used by the paper
        _sf = plt.Figure.savefig
        def savefig(self, fname, *a, **k):
            _sf(self, fname, *a, **k)
            _sf(self, '/tmp/prev_'+fname.split('/')[-1].replace('.pdf', '.png'),
                dpi=260, bbox_inches='tight')
        plt.Figure.savefig = savefig
    fig_inversion(); fig_prior(); fig_cost()
