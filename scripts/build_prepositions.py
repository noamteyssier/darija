"""Build data/prepositions.json from data/raw/prepositions.json.

usage: python3 scripts/build_prepositions.py

Validates prepositions, pronoun paradigms, verb collocations, and idiomatic expressions
in Moroccan Darija (Casablanca / Rabat).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_verbs import ar, lat

PRONOUN_PERSONS = ["ana", "nta / nti", "huwa", "hiya", "7na", "ntuma", "huma"]


def clean_lat(s):
    """Book letters -> arabizi. Raw entries already in arabizi keep their sh / kh / gh digraphs."""
    if s is None:
        return None
    return re.sub(r"([skg])'h", r"\1h", lat(s))


def blank(example, prep, forms):
    """Replace the preposition token (bare, or fused with a pronoun) by ___, or None if absent."""
    tokens = example.split(" ")
    for i, t in enumerate(tokens):
        core = t.rstrip("?!.,")
        if core in forms or core == prep:
            return " ".join(tokens[:i] + ["___" + t[len(core):]] + tokens[i + 1:])
    return None


def clean_ar(s):
    if s is None:
        return None
    return ar(s)


def main():
    src_file = ROOT / "data/raw/prepositions.json"
    if not src_file.exists():
        print(f"Error: {src_file} does not exist", file=sys.stderr)
        sys.exit(1)

    src = json.loads(src_file.read_text(encoding="utf-8"))

    prepositions = []
    for p in src["prepositions"]:
        entry = {
            "id": p["id"],
            "lat": clean_lat(p["lat"]),
            "ar": p["ar"],
            "en": p["en"],
            "type": p["type"],
            "src": p.get("src", ""),
            "with_pronouns": bool(p.get("with_pronouns", False)),
        }
        if "note" in p:
            entry["note"] = p["note"]

        if entry["with_pronouns"]:
            prons = p["pronouns"]
            if len(prons["lat"]) != 7 or len(prons["ar"]) != 7:
                raise ValueError(f"Preposition {p['id']} must have exactly 7 pronoun forms")
            entry["pronouns"] = {
                "lat": [clean_lat(x) for x in prons["lat"]],
                "ar": prons["ar"],
            }
            if "altLat" in prons:
                entry["pronouns"]["altLat"] = [clean_lat(x) if x else None for x in prons["altLat"]]
            if "altAr" in prons:
                entry["pronouns"]["altAr"] = prons["altAr"]

        if "examples" in p:
            entry["examples"] = [
                {
                    "lat": clean_lat(ex["lat"]),
                    "ar": ex["ar"],
                    "en": ex["en"],
                }
                for ex in p["examples"]
            ]

        prepositions.append(entry)

    by_id = {p["id"]: p for p in prepositions}
    collocations = []
    for c in src.get("collocations", []):
        prep = clean_lat(c["prep"])
        forms = set(by_id.get(prep, {}).get("pronouns", {}).get("lat", []))
        example = clean_lat(c["exampleLat"])
        blanked = blank(example, prep, forms)
        if blanked is None:
            raise ValueError(f"collocation {c['verb']} {prep}: no '{prep}' in '{example}'")
        collocations.append({
            "exampleBlank": blanked,
            "verb": clean_lat(c["verb"]),
            "verbAr": c.get("verbAr", ""),
            "en": c["en"],
            "prep": clean_lat(c["prep"]),
            "prepAr": c.get("prepAr", ""),
            "meaning": c["meaning"],
            "exampleLat": clean_lat(c["exampleLat"]),
            "exampleAr": c.get("exampleAr", ""),
            "exampleEn": c.get("exampleEn", ""),
            "src": c.get("src", ""),
        })

    idioms = []
    for im in src.get("idioms", []):
        idioms.append({
            "id": im["id"],
            "pattern": im.get("pattern", ""),
            "prompt": im["prompt"],
            "lat": clean_lat(im["lat"]),
            "ar": im["ar"],
            "en": im["en"],
            "note": im.get("note", ""),
            "src": im.get("src", ""),
        })

    body = {
        "prepositions": prepositions,
        "collocations": collocations,
        "idioms": idioms,
    }

    out = json.dumps(body, ensure_ascii=False, indent=2)
    (ROOT / "data/prepositions.json").write_text(out + "\n", encoding="utf-8")

    with_pron_count = sum(1 for p in prepositions if p["with_pronouns"])
    print(f"{len(prepositions)} prepositions ({with_pron_count} with pronoun forms), "
          f"{len(collocations)} collocations, {len(idioms)} idioms written to data/prepositions.json")


if __name__ == "__main__":
    main()
