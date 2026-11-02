"""Build data/doda.json from the DODa semantic categories in data/raw/doda/*.csv.

usage: python3 scripts/build_doda.py

DODa (https://github.com/darija-open-dataset/dataset, CC BY-NC 4.0) lists each word under up to four
Latin spellings and one Arabic spelling. This picks the spelling people write most (by the corpus
counts in data/raw/spelling_counts.json), rewrites it in the site's letters and drops words the site
already teaches. data/raw/doda_notes.json holds hand fixes, keyed by the DODa first spelling:
{"drop": [...], "fix": {"n1": {"lat": ..., "ar": ..., "en": ...}}}.
"""
import csv
import json
import re
import sys
from pathlib import Path

from spelling import canon, key, load, split, vowels

ROOT = Path(__file__).resolve().parent.parent
# DODa file -> page module. Plants fold into nature; names and numbers have no page here.
MODULES = {
    "family": "family", "humanbody": "body", "health": "health", "clothes": "clothes", "food": "food",
    "animals": "nature", "plants": "nature", "environment": "nature", "colors": "colors", "places": "places",
    "professions": "work", "economy": "work", "education": "school", "art": "culture", "sport": "culture",
    "religion": "culture", "emotions": "feelings",
}


def site(t):
    """A DODa spelling in the site's letters: 9 q, 5 kh, 8 h, sh ch, one u, no hamza digit."""
    t = t.strip().lower().replace("sh", "ch").replace("9", "q").replace("5", "kh").replace("8", "h").replace("2", "")
    t = re.sub(r"([aeiu])\1+", r"\1", t.replace("aa", "a"))
    return vowels(t)


def pick(variants, counts):
    """The variant written most often; the first when none is counted."""
    return max(variants, key=lambda v: (sum(counts.get(s, 0) for s in {site(v), site(v).replace("e", "")}), -variants.index(v)))


def ar_ok(s):
    return bool(s) and re.fullmatch(r"[ء-يٱ-ۓڭپڤ ً-ْ]+", s) is not None


def main():
    notes = json.loads((ROOT / "data/raw/doda_notes.json").read_text(encoding="utf-8")) if (ROOT / "data/raw/doda_notes.json").exists() else {}
    drop, fix = set(notes.get("drop", [])), notes.get("fix", {})
    counts = json.loads((ROOT / "data/raw/spelling_counts.json").read_text())
    spelling = load()
    have = set()
    for f in ("nouns", "words", "prepositions"):
        d = json.loads((ROOT / f"data/{f}.json").read_text(encoding="utf-8"))
        for x in d[next(iter(d))]:
            for l in ([x["lat"]] if isinstance(x["lat"], str) else x["lat"]):
                have.add(key(split(l.lower())[1]))
    for v in json.loads((ROOT / "data/verbs.json").read_text(encoding="utf-8"))["verbs"]:
        have.add(key(split(v["lat"].lower())[1]))
    out, seen_id, seen_en = [], set(), set()
    for name, mod in MODULES.items():
        with open(ROOT / f"data/raw/doda/{name}.csv", encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                first = r["n1"].strip()
                variants = [v.strip() for k, v in r.items() if k.startswith("n") and v and v.strip()]
                en, ar_ = r["eng"].strip().lower(), r["darija_ar"].strip()
                if first in drop or not variants or not en or " " in first and len(first.split()) > 3:
                    continue
                lat = canon(site(pick(variants, counts)), spelling)
                e = {"lat": lat, "ar": ar_, "en": en}
                e.update(fix.get(first, {}))
                if not ar_ok(e["ar"].replace("ـ", "")) or not re.fullmatch(r"[a-z0-9' -]+", e["lat"]):
                    continue
                k = key(split(e["lat"])[1]) if " " not in e["lat"] else e["lat"]
                if k in have or (mod, e["en"]) in seen_en:
                    continue
                wid = re.sub(r"[^a-z0-9]+", "-", e["lat"]).strip("-")
                if wid in seen_id:
                    continue
                seen_id.add(wid), seen_en.add((mod, e["en"])), have.add(k)
                out.append({"id": wid, "topic": mod, **e, "src": f"DODa {name}"})
    body = json.dumps({"words": out}, ensure_ascii=False, separators=(",", ":")).replace('},{"id"', '},\n{"id"').replace('{"words":[', '{"words":[\n')
    (ROOT / "data/doda.json").write_text(body + "\n", encoding="utf-8")
    from collections import Counter
    print(len(out), "words", dict(Counter(w["topic"] for w in out)))


if __name__ == "__main__":
    sys.exit(main())
