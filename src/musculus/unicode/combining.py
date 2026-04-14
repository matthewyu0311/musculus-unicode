from collections.abc import Iterable
from unicodedata import category

from .invariants import ZWJ, ZWNJ

"""
3.6.1 Combining Character Sequences

https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-3/#G37196
D50 Graphic character: A character with the General Category of Letter (L), 
Combining Mark (M), Number (N), Punctuation (P), Symbol (S), or Space Separator (Zs).
D51 Base character: Any graphic character except for those with the General Category of Combining Mark (M).
"""


def combining_character_sequence(s: str) -> Iterable[str]:
    """Combining character sequence: A maximal character sequence consisting of either a base character followed by
    a sequence of one or more characters where each is a combining character, ZERO WIDTH JOINER, or ZERO WIDTH NON-JOINER;
    or a sequence of one or more characters where each is a combining character, ZERO WIDTH JOINER, or ZERO WIDTH NON-JOINER.
    """
    ccs = []
    for ch in s:
        cat = category(ch)
        is_combining_mark = cat in {"Mc", "Mn", "Me"}
        is_zwj_zwnj = ch == ZWJ or ch == ZWNJ
        if (is_combining_mark or is_zwj_zwnj) and ccs:
            # continue the CCS
            ccs.append(ch)
        else:
            # "Any character other than a combining mark (gc=M), ZWJ, or ZWNJ interrupts the combining character sequence."
            if ccs:
                yield "".join(ccs)
                ccs.clear()
            is_base_char = cat[0] in "LNPS" or cat == "Zs"
            if is_base_char or is_combining_mark or is_zwj_zwnj:
                ccs.append(ch)
            else:
                # Non-graphic/ZWJ/ZWNJ characters always yield themselves; they don't form part of CCS
                yield ch
    if ccs:
        yield "".join(ccs)

def combining_character_sequence_extended(s: str) -> Iterable[str]:
    """This function takes into account conjoining Jamo behavior.
    """
    ccs = []
    for ch in s:
        cat = category(ch)
        is_combining_mark = cat in {"Mc", "Mn", "Me"}
        is_zwj_zwnj = ch == ZWJ or ch == ZWNJ
        if (is_combining_mark or is_zwj_zwnj) and ccs:
            # continue the CCS
            ccs.append(ch)
        else:
            if ccs:
                yield "".join(ccs)
                ccs.clear()
            is_base_char = cat[0] in "LNPS" or cat == "Zs"
            # TODO check if CCS is standard Korean syllable block
            if is_base_char or is_combining_mark or is_zwj_zwnj:
                ccs.append(ch)
            else:
                yield ch
    if ccs:
        yield "".join(ccs)

