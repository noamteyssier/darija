"""Slot picking and the verb-form check in scripts/build_examples.py."""
import json
import sys
import unittest
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_examples import bad_script, has_form, negate, reviewed, slots

V = {v["id"]: v for v in json.loads((ROOT / "data/verbs.json").read_text())["verbs"]}


class Slots(unittest.TestCase):
    def test_stable_and_distinct(self):
        a, b = slots(V["kteb"]), slots(V["kteb"])
        self.assertEqual(a, b)
        self.assertEqual([s["tense"] for s in a], ["past", "pres", "fut"])
        self.assertEqual(len({s["p"] for s in a}), 3)

    def test_future_matches_site(self):
        fut = slots(V["msha"])[2]
        pres = V["msha"]["pres"]
        self.assertEqual(fut["lat"], "ghadi " + pres["lat"][fut["p"]][2:])
        self.assertEqual(fut["ar"], "غادي " + pres["ar"][fut["p"]][1:])


class Full(unittest.TestCase):
    def test_every_slot_once(self):
        a = slots(V["kteb"], full=True)
        self.assertEqual(len(a), 48)
        self.assertEqual([s["slot"] for s in a], list(range(48)))
        self.assertEqual(len({(s["tense"], s["p"], s["neg"]) for s in a}), 48)

    def test_negation(self):
        self.assertEqual(negate("ktebt", "كتبت", "past"), ("ma ktebtsh", "ما كتبتش"))
        self.assertEqual(negate("ghadi nkteb", "غادي نكتب", "fut"), ("ma ghadish nkteb", "ما غاديش نكتب"))
        neg = [s for s in slots(V["kteb"], full=True) if s["neg"] and s["tense"] == "fut"]
        self.assertTrue(all(s["lat"].startswith("ma ghadish ") for s in neg))


class Reviewed(unittest.TestCase):
    gem: ClassVar = {"kteb": [{"slot": i, "lat": f"l{i}", "ar": f"a{i}", "en": f"e{i}"} for i in range(4)], "shaf": [{"slot": 0, "lat": "x", "ar": "x", "en": "x"}]}

    def test_ok_fixed_dropped_unreviewed(self):
        rev = {"kteb": {"0": {"ok": True}, "1": {"ok": False, "why": "w", "lat": "L", "ar": "A", "en": "E"},
                        "2": {"ok": False, "why": "w", "lat": "", "ar": "", "en": ""}}}
        out = reviewed(self.gem, rev)
        self.assertEqual(out, {"kteb": [self.gem["kteb"][0], {"slot": 1, "lat": "L", "ar": "A", "en": "E"}]})

    def test_nothing_without_review(self):
        self.assertEqual(reviewed(self.gem, {}), {})


class HasForm(unittest.TestCase):
    slot: ClassVar = {"lat": "ghadi nmshi", "ar": "غادي نمشي"}

    def test_whole_words(self):
        self.assertTrue(has_form({"lat": "Ghadi nmshi l s-suq.", "ar": "غادي نمشي للسوق؟"}, self.slot))

    def test_rejects_attached(self):
        self.assertFalse(has_form({"lat": "ghadi nmshiw", "ar": "غادي نمشيو"}, self.slot))
        self.assertFalse(has_form({"lat": "ghadi nmshi", "ar": "وغادي نمشي"}, self.slot))


    def test_script_check(self):
        self.assertFalse(bad_script({"lat": "kansherbu atay f s-sba7?", "ar": "كنشربو أتاي فالصباح؟"}))
        self.assertTrue(bad_script({"lat": "seddit l-bab mزيان", "ar": "سديت الباب مزيان"}))
        self.assertTrue(bad_script({"lat": "kansherbu atay", "ar": "كنشربو الatay"}))
        self.assertTrue(bad_script({"lat": "s-suâl", "ar": "السؤال"}))


if __name__ == "__main__":
    unittest.main()
