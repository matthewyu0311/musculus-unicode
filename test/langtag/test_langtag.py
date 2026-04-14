import unittest


class TestLanguageTag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global LanguageTag
        global characterize
        from musculus.metadata.langtag import LanguageTag, characterize
    
    def test_characterize(self):
        self.assertEqual(characterize(0, "zh"), ("language", "zh"))
        self.assertEqual(characterize(0, "cmn"), ("language", "cmn"))
        self.assertEqual(characterize(1, "CMN"), ("extlang", "cmn"))
        self.assertEqual(characterize(2, "Hant"), ("script", "Hant"))
        self.assertEqual(characterize(3, "tw"), ("region", "TW"))
        self.assertEqual(characterize(4, "1994"), ("variant", "1994"))

        with self.assertRaises(ValueError):
            characterize(0, "Hant")
        with self.assertRaises(ValueError):
            characterize(0, "123")

    def test_basic(self):
        """Examples adapted from RFC 5646 Section 2.1.1 Formatting of Language Tags"""
        test_cases = {
            "MN-cYRL-mn": "mn-Cyrl-MN",
            "mN-cYrL-Mn": "mn-Cyrl-MN",
            "I-AMI": "ami",
            "EN-CA-X-CA": "en-CA-x-ca",
            "SGN-be-fr": "sfb",
            "Az-latn-X-Latn": "az-Latn-x-latn",
            "en-GB-oed": "en-GB-oxendict",
            "x-FR-CH": "x-fr-ch",
            "az-Arab-IR": "az-Arab-IR",
            "zh-Hant-CN": "zh-Hant-CN",
            "es-419": "es-419",
            "sl-nedis": "sl-nedis",
            "de-CH-1996": "de-CH-1996",
            # "de-a-value": "de-a-value",
            "en-Latn-GB-boont-u-extended-sequence-x-private": "en-GB-boont-u-extended-sequence-x-private",
            "i-kLiNgON": "tlh",
            "NO-NYN": "nn",
            "zh-hakka": "hak",
            "zh-hak-cn": "hak-CN",
            "sgn-CH-DE": "sgg",
            "sl-1994-rozaj-biske": "sl-rozaj-biske-1994",
            "SL-ROZAJ-1994-BISKE": "sl-rozaj-biske-1994",
            "ja-Latn-hepburn-heploc": "ja-Latn-alalc97",
            "sGN-LATN-US": "ase-Latn",
            "en-u-ccc-bbb-t-aaa-X-xyz": "en-t-aaa-u-ccc-bbb-x-xyz",
        }
        for tag, canonicalized in test_cases.items():
            lt = LanguageTag.parse(tag)
            self.assertEqual(lt, LanguageTag.parse(canonicalized))
            self.assertEqual(str(lt), canonicalized)
            self.assertEqual(LanguageTag.parse(str(lt)), lt)
