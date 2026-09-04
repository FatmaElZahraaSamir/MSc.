# -*- coding: utf-8 -*-
"""Search leading + per-float anchor offsets until the Word build reproduces
main.pdf: eight pages, the references alone on page 8, every float on the same
page and column, and no one-character orphan lines."""
import json, os, re, sys, pymupdf, check

WANT = check.floats(pymupdf.open('../paper/main.pdf'))
LABEL = {'tab:coverage':'TABLE I', 'fig:arch':'Fig. 1', 'tab:corpus':'TABLE II',
         'tab:models':'TABLE III', 'fig:prompt':'Fig. 2', 'tab:indomain':'TABLE IV',
         'fig:inversion':'Fig. 3', 'tab:transfer':'TABLE V', 'fig:prior':'Fig. 4',
         'fig:cost':'Fig. 5'}
ORDER = ['tab:coverage','fig:arch','tab:corpus','tab:models','fig:prompt',
         'tab:indomain','fig:inversion','tab:transfer','fig:prior','fig:cost']

def measure(lead, shift):
    json.dump(shift, open('shift.json','w'), indent=1)
    d = check.build(lead)
    got = check.floats(d)
    txt = [d[i].get_text() for i in range(d.page_count)]
    refp = next((i+1 for i in range(d.page_count) if 'REFERENCES' in txt[i]), 99)
    L = [l for l in txt[refp-1].split('\n') if l.strip()] if refp <= d.page_count else []
    pre = L.index('REFERENCES') if 'REFERENCES' in L else 99
    orph = sum(1 for t in txt for ln in t.split('\n') if re.fullmatch(r'[A-Za-z]', ln.strip()))
    hits = sum(1 for k in WANT if got.get(k) == WANT[k])
    return dict(pages=d.page_count, refp=refp, pre=pre, orph=orph, hits=hits, got=got)

def score(m, upto=len(ORDER)):
    early = sum(1 for l in ORDER[:upto] if m['got'].get(LABEL[l]) == WANT[LABEL[l]])
    return (m['pages'] == 8, m['refp'] == 8 and m['pre'] == 0, early, m['hits'], -m['orph'])

def tune(lead, shift=None, rounds=2):
    shift = dict(shift or {})
    m = measure(lead, shift)
    for _ in range(rounds):
        improved = False
        for idx, lab in enumerate(ORDER, 1):
            if m['got'].get(LABEL[lab]) == WANT[LABEL[lab]] and m['pages'] == 8:
                continue                      # already where LaTeX put it
            best = (score(m, idx), shift.get(lab, 0), m)
            for v in (0,1,2,3,4,5,6,7,8,10,-1,-2,-3,-4,-5,-6):
                if v == shift.get(lab, 0): continue
                s = dict(shift)
                if v == 0: s.pop(lab, None)
                else: s[lab] = v
                mm = measure(lead, s)
                if score(mm, idx) > best[0]:
                    best = (score(mm, idx), v, mm)
            if best[1] != shift.get(lab, 0):
                if best[1] == 0: shift.pop(lab, None)
                else: shift[lab] = best[1]
                m = best[2]; improved = True
        if not improved: break
    return shift, m

if __name__ == '__main__':
    results = []
    for lead in sys.argv[1:]:
        sh, m = tune(lead)
        print(f'LEAD={lead}: {m["pages"]}p refs p{m["refp"]}+{m["pre"]} '
              f'floats {m["hits"]}/10 orph {m["orph"]}  {json.dumps(sh)}', flush=True)
        results.append((score(m), lead, sh, m))
    results.sort(reverse=True)
    b = results[0]
    print('\nBEST', b[1], json.dumps(b[2]), b[3]['pages'], 'pages',
          f'refs p{b[3]["refp"]}+{b[3]["pre"]}', f'floats {b[3]["hits"]}/10')
    json.dump(b[2], open('shift.json','w'), indent=1)
    open('lead.txt','w').write(b[1])
