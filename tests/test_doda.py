import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data/doda.json").read_text())["words"]
IDS = {w["id"] for w in D}


class Doda(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(len(IDS), len(D), "ids are unique")
        for w in D:
            for k in ("lat", "ar", "en", "topic", "src"):
                self.assertTrue(w[k], w["id"])
            self.assertTrue(w["src"].startswith("DODa"), w["id"])

    def test_site_letters(self):
        for w in D:
            for bad in "985":
                self.assertNotIn(bad, w["lat"], w["id"])
            self.assertRegex(w["lat"], r"^[a-z0-9' -]+$", w["id"])

    def test_topics_big_enough_to_drill(self):
        topics = {}
        for w in D:
            topics[w["topic"]] = topics.get(w["topic"], 0) + 1
        self.assertGreaterEqual(len(topics), 12)
        for t, n in topics.items():
            self.assertGreaterEqual(n, 20, t)

    def test_no_overlap_with_taught_nouns(self):
        nouns = {n["lat"] for n in json.loads((ROOT / "data/nouns.json").read_text())["nouns"]}
        self.assertFalse(nouns & {w["lat"] for w in D})


if __name__ == "__main__":
    unittest.main()
