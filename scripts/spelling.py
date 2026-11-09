"""Canonical arabizi spellings: one spelling per word, everywhere on the site (docs/spelling.md).

    python3 scripts/spelling.py --doda DIR [--atlaset DIR]   recount the corpora -> data/raw/spelling_counts.json
    python3 scripts/spelling.py                               counts -> data/spelling.json

Letters are fixed rules: ch for ش (what most Moroccans write), q not 9, kh not 5, u not o or ou
(French loanwords listed under "keep" in data/raw/spelling.json keep o). Everything else, mainly schwa (e) and doubled
letters, is a count: spellings that differ only there are one word, and the one native writers use
most wins when it has at least MIN hits and RATIO times the runner-up. Otherwise the one that
writes the most schwa wins among those close to the top. data/raw/spelling.json also holds hand-made
choices ("force") and look-alikes that are different words ("distinct"). A pronoun table is chosen as
a whole (table_force), so all its forms are written the same way.
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
NOUN_KEEP = ("ghda",)  # the noun lunch; ghda as tomorrow is ghedda
WORD = re.compile(r"[A-Za-z0-9'-]+")
SUN = ("ch", "t", "d", "r", "z", "s", "n", "l", "j")  # the article copies these (SUN in build_nouns.py, in arabizi); l- before any other letter
GLUED = 3  # an article stem needs this many hyphenated uses before a glued lbare7 is rewritten to it
# Atlaset rows written by people (no translated, model-written or Wikipedia-style sets), by dataset_source prefix
ATLASET = ("atlasia/Social_Media_Darija_DS", "atlasia/facebook_darija_dataset", "MTCD", "MAC Corpus", "common-crawl",
           "bourbouh/moroccan-darija-youtube-subtitles", "darija_youtube_subtitles")


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
    """'l-khdma' -> ('l-', 'khdma'); 'z-zenqa' -> ('z-', 'zenqa'); other tokens have no article.
    A wrong sun letter is still an article (l-dar, s-chems) so canon() can correct it."""
    m = re.fullmatch(r"([a-z0-9]{1,2})-(.+)", tok)
    if m and (m[1] == "l" or m[2].startswith(m[1]) or (m[1] == "s" and m[2].startswith("ch"))):
        return m[1] + "-", m[2]
    return "", tok


def article(stem):
    """The article before a stem: its own letter if that is a sun letter (d-dar, ch-chems), else l-."""
    return next((a + "-" for a in SUN if stem.startswith(a)), "l-")


def article_stems(strings):
    """Stems the site writes with the article, with how often: l-bare7 -> bare7."""
    c = Counter()
    for s in strings:
        for t in WORD.findall(s.lower()):
            a, stem = split(t)
            if a and a == article(stem):
                c[stem] += 1
    return c


def glued(tokens, stems, skip):
    """token -> token with the hyphen, for the article written glued to a known stem: lbare7 -> l-bare7,
    jjay -> j-jay (a doubled sun letter). A token that is itself a stem (lila, l7em) or a verb form is a word."""
    out = {}
    for t in tokens:
        if t in stems or t in skip or "-" in t or t != t.lower():
            continue
        for a in SUN:
            rest = t[len(a):]
            if t.startswith(a) and (a == "l" or rest.startswith(a)) and stems[rest] >= GLUED and rest not in skip:
                out[t] = f"{a}-{rest}"
    return dict(sorted(out.items()))


def atlaset_latin(directory):
    """Latin-script rows of the Atlaset parquet shards: a real source, 6+ Latin letters, and Arabic letters under a quarter of the letters."""
    import pyarrow.parquet as pq  # only needed here, so the site scripts don't depend on it
    for f in sorted(glob.glob(f"{directory}/*.parquet")):
        for b in pq.ParquetFile(f).iter_batches(columns=["dataset_source", "text"]):
            for src, text in zip(b.column(0).to_pylist(), b.column(1).to_pylist()):
                lat, ar = len(re.findall(r"[A-Za-z]", text)), len(re.findall(r"[\u0600-\u06FF]", text))
                if src.startswith(ATLASET) and lat >= 6 and 3 * ar < lat:
                    yield " ".join(text.split())


def count_corpora(doda, atlaset):
    c = Counter()
    files = [f"{doda}/sentences/sentences.csv", *sorted(glob.glob(f"{doda}/ongoing/*.csv")), f"{doda}/x-tra/shorts.csv"]
    for f in files:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            c.update(site(t) for t in WORD.findall((r.get("darija") or "").lower()))
    if atlaset:
        for text in atlaset_latin(atlaset):
            c.update(site(t) for t in WORD.findall(text.lower()))
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
    for w in json.loads((ROOT / "data/questions.json").read_text())["words"]:
        yield from (s["lat"].replace("{", "").replace("}", "") for s in w["s"])
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


def paradigms():
    """Every pronoun table as written, before canon(): [headword or None, ...7 forms]."""
    from build_nouns import possessives
    from build_verbs import lat
    from build_prepositions import clean_lat
    for p in json.loads((ROOT / "data/raw/prepositions.json").read_text())["prepositions"]:
        prons = p.get("pronouns") or {}
        for forms, head in ((prons.get("lat"), clean_lat(p["lat"])), (prons.get("altLat"), None)):
            if forms and all(forms) and not any(" " in clean_lat(f) for f in forms):
                yield [head if head and " " not in head else None, *map(clean_lat, forms)]
    for n in json.loads((ROOT / "data/raw/nouns.json").read_text())["nouns"]:
        if n["poss"] == "suffix":
            yield [lat(n["lat"]), *possessives(n)[0]]


def table_spellings(table):
    """The uniform ways to write one table: with or without schwa, doubled letters and -ek for you."""
    head, forms = table[0], table[1:]

    def write(w, schwa, double):
        w = w if schwa else w.replace("e", "")
        return w if double else w[0] + re.sub(r"(.)\1+", r"\1", w[1:])

    for schwa in (True, False):
        for double in (True, False):
            for ek in (True, False):
                new = [write(f, schwa, double) for f in forms]
                new[1] = write(forms[1].removesuffix("ek"), schwa, double) + ("ek" if ek else "k") if forms[1].endswith("ek") else new[1]
                yield [write(head, schwa, double) if head else None, *new]


def table_force(c, skip, ours):
    """One spelling per pronoun table: as written, unless another way has clearly more hits on the forms it changes.
    As everywhere, a word only loses its last vowel if the site already writes it that way (mn, 3nd)."""
    force = defaultdict(list)
    for table in paradigms():
        best, top = table, 0
        for t in table_spellings(table):
            changes = [(a, b) for a, b in zip(table, t) if a != b]
            old, new = sum(c.get(a, 0) for a, _ in changes), sum(c.get(b, 0) for _, b in changes)
            if any(a in skip or b in skip for a, b in changes) or (t[0] and not re.search("[aeiu]", t[0]) and t[0] not in ours):
                continue
            if new >= MIN and new >= RATIO * old and new - old > top:
                best, top = t, new - old
        for a, b in zip(table, best):
            if a and a not in skip:
                force[b] += [a] if a != b else []
    return force


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
    tables = table_force(c, skip, ours)
    for by, force in (("table", tables), ("manual", manual["force"])):
        for win, alts in force.items():
            counts = {s: stem_count(c, s) for s in [win, *alts]}
            for w in list(words):
                if win in words[w]["counts"] or any(a in words[w]["counts"] for a in alts):
                    counts = {**words.pop(w)["counts"], **counts}
            words[win] = {"by": by, "counts": dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))}
    texts = list(site_text(raw=True))
    toks = {t for s in texts for t in WORD.findall(s)}
    return {"_doc": "generated by scripts/spelling.py; see docs/spelling.md", "keep": manual["keep"], "tokens": manual["tokens"],
            "glued": glued(toks, article_stems(texts), skip), "words": words}


def table(spelling):
    """variant stem -> canonical stem."""
    return {v: w for w, e in spelling["words"].items() for v in e["counts"] if v != w}


def canon(text, spelling, keep=()):
    """Rewrite each word of an arabizi string to its canonical spelling. Words in keep stay as they are."""
    tab, keep = table(spelling), set(keep) | set(spelling["keep"])

    def fix(m):
        tok = spelling.get("glued", {}).get(m[0], m[0])  # lbare7 -> l-bare7
        if tok in spelling["tokens"]:
            return spelling["tokens"][tok]
        art, stem = split(tok.lower())
        if tok != tok.lower() or tok in keep:  # names (Thomas), book letters (meT3am)
            return tok
        new = stem if stem in keep else tab.get(stem) or tab.get(vowels(stem), vowels(stem))  # loanwords keep their letters, not a wrong article
        right = article(new) if art[:-1] in SUN else art  # d-dar, ch-chems, l- otherwise
        return tok if (new, right) == (stem, art) else right + new
    return WORD.sub(fix, text)


def clean_ar(text):
    """Arabic script conventions (docs/spelling.md): no diacritics, and f, l, b joined to the next word
    (ف الدار -> فالدار, ل الليل -> لليل)."""
    out, particle = [], ""
    for w in re.sub("[\u064b-\u0652]", "", text).split(" "):
        if particle:
            if particle == "ل" and w.startswith("الل"):
                w = w[2:]
            elif particle == "ل" and w.startswith("ال"):
                w = w[1:]
            w, particle = particle + w, ""
        if w in ("ف", "ل", "ب"):
            particle = w
        else:
            out.append(w)
    return " ".join(out + ([particle] if particle else []))


def canon_fields(x, spelling, keys=("lat",), keep=()):
    """canon() on every string under the given keys (and in lists under them), in place."""
    if isinstance(x, list):
        for v in x:
            canon_fields(v, spelling, keys, keep)
    elif isinstance(x, dict):
        for k, v in x.items():
            if k in keys and isinstance(v, str):
                x[k] = canon(v, spelling, keep)
            elif k in keys and isinstance(v, list) and all(isinstance(i, str) or i is None for i in v):
                x[k] = [canon(i, spelling, keep) if i else i for i in v]
            else:
                canon_fields(v, spelling, keys, keep)
    return x


def prompt_words(n=120):
    """The n most used words that the example writers have spelled another way."""
    words = load()["words"]
    c = Counter(vowels(split(t)[1]) for s in site_text(raw=True) for t in WORD.findall(s.lower()))
    slipped = {w: sum(c[v] for v in e["counts"] if v != w) for w, e in words.items()}
    return sorted((w for w in words if slipped[w]), key=lambda w: -(c[w] + slipped[w]))[:n]


def load():
    return json.loads(OUT.read_text()) if OUT.exists() else {"keep": [], "tokens": {}, "words": {}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--doda", help="clone of github.com/darija-open-dataset/dataset")
    ap.add_argument("--atlaset", help="folder with the parquet shards of atlasia/Atlaset (needs pyarrow)")
    a = ap.parse_args()
    if a.doda:
        COUNTS.write_text(json.dumps(count_corpora(a.doda, a.atlaset), ensure_ascii=False, separators=(",", ":")) + "\n")
    out = build(json.loads(COUNTS.read_text()))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(out['words'])} words -> data/spelling.json")


if __name__ == "__main__":
    main()
