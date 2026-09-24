"""Re-apply the Holm / Benjamini-Hochberg corrections over the 200 reported tests.

Stage 4 corrected all 260 encoder-LLM McNemar tests it ran as one family, which
includes 60 tests on the reduced sub-type label sets (top-4, top-6) that the
paper does not report. The paper describes the family as its 200 reported tests
(FR/NFR, security and the eleven-class sub-type task), so this script recomputes
both corrections over exactly those 200 and writes them next to the original.
The BH verdict counts are identical under either family.
"""
import numpy as np
import pandas as pd

Z = '../artefacts/results_Stage4_analysis/'
REPORTED_TASKS = {'fr_nfr', 'security', 'subtype_all'}
ALPHA = 0.05


def holm_bh(p):
    p = np.asarray(p, dtype=float)
    n = len(p)
    o = np.argsort(p)
    holm = np.empty(n)
    holm[o] = np.minimum(np.maximum.accumulate(p[o] * (n - np.arange(n))), 1.0)
    bh = np.empty(n)
    bh[o] = np.minimum(np.minimum.accumulate((p[o] * n / (np.arange(n) + 1))[::-1])[::-1], 1.0)
    return holm, bh


m = pd.read_csv(Z + 'tab4_mcnemar.csv')
fam = m[m.task.isin(REPORTED_TASKS)].copy()
assert len(fam) == 200, len(fam)
fam['p_holm_200'], fam['p_bh_200'] = holm_bh(fam.p_value.values)
fam['verdict_200'] = np.where(fam.p_bh_200 >= ALPHA, 'n.s.',
                              np.where(fam.llm_acc > fam.encoder_acc, 'LLM wins', 'Encoder wins'))
fam.to_csv(Z + 'tab4_mcnemar_family200.csv', index=False)

print(pd.crosstab(fam.encoder_regime, fam.verdict_200))
changed = int((fam.verdict != fam.verdict_200).sum())
print(f'\nverdicts that differ from the 260-test family: {changed}')
print(f'Holm-significant: {int((fam.p_holm < ALPHA).sum())} (260-family) vs '
      f'{int((fam.p_holm_200 < ALPHA).sum())} (200-family)')
