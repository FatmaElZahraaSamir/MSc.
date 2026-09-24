"""Fig. 1 - experimental pipeline, redrawn without text/arrow collisions.

Same content and aspect ratio (2421 x 762 px) as the original image, so it
drops into the same frame in the Word file. Every text block is checked to sit
inside its box with a margin, and the script fails if any does not.
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
})

W_PX, H_PX, DPI = 2421, 762, 384
W, H = W_PX / DPI, H_PX / DPI          # inches: 6.305 x 1.984

INK, BODY = "#222222", "#3a3a3a"
EDGE, BLUE, GOLD = "#444444", "#1f5b8e", "#b5780a"
BAND = "#eeeeee"
T_SIZE, B_SIZE = 7.6, 6.9            # title / body font sizes (pt) at print size

fig = plt.figure(figsize=(W, H), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

boxes = {}
texts = []


def box(name, x, y, w, h, title, lines, edge=EDGE, lw=1.1, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.045",
                       fc="white", ec=edge, lw=lw, ls=ls, zorder=2)
    ax.add_patch(p)
    boxes[name] = (x, y, w, h)
    n = len(lines)
    line_h = 0.118                   # inches between body lines
    block = 0.135 + n * line_h       # title + body lines
    top = y + h / 2 + block / 2
    t = ax.text(x + w / 2, top - 0.06, title, ha="center", va="center", fontsize=T_SIZE,
                fontweight="bold", color=INK, zorder=3)
    texts.append((name, t))
    for k, s in enumerate(lines):
        t = ax.text(x + w / 2, top - 0.06 - 0.135 - k * line_h, s, ha="center", va="center",
                    fontsize=B_SIZE, color=BODY, zorder=3)
        texts.append((name, t))


def arrow(p0, p1, color=EDGE, ls="-", lw=1.0):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7, lw=lw, color=color,
                        ls=ls, shrinkA=0, shrinkB=0, zorder=1)
    ax.add_patch(a)


# ---- layout (inches) --------------------------------------------------------
top_y, bot_y = 1.255, 0.57         # rows for the two stacked columns
row_h = 0.605
full_y, full_h = 0.57, 1.29         # single boxes span both rows

box("promise", 0.04, top_y, 0.84, row_h, "PROMISE_exp", ["969 requirements", "47 projects"])
box("secreq", 0.04, bot_y, 0.84, row_h, "SecReq", ["510 sentences", "3 specifications"])
box("prep", 1.01, full_y, 0.99, full_h, "Data preparation",
    ["normalize text,", "unify label names,", "drop 67 duplicates,", "1,412 rows kept",
     "(968 + 444)"])
box("splits", 2.13, full_y, 0.72, full_h, "Splits", ["drawn once,", "stored,", "never redrawn"])
box("enc", 2.98, top_y, 1.30, row_h, "Fine-tuned encoders",
    ["BERT and RoBERTa,", "each ± class weighting:", "4 configurations"], edge=BLUE, lw=1.7)
box("llm", 2.98, bot_y, 1.30, row_h, "Prompted LLMs",
    ["8 models, one fixed", "instruction, never fitted:", "8 configurations"],
    edge=GOLD, lw=1.5, ls=(0, (3.2, 1.6)))
box("score", 4.41, full_y, 0.90, full_h, "One scoring rule",
    ["identical items,", "unusable reply", "scored as wrong"])
box("analysis", 5.44, full_y, 0.84, full_h, "Analysis",
    ["macro-F1, paired", "tests, cost", "per requirement"])


def right(n, fy=0.5):
    x, y, w, h = boxes[n]
    return (x + w, y + h * fy)


def left(n, fy=0.5):
    x, y, w, h = boxes[n]
    return (x, y + h * fy)


arrow(right("promise"), left("prep", 0.70))
arrow(right("secreq"), left("prep", 0.30))
arrow(right("prep"), left("splits"))
arrow(right("splits", 0.72), left("enc"), color=BLUE)
arrow(right("splits", 0.28), left("llm"), color=GOLD, ls=(0, (3, 1.5)))
arrow(right("enc"), left("score", 0.72), color=BLUE)
arrow(right("llm"), left("score", 0.28), color=GOLD, ls=(0, (3, 1.5)))
arrow(right("score"), left("analysis"))

# ---- "what we vary" band ------------------------------------------------------
band = FancyBboxPatch((0.04, 0.04), W - 0.08, 0.40, boxstyle="round,pad=0,rounding_size=0.03",
                      fc=BAND, ec="none", zorder=0)
ax.add_patch(band)
t = ax.text(0.14, 0.24, "WHAT WE VARY", ha="left", va="center", fontsize=6.6,
            fontweight="bold", color="#8a8a8a")
texts.append(("band", t))
stages = [(1.95, "in-domain", "train and test inside one corpus"),
          (3.55, "cross-project", "test on projects never seen in training"),
          (5.15, "cross-dataset", "train on one corpus, test on the other")]
for cx, name, desc in stages:
    t1 = ax.text(cx, 0.32, name, ha="center", va="center", fontsize=T_SIZE, fontweight="bold",
                 color=INK)
    t2 = ax.text(cx, 0.15, desc, ha="center", va="center", fontsize=6.4, color=BODY)
    texts += [("band", t1), ("band", t2)]
for xa, xb in ((2.62, 2.88), (4.22, 4.48)):
    a = FancyArrowPatch((xa, 0.32), (xb, 0.32), arrowstyle="-|>", mutation_scale=7, lw=1.1,
                        color="#8a8a8a", shrinkA=0, shrinkB=0)
    ax.add_patch(a)

# ---- collision check -----------------------------------------------------------
fig.canvas.draw()
r = fig.canvas.get_renderer()
inv = ax.transData.inverted()
problems = []
band_texts = []
for name, t in texts:
    bb = t.get_window_extent(renderer=r)
    (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
    if name == "band":
        band_texts.append((t.get_text(), x0, x1))
        if x0 < 0.06 or x1 > W - 0.06:
            problems.append(f"band text '{t.get_text()}' leaves the band")
        continue
    bx, by, bw, bh = boxes[name]
    m = 0.035
    if x0 < bx + m or x1 > bx + bw - m or y0 < by + m or y1 > by + bh - m:
        problems.append(f"'{t.get_text()}' ({x0:.3f}-{x1:.3f}) not inside {name} "
                        f"({bx + m:.3f}-{bx + bw - m:.3f})")
band_texts.sort(key=lambda z: z[1])
for (ta, a0, a1), (tb, b0, b1) in zip(band_texts, band_texts[1:]):
    if b0 < a1 + 0.05 and ta != tb and not (abs((a0 + a1) - (b0 + b1)) < 0.05):
        # same-column title/description pairs are centred on each other; others must not touch
        if not any(abs((a0 + a1) / 2 - cx) < 0.02 and abs((b0 + b1) / 2 - cx) < 0.02
                   for cx, _, _ in stages):
            problems.append(f"band texts '{ta}' and '{tb}' too close")
names = list(boxes)
for a in range(len(names)):
    for b in range(a + 1, len(names)):
        ax0, ay0, aw, ah = boxes[names[a]]; bx0, by0, bw, bh = boxes[names[b]]
        if ax0 < bx0 + bw + 0.04 and bx0 < ax0 + aw + 0.04 and ay0 < by0 + bh + 0.04 and by0 < ay0 + ah + 0.04:
            problems.append(f"boxes {names[a]} and {names[b]} overlap or touch")
if problems:
    print("\n".join(problems))
    sys.exit(1)
out = sys.argv[1] if len(sys.argv) > 1 else "../icci2026_word/fig1_pipeline.png"
fig.savefig(out, dpi=DPI)
print("ok", out)
