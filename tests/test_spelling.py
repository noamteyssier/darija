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


# English words that are also variants in the map; the notes mix English and arabizi
ENGLISH = {"like", "me", "be"}


def page_strings():
    """(where, text) for the static <strong>/<em> text in the pages and every note in data/raw/*.json."""
    for f in sorted([*ROOT.glob("assets/*.js"), *ROOT.glob("*.html")]):
        for m in re.finditer(r"<(strong|em)>([^<]*)</\1>", f.read_text()):
            if not re.search(r"['+]|esc\(", m[2]):  # built from data at run time
                yield f.name, m[2]

    def notes(x):
        for k, v in (x.items() if isinstance(x, dict) else enumerate(x)):
            if k == "note" and isinstance(v, str):
                yield v
            elif isinstance(v, (dict, list)):
                yield from notes(v)
    for f in sorted((ROOT / "data/raw").glob("*.json")):
        for n in notes(json.loads(f.read_text())):
            yield f.name, n


def arabizi(text):
    """The words of a page string that can only be arabizi: a digit (3la, d7k), an article hyphen (d-dar),
    or a known variant from the map (menni, qddam, u). Endings and lists of letters are skipped. English cannot be told apart in general, so plain
    words that canon() leaves or only rewrites by letter rules (sokkar, mor, kolchi) are not checked."""
    tab = sp.table(S)
    for t in sp.WORD.findall(text):
        w = t.strip("'-")
        if t.startswith("-") or len(w) == 1 and w != "u":  # endings (-u), lists of letters (t d r z s)
            continue
        if w == w.lower() and w not in ENGLISH and (re.search(r"\d|[a-z]-[a-z]", w) or w in tab or w in S["glued"] or w in S["tokens"]):
            yield w


class PageText(unittest.TestCase):
    maxDiff = None

    """Arabizi in the pages and notes was fixed by hand; this keeps new variants out."""

    def test_canonical(self):
        bad = {(f, w): sp.canon(w, S, sp.NOUN_KEEP) for f, s in page_strings() for w in arabizi(s)
               if sp.canon(w, S, sp.NOUN_KEEP) != w}
        self.assertEqual(bad, {})

    def test_finds_arabizi(self):
        self.assertEqual(list(arabizi("Takes men before nouns: d-dar, 3la, bla sokkar like me")), ["men", "d-dar", "3la"])
        self.assertGreater(len({w for _, s in page_strings() for w in arabizi(s)}), 50)

    def test_no_peace_corps_x(self):
        bad = {(f, w) for f, s in page_strings() for w in sp.WORD.findall(s.lower()) if sp.split(w)[1].startswith("x")}
        self.assertEqual(sorted(bad), [])


if __name__ == "__main__":
    unittest.main()
