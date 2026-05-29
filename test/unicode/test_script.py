import unittest


class TestUnicodeScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global ScriptProperty, sc, scx_set
        from musculus.unicode.script import ScriptProperty, sc, scx_set

    def test_sc(self):
        cases = {
            # NOTE: Script property is subject to change in subsequent Unicode versions
            # Examples from UAX # 24 Section 2.4
            "s": ScriptProperty.LATIN,
            # KATAKANA LETTER SA
            "\u30b5": ScriptProperty.KATAKANA,
            # NEW TAI LUE LETTER LOW SA
            "\u198c": ScriptProperty.NEW_TAI_LUE,
            # PHAGS-PA LETTER SA
            "\ua85b": ScriptProperty.PHAGS_PA,
            # Section 2.7
            # PARENTHESIZED LATIN SMALL LETTER A
            "\u249c": ScriptProperty.COMMON,
            # CIRCLED KATAKANA A
            "\u32d0": ScriptProperty.KATAKANA,
            # COPYRIGHT SIGN
            "\u00a9": ScriptProperty.COMMON,
            # Section 3 Table 7
            "\u0020": ScriptProperty.COMMON,
            "\u0301": ScriptProperty.INHERITED,
            "\u243f": ScriptProperty.UNKNOWN,
            "\uffff": ScriptProperty.UNKNOWN,
            "\u0061": ScriptProperty.LATIN,
            "\u0363": ScriptProperty.INHERITED,
            "\u1cd1": ScriptProperty.INHERITED,
            "\u30fc": ScriptProperty.COMMON,
            "\u3099": ScriptProperty.INHERITED,
            "\u1cd0": ScriptProperty.INHERITED,
            "\u1802": ScriptProperty.COMMON,
            "\u060c": ScriptProperty.COMMON,
            "\u0640": ScriptProperty.COMMON,
            "\u096f": ScriptProperty.DEVANAGARI,
            "\u09ef": ScriptProperty.BENGALI,
            "\u1049": ScriptProperty.MYANMAR,
        }

        for case, expected in cases.items():
            self.assertEqual(sc(case), expected)

    def test_scx_set(self):
        cases = {
            # NOTE: scx property is subject to change in subsequent Unicode versions
            # Section 3 Table 7
            "\u0020": {ScriptProperty.COMMON},
            # XXX: UAX #24 is inconsistent with actual UCD 17.0 data
            # "\u0301": {ScriptProperty.INHERITED},
            "\u243f": {ScriptProperty.UNKNOWN},
            "\uffff": {ScriptProperty.UNKNOWN},
            "\u0061": {ScriptProperty.LATIN},
            "\u0363": {ScriptProperty.LATIN},
            "\u1cd1": {ScriptProperty.DEVANAGARI},
            "\u30fc": {ScriptProperty.HIRAGANA, ScriptProperty.KATAKANA},
            "\u3099": {ScriptProperty.HIRAGANA, ScriptProperty.KATAKANA},
            "\u1cd0": {
                ScriptProperty.BENGALI,
                ScriptProperty.DEVANAGARI,
                ScriptProperty.GRANTHA,
                ScriptProperty.KANNADA,
            },
            "\u1802": {ScriptProperty.MONGOLIAN, ScriptProperty.PHAGS_PA},
            "\u060c": {
                ScriptProperty.ARABIC,
                ScriptProperty.NKO,
                ScriptProperty.HANIFI_ROHINGYA,
                ScriptProperty.SYRIAC,
                ScriptProperty.THAANA,
                ScriptProperty.YEZIDI,
            },
            "\u0640": {
                ScriptProperty.ADLAM,
                ScriptProperty.ARABIC,
                ScriptProperty.MANDAIC,
                ScriptProperty.MANICHAEAN,
                ScriptProperty.OLD_UYGHUR,
                ScriptProperty.PSALTER_PAHLAVI,
                ScriptProperty.HANIFI_ROHINGYA,
                ScriptProperty.SOGDIAN,
                ScriptProperty.SYRIAC,
            },
            "\u096f": {
                ScriptProperty.DEVANAGARI,
                ScriptProperty.DOGRA,
                ScriptProperty.KAITHI,
                ScriptProperty.MAHAJANI,
            },
            "\u09ef": {
                ScriptProperty.BENGALI,
                ScriptProperty.CHAKMA,
                ScriptProperty.SYLOTI_NAGRI,
            },
            "\u1049": {
                ScriptProperty.CHAKMA,
                ScriptProperty.MYANMAR,
                ScriptProperty.TAI_LE,
            },
        }

        for case, expected in cases.items():
            self.assertTrue(expected.issubset(scx_set(case)))
            # self.assertSetEqual(scx_set(case), expected)
