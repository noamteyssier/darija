"""Hand-checked paradigms. Run scripts/build_verbs.py first; python3 -m unittest discover tests"""
import json
import unittest
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parent.parent / "data/verbs.json").read_text())
V = {v["id"]: v for v in DATA["verbs"]}

# ana, nta, nti, huwa, hiya, 7na, ntuma, huma
GOLDEN = {
    "kteb": ("ktebt ktebti ktebti kteb ketbat ktebna ktebtu ketbu",
             "kankteb katkteb katketbi kaykteb katkteb kanketbu katketbu kayketbu"),
    "fhem": ("fhemt fhemti fhemti fhem fehmat fhemna fhemtu fehmu",
             "kanfhem katfhem katfehmi kayfhem katfhem kanfehmu katfehmu kayfehmu"),
    "khdem": ("khdemt khdemti khdemti khdem khedmat khdemna khdemtu khedmu",
              "kankhdem katkhdem katkhedmi kaykhdem katkhdem kankhedmu katkhedmu kaykhedmu"),
    "chaf": ("chft chfti chfti chaf chafat chefna chftu chafu",
             "kanchuf katchuf katchufi kaychuf katchuf kanchufu katchufu kaychufu"),
    "mcha": ("mchit mchiti mchiti mcha mchat mchina mchitu mchaw",
             "kanmchi katmchi katmchi kaymchi katmchi kanmchiw katmchiw kaymchiw"),
    "qra": ("qrit qriti qriti qra qrat qrina qritu qraw",
            "kanqra katqra katqray kayqra katqra kanqraw katqraw kayqraw"),
    "kla": ("klit kliti kliti kla klat klina klitu klaw",
            "kanakul katakul katakli kayakul katakul kanaklu kataklu kayaklu"),
    "khda": ("khdit khditi khditi khda khdat khdina khditu khdaw",
             "kanakhud katakhud katakhdi kayakhud katakhud kanakhdu katakhdu kayakhdu"),
    "ja": ("jit jiti jiti ja jat jina jitu jaw",
           "kanji katji katji kayji katji kanjiw katjiw kayjiw"),
    "chedd": ("cheddit chedditi chedditi chedd cheddat cheddina chedditu cheddu",
              "kanchedd katchedd katcheddi kaychedd katchedd kancheddu katcheddu kaycheddu"),
    "qeddem-2": ("qeddemt qeddemti qeddemti qeddem qeddmat qeddemna qeddemtu qeddmu",
                 "kanqeddem katqeddem katqeddmi kayqeddem katqeddem kanqeddmu katqeddmu kayqeddmu"),
    "jaweb": ("jawebt jawebti jawebti jaweb jawbat jawebna jawebtu jawbu",
              "kanjaweb katjaweb katjawbi kayjaweb katjaweb kanjawbu katjawbu kayjawbu"),
    "terjem": ("terjemt terjemti terjemti terjem terjmat terjemna terjemtu terjmu",
               "kanterjem katterjem katterjmi kayterjem katterjem kanterjmu katterjmu kayterjmu"),
    "kan": ("knt knti knti kan kanat kenna kntu kanu",
            "kankun katkun katkuni kaykun katkun kankunu katkunu kaykunu"),
}
GOLDEN_AR = {
    "kteb": ("كتبت كتبتي كتبتي كتب كتبات كتبنا كتبتو كتبو",
             "كنكتب كتكتب كتكتبي كيكتب كتكتب كنكتبو كتكتبو كيكتبو"),
    "gal": ("قلت قلتي قلتي قال قالت قلنا قلتو قالو",
            "كنقول كتقول كتقولي كيقول كتقول كنقولو كتقولو كيقولو"),
    "qra": ("قريت قريتي قريتي قرا قرات قرينا قريتو قراو",
            "كنقرا كتقرا كتقراي كيقرا كتقرا كنقراو كتقراو كيقراو"),
    "kla": ("كليت كليتي كليتي كلا كلات كلينا كليتو كلاو",
            "كناكل كتاكل كتاكلي كياكل كتاكل كناكلو كتاكلو كياكلو"),
    "kan": ("كنت كنتي كنتي كان كانت كنا كنتو كانو",
            "كنكون كتكون كتكوني كيكون كتكون كنكونو كتكونو كيكونو"),
}


class Verbs(unittest.TestCase):
    def test_golden_latin(self):
        for vid, (past, pres) in GOLDEN.items():
            self.assertEqual(" ".join(V[vid]["past"]["lat"]), past, vid)
            self.assertEqual(" ".join(V[vid]["pres"]["lat"]), pres, vid)

    def test_golden_arabic(self):
        for vid, (past, pres) in GOLDEN_AR.items():
            self.assertEqual(" ".join(V[vid]["past"]["ar"]), past, vid)
            self.assertEqual(" ".join(V[vid]["pres"]["ar"]), pres, vid)

    def test_shape(self):
        self.assertGreater(len(V), 650)
        for v in V.values():
            for t in ("past", "pres"):
                self.assertEqual(len(v[t]["lat"]), 8, v["id"])
                self.assertEqual(len(v[t]["ar"]), 8, v["id"])
                self.assertTrue(all(v[t]["lat"]) and all(v[t]["ar"]), v["id"])
            self.assertIn(v["level"], (1, 2, 3))
            self.assertTrue(v["topics"], v["id"])


if __name__ == "__main__":
    unittest.main()
