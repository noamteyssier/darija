"""Build data/words.json from data/raw/words.json.

usage: python3 scripts/build_words.py

Time and place words that never change form. The source is already in arabizi and Arabic script;
this checks it and gives each entry an id.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GROUPS = ["time", "calendar", "direction"]
KINDS = ["word", "phrase"]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    src = json.loads((ROOT / "data/raw/words.json").read_text(encoding="utf-8"))
    words, seen = [], set()
    for w in src["words"]:
        if w["group"] not in GROUPS or w["kind"] not in KINDS:
            raise ValueError(f"{w['lat']}: bad group or kind")
        wid = slug(w["lat"])
        if wid in seen:
            raise ValueError(f"duplicate id {wid}")
        seen.add(wid)
        e = {"id": wid, "group": w["group"], "kind": w["kind"], "lat": w["lat"], "ar": w["ar"], "en": w["en"]}
        for k in ("note", "ex"):
            if k in w:
                e[k] = w[k]
        words.append(e)
    out = json.dumps({"words": words}, ensure_ascii=False, separators=(",", ":"))
    out = out.replace('},{"id"', '},\n{"id"').replace('{"words":[', '{"words":[\n')
    (ROOT / "data/words.json").write_text(out + "\n", encoding="utf-8")
    counts = {g: sum(1 for w in words if w["group"] == g) for g in GROUPS}
    print(f"{len(words)} words written to data/words.json {counts}")


if __name__ == "__main__":
    sys.exit(main())
