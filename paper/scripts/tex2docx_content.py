"""Turn paper/main.tex into a structured JSON the docx builder can render.

Deliberately narrow: it understands only the constructs this one paper uses, and
raises on anything it does not recognise rather than emitting it silently.
"""
import json, re, os, sys

PAPER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tex = open(os.path.join(PAPER, 'main.tex')).read()
# The architecture figure lives in its own file; inline it so the float scanner
# and the body walker see it in the position where LaTeX would place it.
_arch = open(os.path.join(PAPER, 'figures', 'fig_architecture.tex')).read()
tex = tex.replace('\\input{figures/fig_architecture}', _arch)

# ---------------------------------------------------------------- references
bib = tex[tex.index('\\begin{thebibliography}'):tex.index('\\end{thebibliography}')]
keys, entries = [], []
for m in re.finditer(r'\\bibitem\{([^}]+)\}(.*?)(?=\\bibitem\{|\Z)', bib, re.S):
    keys.append(m.group(1))
    entries.append(m.group(2).strip())
CITE = {k: i + 1 for i, k in enumerate(keys)}

# ------------------------------------------------------------------- floats
# Numbered in order of appearance, as LaTeX does.
ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

LABELS, tabn, fign = {}, 0, 0
for m in re.finditer(r'\\begin\{(table\*?|figure\*?)\}.*?\\label\{([^}]+)\}', tex, re.S):
    kind, lab = m.group(1), m.group(2)
    if kind.startswith('table'):
        tabn += 1
        LABELS[lab] = ('table', ROMAN[tabn])
    else:
        fign += 1
        LABELS[lab] = ('figure', fign)
SEC_ORDER = ['sec:gap', 'sec:design', 'sec:data', 'sec:tasks', 'sec:families',
             'sec:prompt', 'sec:metrics', 'sec:costmodel', 'sec:results',
             'sec:rq2', 'sec:prior', 'sec:rq3']

# Section/subsection numbers, assigned by walking the body once.
body = tex[tex.index('\\section{Introduction}'):tex.index('\\begin{thebibliography}')]
secno, subno = 0, 0
for m in re.finditer(r'\\(section|subsection)\{([^}]*)\}|\\label\{(sec:[^}]+)\}', body):
    if m.group(1) == 'section':
        secno += 1; subno = 0; cur = ROMAN[secno]
    elif m.group(1) == 'subsection':
        subno += 1; cur = f'{ROMAN[secno]}-{chr(64+subno)}'
    elif m.group(3):
        LABELS[m.group(3)] = ('section', cur)

# ------------------------------------------------------------ inline markup
GREEK = {'rho': '\u03c1', 'alpha': '\u03b1', 'Delta': '\u0394', 'star': '\u2605',
         'leftrightarrow': '\u2194', 'rightarrow': '\u2192', 'times': '\u00d7',
         'geq': '\u2265', 'sim': '\u223c', 'approx': '\u2248', 'in': '\u2208',
         'pm': '\u00b1', 'cdot': '\u00b7', 'ldots': '\u2026', 'dots': '\u2026'}


SUBD = {'0': '\u2080', '1': '\u2081', '2': '\u2082', '3': '\u2083'}


def demath(s):
    """Flatten the paper's (very simple) inline maths to Unicode."""
    def one(m):
        t = m.group(1)
        t = t.replace('\\,', '\u2009').replace('\;', '\u2009')
        t = re.sub(r'\\text\{([^}]*)\}', r'\1', t)
        t = re.sub(r'\\frac\s*\{([^{}]*)\}\s*\{(.*)\}\s*$', r'\1 / (\2)', t)
        t = re.sub(r'\\emph\{([^}]*)\}', r'\1', t)
        t = re.sub(r'\\mathrm\{([^}]*)\}', r'\1', t)
        t = re.sub(r'\{([^{}]*)\}', r'\1', t)
        for k, v in GREEK.items():
            t = t.replace('\\' + k, v)
        t = t.replace('\\{', '{').replace('\\}', '}')
        t = re.sub(r'\^\{?([-\d.]+)\}?', lambda mm: sup(mm.group(1)), t)
        t = re.sub(r'\^\s*(\u2605)', r'\1', t)
        t = re.sub(r'_\{?(\d)\}?', lambda mm: SUBD[mm.group(1)], t)
        t = re.sub(r'_\{([^{}]*)\}', r'_\1', t)
        t = t.replace('$', '')
        return t.strip()
    return re.sub(r'\$([^$]*)\$', one, s)


SUP = {'-': '\u207b', '0': '\u2070', '1': '\u00b9', '2': '\u00b2', '3': '\u00b3',
       '4': '\u2074', '5': '\u2075', '6': '\u2076', '7': '\u2077', '8': '\u2078',
       '9': '\u2079', '.': '.'}


def sup(t):
    return ''.join(SUP.get(c, c) for c in t)


def cites(s):
    def one(m):
        nums = [CITE[k.strip()] for k in m.group(2).split(',')]
        lead = '\u00a0' if m.group(1) else ''
        return lead + '[' + ', '.join(str(n) for n in nums) + ']'
    return re.sub(r'(~)?\\cite\{([^}]+)\}', one, s)


def refs(s):
    def one(m):
        kind, num = LABELS[m.group(1)]
        return f'\u00a0{num}' if kind != 'section' else f'\u00a0{num}'
    s = re.sub(r'~?\\ref\{([^}]+)\}', one, s)
    return s


def eqref(s):
    return re.sub(r'~?\\eqref\{eq:breakeven\}', '\u00a0(1)', s)


def runs(s):
    """Return [{text, bold, italic, mono}] for one paragraph of LaTeX."""
    s = cites(refs(eqref(s)))
    s = re.sub(r'\\pex(\{\})?', 'PROMISE_exp', s)
    s = re.sub(r'\\Fm(\{\})?', 'macro-F1', s)
    s = re.sub(r'\\ID(\{\})?', 'ID', s)
    s = re.sub(r'\\XP(\{\})?', 'XP', s)
    s = re.sub(r'\\XD(\{\})?', 'XD', s)
    s = re.sub(r'\\cmark(\{\})?', '\u2713', s)
    s = re.sub(r'\\xmark(\{\})?', '\u2717', s)
    s = s.replace('\\looseness=-1', '').replace('\\balance', '')
    s = s.replace('\\quad', '\u2003')
    s = re.sub(r'\\itshape\s*', '', s)
    s = demath(s)
    s = re.sub(r'\\(?:textsc)\{([^}]*)\}', lambda m: m.group(1).upper(), s)
    out, i = [], 0
    pat = re.compile(r'\\(textbf|emph|textit|texttt|textsubscript)\{')
    while True:
        m = pat.search(s, i)
        if not m:
            out.append((s[i:], None)); break
        out.append((s[i:m.start()], None))
        depth, j = 1, m.end()
        while depth:
            if s[j] == '{': depth += 1
            elif s[j] == '}': depth -= 1
            j += 1
        out.append((s[m.end():j-1], m.group(1)))
        i = j
    res = []
    for txt, kind in out:
        txt = clean(txt)
        if not txt.strip():
            continue
        res.append(dict(text=txt, bold=kind == 'textbf',
                        italic=kind in ('emph', 'textit'), mono=kind == 'texttt',
                        sub=kind == 'textsubscript'))
    # a group boundary that had a space on either side keeps one
    for i in range(len(res) - 1):
        a, b = res[i], res[i + 1]
        if a.get('sub') or b.get('sub'):
            continue
        if not a['text'].endswith(' ') and not b['text'].startswith(' ') \
                and a['text'][-1] not in '(“' and b['text'][0] not in ').,;:”':
            b['text'] = ' ' + b['text']
    if res:
        res[0]['text'] = res[0]['text'].lstrip()
        res[-1]['text'] = res[-1]['text'].rstrip()
    return res


def clean(t):
    t = t.replace('---', '\u2014').replace('--', '\u2013')
    t = t.replace("``", '\u201c').replace("''", '\u201d')
    t = t.replace('\\%', '%').replace('\\$', '$').replace('\\&', '&')
    t = t.replace('\\_', '_').replace('\\#', '#')
    t = t.replace('\\,', '\u2009').replace('~', '\u00a0')
    t = t.replace("\\'{e}", '\u00e9').replace('\\"{u}', '\u00fc')
    t = re.sub(r"\\'\{?([a-zA-Z])\}?", r'\1', t)
    t = re.sub(r'\\[cv]\{([a-zA-Z])\}', r'\1', t)
    t = t.replace('{,}', ',').replace('{', '').replace('}', '')
    t = t.replace('\\ ', ' ').replace('\\@', '')
    t = re.sub(r'\s+', ' ', t)
    return t


# ---------------------------------------------------------------- tabulars
def parse_tabular(src):
    """LaTeX tabular body -> list of rows; each row is a list of cell dicts."""
    src = re.sub(r'(?<!\\)%.*', '', src)
    i = src.index('\\begin{tabular}') + len('\\begin{tabular}')
    while src[i] != '{':
        i += 1
    depth = 0
    while True:
        if src[i] == '{': depth += 1
        elif src[i] == '}':
            depth -= 1
            if depth == 0:
                i += 1
                break
        i += 1
    inner = src[i:src.index('\\end{tabular}')]
    rows, rules = [], []
    for raw in re.split(r'\\\\', inner):
        raw = raw.strip()
        if not raw:
            continue
        rule = 'top' if '\\midrule' in raw else None
        raw = re.sub(r'\\(top|mid|bottom)rule', '', raw)
        raw = re.sub(r'\\cmidrule(\([^)]*\))?\{[^}]*\}', '', raw)
        raw = re.sub(r'\\addlinespace(\[[^\]]*\])?', '', raw)
        raw = re.sub(r'\\(setlength|renewcommand)\{[^}]*\}\{[^}]*\}', '', raw)
        raw = re.sub(r'\\(scriptsize|footnotesize|small)\b', '', raw)
        if not raw.strip():
            continue
        cells = []
        for c in split_cells(raw):
            span, txt = 1, c.strip()
            mm = re.match(r'\\multicolumn\{(\d+)\}\{', txt)
            if mm:
                span = int(mm.group(1))
                k, depth = mm.end(), 1
                while depth:                      # skip the alignment spec
                    if txt[k] == '{': depth += 1
                    elif txt[k] == '}': depth -= 1
                    k += 1
                while txt[k] != '{':
                    k += 1
                k += 1
                depth, start = 1, k
                while depth:
                    if txt[k] == '{': depth += 1
                    elif txt[k] == '}': depth -= 1
                    k += 1
                txt = txt[start:k-1]
            r = runs(txt)
            cells.append(dict(span=span, runs=r,
                              text=''.join(x['text'] for x in r)))
        rows.append(dict(cells=cells, rule=rule))
    return rows


def split_cells(row):
    out, depth, cur, esc = [], 0, '', False
    for ch in row:
        if esc:
            cur += ch; esc = False; continue
        if ch == '\\':
            cur += ch; esc = True; continue
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
        if ch == '&' and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    out.append(cur)
    return out


def load_table(name):
    return parse_tabular(open(os.path.join(PAPER, 'tables', name)).read())


# ------------------------------------------------------------------- body
FIG_IMG = {'fig:arch': 'fig_architecture.png', 'fig:inversion': 'fig_inversion.png',
           'fig:prior': 'fig_prior_shift.png', 'fig:cost': 'fig_cost.png'}
FIG_ASPECT = {}
try:
    from PIL import Image
    for lab, f in FIG_IMG.items():
        w, h = Image.open(os.path.join(PAPER, 'figures', f)).size
        FIG_ASPECT[lab] = w / h
except Exception:
    FIG_ASPECT = {'fig:arch': 3.0, 'fig:inversion': 1.25,
                  'fig:prior': 1.02, 'fig:cost': 1.62}

blocks = []


def caption_of(chunk):
    m = re.search(r'\\caption\{', chunk)
    depth, j = 1, m.end()
    while depth:
        if chunk[j] == '{': depth += 1
        elif chunk[j] == '}': depth -= 1
        j += 1
    return chunk[m.end():j-1]


def emit_float(chunk):
    lab = re.search(r'\\label\{([^}]+)\}', chunk).group(1)
    kind, num = LABELS[lab]
    cap = caption_of(chunk)
    wide = '\\begin{table*}' in chunk or '\\begin{figure*}' in chunk
    if kind == 'table':
        inp = re.search(r'\\input\{tables/([^}]+)\}', chunk)
        rows = load_table(inp.group(1) + ('' if inp.group(1).endswith('.tex') else '.tex')) \
            if inp else parse_tabular(chunk)
        blocks.append(dict(type='table', number=num, label=lab, wide=wide,
                           caption=runs(cap), rows=rows))
    else:
        if lab == 'fig:prompt':
            blocks.append(dict(type='promptbox', number=num, caption=runs(cap)))
        else:
            blocks.append(dict(type='figure', number=num, wide=wide,
                               image=FIG_IMG[lab], aspect=FIG_ASPECT[lab],
                               caption=runs(cap)))


# Walk the body, splitting floats out of the paragraph stream.
EQ = re.compile(r'\\begin\{equation\}(.*?)\\end\{equation\}', re.S)
_eqs = []


def _stash_eq(m):
    _eqs.append(m.group(1))
    return '\n\n@@EQ%d@@\n\n' % (len(_eqs) - 1)


body = EQ.sub(_stash_eq, body)

FLOAT = re.compile(r'\\begin\{(table\*?|figure\*?)\}.*?\\end\{\1\}', re.S)
pos = 0
pieces = []
for m in FLOAT.finditer(body):
    pieces.append(('text', body[pos:m.start()]))
    pieces.append(('float', m.group(0)))
    pos = m.end()
pieces.append(('text', body[pos:]))

secno, subno = 0, 0
for kind, chunk in pieces:
    if kind == 'float':
        emit_float(chunk)
        continue
    chunk = re.sub(r'^%%.*$', '', chunk, flags=re.M)
    chunk = re.sub(r'\\label\{[^}]*\}', '', chunk)
    for para in re.split(r'\n\s*\n', chunk):
        para = para.strip()
        if not para:
            continue
        m = re.match(r'\\section\{(.*?)\}(.*)$', para, re.S)
        if m:
            secno += 1; subno = 0
            blocks.append(dict(type='h1', number=ROMAN[secno],
                               text=clean(m.group(1)).upper()))
            para = m.group(2).strip()
            if not para:
                continue
        m = re.match(r'\\subsection\{(.*?)\}(.*)$', para, re.S)
        if m:
            subno += 1
            blocks.append(dict(type='h2', number=chr(64+subno),
                               text=clean(m.group(1))))
            para = m.group(2).strip()
            if not para:
                continue
        if para.startswith('\\begin{enumerate}'):
            items = re.findall(r'\\item\s+(.*?)(?=\\item|\\end\{enumerate\})',
                               para, re.S)
            for i, it in enumerate(items, 1):
                blocks.append(dict(type='li', number=i, runs=runs(it)))
            continue
        m = re.match(r'@@EQ(\d+)@@$', para)
        if m:
            raw = _eqs[int(m.group(1))]
            raw = re.sub(r'\\label\{[^}]*\}', '', raw).strip().rstrip('.')
            body_txt = clean(demath('$' + raw.replace('\\;', ' ') + '$')).strip()
            blocks.append(dict(type='equation', text=body_txt, number='(1)'))
            continue
        if para.startswith('\\'):
            leftover = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})*', '', para).strip()
            if not leftover:
                continue
        blocks.append(dict(type='p', runs=runs(para)))

# ----------------------------------------------------------------- front
front = tex[:tex.index('\\section{Introduction}')]
title = re.search(r'\\title\{(.*?)\}\s*\n\s*\\author', front, re.S).group(1)
abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', front, re.S).group(1)
kw = re.search(r'\\begin\{IEEEkeywords\}(.*?)\\end\{IEEEkeywords\}', front, re.S).group(1)

doc = dict(
    title=clean(title.replace('\\\\', ' ')),
    authors='Fatma El-Zahraa Samir, Khaled T. Wassif, and Lamia AbouZeid',
    affil='Faculty of Computers and Artificial Intelligence, Cairo University, Giza, Egypt',
    email='fatmaelzahraasamirabdelfattah@gmail.com',
    abstract=runs(abstract),
    keywords=clean(kw),
    blocks=blocks,
    references=[runs(e) for e in entries],
)
json.dump(doc, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'paper.json'), 'w'), indent=1)
print('blocks:', len(blocks), ' refs:', len(entries))
print('tables:', sum(1 for b in blocks if b['type'] == 'table'),
      ' figures:', sum(1 for b in blocks if b['type'] in ('figure', 'promptbox')))
