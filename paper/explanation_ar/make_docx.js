/* Build the Egyptian-Arabic study guide as a right-to-left Word document.
   Input : out/paper_explanation_ar.md  (+ out/figures, out/imgsizes.json)
   Output: out/شرح_البيبر_بالمصري.docx                                        */
const fs = require('fs');
const path = require('path');
const D = require('./node_modules/docx');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  HeadingLevel, TableOfContents, PageBreak, ImageRun, AlignmentType, ShadingType,
  BorderStyle, LevelFormat, Footer, PageNumber, convertInchesToTwip,
} = D;

const SP = __dirname;
const MD = fs.readFileSync(path.join(SP, 'out/paper_explanation_ar.md'), 'utf8');
const IMG = JSON.parse(fs.readFileSync(path.join(SP, 'out/imgsizes.json'), 'utf8'));

// ---------------------------------------------------------------- design tokens
const INK = '17212B', INK2 = '4A5866', MUTED = '7A8794';
const ENC = '0072B2', LLM = 'B67A00', RULE = 'D3DAE2', PANEL = 'EEF2F6', SOFT = 'F6F8FA';
const AR = 'Arial', MONO = 'Consolas';
const BODY = 21;                       // half-points → 10.5pt
const PAGE_W = 11906, MARGIN = 1000;   // A4 portrait, DXA
const CONTENT = PAGE_W - 2 * MARGIN;   // 9906 DXA
const MAX_IMG_PX = Math.round((CONTENT / 1440) * 96);   // ≈ 660 px

const hasArabic = (t) => /[؀-ۿ]/.test(t);
const cellBorder = { style: BorderStyle.SINGLE, size: 4, color: RULE };
const TBL_BORDERS = { top: cellBorder, bottom: cellBorder, left: cellBorder, right: cellBorder,
                      insideHorizontal: cellBorder, insideVertical: cellBorder };

// ---------------------------------------------------------------- inline parsing
// Recursive tokenizer: code spans, then **bold**, then *italic* (guarded so that
// N* in "N* = C0/Delta c" never opens an emphasis span). Bold and italic re-parse
// their contents, so `code` inside **bold** is handled.
// Backslash escapes are neutralised BEFORE emphasis parsing (CommonMark order), so
// "**break-even N\***" keeps its literal star instead of eating a bold delimiter.
const ESC_NAMES = { '*': 'STAR', '_': 'USCORE', '`': 'TICK', '|': 'PIPE', '[': 'LB', ']': 'RB', '\\': 'BSL' };
const ESC_CHARS = { STAR: '*', USCORE: '_', TICK: '`', PIPE: '|', LB: '[', RB: ']', BSL: '\\' };
const protect = (t) => t.replace(/\\([*_`|\[\]\\])/g, (m, c) => `@@ESC${ESC_NAMES[c]}@@`);
const restore = (t) => t.replace(/@@ESC(STAR|USCORE|TICK|PIPE|LB|RB|BSL)@@/g, (m, n) => ESC_CHARS[n]);

const CODE_RE = /`[^`\n]+`/;
const BOLD_RE = /\*\*(.+?)\*\*/;
const ITAL_RE = /(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])/;

function plainRuns(raw, opts, out) {
  if (!raw) return;
  raw = restore(raw);
  for (const piece of raw.split(/(\s+)/)) {
    if (piece === '') continue;
    out.push(new TextRun({ text: piece, rightToLeft: hasArabic(piece), ...opts }));
  }
}

function codeRun(inner, opts) {
  return new TextRun({
    text: restore(inner), font: { ascii: MONO, hAnsi: MONO, cs: MONO },
    size: BODY - 1, sizeComplexScript: BODY - 1, color: '2B3743',
    shading: { type: ShadingType.CLEAR, fill: PANEL }, ...opts,
  });
}

function tokenize(text, opts, out) {
  while (text) {
    const cands = [];
    let m;
    if ((m = CODE_RE.exec(text))) cands.push({ i: m.index, kind: 'code', m });
    if ((m = BOLD_RE.exec(text))) cands.push({ i: m.index, kind: 'bold', m });
    if ((m = ITAL_RE.exec(text))) cands.push({ i: m.index, kind: 'ital', m });
    if (!cands.length) { plainRuns(text, opts, out); return; }
    cands.sort((a, b) => a.i - b.i || (a.kind === 'code' ? -1 : 1));
    const hit = cands[0];
    plainRuns(text.slice(0, hit.i), opts, out);
    if (hit.kind === 'code') out.push(codeRun(hit.m[0].slice(1, -1), opts));
    else if (hit.kind === 'bold') tokenize(hit.m[1], { ...opts, bold: true }, out);
    else tokenize(hit.m[1], { ...opts, italics: true, color: INK2 }, out);
    text = text.slice(hit.i + hit.m[0].length);
  }
}

function inlineRuns(text, base = {}) {
  const out = [];
  tokenize(protect(text), base, out);
  return out.length ? out : [new TextRun({ text: '', ...base })];
}

const para = (text, opts = {}) => new Paragraph({
  bidirectional: true, alignment: AlignmentType.BOTH,
  spacing: { after: 120, line: 300 },
  children: inlineRuns(text),
  ...opts,
});

// ---------------------------------------------------------------- block parsing
function parseBlocks(md) {
  const lines = md.split('\n');
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const t = line.trim();

    if (t === '') { i++; continue; }

    if (t === '---' || t === '***') { blocks.push({ k: 'hr' }); i++; continue; }

    let m;
    if ((m = t.match(/^(#{1,6})\s+(.*)$/))) {
      blocks.push({ k: 'h', level: m[1].length, text: m[2].trim() }); i++; continue;
    }

    if ((m = t.match(/^!\[([^\]]*)\]\(([^)]+)\)\s*$/))) {
      blocks.push({ k: 'img', alt: m[1], src: m[2] }); i++; continue;
    }

    if (t.startsWith('```')) {
      const buf = []; i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) { buf.push(lines[i]); i++; }
      i++; blocks.push({ k: 'code', lines: buf }); continue;
    }

    if (t.startsWith('>')) {
      const buf = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        buf.push(lines[i].trim().replace(/^>\s?/, '')); i++;
      }
      blocks.push({ k: 'quote', text: buf.join(' ') }); continue;
    }

    if (t.startsWith('|') && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) { rows.push(lines[i].trim()); i++; }
      const cells = rows.filter(r => !/^\|[\s:|-]+\|$/.test(r))
        .map(r => r.replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim()));
      blocks.push({ k: 'table', head: cells[0], body: cells.slice(1) }); continue;
    }

    if ((m = line.match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/))) {
      const items = [];
      while (i < lines.length) {
        const mm = lines[i].match(/^(\s*)([-*+]|\d+[.)])\s+(.*)$/);
        if (!mm) {
          // continuation line of the previous item
          if (items.length && lines[i].trim() !== '' && /^\s{2,}\S/.test(lines[i]) && !lines[i].trim().startsWith('|')) {
            items[items.length - 1].text += ' ' + lines[i].trim(); i++; continue;
          }
          break;
        }
        items.push({
          indent: Math.min(2, Math.floor(mm[1].length / 2)),
          ordered: /\d/.test(mm[2]),
          text: mm[3].trim(),
        });
        i++;
      }
      blocks.push({ k: 'list', items }); continue;
    }

    // plain paragraph: gather until a blank line or a new block starts
    const buf = [];
    while (i < lines.length) {
      const l = lines[i], s = l.trim();
      if (s === '' || s.startsWith('#') || s.startsWith('|') || s.startsWith('>') ||
          s.startsWith('```') || s === '---' || /^!\[/.test(s) ||
          /^(\s*)([-*+]|\d+[.)])\s+/.test(l)) break;
      buf.push(s); i++;
    }
    if (buf.length) blocks.push({ k: 'p', text: buf.join(' ') });
  }
  return blocks;
}

// ---------------------------------------------------------------- rendering
function renderTable(b) {
  const n = b.head.length;
  // first column a bit wider (it carries the number / the term)
  const w = [];
  const firstShare = n <= 2 ? 0.42 : 0.30;
  w.push(Math.round(CONTENT * firstShare));
  for (let c = 1; c < n; c++) w.push(Math.round((CONTENT - w[0]) / (n - 1)));
  const row = (cells, header) => new TableRow({
    tableHeader: header,
    children: cells.map((c, idx) => new TableCell({
      width: { size: w[idx] !== undefined ? w[idx] : w[w.length - 1], type: WidthType.DXA },
      shading: header ? { type: ShadingType.CLEAR, fill: PANEL } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({
        bidirectional: true, spacing: { before: 20, after: 20, line: 260 },
        children: inlineRuns(c, header ? { bold: true } : {}),
      })],
    })),
  });
  return new Table({
    visuallyRightToLeft: true,
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: w,
    borders: TBL_BORDERS,
    rows: [row(b.head, true), ...b.body.map(r => {
      while (r.length < n) r.push('');
      return row(r.slice(0, n), false);
    })],
  });
}

function renderImage(b) {
  const file = path.basename(b.src);
  const dims = IMG[file];
  const abs = path.join(SP, 'out/figures', file);
  if (!dims || !fs.existsSync(abs)) return [];
  let [pw, ph] = dims;
  const scale = Math.min(1, MAX_IMG_PX / pw, 760 / ph);
  const width = Math.round(pw * scale), height = Math.round(ph * scale);
  return [new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 },
    children: [new ImageRun({
      type: file.endsWith('.jpg') ? 'jpg' : 'png',
      data: fs.readFileSync(abs),
      transformation: { width, height },
    })],
  })];
}

function renderBlocks(blocks) {
  const out = [];
  let firstH1 = true;
  for (const b of blocks) {
    switch (b.k) {
      case 'h': {
        if (b.level === 2) {
          if (!firstH1) out.push(new Paragraph({ children: [new PageBreak()] }));
          firstH1 = false;
          out.push(new Paragraph({
            heading: HeadingLevel.HEADING_1, bidirectional: true,
            spacing: { before: 120, after: 200 },
            border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ENC, space: 6 } },
            children: inlineRuns(b.text, { bold: true, color: ENC, size: 32, sizeComplexScript: 32 }),
          }));
        } else if (b.level === 3) {
          out.push(new Paragraph({
            heading: HeadingLevel.HEADING_2, bidirectional: true,
            spacing: { before: 280, after: 120 },
            children: inlineRuns(b.text, { bold: true, color: INK, size: 26, sizeComplexScript: 26 }),
          }));
        } else if (b.level >= 4) {
          out.push(new Paragraph({
            heading: HeadingLevel.HEADING_3, bidirectional: true,
            spacing: { before: 200, after: 80 },
            children: inlineRuns(b.text, { bold: true, color: LLM, size: 23, sizeComplexScript: 23 }),
          }));
        }
        break;
      }
      case 'p': out.push(para(b.text)); break;
      case 'quote':
        out.push(new Paragraph({
          bidirectional: true, spacing: { before: 120, after: 160, line: 300 },
          indent: { left: 240, right: 240 },
          shading: { type: ShadingType.CLEAR, fill: SOFT },
          border: { right: { style: BorderStyle.SINGLE, size: 18, color: ENC, space: 8 } },
          children: inlineRuns(b.text),
        }));
        break;
      case 'list':
        for (const it of b.items) {
          out.push(new Paragraph({
            bidirectional: true, spacing: { after: 60, line: 290 },
            numbering: { reference: it.ordered ? 'num' : 'bul', level: it.indent },
            children: inlineRuns(it.text),
          }));
        }
        break;
      case 'table': out.push(renderTable(b)); out.push(new Paragraph({ spacing: { after: 120 }, children: [] })); break;
      case 'img': out.push(...renderImage(b)); break;
      case 'code':
        out.push(new Paragraph({
          spacing: { before: 100, after: 140 },
          shading: { type: ShadingType.CLEAR, fill: PANEL },
          children: b.lines.map((l, idx) => new TextRun({
            text: l, font: { ascii: MONO, hAnsi: MONO, cs: MONO },
            size: BODY - 2, sizeComplexScript: BODY - 2, break: idx ? 1 : 0,
          })),
        }));
        break;
      case 'hr':
        out.push(new Paragraph({
          spacing: { before: 60, after: 160 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 1 } },
          children: [],
        }));
        break;
    }
  }
  return out;
}

// ---------------------------------------------------------------- assemble
const blocks = parseBlocks(MD);
// strip the markdown H1 and the two quote lines that follow it — they become the cover
const firstH2 = blocks.findIndex(b => b.k === 'h' && b.level === 2);
const body = blocks.slice(firstH2);

const cover = [
  new Paragraph({ spacing: { before: 2200, after: 0 }, alignment: AlignmentType.RIGHT, bidirectional: true,
    children: [new TextRun({ text: 'شرح رسالة الماجستير', rightToLeft: true, color: MUTED, size: 24, sizeComplexScript: 24, characterSpacing: 20 })] }),
  new Paragraph({ spacing: { before: 120, after: 40 }, alignment: AlignmentType.RIGHT, bidirectional: true,
    children: [new TextRun({ text: 'البيبر رقم برقم ورسمة برسمة', rightToLeft: true, bold: true, color: INK, size: 56, sizeComplexScript: 56 })] }),
  new Paragraph({ spacing: { after: 300 }, alignment: AlignmentType.RIGHT, bidirectional: true,
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: LLM, space: 10 } },
    children: [new TextRun({ text: 'كل رقم: هو إيه، جاي منين، وليه القيمة دي بالذات', rightToLeft: true, color: INK2, size: 26, sizeComplexScript: 26 })] }),
  new Paragraph({ spacing: { before: 240, after: 60 }, alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: 'Fine-Tuned Encoders or Prompted LLMs for Requirements Classification?', color: INK, size: 22, bold: true })] }),
  new Paragraph({ spacing: { after: 200 }, alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: 'The Verdict Inverts Under Distribution Shift', color: INK, size: 22, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.LEFT,
    children: [new TextRun({ text: 'Fatma El-Zahraa Samir · Khaled T. Wassif · Lamia AbouZeid', color: MUTED, size: 20 })] }),
  new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 500 },
    children: [new TextRun({ text: 'Faculty of Computers and Artificial Intelligence, Cairo University', color: MUTED, size: 20 })] }),
  new Paragraph({ bidirectional: true, alignment: AlignmentType.RIGHT,
    shading: { type: ShadingType.CLEAR, fill: SOFT },
    border: { right: { style: BorderStyle.SINGLE, size: 18, color: ENC, space: 8 } },
    spacing: { before: 200, after: 200 },
    children: inlineRuns('كل رقم في الملف ده اتراجع على ملفات النتايج الخام (الـ CSV بتاعة المراحل 1 إلى 5) وعلى نص الورقة نفسه، مش منقول من الملخصات.') }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, bidirectional: true, spacing: { after: 160 },
    children: [new TextRun({ text: 'المحتويات', rightToLeft: true, bold: true, color: ENC, size: 32, sizeComplexScript: 32 })] }),
  new Paragraph({ bidirectional: true, spacing: { after: 200 },
    children: [new TextRun({ text: 'لو الفهرس ظهر فاضي: اضغطي عليه بزرار الفأرة اليمين واختاري Update Field.', rightToLeft: true, italics: true, color: MUTED, size: 19, sizeComplexScript: 19 })] }),
  new TableOfContents('Contents', { hyperlink: true, headingStyleRange: '1-2' }),
  new Paragraph({ children: [new PageBreak()] }),
];

const doc = new Document({
  creator: 'Fatma El-Zahraa Samir',
  title: 'شرح البيبر رقم برقم ورسمة برسمة',
  description: 'شرح تفصيلي بالعامية المصرية لكل رقم ورسمة في رسالة الماجستير',
  styles: {
    default: {
      document: { run: { font: { ascii: AR, hAnsi: AR, cs: AR }, size: BODY, sizeComplexScript: BODY, color: INK } },
      heading1: { run: { font: { ascii: AR, hAnsi: AR, cs: AR }, bold: true, color: ENC, size: 32, sizeComplexScript: 32 },
                  paragraph: { spacing: { before: 120, after: 200 } } },
      heading2: { run: { font: { ascii: AR, hAnsi: AR, cs: AR }, bold: true, color: INK, size: 26, sizeComplexScript: 26 },
                  paragraph: { spacing: { before: 280, after: 120 } } },
      heading3: { run: { font: { ascii: AR, hAnsi: AR, cs: AR }, bold: true, color: LLM, size: 23, sizeComplexScript: 23 },
                  paragraph: { spacing: { before: 200, after: 80 } } },
    },
  },
  numbering: {
    config: [
      { reference: 'bul', levels: [0, 1, 2].map(l => ({
          level: l, format: LevelFormat.BULLET, text: ['•', '◦', '▪'][l],
          alignment: AlignmentType.START,
          style: { paragraph: { indent: { start: 360 * (l + 1), hanging: 240 } } } })) },
      { reference: 'num', levels: [0, 1, 2].map(l => ({
          level: l, format: LevelFormat.DECIMAL, text: `%${l + 1}.`,
          alignment: AlignmentType.START,
          style: { paragraph: { indent: { start: 360 * (l + 1), hanging: 300 } } } })) },
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER, spacing: { before: 120 },
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } },
        children: [new TextRun({ children: [PageNumber.CURRENT], color: MUTED, size: 18 })] })] }),
    },
    children: [...cover, ...renderBlocks(body)],
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(SP, 'out/شرح_البيبر_بالمصري.docx');
  fs.writeFileSync(out, buf);
  console.log('wrote', out, (buf.length / 1024 / 1024).toFixed(2), 'MB');
  console.log('blocks:', blocks.length, '| body blocks:', body.length);
}).catch(e => { console.error('ERROR', e); process.exit(1); });
