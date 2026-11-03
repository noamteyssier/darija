"""Build data/sentences.json, every example sentence in one file for the Sentences page.

usage: python3 scripts/build_sentences.py

Sources: data/examples/<verb>.json, the examples on prepositions, and the examples on time and place
words. Each row is [lat, ar, en, kind, id]; kind is v (verb), p (preposition) or w (word), id the
dictionary entry it belongs to.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    rows, seen = [], set()

    def add(lat, ar, en, kind, ident):
        if lat not in seen:
            seen.add(lat)
            rows.append([lat, ar, en, kind, ident])

    for f in sorted((ROOT / "data/examples").glob("*.json")):
        for e in json.loads(f.read_text(encoding="utf-8")):
            add(e["lat"], e["ar"], e["en"], "v", f.stem)
    preps = json.loads((ROOT / "data/prepositions.json").read_text(encoding="utf-8"))
    for p in preps["prepositions"]:
        for e in p.get("examples", []):
            add(e["lat"], e["ar"], e["en"], "p", p["id"])
    for w in json.loads((ROOT / "data/words.json").read_text(encoding="utf-8"))["words"]:
        if "ex" in w:
            add(w["ex"]["lat"], w["ex"]["ar"], w["ex"]["en"], "w", w["id"])

    out = json.dumps({"s": rows}, ensure_ascii=False, separators=(",", ":")).replace("],[", "],\n[")
    (ROOT / "data/sentences.json").write_text(out + "\n", encoding="utf-8")
    print(f"{len(rows)} sentences written to data/sentences.json")


if __name__ == "__main__":
    main()
