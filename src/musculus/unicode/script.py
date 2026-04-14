from array import array
from collections.abc import Callable, Iterable, Set
from typing import TYPE_CHECKING

from ..resources.ucd import PVA_PATH, SCRIPT_EXTENSIONS_PATH, SCRIPTS_PATH
from .combining import combining_character_sequence
from .util import (
    MAX_UNICODE,
    LooseMatchStrEnum,
    TwoStageTable,
    dict_from_pva,
    to_code_point,
    ucd_tokenize,
)

if TYPE_CHECKING:

    class ScriptProperty(LooseMatchStrEnum):
        ADLAM = "Adlm"
        CAUCASIAN_ALBANIAN = "Aghb"
        AHOM = "Ahom"
        ARABIC = "Arab"
        IMPERIAL_ARAMAIC = "Armi"
        ARMENIAN = "Armn"
        AVESTAN = "Avst"
        BALINESE = "Bali"
        BAMUM = "Bamu"
        BASSA_VAH = "Bass"
        BATAK = "Batk"
        BENGALI = "Beng"
        BERIA_ERFE = "Berf"
        BHAIKSUKI = "Bhks"
        BOPOMOFO = "Bopo"
        BRAHMI = "Brah"
        BRAILLE = "Brai"
        BUGINESE = "Bugi"
        BUHID = "Buhd"
        CHAKMA = "Cakm"
        CANADIAN_ABORIGINAL = "Cans"
        CARIAN = "Cari"
        CHAM = "Cham"
        CHEROKEE = "Cher"
        CHORASMIAN = "Chrs"
        COPTIC = QAAC = "Copt"
        CYPRO_MINOAN = "Cpmn"
        CYPRIOT = "Cprt"
        CYRILLIC = "Cyrl"
        DEVANAGARI = "Deva"
        DIVES_AKURU = "Diak"
        DOGRA = "Dogr"
        DESERET = "Dsrt"
        DUPLOYAN = "Dupl"
        EGYPTIAN_HIEROGLYPHS = "Egyp"
        ELBASAN = "Elba"
        ELYMAIC = "Elym"
        ETHIOPIC = "Ethi"
        GARAY = "Gara"
        GEORGIAN = "Geor"
        GLAGOLITIC = "Glag"
        GUNJALA_GONDI = "Gong"
        MASARAM_GONDI = "Gonm"
        GOTHIC = "Goth"
        GRANTHA = "Gran"
        GREEK = "Grek"
        GUJARATI = "Gujr"
        GURUNG_KHEMA = "Gukh"
        GURMUKHI = "Guru"
        HANGUL = "Hang"
        HAN = "Hani"
        HANUNOO = "Hano"
        HATRAN = "Hatr"
        HEBREW = "Hebr"
        HIRAGANA = "Hira"
        ANATOLIAN_HIEROGLYPHS = "Hluw"
        PAHAWH_HMONG = "Hmng"
        NYIAKENG_PUACHUE_HMONG = "Hmnp"
        KATAKANA_OR_HIRAGANA = "Hrkt"
        OLD_HUNGARIAN = "Hung"
        OLD_ITALIC = "Ital"
        JAVANESE = "Java"
        KAYAH_LI = "Kali"
        KATAKANA = "Kana"
        KAWI = "Kawi"
        KHAROSHTHI = "Khar"
        KHMER = "Khmr"
        KHOJKI = "Khoj"
        KHITAN_SMALL_SCRIPT = "Kits"
        KANNADA = "Knda"
        KIRAT_RAI = "Krai"
        KAITHI = "Kthi"
        TAI_THAM = "Lana"
        LAO = "Laoo"
        LATIN = "Latn"
        LEPCHA = "Lepc"
        LIMBU = "Limb"
        LINEAR_A = "Lina"
        LINEAR_B = "Linb"
        LISU = "Lisu"
        LYCIAN = "Lyci"
        LYDIAN = "Lydi"
        MAHAJANI = "Mahj"
        MAKASAR = "Maka"
        MANDAIC = "Mand"
        MANICHAEAN = "Mani"
        MARCHEN = "Marc"
        MEDEFAIDRIN = "Medf"
        MENDE_KIKAKUI = "Mend"
        MEROITIC_CURSIVE = "Merc"
        MEROITIC_HIEROGLYPHS = "Mero"
        MALAYALAM = "Mlym"
        MODI = "Modi"
        MONGOLIAN = "Mong"
        MRO = "Mroo"
        MEETEI_MAYEK = "Mtei"
        MULTANI = "Mult"
        MYANMAR = "Mymr"
        NAG_MUNDARI = "Nagm"
        NANDINAGARI = "Nand"
        OLD_NORTH_ARABIAN = "Narb"
        NABATAEAN = "Nbat"
        NEWA = "Newa"
        NKO = "Nkoo"
        NUSHU = "Nshu"
        OGHAM = "Ogam"
        OL_CHIKI = "Olck"
        OL_ONAL = "Onao"
        OLD_TURKIC = "Orkh"
        ORIYA = "Orya"
        OSAGE = "Osge"
        OSMANYA = "Osma"
        OLD_UYGHUR = "Ougr"
        PALMYRENE = "Palm"
        PAU_CIN_HAU = "Pauc"
        OLD_PERMIC = "Perm"
        PHAGS_PA = "Phag"
        INSCRIPTIONAL_PAHLAVI = "Phli"
        PSALTER_PAHLAVI = "Phlp"
        PHOENICIAN = "Phnx"
        MIAO = "Plrd"
        INSCRIPTIONAL_PARTHIAN = "Prti"
        REJANG = "Rjng"
        HANIFI_ROHINGYA = "Rohg"
        RUNIC = "Runr"
        SAMARITAN = "Samr"
        OLD_SOUTH_ARABIAN = "Sarb"
        SAURASHTRA = "Saur"
        SIGNWRITING = "Sgnw"
        SHAVIAN = "Shaw"
        SHARADA = "Shrd"
        SIDDHAM = "Sidd"
        SIDETIC = "Sidt"
        KHUDAWADI = "Sind"
        SINHALA = "Sinh"
        SOGDIAN = "Sogd"
        OLD_SOGDIAN = "Sogo"
        SORA_SOMPENG = "Sora"
        SOYOMBO = "Soyo"
        SUNDANESE = "Sund"
        SUNUWAR = "Sunu"
        SYLOTI_NAGRI = "Sylo"
        SYRIAC = "Syrc"
        TAGBANWA = "Tagb"
        TAKRI = "Takr"
        TAI_LE = "Tale"
        NEW_TAI_LUE = "Talu"
        TAMIL = "Taml"
        TANGUT = "Tang"
        TAI_VIET = "Tavt"
        TAI_YO = "Tayo"
        TELUGU = "Telu"
        TIFINAGH = "Tfng"
        TAGALOG = "Tglg"
        THAANA = "Thaa"
        THAI = "Thai"
        TIBETAN = "Tibt"
        TIRHUTA = "Tirh"
        TANGSA = "Tnsa"
        TODHRI = "Todr"
        TOLONG_SIKI = "Tols"
        TOTO = "Toto"
        TULU_TIGALARI = "Tutg"
        UGARITIC = "Ugar"
        VAI = "Vaii"
        VITHKUQI = "Vith"
        WARANG_CITI = "Wara"
        WANCHO = "Wcho"
        OLD_PERSIAN = "Xpeo"
        CUNEIFORM = "Xsux"
        YEZIDI = "Yezi"
        YI = "Yiii"
        ZANABAZAR_SQUARE = "Zanb"
        INHERITED = QAAI = "Zinh"
        COMMON = "Zyyy"
        UNKNOWN = "Zzzz"

    # Typecode for array storage
    _typecode = "B"
else:
    with PVA_PATH.open("r", encoding="utf-8", errors="strict") as pva:
        ScriptProperty = LooseMatchStrEnum("ScriptProperty", dict_from_pva(pva, "sc"))

_SCRIPT_PROP_LIST = list(ScriptProperty)
_SCRIPT_PROP_INDICES = {v: i for i, v in enumerate(_SCRIPT_PROP_LIST)}
if not TYPE_CHECKING:
    _typecode = "B" if len(_SCRIPT_PROP_LIST) <= 256 else "H"
_SC_UNKNOWN_INDEX = _SCRIPT_PROP_INDICES[ScriptProperty.UNKNOWN]
_SC_SCX_SETS = [frozenset({sc}) for sc in ScriptProperty]

# Performance tuning of the two-stage table
# Each plane officially has 65536 code points
# The more bits per plane, the faster the lookup performance tends to be
# but also the more space wasted

# _BITS_PER_PLANE : sum(getsizeof(x) for x in _SC_ARRAYS.values())
# The storage efficiency depends on the Unicode version
# For UCD 17.0:
# 21: 2097232 bytes
# 20: 1048656 bytes
# 19: 1048376 bytes
# 18:  524448 bytes
# 17:  393456 bytes
# 16:  328080 bytes
# 15:  262784 bytes
# 14:  230496 bytes
# 14 compressed: 197568 bytes
# 13:  223344 bytes
# 12:  208800 bytes
# 11:  195776 bytes
# 10:  193200 bytes
#  9:  201280 bytes
#  8:  223440 bytes

_BITS_PER_PLANE = 14
_tst = TwoStageTable(
    default=_SC_UNKNOWN_INDEX, bits_per_plane=_BITS_PER_PLANE, typecode=_typecode
)


def sc(c: str | int, /) -> ScriptProperty:
    return _SCRIPT_PROP_LIST[_tst[c]]


def _read_ucd_sc():
    with SCRIPTS_PATH.open("r", encoding="utf-8", errors="strict") as sc_txt:
        for token in ucd_tokenize(sc_txt, keep_missing_lines=False):
            code_points, script = token
            script_prop = ScriptProperty(script)
            s, dots, e = code_points.partition("..")
            start_cp = int(s, base=16)
            if dots:
                end_cp = int(e, base=16)
            else:
                end_cp = start_cp
            _tst.insert(start_cp, end_cp, _SCRIPT_PROP_INDICES[script_prop])


_read_ucd_sc()
_tst.compress_planes(0x20000, 0x38FFF)

SCX_COMMON = frozenset({ScriptProperty.COMMON})
SCX_INHERITED = frozenset({ScriptProperty.INHERITED})
SCX_UNKNOWN = frozenset({ScriptProperty.UNKNOWN})

# Only a very small number of code points have scx listings in the file
# Hence, we implement _scx as a flat map
_scx: dict[int, Set[ScriptProperty]] = {}


def _read_ucd_scx():
    with SCRIPT_EXTENSIONS_PATH.open("r", encoding="utf-8", errors="strict") as scx_txt:
        ucd_tokenize(scx_txt)
        for token in ucd_tokenize(scx_txt, keep_missing_lines=False):
            code_points, scx = token
            scx_prop = {ScriptProperty(s) for s in scx.strip().split()}
            s, dots, e = code_points.partition("..")
            start_cp = int(s, base=16)
            if dots:
                end_cp = int(e, base=16)
            else:
                end_cp = start_cp
            for cp in range(start_cp, end_cp + 1):
                _scx[cp] = scx_prop


_read_ucd_scx()


def scx_set(c: str | int, /) -> Set[ScriptProperty]:
    """
    Gets the Scx Set (https://www.unicode.org/reports/tr24/#Script_Extensions) of a code point.
    If there are explicit scx values in the data file,
    Otherwise, the explicit (or implicit) sc value is returned as a set."""
    cp = to_code_point(c)
    if cp in _scx:
        # LBYL, because most code points are not in _scx
        return _scx[cp]
    return _SC_SCX_SETS[_tst[c]]


def scx_set_grapheme(grapheme: str, /) -> Set[ScriptProperty]:
    """Operates on a grapheme, and returns its scx set as recommended by UAX #24 Section 5.2."""

    # UAX #24 Section 5.2 (https://www.unicode.org/reports/tr24/#Nonspacing_Marks)
    # "The recommended implementation strategy is to treat all the characters of a combining character sequence,
    # including spacing combining marks, as having the Script property value of the first character in the sequence.
    # This strategy can also be applied to implementations that use extended grapheme clusters; the differences between
    # combining character sequences and extended grapheme clusters are not material for script resolution...
    # Because of this recommended strategy, even if a combining mark is really only used with a single script,
    # it makes little difference in practice whether the mark has that particular Script property value or Inherited."
    scx = SCX_COMMON
    for c in grapheme:
        x = scx_set(c)
        if x != SCX_COMMON and x != SCX_INHERITED:
            scx = x
            break
    return scx

# def scx_set_text(graphemes: Iterable[str]) -> Iterable[tuple[str, Set[ScriptProperty]]]:
    
#     for grapheme in graphemes:
#         ...