"""One spelling per word (docs/spelling.md). python3 -m unittest discover tests"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import spelling as sp
from build_nouns import SUN
from build_verbs import lat

S = sp.load()


class Canon(unittest.TestCase):
    def test_counted(self):
        self.assertEqual(sp.canon("ghadi nmchi ghda", S), "ghadi nmchi ghedda")
        self.assertEqual(sp.canon("huwa mezyan bzzaf", S), "huwa mzyan bezzaf")

    def test_article(self):
        self.assertEqual(sp.canon("f l-khedma", S), "f l-khdma")
        self.assertEqual(sp.canon("z-znqa", S), "z-zenqa")

    def test_glued_article(self):
        self.assertEqual(sp.canon("kayn lbare7 w lyum", S), "kayn l-bare7 w l-yum")
        self.assertEqual(sp.canon("jjay", S), "j-jay")
        # words that start with l, or with a doubled sun letter, are not the article
        for w in ("lila", "lben", "l7em", "lun", "li", "lik", "lih", "lli"):
            self.assertEqual(sp.canon(w, S), w)

    def test_sun_letters(self):
        self.assertEqual(sp.canon("l-dar ch-chems s-chems z-zenqa l-ktab", S), "d-dar ch-chems ch-chems z-zenqa l-ktab")
        self.assertEqual(sp.canon("l-jiran l-lila l-restoran l-jornal", S), "j-jiran l-lila r-restoran j-jornal")

    def test_letters(self):
        self.assertEqual(sp.canon("l-khobz w kolchi", S), "l-khubz w kulchi")
        self.assertEqual(sp.canon("l-moudir", S), "l-mudir")
        self.assertEqual(sp.site("wach 9al chi 5bar"), "wach qal chi khbar")

    def test_and(self):
        self.assertEqual(sp.canon("khuya u sa7bu", S), "khuya w sa7bu")

    def test_kept(self):
        for s in ("t-tobis", "s-salon", "mmi", "bba", "lli", "ma ktebtch"):
            self.assertEqual(sp.canon(s, S), s)
        self.assertEqual(sp.canon("ghda", S, keep=["ghda"]), "ghda")
        self.assertEqual(sp.canon("kla l-ghda", S), "kla l-ghda")  # lunch, not tomorrow
        self.assertEqual(sp.canon("l-gheda", S), "l-ghda")
        self.assertEqual(sp.canon("Thomas chrah liha", S), "Thomas chrah liha")
        self.assertEqual(sp.canon("meT3am", S), "meT3am")


class Map(unittest.TestCase):
    def test_up_to_date(self):
        built = sp.build(json.loads(sp.COUNTS.read_text()))
        self.assertEqual(built, S, "rerun python3 scripts/spelling.py")

    def test_one_way(self):
        tab = sp.table(S)
        for v, w in tab.items():
            self.assertNotIn(w, tab, f"{v} -> {w} -> {tab.get(w)}")

    def test_verb_forms_untouched(self):
        self.assertFalse(sp.verb_forms() & set(sp.table(S)))

    def test_distinct_not_merged(self):
        tab = sp.table(S)
        for group in json.loads(sp.MANUAL.read_text())["distinct"]:
            for w in group:
                self.assertNotIn(tab.get(w), set(group) - {w}, group)


class Tables(unittest.TestCase):
    def test_one_spelling_per_table(self):
        for table in sp.paradigms():
            got = [sp.canon(f, S, sp.NOUN_KEEP) if f else f for f in table]
            self.assertIn(got, list(sp.table_spellings(table)), table)

    def test_examples(self):
        for raw, want in (("mennek", "mnek"), ("menna", "mna"), ("mennhum", "mnhum"), ("qddamek", "qdamek"), ("3ndek", "3ndk")):
            self.assertEqual(sp.canon(raw, S), want)


class SiteData(unittest.TestCase):
    """Every arabizi string the site shows from data/ is already canonical."""

    def test_canonical(self):
        bad = [s for s in sp.site_text() if sp.canon(s, S, sp.NOUN_KEEP) != s]
        self.assertEqual(bad[:20], [], f"{len(bad)} strings, e.g. {[sp.canon(s, S) for s in bad[:3]]}")

    def test_tomorrow_is_not_lunch(self):
        for f in sorted((ROOT / "data/examples").glob("*.json")):
            for s in json.loads(f.read_text()):
                self.assertNotIn("ghda", s["lat"].split(), s["lat"])

    def test_article_copies_sun_letter(self):
        sun = {lat(c) for c in SUN} - {"l"}  # arabizi of SUN in build_nouns.py: d, ch, z, ...
        self.assertEqual(sun, set(sp.SUN) - {"l"})
        bad = set()
        for s in sp.site_text():
            for t in sp.WORD.findall(s):
                a, stem = sp.split(t)
                if a:
                    first = next((x for x in sorted(sun, key=len, reverse=True) if stem.startswith(x)), "l")
                    if a != first + "-":
                        bad.add(t)
        self.assertEqual(sorted(bad), [])

    def test_letters(self):
        keep = set(S["keep"])
        bad = {t for s in sp.site_text() for t in sp.WORD.findall(s.lower())
               if re.search(r"9|ou", t) or ("o" in t and sp.split(t)[1] not in keep)}
        self.assertEqual(sorted(bad), [])


if __name__ == "__main__":
    unittest.main()
