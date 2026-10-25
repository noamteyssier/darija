"""Example sentences for each verb, written by Claude Sonnet through headless Claude Code.

usage: python3 scripts/build_examples.py [--full] [--level 1] [--ids kteb,shaf] [--limit 20] [--group 20] [--redo]

Default: each verb gets three slots, one per tense, each with a different person picked from the
verb id, so reruns pick the same slots (data/raw/examples/sonnet.json).
--full: each verb gets every slot, 3 tenses x 8 persons x positive/negative = 48
(data/raw/examples/sonnet-full.json). Without --level or --ids it takes levels 1 and 2.
A verb in the full file is built from it; the rest from the short file.

The prompt hands the model the conjugated form from data/verbs.json (negated with ma ... sh for
negative slots): it only writes the sentence around it, and any sentence that lost the form is dropped.

Runs `claude -p` on the logged-in plan, one call per group of verbs, saving after each call; verbs
already in the file are skipped, so a stopped run picks up where it left off. Every run rebuilds
data/examples/<id>.json, one file per verb, from both raw files.
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
RAW_FULL = ROOT / "data/raw/examples/sonnet-full.json"
OUT = ROOT / "data/examples"
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
- A slot marked negative needs a negative statement built on the negated form you are given
  (ma ktebtsh, ma ghadish nkteb), kept exactly as given. The English must be negative too.
- The English must match the slot's tense and person: "we" for 7na, "you (f.)" for nti, and so on.
- Natural, everyday Darija, 3 to 8 words. Not Modern Standard Arabic, not French spelling.
- It must contain the verb form you are given exactly as given, as its own word, in both scripts.
  Do not add object endings or prefixes to it (no ktebtha, no wkteb); put objects in separate words.
- The pronoun word itself is optional, as in speech.
- Use common words a beginner could learn next. Vary the sentences for one verb: no two alike, whatever the slot.
- The English is a plain translation of what the Darija says.
Before answering, reread each sentence word by word against these rules and both scripts.

Examples of the style:
past, ana, ktebt / كتبت: "ktebt bra l khuya" / "كتبت برا لخويا" / "I wrote a letter to my brother."
pres, huma, kayshufu / كيشوفو: "kayshufu t-tilfaza kul lila" / "كيشوفو التلفازة كل ليلة" / "They watch TV every night."
fut, ana, ghadi nmshi / غادي نمشي: "ghadi nmshi l s-suq ghedda" / "غادي نمشي للسوق غدا" / "I'm going to go to the market tomorrow."
past negative, huwa, ma shafsh / ما شافش: "ma shafsh khuya l-yum" / "ما شافش خويا اليوم" / "He didn't see my brother today."
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


def negate(lat, ar, t):
    """ma + form + sh; the future's ghadi takes the sh (same rule as negate in assets/verbs-data.js)."""
    if t == "fut":
        return "ma " + lat.replace("ghadi ", "ghadish ", 1), "ما " + ar.replace("غادي ", "غاديش ", 1)
    return "ma " + lat + "sh", "ما " + ar + "ش"


def forms(v, t):
    if t != "fut":
        return v[t]
    return {
        "lat": ["ghadi " + x.removeprefix("ka") for x in v["pres"]["lat"]],
        "ar": ["غادي " + x[1:] for x in v["pres"]["ar"]],
    }


def slot(i, v, t, p, neg=False):
    f = forms(v, t)
    lat, ar = negate(f["lat"][p], f["ar"][p], t) if neg else (f["lat"][p], f["ar"][p])
    return {"slot": i, "tense": t, "p": p, "neg": neg, "lat": lat, "ar": ar}


def slots(v, full=False):
    if full:
        return [slot(i, v, t, p, bool(n)) for i, (t, p, n) in enumerate(
            (t, p, n) for t in TENSES for p in range(8) for n in (0, 1))]
    persons = random.Random(v["id"]).sample(range(8), 3)
    return [slot(i, v, t, p) for i, (t, p) in enumerate(zip(TENSES, persons))]


def describe(v, full=False):
    s = f"Verb: {v['lat']} / {v['ar']}, 'to {v['en']}'"
    if v.get("prep"):
        s += f", used with {v['prep']}"
    if v.get("note"):
        s += f". Note: {v['note']}"
    s += "\n\nSlots:\n" + "\n".join(
        f"{x['slot']}: {TENSE_EN[x['tense']]}{' NEGATIVE' if x['neg'] else ''}, {PRON[x['p']]} ({PRON_EN[x['p']]}), form {x['lat']} / {x['ar']}"
        for x in slots(v, full))
    return s


def tokens(s):
    return " " + " ".join(re.sub(r"[.,!?؟،«»\"“”:;]", " ", s.lower()).split()) + " "


def bad_script(sent):
    """Latin outside the arabizi alphabet, or Latin inside the Arabic."""
    return not re.fullmatch(r"[a-z37' ?!.,-]+", sent["lat"].lower()) or re.search(r"[A-Za-z]", sent["ar"])


def has_form(sent, slot):
    return f" {slot['lat']} " in tokens(sent["lat"]) and f" {slot['ar']} " in tokens(sent["ar"])


def read(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def ask(group, full=False):
    RAW.parent.mkdir(parents=True, exist_ok=True)
    prompt = "Write one sentence per slot for each verb below. Return every verb by its id.\n\n" + \
        "\n\n".join(f"id: {v['id']}\n{describe(v, full)}" for v in group)
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
    raw, raw_full = read(RAW, {}), read(RAW_FULL, {})
    out, dropped = {}, []
    for v in verbs:
        full = v["id"] in raw_full
        by_slot = {x["slot"]: x for x in (raw_full if full else raw).get(v["id"], [])}
        keep = []
        for s in slots(v, full):
            r = by_slot.get(s["slot"])
            if not r:
                continue
            what = f"{v['id']}/{s['tense']}{'/neg' if s['neg'] else ''}/{PRON[s['p']]}"
            if not has_form(r, s):
                dropped.append(f"{what}: {r['lat']} (needs {s['lat']})")
                continue
            if bad_script(r):
                dropped.append(f"{what}: {r['lat']} / {r['ar']} (mixed script)")
                continue
            keep.append({"t": s["tense"], "p": s["p"], **({"neg": True} if s["neg"] else {}),
                         "lat": r["lat"], "ar": r["ar"], "en": r["en"]})
        if keep:
            out[v["id"]] = keep
    OUT.mkdir(exist_ok=True)
    for f in OUT.glob("*.json"):
        f.unlink()
    for k, keep in out.items():
        (OUT / f"{k}.json").write_text(json.dumps(keep, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{sum(map(len, out.values()))} sentences for {len(out)} verbs -> data/examples/")
    for d in dropped:
        print("  dropped:", d)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--level", help="only verbs at this level (1, 2, 3)")
    ap.add_argument("--ids", help="only these verb ids, comma separated")
    ap.add_argument("--limit", type=int, help="stop after this many verbs")
    ap.add_argument("--full", action="store_true", help="every tense x person x polarity (levels 1-2 unless --level/--ids)")
    ap.add_argument("--group", type=int, help="verbs per claude call (default 20, or 3 with --full)")
    ap.add_argument("--redo", action="store_true", help="rewrite verbs that already have sentences")
    a = ap.parse_args()

    every = json.loads((ROOT / "data/verbs.json").read_text())["verbs"]
    verbs = every
    if a.level:
        verbs = [v for v in verbs if str(v["level"]) == a.level]
    elif a.full and not a.ids:
        verbs = [v for v in verbs if v["level"] in (1, 2)]
    if a.ids:
        want = set(a.ids.split(","))
        verbs = [v for v in verbs if v["id"] in want]
    path = RAW_FULL if a.full else RAW
    raw = read(path, {})
    todo = [v for v in verbs if a.redo or v["id"] not in raw][:a.limit]
    size = a.group or (3 if a.full else 20)
    for i in range(0, len(todo), size):
        group = todo[i:i + size]
        got = ask(group, a.full)
        raw.update({k: x for k, x in got.items() if k in {v["id"] for v in group}})
        write(path, raw)
        missing = [v["id"] for v in group if v["id"] not in got]
        print(f"{min(i + size, len(todo))}/{len(todo)} verbs" + (f", missing: {', '.join(missing)}" if missing else ""))
    build(every)


if __name__ == "__main__":
    main()
