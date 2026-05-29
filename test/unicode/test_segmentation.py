import unittest


class TestUnicodeSegmentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        global grapheme_break, default_sentence_break, default_word_break, word_break, sentence_break
        global GRAPHEME_BREAK_TEST_PATH, WORD_BREAK_TEST_PATH, SENTENCE_BREAK_TEST_PATH, load_test
        from musculus.unicode.segmentation import (
            grapheme_break,
            word_break,
            sentence_break,
            default_sentence_break,
            default_word_break,
        )
        from musculus.resources.ucd.auxiliary import (
            load_test,
            GRAPHEME_BREAK_TEST_PATH,
            SENTENCE_BREAK_TEST_PATH,
            WORD_BREAK_TEST_PATH,
        )

    def test_grapheme_break(self):
        test_cases = load_test(GRAPHEME_BREAK_TEST_PATH)
        for i, expected in enumerate(test_cases, 1):
            source = "".join(expected)
            # with self.subTest(f"Grapheme break test #{i:04d}"):
            result = list(grapheme_break(source))
            self.assertSequenceEqual(result, expected, f"Grapheme break test #{i:04d}")

    def test_word_break(self):
        test_cases = load_test(WORD_BREAK_TEST_PATH)
        for i, expected in enumerate(test_cases, 1):
            source = "".join(expected)
            # with self.subTest(f"Word break test #{i:04d}"):
            result = list(default_word_break(source))
            self.assertSequenceEqual(result, expected, f"Word break test #{i:04d}")

    def test_sentence_break(self):
        test_cases = load_test(SENTENCE_BREAK_TEST_PATH)
        for i, expected in enumerate(test_cases, 1):
            source = "".join(expected)
            # with self.subTest(f"Sentence break test #{i:04d}"):
            result = list(default_sentence_break(source))
            self.assertSequenceEqual(result, expected, f"Sentence break test #{i:04d}")

