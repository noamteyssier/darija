import json
import unittest
from pathlib import Path

D = json.loads((Path(__file__).resolve().parent.parent / "data/questions.json").read_text())["words"]


class Questions(unittest.TestCase):
    def test_nine_words_ten_sentences(self):
        self.assertEqual([w["id"] for w in D], ["fin", "m3ach", "waqtach", "imta", "kifach", "3lach", "achnu", "chkun", "chhal"])
        for w in D:
            self.assertGreaterEqual(len(w["s"]), 10, w["id"])

    def test_blank_marks_the_word(self):
        for w in D:
            for s in w["s"]:
                self.assertEqual(s["lat"].count("{" + w["lat"] + "}"), 1, s["lat"])
                self.assertEqual(s["ar"].count("{" + w["ar"] + "}"), 1, s["ar"])
                self.assertTrue(s["en"])

    def test_like_points_at_a_word(self):
        ids = {w["id"] for w in D}
        for w in D:
            for o in w.get("like", []):
                self.assertIn(o, ids)
                self.assertIn(w["id"], next(x for x in D if x["id"] == o)["like"], f"{o} lists {w['id']} back")

    def test_when_words(self):
        when = {w["id"] for w in D if w["en"] == "when"}
        self.assertEqual(when, {"m3ach", "waqtach", "imta"})
        for w in D:
            if w["id"] in when:
                self.assertEqual(set(w["like"]), when - {w["id"]})
                for s in w["s"]:
                    self.assertTrue(s["en"].startswith("When "), s["en"])

    def test_no_digit_9(self):
        for w in D:
            self.assertNotIn("9", w["lat"] + w["note"])
            for s in w["s"]:
                self.assertNotIn("9", s["lat"])


if __name__ == "__main__":
    unittest.main()
