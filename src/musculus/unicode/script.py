from collections.abc import Container, Iterable, Sequence, Set
from functools import lru_cache
from typing import TYPE_CHECKING
from unicodedata import category

from musculus.util.parse import LooseMatchStrEnum, to_code_point

from .invariants import PROP_SCRIPT
from .segmentation import Grapheme, Word
from ..resources.ucd import SCRIPT_EXTENSIONS_PATH, SCRIPTS_PATH
from ..util.ucd import get_ucd_table, ucd_tokenize

type SCXSet = Set[ScriptProperty]

# NOTE: There are more script subtags in the Language Subtag Registry than in UCD PVA.
# Reconciling the two without circular imports is difficult and not worth the effort.
# (Language Subtag Registry contains way too many things to make enums with)

# Fortunately both ScriptSubtag and ScriptProperty are subtypes of string,
# and as long as ScriptSubtag("Xxxx") == ScriptProperty("Xxxx"), we're happy.

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


ScriptProperty, _sc_table, sc = get_ucd_table(
    SCRIPTS_PATH,
    PROP_SCRIPT,
    "ScriptProperty",
    bits_per_plane=14,
    compress=[(0x20000, 0x3FFFF)],
)

# Unicode regular expressions have this form:
# ((Greek | Common) (Inherited | Me | Mn)*)*
def script_breaker(s: str, /, scripts: Container[ScriptProperty]) -> Iterable[str]:
    """Implements the most common form of Unicode regular expression:
    `((scripts | Common) (Inherited | Me | Mn)*)*`"""
    buf = []
    for c in s:
        script = sc(c)
        cat = category(c)
        if script in scripts or script == ScriptProperty.COMMON:
            buf.append(c)
        elif buf and (script == ScriptProperty.INHERITED or cat == "Me" or cat == "Mn"):
            buf.append(c)
        else:
            if buf:
                yield "".join(buf)
                buf.clear()
            yield c
    if buf:
        yield "".join(buf)


SCX_COMMON: SCXSet = frozenset({ScriptProperty.COMMON})
SCX_INHERITED: SCXSet = frozenset({ScriptProperty.INHERITED})
SCX_UNKNOWN: SCXSet = frozenset({ScriptProperty.UNKNOWN})

# Since only a very small number of code points have explicit scx listings in the file,
# we can implement _scx as a simple dict
_scx: dict[int, SCXSet] = {}

def _read_ucd_scx():
    # scx file is special
    with SCRIPT_EXTENSIONS_PATH.open("r", encoding="utf-8", errors="strict") as scx_txt:
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

def scx_set(c: str | int, /) -> SCXSet:
    """
    Gets the Scx Set (https://www.unicode.org/reports/tr24/#Script_Extensions) of a code point.
    If there are explicit scx values in the data file,
    Otherwise, the explicit (or implicit) sc value is returned as a set."""
    cp = to_code_point(c)
    if cp in _scx:
        # LBYL, because most code points are not in _scx
        return _scx[cp]
    return {sc(cp)}


@lru_cache
def scx_set_grapheme(grapheme: Grapheme, /) -> SCXSet:
    """Operates on a grapheme, and returns its scx set as recommended by UAX #24 Section 5.2."""

    # UAX #24 Section 5.2 (https://www.unicode.org/reports/tr24/#Nonspacing_Marks)
    # "The recommended implementation strategy is to treat all the characters of a combining character sequence,
    # including spacing combining marks, as having the Script property value of the first character in the sequence.
    # This strategy can also be applied to implementations that use extended grapheme clusters; the differences between
    # combining character sequences and extended grapheme clusters are not material for script resolution...
    # Because of this recommended strategy, even if a combining mark is really only used with a single script,
    # it makes little difference in practice whether the mark has that particular Script property value or Inherited.

    is_inherited = False
    for i, c in enumerate(grapheme):
        x = scx_set(c)
        if x == SCX_INHERITED:
            if i == 0:
                is_inherited = True
        elif x != SCX_COMMON:
            return x
    # If the sequence starts with inherited and contains no non-inherited/non-common, return inherited
    return SCX_INHERITED if is_inherited else SCX_COMMON


def scx_set_word(word: Word, /) -> SCXSet:
    """Operates on the multiple graphemes in one single word.
    Returns the applicable scx sets, narrowed by each grapheme cluster.
    """
    scx_sets: list[set[ScriptProperty]] = [set()]
    fallback_inherit = True
    for grapheme in word:
        word_scx = scx_sets[-1]
        grapheme_scx = scx_set_grapheme(grapheme)
        if grapheme_scx == SCX_COMMON:
            # Common grapheme can occur in isolation and should not affect the result.
            fallback_inherit = False
        elif grapheme_scx == SCX_INHERITED:
            # Inherited grapheme should normally not occur in isolation, but if it ever does,
            # it should also not affect the result.
            pass
        elif not word_scx:
            # We're the first grapheme to have a "real" scx set
            word_scx.update(grapheme_scx)
        else:
            overlap = word_scx.intersection(grapheme_scx)
            if overlap:
                # The word scx set is narrowed by the new grapheme
                word_scx = overlap
            else:
                # The word contains graphemes with multiple disjoint scx sets
                scx_sets.append(set(grapheme_scx))
    if not scx_sets[0]:
        # XXX: This has the effect of the pathological empty word returning SCX_INHERITED
        # which is probably the useful behavior
        return SCX_INHERITED if fallback_inherit else SCX_COMMON
    return scx_sets[0].union(*scx_sets)


multiscript_heuristics = {
    "ja": {ScriptProperty.HIRAGANA, ScriptProperty.KATAKANA, ScriptProperty.HAN},
}


def scx_word_grouper(words: Iterable[Word], /) -> Iterable[tuple[SCXSet, Sequence[Word]]]:
    group = []
    group_scx = SCX_COMMON
    for word in words:
        scx = scx_set_word(word)
        if scx == SCX_COMMON or scx == SCX_INHERITED:
            pass
        elif group_scx == SCX_COMMON:
            group_scx = scx
        else:
            for lang, rule in multiscript_heuristics.items():
                scx1 = rule.intersection(group_scx)
                scx2 = rule.intersection(scx)
                if scx1 and scx2:
                    group_scx = {*scx1, *scx2}
                    break
            else:
                if group_scx.isdisjoint(scx):
                    if group:
                        yield group_scx, group
                        group = []
                    group_scx = scx
                else:
                    group_scx = set(scx).intersection(group_scx)
        group.append(word)
    if group:
        yield group_scx, group
