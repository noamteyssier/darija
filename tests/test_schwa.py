"""python3 -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_verbs as b  # noqa: E402

C_FORMS = {
    "ktb": "kteb", "sqqṭ": "seqqeṭ", "trjm": "terjem", "tqddm": "tqeddem", "txaṣm": "txaṣem",
    "jawb": "jaweb", "ttafq": "ttafeq", "stafd": "stafed", "нllel": "нellel", "šdd": "šedd",
    "tšṭṭr": "tšeṭṭer", "wjع": "wjeع", "rkkz": "rekkez", "stعml": "steعmel", "bzzez": "bezzez",
    "عtarf": "عtaref", "nšr": "nšer", "amn": "amen", "kmml": "kemmel", "tškka": "tšekka",
    "wlla": "wella", "tbnna": "tbenna", "mša": "mša", "bda": "bda", "wlli": "welli",
    "šddi": "šeddi", "ḍrr": "ḍerr", "tmdd": "tmedd", "akul": "akul", "xrbq": "xerbeq",
}
V_FORMS = {
    "kteb": "ketb", "terjem": "terjm", "seqqeṭ": "seqqṭ", "jaweb": "jawb", "нellel": "нellel",
    "šedd": "šedd", "wjeع": "wejع", "tqeddem": "tqeddm", "steعmel": "steعml", "fhem": "fehm",
    "amen": "amn",
}


class Schwa(unittest.TestCase):
    def test_c_form(self):
        for pc, want in C_FORMS.items():
            self.assertEqual(b.c_form(pc), want, pc)

    def test_v_form(self):
        for c, want in V_FORMS.items():
            self.assertEqual(b.v_form(c), want, c)

    def test_arabic(self):
        self.assertEqual(b.ar("šaf"), "شاف")
        self.assertEqual(b.ar("нllel"), "حلل")
        self.assertEqual(b.ar("tعuwd"), "تعود")


if __name__ == "__main__":
    unittest.main()
