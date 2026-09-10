// Render paper.json as an IEEE-format .docx: single-column title block and
// full-width floats, two-column body, US Letter.
const fs = require('fs');
const path = require('path');
const D = require('docx');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, WidthType, BorderStyle, ShadingType,
  PageOrientation, SectionType, convertInchesToTwip,
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

// Column geometry: Letter, 0.75in top/bottom, 0.625in sides, 0.25in gutter.
const PAGE_W = 12240, PAGE_H = 15840;
const MARGIN = { top: 1080, bottom: 1080, left: 900, right: 900, gutter: 0 };
const TEXT_W = PAGE_W - MARGIN.left - MARGIN.right;   // 10440 dxa
const GUTTER = 360;
const COL_W = Math.floor((TEXT_W - GUTTER) / 2);      // 5040 dxa

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

// ------------------------------------------------------------- assembly
const front = [];
front.push(new Paragraph({
  children: [new TextRun({ text: doc.title, font: FONT, size: 48 })],
  alignment: AlignmentType.CENTER, spacing: { after: 220, line: 300 },
}));
front.push(txt(doc.authors, { align: AlignmentType.CENTER, after: 40 }));
front.push(txt(doc.affil, { align: AlignmentType.CENTER, italic: true, after: 40 }));
front.push(txt(doc.email, { align: AlignmentType.CENTER, after: 240 }));
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
    page: { size: { width: PAGE_W, height: PAGE_H }, margin: MARGIN },
    column: { count: 1 },
  },
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
