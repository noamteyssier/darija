import json
import unittest
from pathlib import Path

D = json.loads((Path(__file__).resolve().parent.parent / "data/nouns.json").read_text())
N = {n["id"]: n for n in D["nouns"]}
A = {a["id"]: a for a in D["adjectives"]}


class Nouns(unittest.TestCase):
    def test_possessives(self):
        self.assertEqual(N["ktab"]["mine"]["lat"], ["ktabi", "ktabek", "ktabu", "ktabha", "ktabna", "ktabkum", "ktabhum"])
        self.assertEqual(N["magana"]["mine"]["lat"][0], "maganti")
        self.assertEqual(N["magana"]["mine"]["ar"][0], "ماڭانتي")
        self.assertEqual(N["khu"]["mine"]["lat"][0], "khuya")
        self.assertEqual(N["bent"]["mine"]["lat"][3], "bentha")

    def test_dyal(self):
        self.assertEqual(N["dar"]["dyal"]["lat"][0], "d-dar dyali")
        self.assertEqual(N["ktab"]["dyal"]["ar"][6], "الكتاب ديالهم")
        self.assertNotIn("dyal", N["bba"])

    def test_definite(self):
        self.assertEqual(N["shems"]["def"]["lat"], "sh-shems")
        self.assertEqual(N["kelb"]["def"]["lat"], "l-kelb")
        self.assertEqual(A["kbir"]["def"]["lat"], ["l-kbir", "l-kbira", "l-kbar"])

    def test_shape(self):
        for n in N.values():
            self.assertIn(n["g"], "mf")
            if "mine" in n:
                self.assertEqual(len(n["mine"]["lat"]), 7)
                self.assertEqual(len(n["mine"]["ar"]), 7)
        for a in A.values():
            self.assertEqual(len(a["lat"]), 3)
            self.assertEqual(len(a["ar"]), 3)


if __name__ == "__main__":
    unittest.main()
