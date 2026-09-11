// Render paper.json as an IEEE-format .docx: single-column title block and
// full-width floats, two-column body, US Letter.
const fs = require('fs');
const path = require('path');
const D = require('docx');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, WidthType, BorderStyle, ShadingType,
  PageOrientation, SectionType, Footer, convertInchesToTwip,
} = D;

const doc = JSON.parse(fs.readFileSync(path.join(__dirname, 'paper.json'), 'utf8'));
const FIGDIR = '/home/user/MSc./paper/figures';

const FONT = 'Times New Roman';
const BODY = 20;            // half-points => 10pt
const SMALL = 16;           // 8pt
const TINY = 14;            // 7pt
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const NOBORD = { top: NONE, bottom: NONE, left: NONE, right: NONE };
const HAIR = { style: BorderStyle.SINGLE, size: 4, color: '000000' };

// Geometry copied from the ICCI 2026 IEEE conference template (A4 variant):
// page 595.30 x 841.90 pt, body margins top 54pt / sides 45.35pt / bottom 72pt,
// header and footer 36pt, two columns 18pt apart. Word measures in twips.
const PT = 20;
const PAGE_W = Math.round(595.30 * PT), PAGE_H = Math.round(841.90 * PT);
const SIDE = Math.round(45.35 * PT);
const MARGIN = {
  top: Math.round(54 * PT), bottom: Math.round(72 * PT),
  left: SIDE, right: SIDE,
  header: Math.round(36 * PT), footer: Math.round(36 * PT), gutter: 0,
};
// The template opens the title block higher up the page than the body.
const MARGIN_TITLE = Object.assign({}, MARGIN, { top: Math.round(27 * PT) });
const TEXT_W = PAGE_W - MARGIN.left - MARGIN.right;
const GUTTER = Math.round(18 * PT);
const COL_W = Math.floor((TEXT_W - GUTTER) / 2);

const r = (o, size = BODY) => new TextRun({
  text: o.text, bold: !!o.bold, italics: !!o.italic,
  subScript: !!o.sub,
  font: o.mono ? 'Courier New' : FONT, size: o.mono ? size - 2 : size,
});

const para = (runs, opts = {}) => new Paragraph({
  children: runs.map((x) => r(x, opts.size || BODY)),
  alignment: opts.align || AlignmentType.JUSTIFIED,
  spacing: { after: opts.after === undefined ? 0 : opts.after, line: 220 },
  indent: opts.indent,
});

const txt = (s, opts = {}) => para([{ text: s, bold: opts.bold, italic: opts.italic }], opts);

// ---------------------------------------------------------------- tables
function widths(rows, total) {
  let n = 0;
  for (const row of rows) n = Math.max(n, row.cells.reduce((a, c) => a + c.span, 0));
  // first column carries the labels and gets the slack
  const rest = Math.max(3, Math.floor(total * 0.055));
  const firstMin = Math.floor(total * 0.20);
  let w = new Array(n).fill(0);
  const others = n - 1;
  let each = Math.floor((total - firstMin) / others);
  w[0] = total - each * others;
  for (let i = 1; i < n; i++) w[i] = each;
  return w;
}

function buildTable(t, totalWidth) {
  const cw = widths(t.rows, totalWidth);
  const rows = t.rows.map((row, ri) => {
    let col = 0;
    const cells = row.cells.map((c) => {
      let w = 0;
      for (let k = 0; k < c.span; k++) w += cw[col + k] || 0;
      col += c.span;
      const first = col - c.span === 0;
      const cell = new TableCell({
        width: { size: w, type: WidthType.DXA },
        columnSpan: c.span,
        margins: { top: 20, bottom: 20, left: 40, right: 40 },
        borders: {
          top: row.rule === 'top' ? HAIR : NONE,
          bottom: NONE, left: NONE, right: NONE,
        },
        children: [new Paragraph({
          children: (c.runs.length ? c.runs : [{ text: '' }]).map((x) => r(x, TINY)),
          alignment: first ? AlignmentType.LEFT : AlignmentType.CENTER,
          spacing: { after: 0, line: 200 },
        })],
      });
      return cell;
    });
    return new TableRow({ children: cells });
  });
  return new Table({
    columnWidths: cw,
    width: { size: totalWidth, type: WidthType.DXA },
    borders: { top: HAIR, bottom: HAIR, left: NONE, right: NONE,
               insideHorizontal: NONE, insideVertical: NONE },
    rows,
  });
}

const capTable = (t) => new Paragraph({
  children: [new TextRun({ text: `TABLE ${t.number}`, font: FONT, size: SMALL })],
  alignment: AlignmentType.CENTER, spacing: { before: 120, after: 20, line: 200 },
});

const capTableText = (t) => new Paragraph({
  children: t.caption.map((x) => new TextRun({
    text: x.text.toUpperCase(), bold: false, italics: !!x.italic, subScript: !!x.sub,
    font: FONT, size: SMALL,
  })),
  alignment: AlignmentType.CENTER, spacing: { after: 80, line: 200 },
});

const capFig = (f) => new Paragraph({
  children: [new TextRun({ text: `Fig. ${f.number}. `, font: FONT, size: SMALL })]
    .concat(f.caption.map((x) => new TextRun({
      text: x.text, bold: !!x.bold, italics: !!x.italic, subScript: !!x.sub,
      font: FONT, size: SMALL }))),
  alignment: AlignmentType.JUSTIFIED, spacing: { before: 40, after: 140, line: 200 },
});

function figure(f, colWidth) {
  const wPt = (colWidth / 20) * 0.98;            // dxa -> pt
  const w = Math.round(wPt * (96 / 72));         // pt -> px at 96dpi
  const h = Math.round(w / f.aspect);
  return new Paragraph({
    children: [new ImageRun({
      type: 'png',
      data: fs.readFileSync(path.join(FIGDIR, f.image)),
      transformation: { width: w, height: h },
    })],
    alignment: AlignmentType.CENTER, spacing: { before: 120, after: 40 },
  });
}

// The prompt box: a one-cell bordered table holding the instruction verbatim.
const PROMPT_LINES = [
  'You are classifying a software requirement.',
  'Decide whether it is a FUNCTIONAL requirement (FR) -- something the system',
  'must DO -- or a NON-FUNCTIONAL requirement (NFR) -- a quality, constraint',
  'or property such as performance, security or usability.',
  'Answer with exactly one word: "FR" or "NFR".',
  '',
  '⟨few-shot only: k exemplars here⟩',
  '',
  'Requirement:',
  '"""the requirement under test"""',
  '',
  'Answer:',
];

function promptBox(colWidth) {
  const box = new Table({
    columnWidths: [colWidth],
    width: { size: colWidth, type: WidthType.DXA },
    borders: { top: HAIR, bottom: HAIR, left: HAIR, right: HAIR,
               insideHorizontal: NONE, insideVertical: NONE },
    rows: [new TableRow({
      children: [new TableCell({
        width: { size: colWidth, type: WidthType.DXA },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        children: PROMPT_LINES.map((l) => new Paragraph({
          children: [new TextRun({
            text: l || ' ',
            font: 'Courier New', size: 13,
            italics: l.startsWith('⟨') || l.startsWith('…'),
            color: (l.startsWith('⟨') || l.startsWith('…')) ? '767676' : '000000',
          })],
          spacing: { after: 0, line: 180 },
        })),
      })],
    })],
  });
  return box;
}

// The template's first-page footer. IEEE assigns the identifier at
// camera-ready; the X's are the template's own placeholder.
const copyrightFooter = new Footer({
  children: [new Paragraph({
    children: [new TextRun({
      text: 'XXX-X-XXXX-XXXX-X/XX/$XX.00 \u00a920XX IEEE',
      font: FONT, size: SMALL,
    })],
    alignment: AlignmentType.LEFT,
  })],
});

// ------------------------------------------------------------- assembly
const front = [];
front.push(new Paragraph({
  children: [new TextRun({ text: doc.title, font: FONT, size: 48 })],
  alignment: AlignmentType.CENTER, spacing: { after: 220, line: 300 },
}));
front.push(new Paragraph({
  children: [new TextRun({ text: doc.authors, font: FONT, size: 22 })],
  alignment: AlignmentType.CENTER, spacing: { after: 40, line: 240 },
}));
doc.affil_lines.forEach((line, i) => {
  const last = i === doc.affil_lines.length - 1;
  front.push(new Paragraph({
    children: line.map((x) => r(x, BODY)),
    alignment: AlignmentType.CENTER,
    spacing: { after: last ? 240 : 20, line: 230 },
  }));
});
front.push(new Paragraph({
  children: [new TextRun({ text: 'Abstract—', bold: true, italics: true, font: FONT, size: 18 })]
    .concat(doc.abstract.map((x) => new TextRun({
      text: x.text, bold: true, italics: !!x.italic, subScript: !!x.sub,
      font: FONT, size: 18 }))),
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 120, line: 210 },
}));
front.push(new Paragraph({
  children: [new TextRun({ text: 'Keywords—', bold: true, italics: true, font: FONT, size: 18 }),
             new TextRun({ text: doc.keywords, bold: true, font: FONT, size: 18 })],
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 200, line: 210 },
}));

// Body: split into runs of two-column content interrupted by full-width floats.
const sections = [];
sections.push({
  properties: {
    type: SectionType.CONTINUOUS,
    page: { size: { width: PAGE_W, height: PAGE_H }, margin: MARGIN_TITLE },
    column: { count: 1 },
    titlePage: true,
  },
  footers: { first: copyrightFooter },
  children: front,
});

let buf = [];
const flushTwoCol = () => {
  if (!buf.length) return;
  sections.push({
    properties: {
      type: SectionType.CONTINUOUS,
      page: { size: { width: PAGE_W, height: PAGE_H }, margin: MARGIN },
      column: { count: 2, space: GUTTER, equalWidth: true },
    },
    children: buf,
  });
  buf = [];
};
const wideSection = (children) => {
  sections.push({
    properties: {
      type: SectionType.CONTINUOUS,
      page: { size: { width: PAGE_W, height: PAGE_H }, margin: MARGIN },
      column: { count: 1 },
    },
    children,
  });
};

for (const b of doc.blocks) {
  if (b.type === 'h1') {
    buf.push(new Paragraph({
      children: [new TextRun({ text: `${b.number}.  ${b.text}`, font: FONT, size: BODY })],
      alignment: AlignmentType.CENTER, spacing: { before: 200, after: 100, line: 220 },
    }));
  } else if (b.type === 'h2') {
    buf.push(new Paragraph({
      children: [new TextRun({ text: `${b.number}. ${b.text}`, italics: true, font: FONT, size: BODY })],
      spacing: { before: 140, after: 60, line: 220 },
    }));
  } else if (b.type === 'p') {
    buf.push(para(b.runs, { indent: { firstLine: 180 } }));
  } else if (b.type === 'li') {
    buf.push(para([{ text: `${b.number}) ` }].concat(b.runs),
      { indent: { left: 200, hanging: 200 } }));
  } else if (b.type === 'equation') {
    buf.push(new Paragraph({
      children: [new TextRun({ text: b.text, font: FONT, size: BODY, italics: true }),
                 new TextRun({ text: '\t\t' + b.number, font: FONT, size: BODY })],
      alignment: AlignmentType.CENTER, spacing: { before: 100, after: 100 },
    }));
  } else if (b.type === 'table') {
    const w = b.wide ? TEXT_W : COL_W;
    const parts = [capTable(b), capTableText(b), buildTable(b, w),
                   new Paragraph({ text: '', spacing: { after: 160 } })];
    if (b.wide) { flushTwoCol(); wideSection(parts); } else { buf.push(...parts); }
  } else if (b.type === 'figure') {
    const w = b.wide ? TEXT_W : COL_W;
    const parts = [figure(b, w), capFig(b)];
    if (b.wide) { flushTwoCol(); wideSection(parts); } else { buf.push(...parts); }
  } else if (b.type === 'promptbox') {
    buf.push(promptBox(COL_W));
    buf.push(new Paragraph({ text: '', spacing: { after: 120 } }));
  }
}

// references
buf.push(new Paragraph({
  children: [new TextRun({ text: 'REFERENCES', font: FONT, size: BODY })],
  alignment: AlignmentType.CENTER, spacing: { before: 220, after: 100 },
}));
doc.references.forEach((refRuns, i) => {
  buf.push(new Paragraph({
    children: [new TextRun({ text: `[${i + 1}] `, font: FONT, size: SMALL })]
      .concat(refRuns.map((x) => new TextRun({
        text: x.text, italics: !!x.italic, bold: !!x.bold, subScript: !!x.sub,
        font: FONT, size: SMALL }))),
    alignment: AlignmentType.JUSTIFIED,
    indent: { left: 260, hanging: 260 },
    spacing: { after: 20, line: 200 },
  }));
});
flushTwoCol();

const out = new Document({ sections, styles: { default: { document: { run: { font: FONT, size: BODY } } } } });
Packer.toBuffer(out).then((b) => {
  fs.writeFileSync(process.argv[2] || '/tmp/paper.docx', b);
  console.log('wrote', process.argv[2], b.length, 'bytes');
});
