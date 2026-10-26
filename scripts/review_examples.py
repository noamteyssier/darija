"""Review of the Gemini example sentences, by Claude Sonnet through headless Claude Code.

usage: python3 scripts/review_examples.py [--ids kteb,shaf] [--limit 20] [--group 3] [--workers 4] [--src F] [--out F]

Reads data/raw/examples/gemini-full.json and asks the model, per group of verbs, to check every sentence
(same words in both scripts, real everyday Darija, faithful English, required form, sense). Writes
data/raw/examples/gemini-reviewed.json = {verb id: {slot: {"ok": true} | {"ok": false, "why", "lat", "ar", "en"}}}.
A fixed sentence is kept only if it still passes has_form() and bad_script(); otherwise lat/ar/en are
empty, meaning drop. Saves after every call; verbs already in the output are skipped.
"""
import argparse
import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_examples as be  # noqa: E402

ROOT = be.ROOT
SRC = ROOT / "data/raw/examples/gemini-full.json"
OUT = ROOT / "data/raw/examples/gemini-reviewed.json"

SYSTEM = be.STYLE + """
You are now the strict reviewer of example sentences that another model wrote under the rules above.
For every sentence, check:
1. The Latin and Arabic lines say the same words in the same order, word for word. Compare token by
   token (known failure: 'l-ktaf' next to الكتاب).
2. Every word is real, natural, everyday Moroccan Darija: not MSA, not an invented word, not a French
   spelling. The arabizi follows the spelling rules above and the Arabic follows the script rules.
3. The English is a faithful translation of the Darija and matches its tense, person and polarity.
4. The required form appears exactly, as its own word, in both scripts (negated slots: the negated form).
5. Grammar and meaning are sensible; nothing odd, contradictory or unnatural.
Be strict, but do not rewrite acceptable sentences: if all five hold, answer ok. If a sentence fails
and a small fix gives a good sentence that still contains the exact required form in both scripts, give
the corrected lat, ar and en. If it cannot be fixed that way, set lat, ar and en to empty strings
(the sentence is dropped). For ok sentences leave why, lat, ar and en empty. Give why in a few words, naming the actual defect; if you cannot name one, the sentence is ok.
Return a verdict for every slot of every verb, by id and slot number."""

SCHEMA = {
    "type": "object",
    "properties": {"verbs": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "verdicts": {"type": "array", "items": {
            "type": "object",
            "properties": {"slot": {"type": "integer"}, "ok": {"type": "boolean"}, "why": {"type": "string"},
                           "lat": {"type": "string"}, "ar": {"type": "string"}, "en": {"type": "string"}},
            "required": ["slot", "ok", "why", "lat", "ar", "en"], "additionalProperties": False}}},
        "required": ["id", "verdicts"], "additionalProperties": False}}},
    "required": ["verbs"], "additionalProperties": False,
}

lock = threading.Lock()


def block(v, sents):
    by = {x["slot"]: x for x in sents}
    lines = []
    for s in be.slots(v, True):
        x = by.get(s["slot"])
        if x:
            lines.append(f"{s['slot']}: {be.TENSE_EN[s['tense']]}{' NEGATIVE' if s['neg'] else ''}, {be.PRON[s['p']]} "
                         f"({be.PRON_EN[s['p']]}), required form {s['lat']} / {s['ar']}\n"
                         f"   lat: {x['lat']}\n   ar: {x['ar']}\n   en: {x['en']}")
    head = f"id: {v['id']}\nVerb: {v['lat']} / {v['ar']}, 'to {v['en']}'"
    if v.get("prep"):
        head += f", used with {v['prep']}"
    if v.get("note"):
        head += f". Note: {v['note']}"
    return head + "\n\nSentences:\n" + "\n".join(lines)


def ask(group, src):
    prompt = "Review every sentence below. Return every verb by its id.\n\n" + \
        "\n\n".join(block(v, src[v["id"]]) for v in group)
    r = subprocess.run(
        ["claude", "-p", "--model", be.MODEL, "--effort", "high", "--tools", "", "--no-session-persistence",
         "--system-prompt", SYSTEM, "--output-format", "json", "--json-schema", json.dumps(SCHEMA), prompt],
        check=False, capture_output=True, text=True, cwd=OUT.parent)
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None, r.stderr.strip() or r.stdout.strip()
    if out.get("is_error") or "structured_output" not in out:
        return None, out.get("result") or out.get("subtype")
    return {x["id"]: x["verdicts"] for x in out["structured_output"]["verbs"]}, None


def settle(v, sents, verdicts):
    """Verdicts -> {slot: result}; a sentence the model skipped counts as dropped."""
    by, got, res = {x["slot"]: x for x in sents}, {x["slot"]: x for x in verdicts}, {}
    for s in be.slots(v, True):
        i = s["slot"]
        if i not in by:
            continue
        g = got.get(i)
        if g is None:
            res[str(i)] = {"ok": False, "why": "no verdict", "lat": "", "ar": "", "en": ""}
        elif g["ok"] or all(g[k].strip() == by[i][k] for k in ("lat", "ar", "en")):  # unchanged "fix" = fine
            res[str(i)] = {"ok": True}
        else:
            fix = {k: g[k].strip() for k in ("lat", "ar", "en")}
            if not (all(fix.values()) and be.has_form(fix, s) and not be.bad_script(fix)):
                fix = {"lat": "", "ar": "", "en": ""}
            res[str(i)] = {"ok": False, "why": g["why"], **fix}
    return res


def main():
    global OUT
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ids", help="only these verb ids, comma separated")
    ap.add_argument("--limit", type=int, help="stop after this many verbs")
    ap.add_argument("--group", type=int, default=3, help="verbs per claude call (default 3)")
    ap.add_argument("--workers", type=int, default=4, help="concurrent calls (default 4)")
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    OUT = a.out

    src = be.read(a.src, {})
    done = be.read(OUT, {})
    verbs = [v for v in json.loads((ROOT / "data/verbs.json").read_text())["verbs"] if v["id"] in src]
    if a.ids:
        verbs = [v for v in verbs if v["id"] in set(a.ids.split(","))]
    todo = [v for v in verbs if v["id"] not in done][:a.limit]
    groups = [todo[i:i + a.group] for i in range(0, len(todo), a.group)]
    count = [0]

    def run(group):
        got, err = ask(group, src)
        with lock:
            count[0] += 1
            if got is None:
                print(f"call failed ({','.join(v['id'] for v in group)}): {err}", flush=True)
                return
            for v in group:
                if v["id"] in got:
                    done[v["id"]] = settle(v, src[v["id"]], got[v["id"]])
            be.write(OUT, done)
            miss = [v["id"] for v in group if v["id"] not in got]
            print(f"{count[0]}/{len(groups)} calls" + (f", missing: {', '.join(miss)}" if miss else ""), flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(run, groups))


if __name__ == "__main__":
    main()
