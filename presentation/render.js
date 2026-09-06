// Renders deck.json -> .pptx with pptxgenjs.
// usage: node render.js deck.json out.pptx [--notes]
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');

const [,, deckPath, outPath, ...flags] = process.argv;
const WITH_NOTES = flags.includes('--notes');
const deck = JSON.parse(fs.readFileSync(deckPath, 'utf8'));
const FIGS = path.join(__dirname, 'figs');

// ---------------------------------------------------------------- palette (matches the paper's Okabe–Ito figures)
const C = {
  ink: '132238',      // dark slides
  ink2: '1B3352',
  text: '1F2A37',
  muted: '6B7280',
  line: 'D6DAE0',
  panel: 'F2F4F7',
  blue: '0072B2',     // fine-tuned encoders
  blueTint: 'E3EEF7',
  gold: 'E69F00',     // prompted LLMs
  goldTint: 'FBF1DC',
  green: '009E73',    // hosted
  pink: 'CC79A7',     // commercial
  white: 'FFFFFF',
  ice: 'CADCFC',
};
const SERIES = [C.blue, C.gold, C.green, C.pink, '8A94A6', '4C6A92'];
const FONT_H = 'Cambria';
const FONT_B = 'Calibri';

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE'; // 13.33 x 7.5
pres.author = 'Fatma El-Zahraa Samir';
pres.title = 'Fine-Tuned Encoders or Prompted LLMs for Requirements Classification?';
const W = 13.333, H = 7.5, M = 0.6;
const CONTENT_W = W - 2 * M;

// ---------------------------------------------------------------- helpers
const shadow = () => ({ type: 'outer', blur: 6, offset: 2, angle: 90, color: '000000', opacity: 0.10 });
const estLines = (text, widthIn, pt) => {
  const cpl = Math.max(8, Math.floor(widthIn / (pt * 0.0072))); // ~0.52em avg glyph width
  return Math.max(1, Math.ceil((text || '').length / cpl));
};
const lineH = pt => pt * 1.22 / 72;

function frame(slide, n, dark) {
  slide.background = { color: dark ? C.ink : C.white };
  slide.addText('Fine-tuned encoders or prompted LLMs?  ·  The verdict inverts under distribution shift', {
    x: M, y: H - 0.42, w: 8, h: 0.3, fontFace: FONT_B, fontSize: 9, color: dark ? '8FA3BF' : C.muted, isTextBox: true, margin: 0,
  });
  slide.addText(String(n), {
    x: W - M - 1, y: H - 0.42, w: 1, h: 0.3, fontFace: FONT_B, fontSize: 9, color: dark ? '8FA3BF' : C.muted, align: 'right', isTextBox: true, margin: 0,
  });
}

function title(slide, text, dark, opts = {}) {
  text = clean(text);
  const long = text.length > 48;
  slide.addText(text, {
    x: M, y: 0.38, w: CONTENT_W, h: 0.95, fontFace: FONT_H, fontSize: long ? 26 : 30, bold: true,
    color: dark ? C.white : C.text, valign: 'middle', isTextBox: true, margin: 0, ...opts,
  });
}

function takeaway(slide, text, y = 6.18) {
  text = clean(text);
  if (!text) return;
  slide.addShape(pres.ShapeType.roundRect, { x: M, y, w: CONTENT_W, h: 0.72, fill: { color: C.blueTint }, line: { color: C.blueTint }, rectRadius: 0.08 });
  slide.addText(text, {
    x: M + 0.25, y, w: CONTENT_W - 0.5, h: 0.72, fontFace: FONT_B, fontSize: text.length > 150 ? 12 : text.length > 105 ? 13 : 14, bold: true, color: C.ink2, valign: 'middle', isTextBox: true, margin: 0,
  });
}

const clean = t => String(t == null ? '' : t).replace(/\*\*/g, '').replace(/^\s*[-•·]\s+/, '').trim();

// measure a bullet list: pick the largest font ≤ startPt that fits hAvail
function measureRows(items, w, hAvail, opts = {}) {
  const { startPt = 16, minPt = 12, numbered = true } = opts;
  const badge = numbered ? 0.34 : 0.14;
  const gap = 0.16;
  const textW = w - badge - 0.22;
  let pt = startPt, heights, total;
  for (;;) {
    heights = items.map(t => estLines(t, textW, pt) * lineH(pt) + 0.06);
    total = heights.reduce((a, b) => a + b, 0) + gap * (items.length - 1);
    if (total <= hAvail || pt <= minPt) break;
    pt -= 1;
  }
  return { pt, heights, total, badge, gap, textW };
}

// numbered bullet rows with a circle badge; auto-sizes font to fit the box
function bulletRows(slide, items, x, y, w, hAvail, opts = {}) {
  const { color = C.blue, numbered = true, textColor = C.text } = opts;
  items = (items || []).map(clean).filter(Boolean);
  if (!items.length) return y;
  const { pt, heights, badge, gap, textW } = measureRows(items, w, hAvail, opts);
  let cy = y;
  items.forEach((t, i) => {
    const hh = heights[i];
    if (numbered) {
      slide.addShape(pres.ShapeType.ellipse, { x, y: cy + 0.03, w: badge, h: badge, fill: { color }, line: { color } });
      slide.addText(String(i + 1), { x, y: cy + 0.03, w: badge, h: badge, fontFace: FONT_B, fontSize: 11, bold: true, color: C.white, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    } else {
      slide.addShape(pres.ShapeType.ellipse, { x: x + 0.02, y: cy + 0.11, w: badge, h: badge, fill: { color }, line: { color } });
    }
    slide.addText(t, { x: x + badge + 0.22, y: cy, w: textW, h: hh, fontFace: FONT_B, fontSize: pt, color: textColor, valign: 'top', isTextBox: true, margin: 0 });
    cy += hh + gap;
  });
  return cy;
}

function statCards(slide, stats, x, y, w, h, opts = {}) {
  const { vertical = false, valuePt = 34 } = opts;
  const n = stats.length;
  const gap = 0.25;
  stats.forEach((s, i) => {
    const cw = vertical ? w : (w - gap * (n - 1)) / n;
    const ch = vertical ? (h - gap * (n - 1)) / n : h;
    const cx = vertical ? x : x + i * (cw + gap);
    const cy = vertical ? y + i * (ch + gap) : y;
    slide.addShape(pres.ShapeType.roundRect, { x: cx, y: cy, w: cw, h: ch, fill: { color: C.white }, line: { color: C.line, width: 0.75 }, rectRadius: 0.1, shadow: shadow() });
    const vPt = Math.min(valuePt, Math.max(16, Math.floor((cw - 0.3) * 72 / (Math.max(3, s.value.length) * 0.66))));
    slide.addText(s.value, { x: cx + 0.15, y: cy + 0.12, w: cw - 0.3, h: ch * 0.55, fontFace: FONT_H, fontSize: vPt, bold: true, color: C.blue, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    slide.addText(s.label, { x: cx + 0.15, y: cy + ch * 0.62, w: cw - 0.3, h: ch * 0.36, fontFace: FONT_B, fontSize: 12, color: C.muted, align: 'center', valign: 'top', isTextBox: true, margin: 0 });
  });
}

// ---------------------------------------------------------------- layouts
const L = {};

L.title = (s, d) => {
  s.background = { color: C.ink };
  // two-arms motif
  s.addShape(pres.ShapeType.ellipse, { x: 9.3, y: 1.0, w: 3.4, h: 3.4, fill: { color: C.blue, transparency: 25 }, line: { color: C.blue, transparency: 25 } });
  s.addShape(pres.ShapeType.ellipse, { x: 10.6, y: 2.6, w: 3.0, h: 3.0, fill: { color: C.gold, transparency: 30 }, line: { color: C.gold, transparency: 30 } });
  s.addText('Fine-tuned encoders', { x: 9.3, y: 1.7, w: 3.4, h: 0.4, fontFace: FONT_B, fontSize: 12, color: C.white, align: 'center', isTextBox: true, margin: 0 });
  s.addText('Prompted LLMs', { x: 10.6, y: 4.7, w: 3.0, h: 0.4, fontFace: FONT_B, fontSize: 12, color: C.white, align: 'center', isTextBox: true, margin: 0 });
  s.addText('MSc THESIS DEFENSE', { x: M, y: 0.9, w: 8, h: 0.4, fontFace: FONT_B, fontSize: 12, bold: true, color: C.ice, charSpacing: 3, isTextBox: true, margin: 0 });
  s.addText(d.title, { x: M, y: 1.45, w: 8.5, h: 2.6, fontFace: FONT_H, fontSize: 34, bold: true, color: C.white, valign: 'middle', isTextBox: true, margin: 0 });
  if (d.subtitle) s.addText(d.subtitle, { x: M, y: 4.25, w: 8.5, h: 1.6, fontFace: FONT_B, fontSize: 15, color: C.ice, valign: 'top', isTextBox: true, margin: 0, lineSpacingMultiple: 1.2 });
  if (d.bullets && d.bullets.length) s.addText(d.bullets.join('   ·   '), { x: M, y: 6.1, w: 8.5, h: 0.5, fontFace: FONT_B, fontSize: 11, color: '8FA3BF', isTextBox: true, margin: 0 });
};

L.section = (s, d, n) => {
  frame(s, n, true);
  s.addShape(pres.ShapeType.ellipse, { x: 10.2, y: -1.2, w: 5.2, h: 5.2, fill: { color: C.blue, transparency: 70 }, line: { color: C.blue, transparency: 70 } });
  s.addShape(pres.ShapeType.ellipse, { x: 11.4, y: 3.6, w: 3.4, h: 3.4, fill: { color: C.gold, transparency: 70 }, line: { color: C.gold, transparency: 70 } });
  s.addText(d.title, { x: M, y: 2.3, w: 9.5, h: 1.5, fontFace: FONT_H, fontSize: 40, bold: true, color: C.white, valign: 'bottom', isTextBox: true, margin: 0 });
  if (d.subtitle) s.addText(d.subtitle, { x: M, y: 3.95, w: 9.5, h: 1.2, fontFace: FONT_B, fontSize: 18, color: C.ice, valign: 'top', isTextBox: true, margin: 0 });
};

L.bullets = (s, d, n) => {
  frame(s, n); title(s, d.title);
  const hasStats = d.stats && d.stats.length;
  const bottom = d.takeaway ? 6.0 : 6.85;
  const bw = hasStats ? 7.7 : CONTENT_W;
  let end = bulletRows(s, d.bullets, M, 1.55, bw, bottom - 1.55);
  if (hasStats) {
    const k = Math.min(3, d.stats.length);
    const sh = Math.min(bottom - 1.55, 1.45 * k + 0.25 * (k - 1));
    statCards(s, d.stats.slice(0, 3), 8.75, 1.55, W - M - 8.75, sh, { vertical: true, valuePt: 30 });
    end = Math.max(end, 1.55 + sh);
  }
  takeaway(s, d.takeaway, Math.min(6.18, end + 0.35));
};

L.two_column = (s, d, n) => {
  frame(s, n); title(s, d.title);
  const top = 1.55, bottom = d.takeaway ? 6.0 : 6.85, gap = 0.3;
  const cw = (CONTENT_W - gap) / 2;
  const cols = [
    { x: M, heading: d.left_heading, items: d.bullets || [], color: C.blue, tint: C.blueTint },
    { x: M + cw + gap, heading: d.right_heading, items: d.right_bullets || [], color: C.gold, tint: C.goldTint },
  ];
  const measured = cols.map(c => measureRows(c.items.map(clean).filter(Boolean), cw - 0.55, bottom - top - 1.05, { numbered: false, startPt: 15, minPt: 11 }));
  const panelH = Math.min(bottom - top, Math.max(2.4, 1.05 + Math.max(...measured.map(m => m.total)) + 0.35));
  cols.forEach(c => {
    s.addShape(pres.ShapeType.roundRect, { x: c.x, y: top, w: cw, h: panelH, fill: { color: C.panel }, line: { color: C.panel }, rectRadius: 0.1 });
    s.addShape(pres.ShapeType.ellipse, { x: c.x + 0.25, y: top + 0.25, w: 0.28, h: 0.28, fill: { color: c.color }, line: { color: c.color } });
    s.addText(c.heading || '', { x: c.x + 0.65, y: top + 0.15, w: cw - 0.9, h: 0.5, fontFace: FONT_H, fontSize: 18, bold: true, color: C.text, valign: 'middle', isTextBox: true, margin: 0 });
    bulletRows(s, c.items, c.x + 0.3, top + 0.85, cw - 0.55, bottom - top - 1.05, { color: c.color, numbered: false, startPt: 15, minPt: 11 });
  });
  takeaway(s, d.takeaway, Math.min(6.18, top + panelH + 0.35));
};

L.stats = (s, d, n) => {
  frame(s, n); title(s, d.title);
  const stats = (d.stats || []).slice(0, 4);
  statCards(s, stats, M, 1.55, CONTENT_W, 2.1, { valuePt: 38 });
  const bottom = d.takeaway ? 6.0 : 6.85;
  const end = bulletRows(s, d.bullets, M, 3.95, CONTENT_W, bottom - 3.95, { startPt: 15 });
  takeaway(s, d.takeaway, Math.min(6.18, Math.max(end, 3.95) + 0.35));
};

L.table = (s, d, n) => {
  frame(s, n); title(s, d.title);
  const { headers, rows } = d.table;
  const ncol = headers.length;
  const scoreLike = rows.every(r => r.slice(1).every(v => v === '—' || v === '-' || v === '--' || v === '' || (!isNaN(parseFloat(v)) && Math.abs(parseFloat(v)) <= 1.5)));
  const maxByCol = [];
  if (scoreLike) for (let j = 1; j < ncol; j++) {
    let best = -Infinity;
    rows.forEach(r => { if (/baseline/i.test(r[0])) return; const v = parseFloat(r[j]); if (!isNaN(v) && v > best) best = v; });
    maxByCol[j] = best;
  }
  const longCells = rows.some(r => r.some(v => String(v).length > 70));
  const pt = longCells ? 10 : rows.length > 9 ? 11 : rows.length > 6 ? 12 : 13;
  const firstW = ncol <= 3 ? 1.5 : Math.min(3.6, Math.max(2.4, CONTENT_W * 0.28));
  const otherW = (CONTENT_W - firstW) / (ncol - 1);
  const colW = [firstW, ...Array(ncol - 1).fill(otherW)];
  const head = headers.map(h => ({ text: h, options: { bold: true, color: C.white, fill: { color: C.ink2 }, fontFace: FONT_B, fontSize: pt, align: 'center', valign: 'middle' } }));
  const body = rows.map((r, i) => r.map((v, j) => {
    const isSection = r.slice(1).every(x => !x || x === '') && j === 0;
    const bold = isSection || (scoreLike && j > 0 && !isNaN(parseFloat(v)) && parseFloat(v) === maxByCol[j] && !/baseline/i.test(r[0]));
    return { text: v, options: { bold, italic: /baseline/i.test(r[0]) || isSection, color: bold && j > 0 ? C.blue : C.text, fill: { color: i % 2 ? C.panel : C.white }, fontFace: FONT_B, fontSize: pt, align: j === 0 ? 'left' : 'center', valign: 'middle' } };
  }));
  const hasNotes = d.bullets && d.bullets.length;
  const bottom = (d.takeaway ? 6.0 : 6.85) - (hasNotes ? 0.55 : 0);
  const rowH = Math.min(0.42, (bottom - 1.5) / (rows.length + 1));
  s.addTable([head, ...body], { x: M, y: 1.5, w: CONTENT_W, colW, rowH, border: { type: 'solid', color: C.line, pt: 0.5 }, margin: 0.04 });
  const tableEnd = 1.5 + Math.max(rowH, pt * 1.35 / 72 + 0.1) * (rows.length + 1);
  if (hasNotes) s.addText(d.bullets.map(clean).join('   ·   '), { x: M, y: tableEnd + 0.08, w: CONTENT_W, h: 0.5, fontFace: FONT_B, fontSize: 10.5, color: C.muted, valign: 'top', isTextBox: true, margin: 0 });
  takeaway(s, d.takeaway, Math.max(6.18, tableEnd + (hasNotes ? 0.62 : 0.15)));
};

L.chart = (s, d, n) => {
  frame(s, n); title(s, d.title);
  const ch = d.chart;
  const many = ch.categories.length > 6;
  const data = ch.series.map(se => ({ name: se.name, labels: ch.categories, values: se.values }));
  const type = ch.type === 'line' ? pres.ChartType.line : pres.ChartType.bar;
  const bottom = d.takeaway ? 6.0 : 6.85;
  const cw = 8.1;
  s.addChart(type, data, {
    x: M, y: 1.5, w: cw, h: bottom - 1.5,
    barDir: many ? 'bar' : 'col', barGapWidthPct: 60,
    chartColors: SERIES.slice(0, ch.series.length),
    showValue: true, dataLabelPosition: ch.type === 'line' ? 't' : 'outEnd', dataLabelFontSize: 9, dataLabelColor: C.text, dataLabelFormatCode: '0.000',
    showLegend: ch.series.length > 1, legendPos: 'b', legendFontSize: 10, legendColor: C.text,
    catAxisLabelFontSize: 10, catAxisLabelColor: C.text, valAxisLabelFontSize: 9, valAxisLabelColor: C.muted,
    valAxisMinVal: typeof ch.y_min === 'number' ? ch.y_min : undefined, valAxisMaxVal: typeof ch.y_max === 'number' ? ch.y_max : undefined,
    valGridLine: { color: 'E5E7EB', size: 0.5 }, catGridLine: { style: 'none' },
    showValAxisTitle: !!ch.y_label, valAxisTitle: ch.y_label || '', valAxisTitleFontSize: 10, valAxisTitleColor: C.muted,
    lineSize: 2, lineDataSymbolSize: 7,
    catAxisOrientation: many ? 'maxMin' : 'minMax',
  });
  bulletRows(s, d.bullets, M + cw + 0.35, 1.6, W - M - (M + cw + 0.35), bottom - 1.6, { startPt: 14, minPt: 11, numbered: false });
  takeaway(s, d.takeaway);
};

const PROMPT_TEXT = [
  'You are classifying a software requirement.',
  'Decide whether it is a FUNCTIONAL requirement (FR) -- something the system must DO -- or a NON-FUNCTIONAL requirement (NFR) -- a quality, constraint or property such as performance, security or usability.',
  'Answer with exactly one word: "FR" or "NFR".',
  '',
  '<few-shot conditions only>',
  'Examples:',
  'Requirement: """<exemplar>"""        Answer: FR',
  '... k class-balanced exemplars, carved out before the evaluation frames',
  '',
  'Now classify this one:',
  'Requirement:',
  '"""<the requirement under test>"""',
  'Answer:',
];

function drawArchitecture(s, y0, hTot) {
  const box = (x, y, w, h, head, lines, style) => {
    const isEnc = style === 'enc', isLlm = style === 'llm';
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w, h, rectRadius: 0.06,
      fill: { color: isEnc ? C.blueTint : isLlm ? C.goldTint : C.panel },
      line: { color: isEnc ? C.blue : isLlm ? C.gold : C.line, width: isEnc || isLlm ? 1.5 : 0.75, dashType: isLlm ? 'dash' : 'solid' },
    });
    s.addText([{ text: head, options: { bold: true, fontSize: 11, color: C.text, breakLine: true } }, ...lines.map((t, i) => ({ text: t, options: { fontSize: 9.5, color: C.muted, breakLine: i < lines.length - 1 } }))],
      { x: x + 0.06, y, w: w - 0.12, h, fontFace: FONT_B, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
  };
  const arrow = (x1, y1, x2, y2, color, dashed) => s.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001, line: { color, width: 1.25, dashType: dashed ? 'dash' : 'solid', endArrowType: 'triangle' }, flipV: y2 < y1, flipH: x2 < x1 });
  const bw = 1.75, bh = 1.05, midY = y0 + 1.35;
  const xs = [M, M + 2.0, M + 4.0, M + 6.1, M + 8.4, M + 10.35];
  box(xs[0], midY - 1.15, bw, 1.0, 'PROMISE_exp', ['969 → 968', '47 projects'], 'src');
  box(xs[0], midY + 0.15, bw, 1.0, 'SecReq', ['510 → 444', '3 specifications'], 'src');
  box(xs[1], midY - 0.55, bw, 1.1, 'Unified corpus', ['1,412 requirements', '50 project groups', '67 duplicates dropped'], 'src');
  box(xs[2], midY - 0.55, bw, 1.1, 'Frozen splits', ['14 families, 107 folds', 'seed 42', 'SHA-256-pinned ids'], 'src');
  box(xs[3], midY - 1.3, 2.05, bh, 'Encoder arm', ['BERT, RoBERTa ± weighting', 're-fitted per regime'], 'enc');
  box(xs[3], midY + 0.25, 2.05, bh, 'Prompted arm', ['8 LLMs, 3 tiers', 'zero- and few-shot, never fitted'], 'llm');
  box(xs[4], midY - 0.7, bw, 1.4, 'Strict scoring', ['identical test items', 'unparseable = wrong', '76,115 predictions', 'gate: 81 of 87 cells'], 'src');
  box(xs[5], midY - 0.7, bw + 0.2, 1.4, 'Analysis', ['macro-F1 + bootstrap CI', '260 paired McNemar', 'Holm & BH, α = 0.05', 'cost, N* = C0 / Δc'], 'src');
  arrow(xs[0] + bw, midY - 0.65, xs[1], midY - 0.2, C.muted);
  arrow(xs[0] + bw, midY + 0.65, xs[1], midY + 0.2, C.muted);
  arrow(xs[1] + bw, midY, xs[2], midY, C.muted);
  arrow(xs[2] + bw, midY - 0.1, xs[3], midY - 0.78, C.blue);
  arrow(xs[2] + bw, midY + 0.1, xs[3], midY + 0.78, C.gold, true);
  arrow(xs[3] + 2.05, midY - 0.78, xs[4], midY - 0.3, C.blue);
  arrow(xs[3] + 2.05, midY + 0.78, xs[4], midY + 0.3, C.gold, true);
  arrow(xs[4] + bw, midY, xs[5], midY, C.muted);
  // regime band
  const by = y0 + hTot - 0.62;
  s.addShape(pres.ShapeType.roundRect, { x: M, y: by, w: CONTENT_W, h: 0.58, fill: { color: C.panel }, line: { color: C.panel }, rectRadius: 0.06 });
  s.addText('REGIME', { x: M + 0.2, y: by, w: 1.2, h: 0.58, fontFace: FONT_B, fontSize: 10, bold: true, color: C.muted, valign: 'middle', isTextBox: true, margin: 0 });
  const regimes = [['in-domain', 'stratified 5-fold, one corpus'], ['cross-project', 'unseen project groups + LOPO'], ['cross-dataset', 'train PROMISE_exp ↔ test SecReq']];
  regimes.forEach((r, i) => {
    const rx = M + 1.6 + i * 3.6;
    s.addText([{ text: r[0], options: { bold: true, fontSize: 11, color: C.text, breakLine: true } }, { text: r[1], options: { fontSize: 9, color: C.muted } }], { x: rx, y: by, w: 3.0, h: 0.58, fontFace: FONT_B, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    if (i < 2) s.addShape(pres.ShapeType.rightArrow, { x: rx + 3.05, y: by + 0.19, w: 0.5, h: 0.2, fill: { color: 'B0B7C3' }, line: { color: 'B0B7C3' } });
  });
  s.addText('increasing distribution shift →', { x: W - M - 3.2, y: by - 0.32, w: 3.2, h: 0.3, fontFace: FONT_B, fontSize: 9, italic: true, color: C.muted, align: 'right', isTextBox: true, margin: 0 });
}

L.figure = (s, d, n) => {
  frame(s, n); title(s, d.title);
  const bottom = d.takeaway ? 6.0 : 6.85;
  if (d.figure === 'architecture') {
    drawArchitecture(s, 1.45, 3.7);
    const y = 5.35;
    if (d.bullets && d.bullets.length) bulletRows(s, d.bullets.slice(0, d.takeaway ? 2 : 3), M, y, CONTENT_W, (d.takeaway ? 6.08 : 6.9) - y, { startPt: 12.5, minPt: 11, numbered: false });
    takeaway(s, d.takeaway, 6.2);
    return;
  }
  if (d.figure === 'prompt') {
    const pw = 7.4, ph = Math.min(bottom - 1.5, 4.2);
    s.addShape(pres.ShapeType.roundRect, { x: M, y: 1.5, w: pw, h: ph, fill: { color: '1E1E1E' }, line: { color: '1E1E1E' }, rectRadius: 0.08 });
    s.addText(PROMPT_TEXT.map((t, i) => ({ text: t, options: { breakLine: i < PROMPT_TEXT.length - 1, color: /^<|^\.\.\./.test(t) ? '9CA3AF' : t.startsWith('Answer') || t.startsWith('Now') ? 'FFD166' : 'E5E7EB', italic: /^<|^\.\.\./.test(t) } })),
      { x: M + 0.25, y: 1.65, w: pw - 0.5, h: ph - 0.3, fontFace: 'Courier New', fontSize: 11.5, valign: 'top', isTextBox: true, margin: 0, lineSpacingMultiple: 1.15 });
    s.addText('Fig. 2 of the paper — the terse and verbose phrasings vary only the instruction block; the one-word answer contract is identical.', { x: M, y: 1.5 + ph + 0.15, w: pw, h: 0.5, fontFace: FONT_B, fontSize: 11, italic: true, color: C.muted, isTextBox: true, margin: 0 });
    bulletRows(s, d.bullets, M + pw + 0.4, 1.6, W - M - (M + pw + 0.4), bottom - 1.6, { startPt: 14, minPt: 11, numbered: false });
    takeaway(s, d.takeaway);
    return;
  }
  const img = path.join(FIGS, d.figure + '.png');
  const fw = 7.4, fh = bottom - 1.5;
  s.addShape(pres.ShapeType.roundRect, { x: M, y: 1.45, w: fw + 0.2, h: fh + 0.1, fill: { color: C.white }, line: { color: C.line, width: 0.75 }, rectRadius: 0.08, shadow: shadow() });
  s.addImage({ path: img, x: M + 0.1, y: 1.5, w: fw, h: fh, sizing: { type: 'contain', w: fw, h: fh } });
  bulletRows(s, d.bullets, M + fw + 0.6, 1.6, W - M - (M + fw + 0.6), bottom - 1.6, { startPt: 14, minPt: 11, numbered: false });
  takeaway(s, d.takeaway);
};

L.flow = (s, d, n) => {
  frame(s, n); title(s, d.title);
  const steps = (d.flow || []).slice(0, 7);
  const k = steps.length, gap = 0.28;
  const cw = (CONTENT_W - gap * (k - 1)) / k;
  const top = 1.75, limit = d.takeaway ? 5.95 : 6.7;
  const dPt = k > 5 ? 11 : 12.5;
  const maxLines = Math.max(...steps.map(st => estLines(clean(st.detail), cw - 0.28, dPt)));
  const bottom = Math.min(limit, top + 1.6 + maxLines * lineH(dPt) + 0.45);
  steps.forEach((st, i) => {
    const x = M + i * (cw + gap);
    s.addShape(pres.ShapeType.roundRect, { x, y: top + 0.35, w: cw, h: bottom - top - 0.35, fill: { color: C.panel }, line: { color: C.panel }, rectRadius: 0.1 });
    s.addShape(pres.ShapeType.ellipse, { x: x + cw / 2 - 0.3, y: top, w: 0.6, h: 0.6, fill: { color: C.blue }, line: { color: C.white, width: 2 } });
    s.addText(String(i + 1), { x: x + cw / 2 - 0.3, y: top, w: 0.6, h: 0.6, fontFace: FONT_B, fontSize: 16, bold: true, color: C.white, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText(clean(st.step), { x: x + 0.12, y: top + 0.75, w: cw - 0.24, h: 0.8, fontFace: FONT_H, fontSize: k > 5 ? 13 : 15, bold: true, color: C.text, align: 'center', valign: 'middle', isTextBox: true, margin: 0 });
    s.addText(clean(st.detail), { x: x + 0.14, y: top + 1.6, w: cw - 0.28, h: bottom - top - 1.75, fontFace: FONT_B, fontSize: dPt, color: C.text, align: 'left', valign: 'top', isTextBox: true, margin: 0 });
    if (i < k - 1) s.addShape(pres.ShapeType.rightArrow, { x: x + cw + 0.03, y: top + 0.4 + (bottom - top - 0.35) / 2 - 0.12, w: gap - 0.06, h: 0.24, fill: { color: 'B0B7C3' }, line: { color: 'B0B7C3' } });
  });
  takeaway(s, d.takeaway, Math.min(6.18, bottom + 0.35));
};

L.comparison = (s, d, n) => {
  frame(s, n); title(s, d.title);
  const top = 1.55, bottom = d.takeaway ? 6.0 : 6.85, gap = 0.3;
  const cw = (CONTENT_W - gap) / 2;
  const panels = [
    { x: M, ...d.comparison.left, color: C.blue, tint: C.blueTint },
    { x: M + cw + gap, ...d.comparison.right, color: C.gold, tint: C.goldTint },
  ];
  const measured = panels.map(p => measureRows((p.items || []).map(clean).filter(Boolean), cw - 0.55, bottom - top - 1.15, { numbered: false, startPt: 15, minPt: 11 }));
  const panelH = Math.min(bottom - top, Math.max(2.6, 1.15 + Math.max(...measured.map(m => m.total)) + 0.4));
  panels.forEach(p => {
    s.addShape(pres.ShapeType.roundRect, { x: p.x, y: top, w: cw, h: panelH, fill: { color: p.tint }, line: { color: p.tint }, rectRadius: 0.12 });
    s.addText(p.heading, { x: p.x + 0.3, y: top + 0.2, w: cw - 0.6, h: 0.6, fontFace: FONT_H, fontSize: 19, bold: true, color: p.color === C.gold ? '9A6700' : C.blue, valign: 'middle', isTextBox: true, margin: 0 });
    bulletRows(s, p.items, p.x + 0.3, top + 0.95, cw - 0.55, bottom - top - 1.15, { color: p.color, numbered: false, startPt: 15, minPt: 11 });
  });
  takeaway(s, d.takeaway, Math.min(6.18, top + panelH + 0.35));
};

// ---------------------------------------------------------------- build
deck.slides.forEach((d, i) => {
  const s = pres.addSlide();
  const fn = L[d.layout] || L.bullets;
  try { fn(s, d, i + 1); } catch (e) { console.error(`slide ${i + 1} [${d.id}] (${d.layout}) failed:`, e.message); throw e; }
  if (WITH_NOTES && d.notes_ar) s.addNotes(d.notes_ar);
});

pres.writeFile({ fileName: outPath }).then(f => console.log('wrote', f, 'slides:', deck.slides.length, 'notes:', WITH_NOTES));
