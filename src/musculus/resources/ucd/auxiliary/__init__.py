from collections.abc import Iterable, Sequence
import importlib.resources
from importlib.resources.abc import Traversable

if __package__ is None:
    raise ImportError("This shall not be used as a top-level module.")

AUXILIARY_PATH: Traversable = importlib.resources.files(__package__)
GRAPHEME_BREAK_PATH: Traversable = AUXILIARY_PATH.joinpath("GraphemeBreakProperty.txt")
WORD_BREAK_PATH: Traversable = AUXILIARY_PATH.joinpath("WordBreakProperty.txt")
SENTENCE_BREAK_PATH: Traversable = AUXILIARY_PATH.joinpath("SentenceBreakProperty.txt")

GRAPHEME_BREAK_TEST_PATH: Traversable = AUXILIARY_PATH.joinpath("GraphemeBreakTest.txt")
WORD_BREAK_TEST_PATH: Traversable = AUXILIARY_PATH.joinpath("WordBreakTest.txt")
SENTENCE_BREAK_TEST_PATH: Traversable = AUXILIARY_PATH.joinpath("SentenceBreakTest.txt")


def load_test(t: Traversable, /) -> list[list[str]]:
    result = []
    with t.open(mode="r", encoding="utf-8") as txt:
        for line in txt:
            p = process_test_line(line)
            if p:
                result.append(p)
    return result


def process_test_line(line: str, /) -> list[str] | None:
    if not line.startswith("÷"):
        return
    test_case, _, _comment = line.partition("#")
    test_case = test_case[1:].strip().removesuffix("÷")
    segments = test_case.split("÷")
    result = []
    for segment in segments:
        s = []
        for x in segment.split("×"):
            x = x.strip()
            if not x:
                continue
            c = chr(int(x, base=16))
            s.append(c)
        if s:
            result.append("".join(s))
    return result
