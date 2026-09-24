"""The API tier after Groq retired Llama 3.3 70B (16 August 2026).

Run:  python3 tests/test_hosted_models.py

Everything here executes the notebooks' own code, lifted by AST, so it cannot
drift from what Kaggle runs. No key, no network and no GPU is needed.
"""
import ast, sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbcode import notebook_source

HARNESSES = ["stage3-llm-harnes", "stage3b-subtype-harness"]
PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  PASS  {name}")
    else:    FAIL += 1; print(f"  FAIL  {name}  {detail}")


def lift(nbname, funcs, names):
    """Execute only the named top-level defs and assignments of a notebook."""
    src = "".join(l for l in notebook_source(nbname).splitlines(keepends=True)
                  if not l.startswith(("!", "%")))
    keep = []
    for node in ast.parse(src).body:
        if isinstance(node, ast.FunctionDef) and node.name in funcs:
            keep.append(node)
        elif isinstance(node, ast.Assign):
            if {t.id for t in node.targets if isinstance(t, ast.Name)} & names:
                keep.append(node)
    ns = {"np": np, "pd": pd}
    exec(compile(ast.fix_missing_locations(ast.Module(body=keep, type_ignores=[])),
                 "<lifted>", "exec"), ns)
    return ns


FUNCS = {"price_override_for", "hosted_tag", "report_retired_api_models"}
NAMES = {"CONFIG", "PROBE_RAN", "RETIRED_API_MODELS", "HOSTED"}
NS = {nb: lift(nb, FUNCS, NAMES) for nb in HARNESSES}


# =============================================================================
print("\n== 1. the two harnesses cannot disagree about the API tier ==")
# Stage 3 and Stage 3b probe independently. If their provider blocks ever
# diverge, the main table and the sub-type tables report different hosted
# models and the paper contradicts itself.
def block(src, start, end):
    i = src.index(start); return src[i:src.index(end, i)]

SRC = {nb: notebook_source(nb) for nb in HARNESSES}
for label, start, end in [
        ("price_overrides",  '    "price_overrides": {', '    "estimated_output_multiplier"'),
        ("hosted_providers", '    "hosted_providers": {', '    # ====================================================================='),
        ("price_override_for", 'def price_override_for(', 'def make_client('),
        ("discovery pricing", '                base_in = min(', '            for mid, p_in, p_out in attempts:'),
        ("retired-model report", 'def report_retired_api_models(', 'def hosted_call(')]:
    a, b = (block(SRC[nb], start, end) for nb in HARNESSES)
    check(f"{label} is byte-identical in both harnesses", a == b,
          f"{len(a)} vs {len(b)} chars")

for nb in HARNESSES:
    cands = NS[nb]["CONFIG"]["hosted_providers"]["groq"]["candidates"]
    check(f"{nb}: groq candidate order is pinned",
          [m for m, _, _ in cands] == ["qwen/qwen3.8-27b", "qwen/qwen3.6-27b",
                                       "openai/gpt-oss-120b", "openai/gpt-oss-20b"],
          str([m for m, _, _ in cands]))

# =============================================================================
print("\n== 2. the retired Groq models are gone from the candidate lists ==")
for nb in HARNESSES:
    prov = NS[nb]["CONFIG"]["hosted_providers"]
    named = {m for p in prov.values() for m, _, _ in p["candidates"]}
    for dead in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"):
        check(f"{nb}: {dead} is not probed any more", dead not in named)
    # ...but their published rates stay on record, because the committed rows
    # were priced with them and the write-up has to be able to cite them.
    for dead, rate in (("llama-3.3-70b-versatile", (0.59, 0.79)),
                       ("llama-3.1-8b-instant", (0.05, 0.08))):
        check(f"{nb}: {dead} keeps its historical rate on record",
              NS[nb]["CONFIG"]["price_overrides"].get(dead) == rate)

# =============================================================================
print("\n== 3. one price per model: the two tables cannot contradict ==")
# Every declared candidate's price appears twice - in "candidates" and in
# "price_overrides". A mismatch would price a model differently depending on
# whether the probe reached it by name or by discovery.
for nb in HARNESSES:
    cfg = NS[nb]["CONFIG"]
    pof = NS[nb]["price_override_for"]
    for prov, spec in cfg["hosted_providers"].items():
        for mid, p_in, p_out in spec["candidates"]:
            ov = pof(mid)
            if ov is None:
                continue
            check(f"{nb}: {mid} priced the same in both tables",
                  (float(ov[0]), float(ov[1])) == (float(p_in), float(p_out)),
                  f"candidates={p_in}/{p_out}  overrides={ov[0]}/{ov[1]}")

# =============================================================================
print("\n== 4. price_override_for resolves either spelling of an id ==")
pof = NS["stage3-llm-harnes"]["price_override_for"]
check("full id resolves",            pof("qwen/qwen3.8-27b") == (0.80, 4.00))
check("short id resolves",           pof("qwen3.8-27b") == (0.80, 4.00))
check("gemini's flat id resolves",   pof("gemini-3.1-flash-lite") == (0.25, 1.50))
check("a prefixed gemini id resolves",
      pof("models/gemini-3.1-flash-lite") == (0.25, 1.50))
check("an unknown model has no override", pof("acme/never-heard-of-it") is None)

# No two keys may collapse to the same short name: the fallback would then have
# to choose, and a wrong rate on RQ3's cost axis is worse than no rate at all.
for nb in HARNESSES:
    ov = NS[nb]["CONFIG"]["price_overrides"]
    shorts = [k.split("/")[-1].replace(":free", "") for k in ov]
    dupes = sorted({s for s in shorts if shorts.count(s) > 1})
    check(f"{nb}: no two override keys share a short name", not dupes, str(dupes))

# ...and if a future edit introduces one at different rates, the lookup must
# decline rather than guess.
import logging as _logging
_ns = NS["stage3-llm-harnes"]
_saved = dict(_ns["CONFIG"]["price_overrides"])
try:
    _ns["CONFIG"]["price_overrides"] = {"a/clash-7b": (1.0, 2.0),
                                        "b/clash-7b": (3.0, 4.0)}
    _ns.setdefault("log", _logging.getLogger("test"))
    check("an ambiguous short name is declined, not guessed",
          pof("c/clash-7b") is None)
    _ns["CONFIG"]["price_overrides"] = {"a/same-7b": (1.0, 2.0),
                                        "b/same-7b": (1.0, 2.0)}
    check("...but agreeing duplicates still resolve",
          pof("c/same-7b") == (1.0, 2.0))
finally:
    _ns["CONFIG"]["price_overrides"] = _saved
check("the real table is restored after the ambiguity test",
      pof("qwen/qwen3.8-27b") == (0.80, 4.00))
check("gpt-oss-20b resolves to the published rate",
      pof("openai/gpt-oss-20b") == (0.075, 0.30))
# The two Groq Qwen tiers differ by one character; a sloppy match would
# silently price 3.8 at 3.6's rate.
check("qwen3.6 and qwen3.8 do not collide",
      pof("qwen/qwen3.6-27b") == (0.60, 3.00) and pof("qwen/qwen3.8-27b") == (0.80, 4.00))

# =============================================================================
print("\n== 5. a ':free' route is priced exactly, not by estimate ==")
# The rule lives in probe_hosted's discovery branch. Re-running the probe needs
# a live key, so the check is on the source: ":free" must be tested BEFORE the
# override table, or a paid model of the same short name could price it.
for nb in HARNESSES:
    seg = block(SRC[nb], '                base_in = min(',
                '            for mid, p_in, p_out in attempts:')
    i_free = seg.find('endswith(":free")')
    i_ov = seg.find("price_override_for(f)")
    i_est = seg.find("ESTIMATED_PRICES.add(f)")
    check(f"{nb}: ':free' is handled", i_free > 0)
    check(f"{nb}: ':free' is tested before the override table", 0 < i_free < i_ov)
    check(f"{nb}: ':free' never reaches the estimate branch", 0 < i_free < i_est)
    check(f"{nb}: a free route is priced 0.0/0.0", "(f, 0.0, 0.0)" in seg)

# =============================================================================
print("\n== 6. a model retired mid-study is announced, not swallowed ==")
STORE = pd.DataFrame({
    "model_tag":  (["groq-llama-3.3-70b-versatile"] * 870 +
                   ["gemini-3.1-flash-lite"] * 180 +
                   ["qwen2.5-7b-instruct"] * 6856),
    "model_type": (["open_hosted"] * 870 + ["commercial"] * 180 +
                   ["open_local"] * 6856)})

for nb in HARNESSES:
    ns = NS[nb]
    rep, tag = ns["report_retired_api_models"], ns["hosted_tag"]

    # (a) the probe ran and found a substitute: the retired model is named.
    ns["PROBE_RAN"] = True
    ns["RETIRED_API_MODELS"] = []
    ns["HOSTED"] = {"groq":   {"model": "qwen/qwen3.8-27b"},
                    "gemini": {"model": "gemini-3.1-flash-lite"}}
    gone = rep(STORE)
    check(f"{nb}: the retired Groq model is reported",
          gone == ["groq-llama-3.3-70b-versatile"], str(gone))
    check(f"{nb}: a model still in play is NOT reported",
          "gemini-3.1-flash-lite" not in gone)
    check(f"{nb}: a local model is never called an API model",
          "qwen2.5-7b-instruct" not in gone)
    check(f"{nb}: the row count is carried into the manifest",
          ns["RETIRED_API_MODELS"] == [{"model_tag": "groq-llama-3.3-70b-versatile",
                                        "committed_rows": 870}],
          str(ns["RETIRED_API_MODELS"]))

    # (b) the substitute's tag is new, so its rows never overwrite the old ones.
    check(f"{nb}: the substitute gets its own model_tag",
          tag("groq", "qwen/qwen3.8-27b") == "groq-qwen3.8-27b",
          tag("groq", "qwen/qwen3.8-27b"))
    check(f"{nb}: an OpenRouter free route tags without ':free'",
          tag("openrouter", "nex-agi/nex-n2.5-mini:free") == "openrouter-nex-n2.5-mini",
          tag("openrouter", "nex-agi/nex-n2.5-mini:free"))

    # (c) no probe (run_hosted=False, or no key at all): silence, not a false
    #     alarm that every API model has been retired.
    ns["PROBE_RAN"] = False
    ns["RETIRED_API_MODELS"] = []
    ns["HOSTED"] = {}
    check(f"{nb}: an unprobed run reports nothing", rep(STORE) == [])
    check(f"{nb}: ...and writes nothing to the manifest",
          ns["RETIRED_API_MODELS"] == [])

    # (d) a fresh run with no seeded store has nothing to compare against.
    ns["PROBE_RAN"] = True
    check(f"{nb}: an empty store reports nothing",
          rep(pd.DataFrame(columns=["model_tag", "model_type"])) == [])

# =============================================================================
print("\n== 7. the run says so when no store was attached ==")
for nb in HARNESSES:
    seg = block(SRC[nb], "def seed_store_from_inputs(", "def load_store(")
    check(f"{nb}: the empty-input case is unmissable",
          "NO PREVIOUS PREDICTION STORE FOUND" in seg)
    store = "predictions_llm" if nb == "stage3-llm-harnes" else "predictions_subtype"
    check(f"{nb}: it names the file the seeder globs for",
          f"{store}.parquet" in seg.split("NO PREVIOUS PREDICTION STORE")[1])
    check(f"{nb}: the named file is the one the glob really uses",
          f'glob.glob("/kaggle/input/**/{store}.parquet"' in seg)
    check(f"{nb}: it offers both the notebook and the dataset route",
          "Your Work -> Notebooks" in seg and "Add Input -> Datasets" in seg)
    check(f"{nb}: it warns that a retired model cannot be rebuilt",
          "retired" in seg)

# =============================================================================
print("\n== 8. the manifest records what changed under us ==")
for nb in HARNESSES:
    check(f"{nb}: manifest carries the retired-model list",
          '"api_models_retired_since_committed_run": RETIRED_API_MODELS,' in SRC[nb])
    check(f"{nb}: manifest still carries the estimated-price list",
          '"models_with_estimated_prices": sorted(ESTIMATED_PRICES),' in SRC[nb])

print(f"\n{'=' * 60}\n  {PASS} passed, {FAIL} failed\n{'=' * 60}")
sys.exit(1 if FAIL else 0)
