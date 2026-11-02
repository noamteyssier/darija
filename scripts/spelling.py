"""Canonical arabizi spellings: one spelling per word, everywhere on the site (docs/spelling.md).

    python3 scripts/spelling.py --doda DIR [--atlaset TSV]   recount the corpora -> data/raw/spelling_counts.json
    python3 scripts/spelling.py                               counts -> data/spelling.json

Letters are fixed rules: ch for ش (what most Moroccans write), q not 9, kh not 5, u not o or ou
(French loanwords listed under "keep" in data/raw/spelling.json keep o). Everything else, mainly schwa (e) and doubled
letters, is a count: spellings that differ only there are one word, and the one native writers use
most wins when it has at least MIN hits and RATIO times the runner-up. Otherwise the one that
writes the most schwa wins among those close to the top. data/raw/spelling.json also holds hand-made
choices ("force") and look-alikes that are different words ("distinct").
"""
import argparse
import csv
import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTS = ROOT / "data/raw/spelling_counts.json"
MANUAL = ROOT / "data/raw/spelling.json"
OUT = ROOT / "data/spelling.json"
MIN, RATIO = 20, 1.5
WORD = re.compile(r"[A-Za-z0-9'-]+")


def site(t):
    """Corpus token -> the site's letters."""
    t = t.lower().replace("-", "").replace("sh", "ch").replace("9", "q").replace("5", "kh")
    return vowels(t).replace("ss", "s")  # French ss keeps an s from sounding like z


def vowels(stem):
    """u, never o or ou: kolchi -> kulchi, moudir -> mudir, sowt -> sut."""
    if "o" not in stem:
        return stem
    s = re.sub(r"o+u?|ou", "u", stem)
    return re.sub(r"uw(?=[^aeiuy]|$)", "u", s)


def key(stem):
    """Spellings with the same key are one word: no schwa, no doubled letters. A doubled first
    letter stays (mmi my mother, mi; bba my father, ba), and so does doubling in very short words."""
    s = stem.replace("e", "")
    short = s[0] + re.sub(r"(.)\1+", r"\1", s[1:]) if s else s
    return short if len(short) >= 3 else s


def split(tok):
    """'l-khdma' -> ('l-', 'khdma'); 'z-zenqa' -> ('z-', 'zenqa'); other tokens have no article."""
    m = re.fullmatch(r"([a-z0-9]{1,2})-(.+)", tok)
    if m and (m[1] == "l" or m[2].startswith(m[1])):
        return m[1] + "-", m[2]
    return "", tok


def count_corpora(doda, atlaset):
    c = Counter()
    files = [f"{doda}/sentences/sentences.csv", *sorted(glob.glob(f"{doda}/ongoing/*.csv")), f"{doda}/x-tra/shorts.csv"]
    for f in files:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            c.update(site(t) for t in WORD.findall((r.get("darija") or "").lower()))
    if atlaset:
        for line in open(atlaset, encoding="utf-8"):
            c.update(site(t) for t in WORD.findall(line.split("\t", 1)[-1].lower()))
    return {t: n for t, n in sorted(c.items()) if n >= 3}


def latin(x):
    """Every arabizi string in a data file."""
    if isinstance(x, dict):
        for k, v in x.items():
            if "lat" in k.lower() and isinstance(v, str):
                yield v
            else:
                yield from latin(v)
    elif isinstance(x, list):
        for v in x:
            yield from (v,) if isinstance(v, str) else latin(v)


def site_text(raw=False):
    """The site's arabizi. raw=True adds the inputs as written, before canon(), so rebuilding the map
    from data it has already rewritten gives the same map."""
    for f in sorted((ROOT / "data/examples").glob("*.json")):
        yield from (s["lat"] for s in json.loads(f.read_text()))
    for f in ("words", "prepositions", "nouns"):
        yield from latin(json.loads((ROOT / f"data/{f}.json").read_text()))
    if raw:
        for f in sorted((ROOT / "data/raw/examples").glob("*.json")):
            yield from latin(json.loads(f.read_text()))
        for f in ("words", "prepositions"):
            yield from latin(json.loads((ROOT / f"data/raw/{f}.json").read_text()))


def verb_forms():
    """Conjugated forms keep the spelling build_verbs.py gives them."""
    out = set()
    for v in json.loads((ROOT / "data/verbs.json").read_text())["verbs"]:
        for t in ("past", "pres"):
            for f in v[t]["lat"]:
                out |= {f, f + "ch", f.removeprefix("ka"), *f.split(), *(split(w)[1] for w in f.split())}  # kandenn blli
    return out | {"ghadi", "ghadich"}


def stem_count(c, s):
    return c.get(s, 0) + c.get("l" + s, 0) + (c.get(s[0] + s, 0) if s[0] not in "aeiu" else 0)


def build(c):
    manual = json.loads(MANUAL.read_text())
    skip = verb_forms() | {w for pair in manual["distinct"] for w in pair} | set(manual["keep"])
    ours = Counter(vowels(split(t)[1]) for s in site_text(raw=True) for t in WORD.findall(s.lower()))
    # spellings the site used before canon() rewrote them, so a rebuild keeps their entries
    seen = set(ours) | {v for e in (json.loads(OUT.read_text())["words"] if OUT.exists() else {}).values() for v in e["counts"]}
    groups = defaultdict(set)
    for s in [*c, *seen]:
        groups[key(s)].add(s)
    words = {}
    for k in sorted({key(s) for s in seen}):
        cands = {s: stem_count(c, s) for s in groups[k] if s not in skip}
        cands = {s: n for s, n in cands.items() if n >= 3 or s in seen}
        if len(cands) < 2 or sum(cands.values()) < MIN:
            continue
        top = sorted(cands.items(), key=lambda x: (-x[1], x[0]))
        # no French final e (tajin, not tajine), no stretched vowels (bzaaf), no vowel-less
        # abbreviations (bzf) unless the site already writes the word that way (mn, b3d)
        ok = [x for x in top if not x[0].endswith("e") and not re.search(r"([aeiu])\1", x[0])
              and (re.search(r"[aeiu]", x[0]) or x[0] in ours)]
        if not ok:
            continue
        if ok[0][1] >= MIN and ok[0][1] >= RATIO * (ok[1][1] if len(ok) > 1 else 0):
            win, by = ok[0][0], "corpus"
        else:
            near = [s for s, n in ok if n * RATIO >= ok[0][1]]
            win, by = max(near, key=lambda s: (s.count("e"), cands[s])), "schwa"
        words[win] = {"by": by, "counts": dict(top)}
    for win, alts in manual["force"].items():
        counts = {s: stem_count(c, s) for s in [win, *alts]}
        for w in list(words):
            if win in words[w]["counts"] or any(a in words[w]["counts"] for a in alts):
                counts = {**words.pop(w)["counts"], **counts}
        words[win] = {"by": "manual", "counts": dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))}
    return {"_doc": "generated by scripts/spelling.py; see docs/spelling.md", "keep": manual["keep"], "words": words}


def table(spelling):
    """variant stem -> canonical stem."""
    return {v: w for w, e in spelling["words"].items() for v in e["counts"] if v != w}


def canon(text, spelling, keep=()):
    """Rewrite each word of an arabizi string to its canonical spelling. Words in keep stay as they are."""
    tab, keep = table(spelling), set(keep) | set(spelling["keep"])

    def fix(m):
        tok = m[0]
        art, stem = split(tok.lower())
        if tok != tok.lower() or tok in keep or stem in keep:  # names (Thomas), book letters (meT3am)
            return tok
        new = tab.get(stem) or tab.get(vowels(stem), vowels(stem))
        if new == stem:
            return tok
        if art not in ("", "l-") and not new.startswith(art[:-1]):
            art = "l-"
        return art + new
    return WORD.sub(fix, text)


def canon_fields(x, spelling, keys=("lat",)):
    """canon() on every string under the given keys (and in lists under them), in place."""
    if isinstance(x, list):
        for v in x:
            canon_fields(v, spelling, keys)
    elif isinstance(x, dict):
        for k, v in x.items():
            if k in keys and isinstance(v, str):
                x[k] = canon(v, spelling)
            elif k in keys and isinstance(v, list) and all(isinstance(i, str) or i is None for i in v):
                x[k] = [canon(i, spelling) if i else i for i in v]
            else:
                canon_fields(v, spelling, keys)
    return x


def prompt_words(n=120):
    """The n most used words that the example writers have spelled another way."""
    words = load()["words"]
    c = Counter(vowels(split(t)[1]) for s in site_text(raw=True) for t in WORD.findall(s.lower()))
    slipped = {w: sum(c[v] for v in e["counts"] if v != w) for w, e in words.items()}
    return sorted((w for w in words if slipped[w]), key=lambda w: -(c[w] + slipped[w]))[:n]


def load():
    return json.loads(OUT.read_text()) if OUT.exists() else {"keep": [], "words": {}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doda", help="clone of github.com/darija-open-dataset/dataset")
    ap.add_argument("--atlaset", help="tsv of source<TAB>text, Latin-script rows of atlasia/Atlaset")
    a = ap.parse_args()
    if a.doda:
        COUNTS.write_text(json.dumps(count_corpora(a.doda, a.atlaset), ensure_ascii=False, separators=(",", ":")) + "\n")
    out = build(json.loads(COUNTS.read_text()))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(out['words'])} words -> data/spelling.json")


if __name__ == "__main__":
    main()
