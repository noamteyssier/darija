"""Example sentences for each verb, written by Claude Sonnet through headless Claude Code.

usage: python3 scripts/build_examples.py [--level 1] [--ids kteb,shaf] [--limit 20] [--group 20] [--redo]

Each verb gets three slots, one per tense, each with a different person picked from the verb id,
so reruns pick the same slots. The prompt hands the model the conjugated form from data/verbs.json:
it only writes the sentence around it, and any sentence that lost the form is dropped.

Runs `claude -p` on the logged-in plan, one call per group of verbs, saving after each call to
data/raw/examples/sonnet.json; verbs already there are skipped, so a stopped run picks up where it
left off. Every run rebuilds data/examples.json from that file.
"""
import argparse
import json
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/examples/sonnet.json"
MODEL = "claude-sonnet-5-5"  # the bare "sonnet" alias gives an older Sonnet
PRON = ["ana", "nta", "nti", "huwa", "hiya", "7na", "ntuma", "huma"]
PRON_EN = ["I", "you (m.)", "you (f.)", "he", "she", "we", "you (pl.)", "they"]
TENSES = ["past", "pres", "fut"]
TENSE_EN = {"past": "past", "pres": "present (habitual / ongoing)", "fut": "future"}

STYLE = """You write example sentences for learners of Moroccan Arabic (Casablanca / Rabat Darija).

Arabizi spelling, as used on the site: lowercase ASCII only, no accents. 3 = ع, 7 = ح (always:
b7er, 7efla, m7etta), q = ق, gh = غ, kh = خ, sh = ش, 2 is never used, 9 is never used (write q),
ch is never used. Write the schwa as e where it is pronounced (ketbat, l-mektab). Spell words out
in full (daba, not db). The article takes a hyphen and assimilates before sun letters (l-ktab,
d-dar, sh-shems, t-tumubil, r-rbat). The prepositions f, l, b, mn, 3la are separate words before
the noun (f d-dar, l s-suq, b t-tobis, f s-sba7). A noun with a possessive ending takes no article
(khuya, not l-khuya). Possessives as the site spells them: dyali, dyalek, dyalu, dyalha, dyalna,
dyalkum, dyalhum, and the same endings on nouns (khuk, khuha, khukum).

Arabic script: Arabic letters only, no diacritics. The article is always ال; f, l, b join the next
word the way Moroccans write them (فالدار, للسوق, بالطوبيس, لخويا). Future marker غادي.
The two scripts must spell the same words in the same order.

Rules for every sentence:
- Natural, everyday Darija, 3 to 8 words. Not Modern Standard Arabic, not French spelling.
- It must contain the verb form you are given exactly as given, as its own word, in both scripts.
  Do not add object endings or prefixes to it (no ktebtha, no wkteb); put objects in separate words.
- The pronoun word itself is optional, as in speech.
- Use common words a beginner could learn next. Vary the sentences for one verb.
- The English is a plain translation of what the Darija says.
Before answering, reread each sentence word by word against these rules and both scripts.

Examples of the style:
past, ana, ktebt / كتبت: "ktebt bra l khuya" / "كتبت برا لخويا" / "I wrote a letter to my brother."
pres, huma, kayshufu / كيشوفو: "kayshufu t-tilfaza kul lila" / "كيشوفو التلفازة كل ليلة" / "They watch TV every night."
fut, ana, ghadi nmshi / غادي نمشي: "ghadi nmshi l s-suq ghedda" / "غادي نمشي للسوق غدا" / "I'm going to go to the market tomorrow."
"""

SCHEMA = {
    "type": "object",
    "properties": {"verbs": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "sentences": {"type": "array", "items": {
            "type": "object",
            "properties": {"slot": {"type": "integer"}, "lat": {"type": "string"},
                           "ar": {"type": "string"}, "en": {"type": "string"}},
            "required": ["slot", "lat", "ar", "en"], "additionalProperties": False}}},
        "required": ["id", "sentences"], "additionalProperties": False}}},
    "required": ["verbs"], "additionalProperties": False,
}


def slots(v):
    persons = random.Random(v["id"]).sample(range(8), 3)
    out = []
    for i, (t, p) in enumerate(zip(TENSES, persons)):
        f = v[t] if t != "fut" else {
            "lat": ["ghadi " + x.removeprefix("ka") for x in v["pres"]["lat"]],
            "ar": ["غادي " + x[1:] for x in v["pres"]["ar"]],
        }
        out.append({"slot": i, "tense": t, "p": p, "lat": f["lat"][p], "ar": f["ar"][p]})
    return out


def describe(v):
    s = f"Verb: {v['lat']} / {v['ar']}, 'to {v['en']}'"
    if v.get("prep"):
        s += f", used with {v['prep']}"
    if v.get("note"):
        s += f". Note: {v['note']}"
    s += "\n\nSlots:\n" + "\n".join(
        f"{x['slot']}: {TENSE_EN[x['tense']]}, {PRON[x['p']]} ({PRON_EN[x['p']]}), form {x['lat']} / {x['ar']}"
        for x in slots(v))
    return s


def tokens(s):
    return " " + " ".join(re.sub(r"[.,!?؟،«»\"“”:;]", " ", s.lower()).split()) + " "


def bad_script(sent):
    """Latin outside the arabizi alphabet, or Latin inside the Arabic."""
    return not re.fullmatch(r"[a-z0-9' ?!.,-]+", sent["lat"].lower()) or re.search(r"[A-Za-z]", sent["ar"])


def has_form(sent, slot):
    return f" {slot['lat']} " in tokens(sent["lat"]) and f" {slot['ar']} " in tokens(sent["ar"])


def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def ask(group):
    RAW.parent.mkdir(parents=True, exist_ok=True)
    prompt = "Write one sentence per slot for each verb below. Return every verb by its id.\n\n" + \
        "\n\n".join(f"id: {v['id']}\n{describe(v)}" for v in group)
    r = subprocess.run(
        ["claude", "-p", "--model", MODEL, "--effort", "high", "--tools", "", "--no-session-persistence",
         "--system-prompt", STYLE, "--output-format", "json", "--json-schema", json.dumps(SCHEMA), prompt],
        check=False, capture_output=True, text=True, cwd=RAW.parent)
    try:
        out = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"claude failed: {r.stderr.strip() or r.stdout.strip()}")
    if out.get("is_error") or "structured_output" not in out:
        sys.exit(f"claude failed: {out.get('result') or out.get('subtype')}")
    return {x["id"]: x["sentences"] for x in out["structured_output"]["verbs"]}


def build(verbs):
    raw = read(RAW, {})
    out, dropped = {}, []
    for v in verbs:
        by_slot = {x["slot"]: x for x in raw.get(v["id"], [])}
        keep = []
        for s in slots(v):
            r = by_slot.get(s["slot"])
            if not r:
                continue
            if not has_form(r, s):
                dropped.append(f"{v['id']}/{s['tense']}: {r['lat']} (needs {s['lat']})")
                continue
            if bad_script(r):
                dropped.append(f"{v['id']}/{s['tense']}: {r['lat']} / {r['ar']} (mixed script)")
                continue
            keep.append({"t": s["tense"], "p": s["p"], "lat": r["lat"], "ar": r["ar"], "en": r["en"]})
        if keep:
            out[v["id"]] = keep
    write(ROOT / "data/examples.json", out)
    print(f"{sum(map(len, out.values()))} sentences for {len(out)} verbs -> data/examples.json")
    for d in dropped:
        print("  dropped, verb form missing:", d)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--level", help="only verbs at this level (1, 2, 3)")
    ap.add_argument("--ids", help="only these verb ids, comma separated")
    ap.add_argument("--limit", type=int, help="stop after this many verbs")
    ap.add_argument("--group", type=int, default=20, help="verbs per claude call")
    ap.add_argument("--redo", action="store_true", help="rewrite verbs that already have sentences")
    a = ap.parse_args()

    every = json.loads((ROOT / "data/verbs.json").read_text())["verbs"]
    verbs = every
    if a.level:
        verbs = [v for v in verbs if str(v["level"]) == a.level]
    if a.ids:
        want = set(a.ids.split(","))
        verbs = [v for v in verbs if v["id"] in want]
    raw = read(RAW, {})
    todo = [v for v in verbs if a.redo or v["id"] not in raw][:a.limit]
    for i in range(0, len(todo), a.group):
        group = todo[i:i + a.group]
        got = ask(group)
        raw.update({k: x for k, x in got.items() if k in {v["id"] for v in group}})
        write(RAW, raw)
        missing = [v["id"] for v in group if v["id"] not in got]
        print(f"{min(i + a.group, len(todo))}/{len(todo)} verbs" + (f", missing: {', '.join(missing)}" if missing else ""))
    build(every)


if __name__ == "__main__":
    main()
