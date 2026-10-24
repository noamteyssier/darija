"""Build data/nouns.json from data/raw/nouns.json.

usage: python3 scripts/build_nouns.py

The source is written in the Peace Corps letters (š x ġ ع н ṭ ṣ ḍ) with schwa (e) already placed;
this adds arabizi spellings, the definite form, the 7 possessive forms and the dyal forms.
Possessive persons: ana, nta/nti, huwa, hiya, 7na, ntuma, huma.
"""
import json
from pathlib import Path

from build_verbs import ar, lat

ROOT = Path(__file__).resolve().parent.parent
SUN = set("tdrzsšṣḍṭẓnlj")
SUF_C = ["i", "ek", "u", "ha", "na", "kum", "hum"]  # after a consonant
SUF_V = ["ya", "k", "h", "ha", "na", "kum", "hum"]  # after a vowel
AR_C = ["ي", "ك", "و", "ها", "نا", "كم", "هم"]
AR_V = ["يا", "ك", "ه", "ها", "نا", "كم", "هم"]
DYAL_L = ["dyal" + s for s in ["i", "ek", "u", "ha", "na", "kum", "hum"]]
DYAL_A = ["ديال" + s for s in AR_C]


def definite(pc, arabic):
    """l-ktab, d-dar, sh-shems; Arabic always writes ال."""
    first = pc[0]
    la = lat(pc)
    if first in SUN:
        head = lat(first)
        return head + "-" + la, "ال" + arabic
    return "l-" + la, "ال" + arabic


def possessives(n):
    if "possLat" in n:
        return [lat(x) for x in n["possLat"]], n["possAr"]
    pc = n["lat"]
    if pc.endswith("a") and n["g"] == "f":  # magana -> magant-i
        ps = psc = n.get("ps", pc[:-1] + "t")
        psc = n.get("psc", ps)
        stem_ar = ar(n["ps"]) if "ps" in n else n["ar"][:-1] + "ت"
        return [lat(ps + s) if i < 3 else lat(psc + s) for i, s in enumerate(SUF_C)], [stem_ar + s for s in AR_C]
    if pc[-1] in "aiuo":
        return [lat(pc + s) for s in SUF_V], [n["ar"] + (s[1:] if n["ar"][-1] == s[0] else s) for s in AR_V]
    ps, psc = n.get("ps", pc), n.get("psc", n.get("ps", pc))
    stem_ar = ar(ps) if "ps" in n else n["ar"]
    return [lat(ps + s) if i < 3 else lat(psc + s) for i, s in enumerate(SUF_C)], [stem_ar + s for s in AR_C]


def main():
    src = json.loads((ROOT / "data/raw/nouns.json").read_text())
    nouns = []
    for n in src["nouns"]:
        dl, da = definite(n["lat"], n["ar"])
        e = {"id": lat(n["lat"]), "lat": lat(n["lat"]), "ar": n["ar"], "en": n["en"], "g": n["g"],
             "topic": n["topic"], "poss": n["poss"], "def": {"lat": dl, "ar": da}}
        if n.get("pl"):
            pdl, pda = definite(n["pl"], n["plar"])
            e["pl"] = {"lat": lat(n["pl"]), "ar": n["plar"], "def": {"lat": pdl, "ar": pda}}
        if n["poss"] == "suffix":
            pl_, pa = possessives(n)
            e["mine"] = {"lat": pl_, "ar": pa}
        if n["poss"] != "none" and not n.get("nodyal"):  # kin terms only take the ending
            e["dyal"] = {"lat": [dl + " " + d for d in DYAL_L], "ar": [da + " " + d for d in DYAL_A]}
        for k in ("note", "src"):
            if k in n:
                e[k] = n[k]
        if n.get("pl_src") == "author":
            e["plSrc"] = "not in the book"
        nouns.append(e)
    adjs = []
    for a in src["adjectives"]:
        forms = [a["m"], a["f"], a["pl"]]
        e = {"id": lat(a["m"]), "en": a["en"], "lat": [lat(f) for f in forms], "ar": a["ar"],
             "def": {"lat": [definite(f, x)[0] for f, x in zip(forms, a["ar"])],
                     "ar": ["ال" + x for x in a["ar"]]}, "src": a["src"]}
        if a.get("human"):
            e["human"] = True
        adjs.append(e)
    body = {"nouns": nouns, "adjectives": adjs}
    out = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    out = out.replace('},{"id"', '},\n{"id"')
    (ROOT / "data/nouns.json").write_text(out + "\n")
    print(f"{len(nouns)} nouns, {len(adjs)} adjectives")


if __name__ == "__main__":
    main()
