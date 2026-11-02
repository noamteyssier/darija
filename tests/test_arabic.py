"""Arabic-script conventions from docs/spelling.md, over every Arabic string in the data."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from spelling import clean_ar

DATA = ROOT / "data"
KEY = re.compile(r"ar|alt[Aa]r|\w+Ar")
SHADDA_NOUNS = {"bba", "mmi"}  # their possessives carry a shadda (مّي, بّا)


def walk(o, key=None):
    if isinstance(o, str):
        if key and KEY.fullmatch(key):
            yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, k)
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, key)


def files():
    for name in ("nouns", "verbs", "words", "prepositions"):
        yield f"{name}.json", json.loads((DATA / f"{name}.json").read_text())
    for p in sorted((DATA / "examples").glob("*.json")):
        yield f"examples/{p.name}", json.loads(p.read_text())


ALL = [(n, s) for n, d in files() for s in walk(d)]
SENTENCES = [(n, x) for n, d in files() if n.startswith("examples/") for x in d]


def bad(pred, rows=ALL):
    return [f"{n}: {s}" for n, s in rows if pred(s)][:5]


class Script(unittest.TestCase):
    def test_arabic_letters_only(self):
        self.assertEqual(bad(lambda s: re.search(r"[A-Za-z0-9]", s)), [])

    def test_no_diacritics_but_the_shadda_on_two_nouns(self):
        self.assertEqual(bad(lambda s: re.search("[ً-ِْ]", s)), [])
        self.assertEqual({n for n, s in ALL if "ّ" in s}, {"nouns.json"})
        nouns = json.loads((DATA / "nouns.json").read_text())
        shadda = {x["id"] for k in nouns for x in nouns[k] if "ّ" in json.dumps(x, ensure_ascii=False)}
        self.assertEqual(shadda, SHADDA_NOUNS)

    def test_article_is_not_a_word_of_its_own(self):
        self.assertEqual(bad(lambda s: re.search(r"(^|\s)ال(\s|$)", s)), [])

    def test_f_l_b_join_the_next_word(self):
        # a lone letter is allowed only as the whole field (the preposition itself: ف, ل, ب)
        self.assertEqual(bad(lambda s: " " in s and re.search(r"(^|\s)[فلب](\s|$)", s)), [])

    def test_clean_ar_leaves_the_data_alone(self):
        self.assertEqual(bad(lambda s: " " in s and clean_ar(s) != s), [])

    def test_future_is_ghadi(self):
        fut = [(n, x["ar"]) for n, x in SENTENCES if x["t"] == "fut"]
        self.assertTrue(fut)
        self.assertEqual(bad(lambda s: not re.search(r"(^|\s)غادي(ش)?(\s|$)", s), fut), [])
        self.assertEqual(bad(lambda s: re.search(r"(^|\s)(راح|غاد|رح)(\s|$)", s)), [])


class CleanAr(unittest.TestCase):
    def test_joins_and_strips(self):
        self.assertEqual(clean_ar("شد ف الحبس"), "شد فالحبس")
        self.assertEqual(clean_ar("مشيت ل السوق"), "مشيت للسوق")
        self.assertEqual(clean_ar("حتى ل الليل"), "حتى لليل")
        self.assertEqual(clean_ar("ب الطوبيس"), "بالطوبيس")
        self.assertEqual(clean_ar("كَتَبْت"), "كتبت")
        self.assertEqual(clean_ar("ف"), "ف")


if __name__ == "__main__":
    unittest.main()
