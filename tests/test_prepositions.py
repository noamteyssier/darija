import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data/prepositions.json"


class TestPrepositions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.preps = {p["id"]: p for p in cls.data["prepositions"]}
        cls.collocations = cls.data["collocations"]
        cls.idioms = cls.data["idioms"]

    def test_file_exists_and_not_empty(self):
        self.assertTrue(DATA_PATH.exists())
        self.assertGreater(len(self.preps), 20)
        self.assertGreater(len(self.collocations), 20)
        self.assertGreater(len(self.idioms), 10)

    def test_preposition_fields(self):
        valid_types = {"simple", "locative", "temporal", "relational"}
        for p in self.preps.values():
            self.assertTrue(p["id"])
            self.assertTrue(p["lat"])
            self.assertTrue(p["ar"])
            self.assertTrue(p["en"])
            self.assertIn(p["type"], valid_types)

            if p["with_pronouns"]:
                self.assertIn("pronouns", p)
                self.assertEqual(len(p["pronouns"]["lat"]), 7)
                self.assertEqual(len(p["pronouns"]["ar"]), 7)
                for lat_form, ar_form in zip(p["pronouns"]["lat"], p["pronouns"]["ar"]):
                    self.assertTrue(lat_form)
                    self.assertTrue(ar_form)

    def test_primary_pronoun_paradigms(self):
        # m3a: m3aya, m3ak, m3ah, m3aha, m3ana, m3akum, m3ahum
        m3a = self.preps["m3a"]["pronouns"]["lat"]
        self.assertEqual(m3a, ["m3aya", "m3ak", "m3ah", "m3aha", "m3ana", "m3akum", "m3ahum"])
        self.assertEqual(self.preps["m3a"]["pronouns"]["ar"][0], "معايا")

        # l: liya, lik, lih, liha, lina, likum, lihum
        l = self.preps["l"]["pronouns"]["lat"]
        self.assertEqual(l, ["liya", "lik", "lih", "liha", "lina", "likum", "lihum"])
        self.assertEqual(self.preps["l"]["pronouns"]["ar"][0], "ليا")

        # f: fiya, fik, fih, fiha, fina, fikum, fihum
        f = self.preps["f"]["pronouns"]["lat"]
        self.assertEqual(f, ["fiya", "fik", "fih", "fiha", "fina", "fikum", "fihum"])
        self.assertEqual(self.preps["f"]["pronouns"]["ar"][0], "فيا")

        # 3nd: 3ndi, 3ndek, 3ndu, 3ndha, 3ndna, 3ndkum, 3ndhum
        nd = self.preps["3nd"]["pronouns"]["lat"]
        self.assertEqual(nd, ["3ndi", "3ndek", "3ndu", "3ndha", "3ndna", "3ndkum", "3ndhum"])
        self.assertEqual(self.preps["3nd"]["pronouns"]["ar"][0], "عندي")

        # men: menni, mennek, mennu, mennha, menna, mennkum, mennhum
        men = self.preps["men"]["pronouns"]["lat"]
        self.assertEqual(men, ["menni", "mennek", "mennu", "mennha", "menna", "mennkum", "mennhum"])
        self.assertEqual(self.preps["men"]["pronouns"]["ar"][0], "مني")

        # 3la: 3liya, 3lik, 3lih, 3liha, 3lina, 3likum, 3lihum
        la = self.preps["3la"]["pronouns"]["lat"]
        self.assertEqual(la, ["3liya", "3lik", "3lih", "3liha", "3lina", "3likum", "3lihum"])
        self.assertEqual(self.preps["3la"]["pronouns"]["ar"][0], "عليا")

        # bla: blaya, blak, blah, blaha, blana, blakum, blahum
        bla = self.preps["bla"]["pronouns"]["lat"]
        self.assertEqual(bla, ["blaya", "blak", "blah", "blaha", "blana", "blakum", "blahum"])

    def test_collocations(self):
        for c in self.collocations:
            self.assertTrue(c["verb"])
            self.assertTrue(c["prep"])
            self.assertTrue(c["meaning"])
            self.assertTrue(c["exampleLat"])
            self.assertTrue(c["exampleAr"])
            self.assertTrue(c["exampleEn"])

    def test_collocation_blank(self):
        for c in self.collocations:
            self.assertEqual(c["exampleBlank"].count("___"), 1, c["exampleLat"])
        by_verb = {(c["verb"], c["prep"]): c for c in self.collocations}
        self.assertEqual(by_verb[("fkkr", "f")]["exampleBlank"], "kan-fkkr ___")
        self.assertEqual(by_verb[("khaf", "men")]["exampleBlank"], "Jerry kay-khaf ___ Tom")

    def test_no_stray_apostrophe_digraphs(self):
        text = DATA_PATH.read_text(encoding="utf-8")
        for bad in ("s'h", "k'h", "g'h"):
            self.assertNotIn(bad, text)

    def test_idioms(self):
        for im in self.idioms:
            self.assertTrue(im["id"])
            self.assertTrue(im["prompt"])
            self.assertTrue(im["lat"])
            self.assertTrue(im["ar"])
            self.assertTrue(im["en"])


if __name__ == "__main__":
    unittest.main()
