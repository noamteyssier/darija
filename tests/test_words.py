import json
import unittest
from pathlib import Path

D = json.loads((Path(__file__).resolve().parent.parent / "data/words.json").read_text())
W = {w["id"]: w for w in D["words"]}


class Words(unittest.TestCase):
    def test_known_words(self):
        self.assertEqual(W["lyum"]["en"], "today")
        self.assertEqual(W["ghedda"]["ar"], "غدا")
        self.assertEqual(W["limen"]["group"], "direction")
        self.assertEqual(W["had-s-semmana"]["en"], "this week")

    def test_shape(self):
        self.assertEqual(len(W), len(D["words"]), "ids are unique")
        for w in W.values():
            self.assertIn(w["group"], ("time", "calendar", "direction"))
            self.assertIn(w["kind"], ("word", "phrase"))
            for k in ("lat", "ar", "en"):
                self.assertTrue(w[k], w["id"])

    def test_groups_big_enough_to_drill(self):
        for g in ("time", "calendar", "direction"):
            self.assertGreaterEqual(sum(w["group"] == g for w in W.values()), 8)

    def test_compass_and_days(self):
        ens = {w["en"] for w in W.values()}
        for e in ("north", "south", "east", "west", "left", "right", "yesterday", "week", "month", "year", "Monday", "Sunday"):
            self.assertIn(e, ens)


if __name__ == "__main__":
    unittest.main()
