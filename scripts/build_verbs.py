"""Build data/verbs.json from the Peace Corps glossary TSV plus hand-curated notes.

usage: python3 scripts/build_verbs.py

Inputs
  data/raw/pc_glossary.tsv   extracted by extract_glossary.py (book transcription, I-present, I-past)
  data/raw/verb_notes.json   hand edits: overrides, glosses, exclusions
  data/raw/verb_tags.json    levels (1 starter, 2 everyday, 3 the rest) and topics

Each verb gets stems; assets/js/conjugate.js glues person affixes onto them.
  past.c  stem before consonant endings (-t, -ti, -na, -tu)
  past.l  huwa form
  past.v  stem before vowel endings (-at, -u / -aw)
  pres.c  present stem with no ending
  pres.v  present stem before -i / -u
Latin stems are arabizi with schwa (e) placed; Arabic stems are plain letters.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOWELS = set("aiu")
LAT = {"š": "sh", "x": "kh", "ġ": "gh", "ع": "3", "н": "7", "ṭ": "t", "ṣ": "s", "ḍ": "d", "ẓ": "z", "ḥ": "7"}
AR = {
    "b": "ب", "t": "ت", "j": "ج", "н": "ح", "x": "خ", "d": "د", "r": "ر", "z": "ز", "s": "س",
    "š": "ش", "ṣ": "ص", "ḍ": "ض", "ṭ": "ط", "ẓ": "ظ", "ع": "ع", "ġ": "غ", "f": "ف", "q": "ق",
    "k": "ك", "g": "ڭ", "l": "ل", "m": "م", "n": "ن", "h": "ه", "w": "و", "y": "ي",
    "a": "ا", "i": "ي", "u": "و", "v": "ڤ", "p": "پ", "'": "ء",
}
PREPS = {"mn", "عla", "mعa", "b", "f", "l", "fih", "fiha"}


# ---------- syllabification ----------
# The book leaves out schwa except between identical letters (нllel). We keep the book's e
# as a fixed vowel and place the rest: in each consonant run the consonant before a vowel is
# its onset, a geminate split across syllables gets e before it (wlla -> wella), and anything
# left is paired right to left, CC -> CeC, keeping a final geminate whole (šdd -> šedd).

def segs(pc):
    return list(unicodedata.normalize("NFC", pc))


def is_v(c):
    return c in VOWELS or c == "e"


def pair_run(run):
    out = []
    while run:
        if len(run) >= 2 and run[-1] == run[-2]:
            gem, run = run[-2:], run[:-2]
            if run:
                out = [run[-1], "e"] + gem + out
                run = run[:-1]
            else:
                out = gem + out
        elif len(run) >= 2:
            out = [run[-2], "e", run[-1]] + out
            run = run[:-2]
        else:
            out = run + out
            run = []
    return out


def syllabify(s):
    out, i, n = [], 0, len(s)
    while i < n:
        if is_v(s[i]):
            out.append(s[i])
            i += 1
            continue
        j = i
        while j < n and not is_v(s[j]):
            j += 1
        run = s[i:j]
        if j < n:  # run before a vowel
            head, onset = run[:-1], run[-1]
            if head and head[-1] == onset:  # geminate across the syllable edge
                out += head[:-1] + ["e"] * bool(head[:-1]) + [head[-1]]
            else:
                out += head if len(head) <= 1 else pair_run(head)
            out.append(onset)
        else:  # word-final run
            if i > 0 and (len(run) == 1 or (len(run) == 2 and run[0] == run[1])):
                out += run
            else:
                out += pair_run(run)
        i = j
    return out


def c_form(pc):
    """Stem for huwa / before -t: ktb -> kteb, sqqṭ -> seqqeṭ, trjm -> terjem, šdd -> šedd."""
    return "".join(syllabify(segs(pc)))


def v_form(cform):
    """Stem before a vowel ending: the final-syllable schwa drops and the rest re-pairs.
    kteb -> ketb, terjem -> terjm, seqqeṭ -> seqqṭ, jaweb -> jawb; нellel keeps its e."""
    m = re.match(r"^(.*[^aieu])e([^aieu])$", cform)
    if not m or m.group(1)[-1] == m.group(2):
        return cform
    rest, last = m.group(1), m.group(2)
    if not any(is_v(c) for c in rest):
        rest = "".join(pair_run(list(rest)))
    return rest + last


def lat(pc_syll):
    """Book letters -> arabizi. A real s+h, k+h or g+h gets an apostrophe so it can't be
    read as the digraphs sh / kh / gh (s'her, stay up late)."""
    s = unicodedata.normalize("NFC", pc_syll)
    out = []
    for i, c in enumerate(s):
        out.append(LAT.get(c, c))
        if c in "skg" and s[i + 1:i + 2] == "h":
            out.append("'")
    return "".join(out)


def ar(pc):
    """Book transcription -> Arabic letters. Geminates (and uw / iy) are written once;
    the book's e between identical letters marks two letters (нllel -> حلل)."""
    out, last = [], None
    for c in unicodedata.normalize("NFC", pc):
        if c in "e-":
            last = None
            continue
        letter = AR.get(c)
        if letter is None:
            raise ValueError(f"no arabic letter for {c!r} in {pc!r}")
        if letter != last:
            out.append(letter)
        last = letter
    return "".join(out)


# ---------- classification ----------

def classify(lemma, pres, past):
    """Return (kind, stems) from the book's lemma, I-present stem and I-past form."""
    if pres.startswith("a") and not lemma.startswith("a"):
        return "hamza", None
    if past.endswith("it") and lemma.endswith("a"):
        return "final", None
    if past.endswith("it"):
        return "doubled", None
    lv = [c for c in lemma if c in VOWELS]
    if lv == ["a"] and past.endswith("t") and "a" not in past and len(segs(lemma)) == 3 and lemma[-2] == "a":
        return "hollow", None
    if past == lemma + "t":
        if lemma.startswith("w"):
            return "initial", None
        return "sound", None
    return None, None


def syl(pc):
    return "".join(syllabify(segs(pc)))


def stems(kind, lemma, pres, past):
    """Latin (book letters, schwa placed) and Arabic stems:
    c = before consonant endings, l = huwa, v = before vowel endings (past);
    c = no ending, v = before -i / -u (present)."""
    if kind in ("sound", "initial"):
        lc, pc_ = c_form(lemma), c_form(pres)
        L = {"c": lc, "l": lc, "v": v_form(lc), "pc": pc_, "pv": v_form(pc_)}
        A = {"c": ar(lemma), "l": ar(lemma), "v": ar(lemma), "pc": ar(pres), "pv": ar(pres)}
    elif kind == "hollow":
        short = past[:-1]  # šft -> šf
        L = {"c": short, "l": lemma, "v": lemma, "pc": syl(pres), "pv": syl(pres)}
        A = {"c": ar(short), "l": ar(lemma), "v": ar(lemma), "pc": ar(pres), "pv": ar(pres)}
    elif kind in ("final", "hamza"):
        cs = past[:-1]  # bghit -> bghi
        pv = re.sub(r"[aiu]([^aiue])$", r"\1", pres) if kind == "hamza" else pres  # akul -> akl
        L = {"c": syl(cs), "l": syl(lemma), "v": syl(lemma), "pc": syl(pres), "pv": syl(pv + "u")[:-1]}
        A = {"c": ar(cs), "l": ar(lemma), "v": ar(lemma), "pc": ar(pv), "pv": ar(pv)}
    elif kind == "doubled":
        cs = past[:-1]  # šddit -> šddi
        L = {"c": syl(cs), "l": c_form(lemma), "v": c_form(lemma), "pc": c_form(pres), "pv": c_form(pres)}
        A = {"c": ar(cs), "l": ar(lemma), "v": ar(lemma), "pc": ar(pres), "pv": ar(pres)}
    else:
        raise ValueError(kind)
    return L, A


def glue(stem, suf):
    """Arabic writes a geminate once across stem + ending (كن + نا = كنا)."""
    return stem + suf[1:] if stem.endswith(suf[0]) else stem + suf


PREF_L = ["kan", "kat", "kat", "kay", "kat", "kan", "kat", "kay"]
PREF_A = ["كن", "كت", "كت", "كي", "كت", "كن", "كت", "كي"]


def paradigm(kind, L, A):
    """All 8 persons (ana, nta, nti, huwa, hiya, 7na, ntuma, huma) for past and present."""
    c, l, v = L["c"], L["l"], L["v"]
    weak = kind in ("final", "hamza")
    na = c[:-1] + "e" + c[-1] + "na" if kind == "hollow" and len(c) == 2 else c + "na"  # šf -> šefna
    past_l = [c + "t", c + "ti", c + "ti", l, v + ("t" if weak else "at"), na, c + "tu", v + ("w" if weak else "u")]
    hiya_a = A["l"] + "ت" if kind in ("hollow", "final", "hamza") else A["v"] + "ات"
    past_a = [glue(A["c"], "ت"), glue(A["c"], "تي"), glue(A["c"], "تي"), A["l"], hiya_a, glue(A["c"], "نا"), glue(A["c"], "تو"),
              A["l"] + "و" if kind in ("hollow", "final", "hamza") else A["v"] + "و"]
    pc_, pv = L["pc"], L["pv"]
    if kind == "final":
        nti = "y" if pc_.endswith("a") else ""
        sl = [pc_, pc_, pc_ + nti, pc_, pc_, pc_ + "w", pc_ + "w", pc_ + "w"]
        sa = [A["pc"]] * 3 + [A["pc"]] * 2 + [A["pc"] + "و"] * 3
        sa[2] = A["pc"] + ("ي" if nti else "")
    else:
        sl = [pc_, pc_, pv + "i", pc_, pc_, pv + "u", pv + "u", pv + "u"]
        sa = [A["pc"], A["pc"], A["pv"] + "ي", A["pc"], A["pc"], A["pv"] + "و", A["pv"] + "و", A["pv"] + "و"]
    pres_l = [PREF_L[i] + sl[i] for i in range(8)]
    pres_a = [PREF_A[i] + sa[i] for i in range(8)]
    return {
        "past": {"lat": [lat(x) for x in past_l], "ar": past_a},
        "pres": {"lat": [lat(x) for x in pres_l], "ar": pres_a},
    }


# ---------- glosses ----------

def ar_phrase(s):
    return " ".join(ar(w) if w != "l-bal" else "البال" for w in s.split())


def gloss(en):
    en = re.sub(r"\s+", " ", en).strip()
    en = re.sub(r"\bsth\b", "something", en)
    en = re.sub(r"\bsb\b", "someone", en)
    m = re.match(r"^(.*?), (to )?(be|make|get|pay|take|have|give|become|do|fall)( a| an)?$", en)
    if m:
        art = (m.group(4) or "")
        return f"{m.group(3)}{art} {m.group(1)}"
    return en


def split_lemma(pc):
    """'xaf (mn)' -> ('xaf', 'mn', None); 'qddm ṭalab' -> ('qddm', None, 'ṭalab')."""
    pc = pc.strip()
    m = re.match(r"^(\S+)\s*\((.+)\)$", pc)
    if m:
        return m.group(1), m.group(2), None
    parts = pc.split()
    if len(parts) == 1:
        return parts[0], None, None
    if len(parts) == 2 and all(p in PREPS for p in parts[1].split("/")):
        return parts[0], parts[1], None
    return parts[0], None, " ".join(parts[1:])


def main():
    notes = json.loads((ROOT / "data/raw/verb_notes.json").read_text())
    rows = []
    with open(ROOT / "data/raw/pc_glossary.tsv") as f:
        next(f)
        for line in f:
            page, en, pc, pres1, past1 = line.rstrip("\n").split("\t")
            rows.append((int(page), en, unicodedata.normalize("NFC", pc), unicodedata.normalize("NFC", pres1), unicodedata.normalize("NFC", past1)))

    verbs, by_key, skipped = [], {}, []
    for page, en, pc, pres1, past1 in rows:
        lemma, prep, obj = split_lemma(pc)
        if not pres1.startswith("kan-"):
            skipped.append((pc, "impersonal or special"))
            continue
        pres = pres1[4:].split()[0]
        past_parts = past1.split()
        past = past_parts[0] if past_parts else ""
        if obj and len(pres1.split()) > 1 and pres1.split()[1:] != obj.split():
            skipped.append((pc, "object changes with person"))
            continue
        key = (lemma, pres, past, obj)
        if key in by_key:
            v = by_key[key]
            g = gloss(en)
            if g not in v["en"]:
                v["en"].append(g)
            if prep and prep not in v["preps"]:
                v["preps"].append(prep)
            continue
        kind, _ = classify(lemma, pres, past)
        v = {"raw": pc, "pc": lemma, "pres1": pres, "past1": past, "obj": obj, "preps": [prep] if prep else [],
             "en": [gloss(en)], "page": page, "kind": kind}
        by_key[key] = v
        verbs.append(v)

    over = notes.get("override", {})
    out, unknown, ids = [], [], {}
    for v in verbs:
        o = over.get(f'{v["raw"]}|{v["pres1"]}|{v["past1"]}') or over.get(f'{v["raw"]}|{v["pres1"]}') or over.get(v["raw"], {})
        if o.get("exclude"):
            skipped.append((v["pc"], o.get("why", "excluded")))
            continue
        kind = o.get("kind", v["kind"])
        if kind is None:
            unknown.append(v)
            continue
        lemma = o.get("pc", v["pc"])
        pres1, past1 = o.get("pres1", v["pres1"]), o.get("past1", v["past1"])
        L, A = stems(kind, lemma, pres1, past1)
        if "ar_pc" in o:  # spell the Arabic from another transcription (gal is written قال)
            _, A = stems(kind, *o["ar_pc"])
        forms = paradigm(kind, L, A)
        for t, fs in o.get("forms", {}).items():  # per-form corrections {"pres": {"lat": {"5": "..."}}}
            for script, idx in fs.items():
                for i, f in idx.items():
                    forms[t][script][int(i)] = f
        if v["obj"]:
            ol, oa = (o["obj"]["lat"], o["obj"]["ar"]) if "obj" in o else (lat(v["obj"]), ar_phrase(v["obj"]))
            for t in forms:
                forms[t]["lat"] = [f + " " + ol for f in forms[t]["lat"]]
                forms[t]["ar"] = [f + " " + oa for f in forms[t]["ar"]]
        vid = o.get("id") or lat(L["l"])
        base, n = vid, 2
        while vid in ids:
            vid = f"{base}-{n}"
            n += 1
        ids[vid] = True
        entry = {
            "id": vid,
            "lat": forms["past"]["lat"][3],
            "ar": o.get("ar", forms["past"]["ar"][3]),
            "en": " / ".join(o.get("en", v["en"])),
            "kind": o.get("label", kind),
        }
        if v["preps"]:
            entry["prep"] = " / ".join(lat(p) for p in v["preps"])
        entry.update({"pc": v["raw"], "src": f"PC {v['page']}"})
        for k in ("verify", "note"):
            if k in o:
                entry[k] = o[k]
        entry.update(forms)
        out.append(entry)

    tags = json.loads((ROOT / "data/raw/verb_tags.json").read_text())
    level = {vid: int(k) for k, vids in tags["levels"].items() for vid in vids}
    for e in out:
        e["level"] = level.get(e["id"], 3)
        topics = [t for t, vids in tags["topics"].items() if e["id"] in vids]
        if not topics:
            topics = [t for t, rx in tags["keywords"].items() if re.search(rx, e["en"])][:2] or ["other"]
        e["topics"] = topics

    body = ",\n".join(json.dumps(e, ensure_ascii=False, separators=(",", ":")) for e in out)
    head = json.dumps({"levels": tags["levelNames"], "topics": tags["topicNames"]}, ensure_ascii=False)
    (ROOT / "data/verbs.json").write_text(head[:-1] + ',"verbs":[\n' + body + "\n]}\n")
    print(f"{len(out)} verbs, {len(unknown)} unclassified, {len(skipped)} skipped", file=sys.stderr)
    for v in unknown:
        print("UNCLASSIFIED", v["pc"], v["pres1"], v["past1"], v["en"], file=sys.stderr)


if __name__ == "__main__":
    main()
