"""Implements Unicode Text Segmentation algorithms.
If installed, the breakers from icu4py will be used. Otherwise, the fallbacks
"""

from collections import deque
from itertools import chain
from typing import TYPE_CHECKING, ClassVar, NewType, cast
import unicodedata
from collections.abc import Callable, Iterable, Sequence, Set

from musculus.util.parse import LooseMatchStrEnum
from musculus.util.functions import LookaheadIterator

from .invariants import PROP_SENTENCE_BREAK, PROP_WORD_BREAK, ZWJ
from .emoji import is_extended_pictographic
from ..resources.ucd.auxiliary import SENTENCE_BREAK_PATH, WORD_BREAK_PATH
from ..util.ucd import get_ucd_table

ROOT_LOCALE = "root"
Grapheme = NewType("Grapheme", str)
type Word = Sequence[Grapheme]


if TYPE_CHECKING:

    class WordBreakProperty(LooseMatchStrEnum):
        CR = "CR"
        DOUBLE_QUOTE = "DQ"
        E_BASE = "EB"
        E_BASE_GAZ = "EBG"
        E_MODIFIER = "EM"
        EXTENDNUMLET = "EX"
        EXTEND = "Extend"
        FORMAT = "FO"
        GLUE_AFTER_ZWJ = "GAZ"
        HEBREW_LETTER = "HL"
        KATAKANA = "KA"
        ALETTER = "LE"
        LF = "LF"
        MIDNUMLET = "MB"
        MIDLETTER = "ML"
        MIDNUM = "MN"
        NEWLINE = "NL"
        NUMERIC = "NU"
        REGIONAL_INDICATOR = "RI"
        SINGLE_QUOTE = "SQ"
        WSEGSPACE = "WSegSpace"
        OTHER = "XX"
        ZWJ = "ZWJ"

    class SentenceBreakProperty(LooseMatchStrEnum):
        ATERM = "AT"
        CLOSE = "CL"
        CR = "CR"
        EXTEND = "EX"
        FORMAT = "FO"
        OLETTER = "LE"
        LF = "LF"
        LOWER = "LO"
        NUMERIC = "NU"
        SCONTINUE = "SC"
        SEP = "SE"
        SP = "SP"
        STERM = "ST"
        UPPER = "UP"
        OTHER = "XX"


wb: Callable[[str | int], WordBreakProperty]

WordBreakProperty, _wb_table, wb = get_ucd_table(
    WORD_BREAK_PATH, PROP_WORD_BREAK, "WordBreakProperty", bits_per_plane=16
)

_AHLetter = {WordBreakProperty.ALETTER, WordBreakProperty.HEBREW_LETTER}
_MidNumLetQ = {WordBreakProperty.MIDNUMLET, WordBreakProperty.SINGLE_QUOTE}


def _make_set[P](foo) -> P | Set[P] | None:
    match foo:
        case None:
            return None
        case str(s):
            return {s}  # type: ignore
        case _:
            return foo


type BreakRule[P: WordBreakProperty | SentenceBreakProperty] = Callable[
    [
        Sequence[tuple[str, P]],
        tuple[str, P],
        LookaheadIterator[tuple[str, P]],
    ],
    bool | None,
]


class IgnoreBreakRule[P: WordBreakProperty | SentenceBreakProperty]:
    result: bool
    left2: Set[P] | None
    left: Set[P] | None
    cur: Set[P] | None
    right: Set[P] | None
    right2: Set[P] | None
    ignores: ClassVar[Set]

    def __init__(
        self,
        result: bool,
        *,
        left2: Set[P] | P | None = None,
        left: Set[P] | P | None = None,
        cur: Set[P] | P | None = None,
        right: Set[P] | P | None = None,
        right2: Set[P] | P | None = None,
        ignore: bool = True,
    ):
        self.left2 = _make_set(left2)
        self.left = _make_set(left)
        self.cur = _make_set(cur)
        self.right = _make_set(right)
        self.right2 = _make_set(right2)
        self.result = result
        self.ignore = ignore

    def __call__(
        self,
        lookbehind: Sequence[tuple[str, P]],
        current: tuple[str, P],
        lookahead: LookaheadIterator[tuple[str, P]],
        /,
    ) -> bool | None:
        if self.cur is not None:
            if current[1] not in self.cur:
                return

        if self.left is not None:
            if not lookbehind:
                return None
            lb_iter = reversed(lookbehind)
            lp = None
            for item in lb_iter:
                c, prop_value = item
                if not self.ignore or prop_value not in self.ignores:
                    lp = item
                    break
            if lp is None:
                lp = lookbehind[0]
            if lp[1] not in self.left:
                return
            if self.left2 is not None:
                lp2 = None
                for item in lb_iter:
                    c, prop_value = item
                    if not self.ignore or prop_value not in self.ignores:
                        lp2 = item
                        break
                if lp2 is None or lp2[1] not in self.left2:
                    return

        if self.right is not None:
            i = 0
            count = 0
            rp = None
            rp2 = None
            while True:
                i += 1
                try:
                    lh = lookahead.lookahead(i)[i - 1]
                except IndexError:
                    return
                c, prop_value = lh
                if self.ignore and prop_value in self.ignores:
                    continue
                count += 1
                if count == 1:
                    rp = lh
                if self.right2 is None:
                    break
                if count == 2:
                    rp2 = lh
                    break
            if rp is None or rp[1] not in self.right:
                return
            if self.right2 is not None and (rp2 is None or rp2[1] not in self.right2):
                return
        return self.result


WB_IGNORES = {
    WordBreakProperty.EXTEND,
    WordBreakProperty.FORMAT,
    WordBreakProperty.ZWJ,
}


class WordBreakRule(IgnoreBreakRule[WordBreakProperty]):
    ignores = WB_IGNORES


WB3 = WordBreakRule(
    False, left=WordBreakProperty.CR, cur=WordBreakProperty.LF, ignore=False
)
# WB 3a, 3b Otherwise break before and after Newlines (including CR and LF)
WB3A = WordBreakRule(
    True,
    left={WordBreakProperty.NEWLINE, WordBreakProperty.CR, WordBreakProperty.LF},
    ignore=False,
)
WB3B = WordBreakRule(
    True,
    cur={WordBreakProperty.NEWLINE, WordBreakProperty.CR, WordBreakProperty.LF},
    ignore=False,
)


# WB 3c Do not break within emoji zwj sequences.
def WB3C(
    lookbehind: Sequence[tuple[str, WordBreakProperty]],
    current: tuple[str, WordBreakProperty],
    lookahead: LookaheadIterator[tuple[str, WordBreakProperty]],
    /,
) -> bool | None:
    c, _ = current
    if not is_extended_pictographic(c):
        return None
    try:
        # Check if the last code point of lookbehind is ZWJ
        if lookbehind[-1][0] == ZWJ:
            return False
    except IndexError:
        return None


# WB 3d Keep horizontal whitespace together.
WB3D = WordBreakRule(
    False,
    left=WordBreakProperty.WSEGSPACE,
    cur=WordBreakProperty.WSEGSPACE,
    ignore=False,
)

# WB 4 This also has the effect of  Any × (Format | Extend | ZWJ)
WB4 = WordBreakRule(
    False,
    cur={WordBreakProperty.FORMAT, WordBreakProperty.EXTEND, WordBreakProperty.ZWJ},
    ignore=False,
)
# WB 5 Do not break between most letters.
WB5 = WordBreakRule(False, left=_AHLetter, cur=_AHLetter)
# Do not break letters across certain punctuation, such as within “e.g.” or “example.com”.
WB6 = WordBreakRule(
    False,
    left=_AHLetter,
    cur={WordBreakProperty.MIDLETTER, *_MidNumLetQ},
    right=_AHLetter,
)
WB7 = WordBreakRule(
    False,
    left2=_AHLetter,
    left={WordBreakProperty.MIDLETTER, *_MidNumLetQ},
    cur=_AHLetter,
)
WB7A = WordBreakRule(
    False, left=WordBreakProperty.HEBREW_LETTER, cur=WordBreakProperty.SINGLE_QUOTE
)
WB7B = WordBreakRule(
    False,
    left=WordBreakProperty.HEBREW_LETTER,
    cur=WordBreakProperty.DOUBLE_QUOTE,
    right=WordBreakProperty.HEBREW_LETTER,
)
WB7C = WordBreakRule(
    False,
    left2=WordBreakProperty.HEBREW_LETTER,
    left=WordBreakProperty.DOUBLE_QUOTE,
    cur=WordBreakProperty.HEBREW_LETTER,
)
# Do not break within sequences of digits, or digits adjacent to letters (“3a”, or “A3”).
WB8 = WordBreakRule(
    False, left=WordBreakProperty.NUMERIC, cur=WordBreakProperty.NUMERIC
)
WB9 = WordBreakRule(False, left=_AHLetter, cur=WordBreakProperty.NUMERIC)
WB10 = WordBreakRule(False, left=WordBreakProperty.NUMERIC, cur=_AHLetter)

# Do not break within sequences, such as “3.2” or “3,456.789”.
WB11 = WordBreakRule(
    False,
    left2=WordBreakProperty.NUMERIC,
    left={WordBreakProperty.MIDNUM, *_MidNumLetQ},
    cur=WordBreakProperty.NUMERIC,
)
WB12 = WordBreakRule(
    False,
    left=WordBreakProperty.NUMERIC,
    cur={WordBreakProperty.MIDNUM, *_MidNumLetQ},
    right=WordBreakProperty.NUMERIC,
)
# Do not break between Katakana.
WB13 = WordBreakRule(
    False, left=WordBreakProperty.KATAKANA, cur=WordBreakProperty.KATAKANA
)
# Do not break from extenders.
WB13A = WordBreakRule(
    False,
    left={
        *_AHLetter,
        WordBreakProperty.NUMERIC,
        WordBreakProperty.KATAKANA,
        WordBreakProperty.EXTENDNUMLET,
    },
    cur=WordBreakProperty.EXTENDNUMLET,
)
WB13B = WordBreakRule(
    False,
    left=WordBreakProperty.EXTENDNUMLET,
    cur={
        *_AHLetter,
        WordBreakProperty.NUMERIC,
        WordBreakProperty.KATAKANA,
        WordBreakProperty.EXTENDNUMLET,
    },
)


def WB15_16(
    lookbehind: Sequence[tuple[str, WordBreakProperty]],
    current: tuple[str, WordBreakProperty],
    lookahead: LookaheadIterator[tuple[str, WordBreakProperty]],
) -> bool | None:
    # XXX: Unicode Word Break Test Case #1822 expects us to break across a grapheme cluster...
    
    # Source: 'a🇦\u200d🇧🇨b'
    # Graphemes: ['a', '🇦\u200d', '🇧🇨', 'b']
    # Expected Word Break: ['a', '🇦\u200d🇧', '🇨', 'b']

    # UAX #29:
    # "The other default boundary specifications never break within grapheme clusters, and they
    # always use a consistent property value for each grapheme cluster as a whole."
    
    _, cur_wb = current
    if cur_wb != WordBreakProperty.REGIONAL_INDICATOR:
        return None
    count = 0

    for cp in (h for g, _ in reversed(lookbehind) for h in reversed(g)):
        gsb2 = wb(cp)
        if gsb2 == WordBreakProperty.REGIONAL_INDICATOR:
            count += 1
        elif gsb2 in WB_IGNORES:
            continue
        else:
            break
    if count % 2:
        return False


WB999 = WordBreakRule(True)

WORD_BREAK_RULES: Sequence[BreakRule[WordBreakProperty]] = [
    WB3,
    WB3A,
    WB3B,
    WB3C,
    WB3D,
    WB4,
    WB5,
    WB6,
    WB7,
    WB7A,
    WB7B,
    WB7C,
    WB8,
    WB9,
    WB10,
    WB11,
    WB12,
    WB13,
    WB13A,
    WB13B,
    WB15_16,
    WB999,
]


sb: Callable[[str | int], SentenceBreakProperty]

SentenceBreakProperty, _sb_table, sb = get_ucd_table(
    SENTENCE_BREAK_PATH, PROP_SENTENCE_BREAK, "SentenceBreakProperty", bits_per_plane=16
)


class SentenceBreakRule(IgnoreBreakRule[SentenceBreakProperty]):
    ignores = {SentenceBreakProperty.EXTEND, SentenceBreakProperty.FORMAT}


_PARA_SEP = {
    SentenceBreakProperty.SEP,
    SentenceBreakProperty.CR,
    SentenceBreakProperty.LF,
}

SB3 = SentenceBreakRule(
    False, left=SentenceBreakProperty.CR, cur=SentenceBreakProperty.LF, ignore=False
)
# Break after paragraph separators.
SB4 = SentenceBreakRule(True, left=_PARA_SEP, ignore=False)
# This also has the effect of: Any × (Format | Extend)
SB5 = SentenceBreakRule(
    False,
    cur={SentenceBreakProperty.FORMAT, SentenceBreakProperty.EXTEND},
    ignore=False,
)
# Do not break after full stop in certain contexts.
# Break after sentence terminators, but include closing punctuation, trailing spaces, and any
# paragraph separator.
SB6 = SentenceBreakRule(
    False, left=SentenceBreakProperty.ATERM, cur=SentenceBreakProperty.NUMERIC
)
SB7 = SentenceBreakRule(
    False,
    left2={SentenceBreakProperty.UPPER, SentenceBreakProperty.LOWER},
    left=SentenceBreakProperty.ATERM,
    cur=SentenceBreakProperty.UPPER,
)
_SB8A_10_SET = {
    SentenceBreakProperty.SCONTINUE,
    SentenceBreakProperty.STERM,
    SentenceBreakProperty.ATERM,
    SentenceBreakProperty.SP,
    *_PARA_SEP,
}
_SB8_EXCLUDES = {
    SentenceBreakProperty.OLETTER,
    SentenceBreakProperty.UPPER,
    SentenceBreakProperty.LOWER,
    SentenceBreakProperty.STERM,
    SentenceBreakProperty.ATERM,
    *_PARA_SEP,
}


def SB8_8A_9_10_11(
    lookbehind: Sequence[tuple[str, SentenceBreakProperty]],
    current: tuple[str, SentenceBreakProperty],
    lookahead: LookaheadIterator[tuple[str, SentenceBreakProperty]],
) -> bool | None:
    history = set()
    state = SentenceBreakProperty.SP
    for _, gsb in reversed(lookbehind):
        history.add(gsb)
        match state, gsb:
            case SentenceBreakProperty.SP, (
                SentenceBreakProperty.SP
                | SentenceBreakProperty.EXTEND
                | SentenceBreakProperty.FORMAT
            ):
                continue
            case SentenceBreakProperty.CLOSE, (
                SentenceBreakProperty.CLOSE
                | SentenceBreakProperty.EXTEND
                | SentenceBreakProperty.FORMAT
            ):
                continue
            case SentenceBreakProperty.SP, SentenceBreakProperty.CLOSE:
                state = gsb
                continue
            case (
                SentenceBreakProperty.SP | SentenceBreakProperty.CLOSE,
                SentenceBreakProperty.ATERM | SentenceBreakProperty.STERM,
            ):
                state = gsb
                break
            case _:
                return None
    else:
        return None
    cur, cur_sb = current
    # SB8A and SB10
    if cur_sb in _SB8A_10_SET:
        return False
    # SB9 residual case
    if (
        SentenceBreakProperty.SP not in history
        and cur_sb == SentenceBreakProperty.CLOSE
    ):
        return False
    # SB8
    if state == SentenceBreakProperty.STERM:
        return True
    # FIXME: don't consume the lookahead iterator
    next_props = chain((cur_sb,), (p for _, p in lookahead.lookahead(-1)))
    for prop in next_props:
        if prop == SentenceBreakProperty.LOWER:
            return False
        elif prop in _SB8_EXCLUDES:
            return True
    # SB11
    return True


SB999 = SentenceBreakRule(False)
SENTENCE_BREAK_RULES: Sequence[BreakRule] = [
    SB3,
    SB4,
    SB5,
    SB6,
    SB7,
    SB8_8A_9_10_11,
    SB999,
]


def default_break_impl[P: WordBreakProperty | SentenceBreakProperty](
    s: Iterable[str] | str,
    /,
    rules: Sequence[BreakRule[P]],
    prop_fn: Callable[[str], P],
) -> Iterable[Sequence[str]]:
    it = LookaheadIterator((c, prop_fn(c[0])) for c in s)
    lookbehinds: deque[tuple[str, P]] = deque()
    for current in it:
        should_break = True
        for rule in rules:
            result = rule(lookbehinds, current, it)
            if result is not None:
                should_break = result
                break
        if should_break and lookbehinds:
            yield [g for g, _ in lookbehinds]
            lookbehinds.clear()
        lookbehinds.append(current)
    if lookbehinds:
        yield [g for g, _ in lookbehinds]


def default_word_break(s: Iterable[str] | str, /) -> Iterable[str]:
    return [
        "".join(w) for w in default_break_impl(s, rules=WORD_BREAK_RULES, prop_fn=wb)
    ]


def default_sentence_break(s: Iterable[str] | str, /) -> Iterable[str]:
    return [
        "".join(w)
        for w in default_break_impl(s, rules=SENTENCE_BREAK_RULES, prop_fn=sb)
    ]


def grapheme_break(s: str, /, *, locale=ROOT_LOCALE) -> Iterable[Grapheme]:
    try:
        from icu4py.breakers import CharacterBreaker
    except ImportError:
        return unicodedata.iter_graphemes(s)  # type: ignore
    else:
        return cast(Iterable[Grapheme], CharacterBreaker(s, locale=locale))


def word_break(s: str, /, *, locale=ROOT_LOCALE) -> Iterable[str]:
    try:
        from icu4py.breakers import WordBreaker
    except ImportError:
        return default_word_break(s)
    else:
        return WordBreaker(s, locale=locale)


def sentence_break(s: str, /, *, locale=ROOT_LOCALE) -> Iterable[str]:
    try:
        from icu4py.breakers import SentenceBreaker
    except ImportError:
        return default_sentence_break(s)
    else:
        return SentenceBreaker(s, locale=locale)
