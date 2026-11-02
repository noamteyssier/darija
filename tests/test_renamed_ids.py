import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    return json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))


# RENAMED in assets/common.js: one 'old': 'new' per line (or "old" for ids with a quote).
SRC = (ROOT / "assets/common.js").read_text(encoding="utf-8")
TABLE = SRC[SRC.index("const RENAMED = {"):].split("\n};")[0]
RENAMED = {
    a or b: c
    for a, b, c in re.findall(r"""^\s*(?:'([^']+)'|"([^"]+)"): '([^']+)',""", TABLE, re.M)
}

IDS = {
    x["id"]
    for f, keys in {
        "verbs": ["verbs"],
        "nouns": ["nouns", "adjectives"],
        "words": ["words"],
        "prepositions": ["prepositions", "idioms"],
    }.items()
    for k in keys
    for x in load(f)[k]
}
COLLOCATIONS = {
    f"c|{i}|{c['verb']}|{c['prep']}" for i, c in enumerate(load("prepositions")["collocations"])
}


class RenamedIds(unittest.TestCase):
    def test_table_parsed(self):
        entries = [l for l in TABLE.splitlines() if l.strip() and not l.strip().startswith("//") and "{" not in l]
        self.assertEqual(len(RENAMED), len(entries), "every table line parses")

    def test_new_ids_exist(self):
        for old, new in RENAMED.items():
            self.assertIn(new, COLLOCATIONS if old.startswith("c|") else IDS, f"{old} -> {new}")

    def test_old_ids_gone(self):
        for old in RENAMED:
            self.assertNotIn(old, IDS | COLLOCATIONS, f"{old} still exists")


if __name__ == "__main__":
    unittest.main()
