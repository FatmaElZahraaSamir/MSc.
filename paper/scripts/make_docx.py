"""Build a Word copy of the paper straight from main.tex.

The LaTeX source stays the master: this script reads it, expands the numeric
macros from tables/numbers.json, and lays the result out in the IEEE two-column
Word format supervisors usually read in.  Run it after main.tex builds.

    cd paper/scripts && python3 make_docx.py
"""
import json
import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

TEX = '../main.tex'
ARCH = '../figures/fig_architecture.tex'
NUMS = '../tables/numbers.json'
IMG = '/tmp/docximg/'
OUT = '../paper.docx'

NUM = json.load(open(NUMS))
FMT = {}
for line in open('../tables/numbers.tex'):
    m = re.match(r'\\newcommand\{\\n(\w+)\}\{(.*)\}\s*$', line)
    if m:
        FMT[m.group(1)] = m.group(2).replace('$-$', '\u2212')


# ------------------------------------------------------------ LaTeX -> text
def detex(s):
    # protect escaped punctuation first: a comment strip or the maths pass
    # would otherwise swallow \% and pair two \$ as formula delimiters
    prot = {r'\$': '\x01', r'\%': '\x02', r'\&': '\x03',
            r'\_': '\x04', r'\#': '\x05'}
    for k, v in prot.items():
        s = s.replace(k, v)
    s = re.sub(r'%.*', '', s)
    s = re.sub(r'\\n([A-Z][A-Za-z]*)\{\}', lambda m: FMT.get(m.group(1), '?'), s)
    s = re.sub(r'\\n([A-Z][A-Za-z]*)', lambda m: FMT.get(m.group(1), '?'), s)
    s = s.replace(r'\pex{}', 'PROMISE\x04exp').replace(r'\pex', 'PROMISE\x04exp')
    s = s.replace(r'\Fm{}', 'macro-F1').replace(r'\Fm', 'macro-F1')
    s = re.sub(r'\\(?:emph|textbf|textit|texttt)\{([^{}]*)\}', r'\1', s)
    s = re.sub(r'~?\\cite\{([^}]*)\}',
               lambda m: ' [' + ', '.join(REFNUM.get(k.strip(), '?')
                                          for k in m.group(1).split(',')) + ']', s)
    s = re.sub(r'~?\\ref\{([^}]*)\}',
               lambda m: ' ' + LABEL.get(m.group(1), '?'), s)
    s = re.sub(r'~?\\eqref\{([^}]*)\}', ' (1)', s)
    # maths, one construct at a time, then anything left between single $
    MATH = [(r'\$N\^\{\\star\}\$', 'N*'),
            (r'\$C\_0\$', 'C0'),
            (r'\$\\Delta\x02\$', '\u0394%'),
            (r'\$\\times\$', 'x'),
            (r'\$\\alpha = 0\.05\$', 'alpha = 0.05'),
            (r'\$2\\times10\^\{-5\}\$', '2e-5'),
            (r'\$\\rho = ([^$]*)\$', '\u03c1 = \\1'),
            (r'\$k \\in \\\{([^}]*)\\\}\$', r'k in {\1}'),
            (r'\$c\_\\text\{(\w+)\}\$', r'c_\1'),
            (r'\$([^$]*)\$', r'\1')]
    for pat, rep in MATH:
        s = re.sub(pat, rep, s)
    s = s.replace('``', '\u201c').replace("''", '\u201d')
    s = s.replace('---', '\u2014').replace('--', '\u2013')
    for acc, plain in ((r"\'c", '\u0107'), (r'\"u', '\u00fc'),
                       (r"\'{c}", '\u0107'), (r'\"{u}', '\u00fc')):
        s = s.replace(acc, plain)
    s = s.replace(r'\,', '\u2009').replace(r'\allowbreak', '')
    s = s.replace(r'\ ', ' ').replace('\\\\', ' ')
    s = re.sub(r'\\[a-zA-Z]+\*?', '', s)
    s = s.replace('{', '').replace('}', '')
    for k, v in prot.items():
        s = s.replace(v, k[1:])
    return re.sub(r'\s+', ' ', s).strip()


src = open(TEX).read()

# reference numbering, in order of \bibitem
keys = re.findall(r'\\bibitem\{([^}]*)\}', src)
REFNUM = {k: str(i + 1) for i, k in enumerate(keys)}
LABEL = {'fig:arch': 'Fig. 1', 'fig:inv': 'Fig. 2', 'fig:prior': 'Fig. 3',
         'fig:cost': 'Fig. 4', 'tab:coverage': 'Table I',
         'tab:configs': 'Table II', 'tab:main': 'Table III',
         'sec:data': 'Section III-A', 'sec:regimes': 'Section III-C',
         'sec:families': 'Section III-D', 'sec:prompt': 'Section III-E',
         'sec:scoring': 'Section III-F', 'sec:cost': 'Section III-G',
         'sec:results': 'Section IV', 'sec:rqtwo': 'Section IV-B',
         'sec:mechanism': 'Section IV-C', 'sec:rqthree': 'Section IV-D',
         'sec:threats': 'Section VI', 'eq:breakeven': '(1)'}

# ------------------------------------------------------------------ document
doc = Document()
st = doc.styles['Normal']
st.font.name = 'Times New Roman'
st.font.size = Pt(9.5)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
st.paragraph_format.space_after = Pt(0)
st.paragraph_format.line_spacing = 1.0

sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
for side in ('left_margin', 'right_margin'):
    setattr(sec, side, Inches(0.62))
sec.top_margin, sec.bottom_margin = Inches(0.75), Inches(1.0)


def set_cols(section, n):
    cols = section._sectPr.xpath('./w:cols')[0]
    cols.set(qn('w:num'), str(n))
    cols.set(qn('w:space'), '240')


def para(text, size=9.5, bold=False, italic=False, align=None,
         before=0, after=0, indent=0.18, font='Times New Roman'):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.first_line_indent = Inches(indent)
    pf.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.size, r.bold, r.italic, r.font.name = Pt(size), bold, italic, font
    return p


# ---- title block, single column
set_cols(sec, 1)
para('Large Language Models for Software Requirements Classification: '
     'Cross-Dataset Generalisation and Cost-Efficiency',
     size=20, align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, after=8)
para('Fatma El-Zahraa Samir, Khaled T. Wassif, and Lamia AbouZeid',
     size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)
para('Faculty of Computers and Artificial Intelligence, Cairo University, '
     'Giza, Egypt', size=9.5, italic=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, indent=0)
para('fatmaelzahraasamirabdelfattah@gmail.com', size=9.5,
     align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, after=10)

body = doc.add_section(WD_SECTION.CONTINUOUS)
set_cols(body, 2)


def new_section(ncols):
    s = doc.add_section(WD_SECTION.CONTINUOUS)
    set_cols(s, ncols)
    return s


# ---- abstract and keywords
abstract = detex(src[src.index(r'\begin{abstract}') + 16:src.index(r'\end{abstract}')])
p = doc.add_paragraph()
p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p.paragraph_format.first_line_indent = Inches(0.18)
r = p.add_run('Abstract\u2014')
r.bold = True; r.italic = True; r.font.size = Pt(9)
r = p.add_run(abstract)
r.bold = True; r.font.size = Pt(9)

kw = detex(src[src.index(r'\begin{IEEEkeywords}') + 20:src.index(r'\end{IEEEkeywords}')])
p = doc.add_paragraph()
p.paragraph_format.first_line_indent = Inches(0.18)
p.paragraph_format.space_before = Pt(6)
r = p.add_run('Index Terms\u2014'); r.bold = True; r.italic = True; r.font.size = Pt(9)
r = p.add_run(kw); r.bold = True; r.italic = True; r.font.size = Pt(9)

ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX']
LETTER = 'ABCDEFGH'


def heading(text, level):
    if level == 1:
        para(text.upper(), size=10, align=WD_ALIGN_PARAGRAPH.CENTER,
             indent=0, before=10, after=4)
    else:
        para(text, size=9.5, italic=True, indent=0, before=7, after=2,
             align=WD_ALIGN_PARAGRAPH.LEFT)


def add_table(rows, header_rows=1, widths=None, size=7.5, caption=None,
              number=None):
    if caption:
        para(f'TABLE {number}', size=8, align=WD_ALIGN_PARAGRAPH.CENTER,
             indent=0, before=8)
        para(caption, size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER, indent=0,
             after=3)
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = 'Table Grid'
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for c, val in zip(cells, row):
            c.text = ''
            pp = c.paragraphs[0]
            pp.paragraph_format.space_before = Pt(0.5)
            pp.paragraph_format.space_after = Pt(0.5)
            pp.alignment = (WD_ALIGN_PARAGRAPH.LEFT if c is cells[0]
                            else WD_ALIGN_PARAGRAPH.CENTER)
            rr = pp.add_run(str(val))
            rr.font.size = Pt(size)
            rr.font.name = 'Times New Roman'
            rr.bold = i < header_rows
    para('', size=4, indent=0)
    return t


def add_figure(png, caption, number, width):
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(IMG + png, width=Inches(width))
    para(f'Fig. {number}. ' + caption, size=8, indent=0, after=6,
         align=WD_ALIGN_PARAGRAPH.JUSTIFY)


# ---- table contents, read from the same generated file the paper uses
def coverage_rows():
    block = src[src.index(r'\label{tab:coverage}'):src.index(r'\end{tabular}',
                                                            src.index(r'\label{tab:coverage}'))]
    rows = [['Study', 'Open LLMs', 'Comm. LLMs', 'Cross-project',
             'Cross-dataset', 'Cost']]
    for line in block.split('\n'):
        if r'\cite{' in line and '&' in line:
            cells = [c.strip() for c in line.replace(r'\\', '').split('&')]
            cells = [detex(cells[0])] + [
                {'\\cmark': '\u2713', '\\xmark': '\u2717',
                 '$\\sim$': '~'}.get(c, c) for c in cells[1:]]
            rows.append(cells)
    return rows


def config_rows():
    block = src[src.index(r'\label{tab:configs}'):src.index(r'\end{tabular}',
                                                            src.index(r'\label{tab:configs}'))]
    rows = [['Configuration', 'Checkpoint / endpoint', 'B', 'Access']]
    for line in block.split('\n'):
        if line.count('&') == 3 and r'\textbf' not in line:
            rows.append([detex(c) for c in line.replace(r'\\', '').split('&')])
    return rows


def main_rows():
    rows = [['Configuration',
             'Security \u2014 PROMISE_exp\nID | XP | XD',
             'Security \u2014 SecReq\nID | XP | XD',
             'FR/NFR\nID | XP', 'Top-4\nID | XP', 'Top-6\nID | XP',
             'All-11\nID | XP']]
    spans = [3, 3, 2, 2, 2, 2]
    for line in open('../tables/tab_main.tex'):
        line = line.strip()
        if not line or line.startswith(('\\setlength', '\\renewcommand',
                                        '\\scriptsize', '\\begin', '\\toprule',
                                        '\\midrule', '\\bottomrule', '\\end',
                                        '&', '\\cmidrule', '\\addlinespace',
                                        '\\textbf')):
            continue
        cells = [c.strip() for c in line.replace(r'\\', '').split('&')]
        name = detex(cells[0])
        vals = []
        for c in cells[1:]:
            m = re.match(r'\\multicolumn\{(\d+)\}\{c\}\{(.*)\}$', c)
            vals.append((int(m.group(1)), detex(m.group(2))) if m
                        else (1, detex(c)))
        out, i = [], 0
        for width in spans:
            taken, got = 0, []
            while taken < width and i < len(vals):
                n, v = vals[i]
                got.append(v)
                taken += n
                i += 1
            out.append(' | '.join(got))
        rows.append([name] + out)
    return rows


# ------------------------------------------------------- walk the LaTeX body
FIGS = {
    'fig:arch': ('fig_architecture.png', 1, 6.9),
    'fig:inv': ('fig_inversion.png', 2, 3.3),
    'fig:prior': ('fig_prior.png', 3, 3.3),
    'fig:cost': ('fig_cost.png', 4, 3.3),
}
CAPS = {}
for lbl in FIGS:
    if lbl == 'fig:arch':
        blk = open(ARCH).read()
    else:
        i = src.index(r'\label{' + lbl + '}')
        blk = src[src.rindex(r'\caption{', 0, i):i]
    cap = blk[blk.index(r'\caption{') + 9:]
    depth, j = 1, 0
    while depth and j < len(cap):
        depth += (cap[j] == '{') - (cap[j] == '}')
        j += 1
    CAPS[lbl] = detex(cap[:j - 1])

secno, subno = 0, 0
i = src.index(r'\section{Introduction}')
end = src.index(r'\balance')
chunk = src[i:end]

# drop float environments; they are re-inserted at their anchors
chunk = re.sub(r'\\begin\{table\*?\}.*?\\end\{table\*?\}', '@@TABLE@@', chunk,
               flags=re.S)
chunk = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '@@FIGURE@@', chunk,
               flags=re.S)
chunk = chunk.replace(r'\input{figures/fig_architecture}', '@@ARCH@@')

table_order = ['tab:coverage', 'tab:configs', 'tab:main']
figure_order = ['fig:inv', 'fig:prior', 'fig:cost']
ti = fi = 0

chunk = '\n'.join(l for l in chunk.split('\n') if not l.lstrip().startswith('%%'))
# make every sectioning command start its own block
chunk = re.sub(r'\n(\\(?:sub)?section\{)', r'\n\n\1', chunk)
chunk = re.sub(r'(\\(?:sub)?section\{[^}]*\}\n(?:\\label\{[^}]*\}\n)?)', r'\1\n', chunk)
blocks = re.split(r'\n\s*\n', chunk)
in_item = False
for blk in blocks:
    blk = blk.strip()
    if not blk or set(blk) <= set('%= \n'):
        continue
    if blk == '@@ARCH@@':
        new_section(1)
        add_figure(*FIGS['fig:arch'][:1], caption=CAPS['fig:arch'],
                   number=1, width=FIGS['fig:arch'][2])
        new_section(2)
        continue
    if blk.startswith('@@TABLE@@'):
        lbl = table_order[ti]; ti += 1
        if lbl == 'tab:coverage':
            add_table(coverage_rows(), caption=detex(
                src[src.index(r'\caption{', src.index(r'\begin{table}[t]')) + 9:
                    src.index(r'\label{tab:coverage}')].rstrip()[:-1]),
                number='I')
        elif lbl == 'tab:configs':
            k = src.index(r'\label{tab:configs}')
            add_table(config_rows(), caption=detex(
                src[src.rindex(r'\caption{', 0, k) + 9:k].rstrip()[:-1]),
                number='II')
        else:
            k = src.index(r'\label{tab:main}')
            new_section(1)
            add_table(main_rows(), size=7, caption=detex(
                src[src.rindex(r'\caption{', 0, k) + 9:k].rstrip()[:-1]),
                number='III')
            new_section(2)
        continue
    if blk.startswith('@@FIGURE@@'):
        lbl = figure_order[fi]; fi += 1
        png, num, w = FIGS[lbl]
        add_figure(png, CAPS[lbl], num, w)
        continue
    m = re.match(r'\\section\{([^}]*)\}', blk)
    if m:
        secno += 1; subno = 0
        heading(f'{ROMAN[secno-1]}. ' + detex(m.group(1)), 1)
        rest = blk[m.end():].strip()
        if rest and not rest.startswith('\\label'):
            para(detex(rest))
        continue
    m = re.match(r'\\subsection\{([^}]*)\}', blk)
    if m:
        heading(f'{LETTER[subno]}. ' + detex(m.group(1)), 2)
        subno += 1
        rest = re.sub(r'^\\label\{[^}]*\}', '', blk[m.end():].strip()).strip()
        if rest:
            para(detex(rest))
        continue
    if r'\begin{itemize}' in blk:
        for item in re.split(r'\\item', blk)[1:]:
            item = item.replace(r'\end{itemize}', '')
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(detex(item)); r.font.size = Pt(9)
            r.font.name = 'Times New Roman'
        continue
    if r'\begin{equation}' in blk:
        before = detex(blk.split(r'\begin{equation}')[0])
        if before:
            para(before)
        para('N* = C0 / (c_alt \u2212 c_enc)\u2003\u2003(1)', size=9.5,
             align=WD_ALIGN_PARAGRAPH.CENTER, indent=0, before=4, after=4)
        rest = detex(blk.split(r'\end{equation}')[-1])
        if rest:
            para(rest)
        continue
    if r'\ttfamily' in blk:
        for line in blk.split('\n'):
            line = line.strip()
            if not line or line.startswith(('{', '\\noindent', '\\vspace')):
                continue
            txt = detex(line.replace('\\\\[1.5pt]', '').replace('\\\\', ''))
            if txt:
                para(txt, size=8, indent=0, font='Consolas',
                     align=WD_ALIGN_PARAGRAPH.LEFT)
        para('', size=4, indent=0)
        continue
    txt = detex(blk)
    if txt:
        para(txt)

# ---- references
heading('References', 1)
for k, key in enumerate(keys, 1):
    a = src.index(r'\bibitem{' + key + '}')
    b = src.find(r'\bibitem{', a + 1)
    if b == -1:
        b = src.index(r'\end{thebibliography}')
    entry = src[a + len(r'\bibitem{' + key + '}'):b]
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Inches(-0.2)
    p.paragraph_format.left_indent = Inches(0.2)
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(f'[{k}] ' + detex(entry))
    r.font.size = Pt(8)
    r.font.name = 'Times New Roman'

doc.save(OUT)
print('wrote', os.path.abspath(OUT))
