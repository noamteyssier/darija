"""Slot picking and the verb-form check in scripts/build_examples.py."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_examples import bad_script, has_form, slots  # noqa: E402

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


class HasForm(unittest.TestCase):
    slot = {"lat": "ghadi nmshi", "ar": "غادي نمشي"}

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
