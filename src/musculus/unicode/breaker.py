from collections.abc import Iterable

from icu4py.breakers import CharacterBreaker, SentenceBreaker, WordBreaker

LOCALE = "root"


def grapheme_break(s: str, *, locale=LOCALE) -> Iterable[str]:
    return CharacterBreaker(s, locale)


def word_break(s: str, *, locale=LOCALE) -> Iterable[str]:
    return WordBreaker(s, locale)


def sentence_break(s: str, *, locale=LOCALE) -> Iterable[str]:
    return SentenceBreaker(s, locale)

