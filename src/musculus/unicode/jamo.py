"""Implements algorithmic Conjoining Jamo Behavior.
This is another example of hardcoded data guaranteed by Unicode Stability Policy.
"""

from collections.abc import Mapping
from typing import cast

from .util import LooseMatchStrEnum

# Precomposed syllables
SBASE = 0xAC00
SCOUNT = 11172
LBASE = 0x1100
VBASE = 0x1161
TBASE = 0x11A7
LCOUNT = 19
VCOUNT = 21
TCOUNT = 28
NCOUNT = 588

SLAST = SBASE + SCOUNT - 1


# JSN
# This is an exceptional contributory property
class JamoShortName(LooseMatchStrEnum):
    A = "A"
    AE = "AE"
    B = "B"
    BB = "BB"
    BS = "BS"
    C = "C"
    D = "D"
    DD = "DD"
    E = "E"
    EO = "EO"
    EU = "EU"
    G = "G"
    GG = "GG"
    GS = "GS"
    H = "H"
    I = "I"
    J = "J"
    JJ = "JJ"
    K = "K"
    L = "L"
    LB = "LB"
    LG = "LG"
    LH = "LH"
    LM = "LM"
    LP = "LP"
    LS = "LS"
    LT = "LT"
    M = "M"
    N = "N"
    NG = "NG"
    NH = "NH"
    NJ = "NJ"
    O = "O"
    OE = "OE"
    P = "P"
    R = "R"
    S = "S"
    SS = "SS"
    T = "T"
    U = "U"
    WA = "WA"
    WAE = "WAE"
    WE = "WE"
    WEO = "WEO"
    WI = "WI"
    YA = "YA"
    YAE = "YAE"
    YE = "YE"
    YEO = "YEO"
    YI = "YI"
    YO = "YO"
    YU = "YU"


JAMO_SHORT_NAME = {
    0x1100: JamoShortName.G,
    0x1101: JamoShortName.GG,
    0x1102: JamoShortName.N,
    0x1103: JamoShortName.D,
    0x1104: JamoShortName.DD,
    0x1105: JamoShortName.R,
    0x1106: JamoShortName.M,
    0x1107: JamoShortName.B,
    0x1108: JamoShortName.BB,
    0x1109: JamoShortName.S,
    0x110A: JamoShortName.SS,
    # 0x110B: ""    ,
    0x110C: JamoShortName.J,
    0x110D: JamoShortName.JJ,
    0x110E: JamoShortName.C,
    0x110F: JamoShortName.K,
    0x1110: JamoShortName.T,
    0x1111: JamoShortName.P,
    0x1112: JamoShortName.H,
    0x1161: JamoShortName.A,
    0x1162: JamoShortName.AE,
    0x1163: JamoShortName.YA,
    0x1164: JamoShortName.YAE,
    0x1165: JamoShortName.EO,
    0x1166: JamoShortName.E,
    0x1167: JamoShortName.YEO,
    0x1168: JamoShortName.YE,
    0x1169: JamoShortName.O,
    0x116A: JamoShortName.WA,
    0x116B: JamoShortName.WAE,
    0x116C: JamoShortName.OE,
    0x116D: JamoShortName.YO,
    0x116E: JamoShortName.U,
    0x116F: JamoShortName.WEO,
    0x1170: JamoShortName.WE,
    0x1171: JamoShortName.WI,
    0x1172: JamoShortName.YU,
    0x1173: JamoShortName.EU,
    0x1174: JamoShortName.YI,
    0x1175: JamoShortName.I,
    0x11A8: JamoShortName.G,
    0x11A9: JamoShortName.GG,
    0x11AA: JamoShortName.GS,
    0x11AB: JamoShortName.N,
    0x11AC: JamoShortName.NJ,
    0x11AD: JamoShortName.NH,
    0x11AE: JamoShortName.D,
    0x11AF: JamoShortName.L,
    0x11B0: JamoShortName.LG,
    0x11B1: JamoShortName.LM,
    0x11B2: JamoShortName.LB,
    0x11B3: JamoShortName.LS,
    0x11B4: JamoShortName.LT,
    0x11B5: JamoShortName.LP,
    0x11B6: JamoShortName.LH,
    0x11B7: JamoShortName.M,
    0x11B8: JamoShortName.B,
    0x11B9: JamoShortName.BS,
    0x11BA: JamoShortName.S,
    0x11BB: JamoShortName.SS,
    0x11BC: JamoShortName.NG,
    0x11BD: JamoShortName.J,
    0x11BE: JamoShortName.C,
    0x11BF: JamoShortName.K,
    0x11C0: JamoShortName.T,
    0x11C1: JamoShortName.P,
    0x11C2: JamoShortName.H,
}


def is_jamo_syllable(s: int, /) -> bool:
    return SBASE <= s <= SLAST


def syllable_index(s: int, /) -> int:
    return s - SBASE


def decomposition_mapping(s: int) -> tuple[int, int]:
    s_index = s - SBASE
    if not 0 <= s_index < SCOUNT:
        raise ValueError(f"Not a Hangul syllable: U+{s:04X}")
    t_index = s_index % TCOUNT

    if t_index:
        _lv, t_index = divmod(s_index, TCOUNT)
        lv_index = _lv * TCOUNT

        lv_part = SBASE + lv_index
        t_part = TBASE + t_index
        return (lv_part, t_part)
    else:
        l_index, _v = divmod(s_index, NCOUNT)
        v_index = _v // TCOUNT

        l_part = LBASE + l_index
        v_part = VBASE + v_index
        return (l_part, v_part)


def full_canonical_decomposition(
    s: int,
) -> tuple[int, int] | tuple[int, int, int]:
    s_index = s - SBASE
    if not 0 <= s_index < SCOUNT:
        raise ValueError(f"Not a Hangul syllable: U+{s:04X}")
    l_index, _v = divmod(s_index, NCOUNT)
    v_index = _v // TCOUNT
    t_index = s_index % TCOUNT

    l_part = LBASE + l_index
    v_part = VBASE + v_index
    if t_index > 0:
        t_part = TBASE + t_index
        return (l_part, v_part, t_part)
    return (l_part, v_part)


def primary_composite_mapping(l_part: int, v_part: int, t_part: int = TBASE) -> int:
    l_index = l_part - LBASE
    v_index = v_part - VBASE
    lv_index = l_index * NCOUNT + v_index * TCOUNT
    t_index = t_part - TBASE
    result = SBASE + lv_index + t_index
    if not 0 <= result < SCOUNT:
        raise ValueError(f"Not a Hangul syllable: U+{result:04X}")
    return result


def _name(parts) -> str:
    # parts = full_canonical_decomposition(s)
    o = ["HANGUL SYLLABLE "]
    for part in parts:
        o.append(JAMO_SHORT_NAME.get(part, ""))
    return "".join(o)


JAMO_NAMES = {}
JAMO_DECOMPOSITION_MAPPINGS = {}
JAMO_FULL_DECOMPOSITION_MAPPINGS = {}
JAMO_DECOMPOSITION_TYPE = {SBASE: "Can"}
JAMO_PRIMARY_COMPOSITE_PAIRWISE: Mapping[tuple[int, int], int] = {}

for cp in map(int, range(SBASE, SBASE + SCOUNT)):
    parts = full_canonical_decomposition(cp)
    JAMO_NAMES[cp] = _name(parts)
    dm = decomposition_mapping(cp)
    JAMO_DECOMPOSITION_MAPPINGS[cp] = dm
    JAMO_PRIMARY_COMPOSITE_PAIRWISE[dm] = cp
    JAMO_FULL_DECOMPOSITION_MAPPINGS[cp] = parts
