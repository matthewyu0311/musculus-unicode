from collections.abc import Mapping, Sequence
from sys import intern
from typing import Literal, NewType, NotRequired, TypedDict, cast

from musculus.util.parse import WellFormednessError

ScopeField = Literal[
    "individual", "macrolanguage", "collection", "special", "private-use"
]
SubtagTypeField = Literal[
    "language", "extlang", "script", "region", "variant", "grandfathered", "redundant"
]

TypeField = Literal["language", "extlang", "script", "region", "variant", "extension"]
GrandfatheredKey = Literal[
    "art-lojban",
    "cel-gaulish",
    "en-GB-oed",
    "i-ami",
    "i-bnn",
    "i-default",
    "i-enochian",
    "i-hak",
    "i-klingon",
    "i-lux",
    "i-mingo",
    "i-navajo",
    "i-pwn",
    "i-tao",
    "i-tay",
    "i-tsu",
    "no-bok",
    "no-nyn",
    "sgn-BE-FR",
    "sgn-BE-NL",
    "sgn-CH-DE",
    "zh-guoyu",
    "zh-hakka",
    "zh-min",
    "zh-min-nan",
    "zh-xiang",
]
RedundantTag = Literal[
    "az-Arab",
    "az-Cyrl",
    "az-Latn",
    "be-Latn",
    "bs-Cyrl",
    "bs-Latn",
    "de-1901",
    "de-1996",
    "de-AT-1901",
    "de-AT-1996",
    "de-CH-1901",
    "de-CH-1996",
    "de-DE-1901",
    "de-DE-1996",
    "en-boont",
    "en-scouse",
    "es-419",
    "iu-Cans",
    "iu-Latn",
    "mn-Cyrl",
    "mn-Mong",
    "sgn-BR",
    "sgn-CO",
    "sgn-DE",
    "sgn-DK",
    "sgn-ES",
    "sgn-FR",
    "sgn-GB",
    "sgn-GR",
    "sgn-IE",
    "sgn-IT",
    "sgn-JP",
    "sgn-MX",
    "sgn-NI",
    "sgn-NL",
    "sgn-NO",
    "sgn-PT",
    "sgn-SE",
    "sgn-US",
    "sgn-ZA",
    "sl-nedis",
    "sl-rozaj",
    "sr-Cyrl",
    "sr-Latn",
    "tg-Arab",
    "tg-Cyrl",
    "uz-Cyrl",
    "uz-Latn",
    "yi-Latn",
    "zh-cmn",
    "zh-cmn-Hans",
    "zh-cmn-Hant",
    "zh-gan",
    "zh-Hans",
    "zh-Hans-CN",
    "zh-Hans-HK",
    "zh-Hans-MO",
    "zh-Hans-SG",
    "zh-Hans-TW",
    "zh-Hant",
    "zh-Hant-CN",
    "zh-Hant-HK",
    "zh-Hant-MO",
    "zh-Hant-SG",
    "zh-Hant-TW",
    "zh-wuu",
]


LanguageSubtag = NewType("LanguageSubtag", str)
ScriptSubtag = NewType("ScriptSubtag", str)
RegionSubtag = NewType("RegionSubtag", str)
VariantSubtag = NewType("VariantSubtag", str)
ExtensionSubtag = NewType("ExtensionSubtag", str)


###########################################################

# Unicode Technical Standard #35 CLDR special codes

LANGUAGE_UNDETERMINED = LanguageSubtag("und")
SCRIPT_ZAWGYI = ScriptSubtag("Qaag")  # Code for inherited script
SCRIPT_INHERITED_DEPRECATED = ScriptSubtag("Qaai")  # CLDR special value
SCRIPT_INHERITED = ScriptSubtag("Zinh")  # Code for inherited script
SCRIPT_EMOJI_VARIANT = ScriptSubtag("Zsye")  # Symbols (Emoji variant)
SCRIPT_SYMBOLS = ScriptSubtag("Zsym")  # Symbols
SCRIPT_UNWRITTEN = ScriptSubtag("Zxxx")  # Code for unwritten documents
SCRIPT_COMMON = SCRIPT_UNDETERMINED = ScriptSubtag("Zyyy")  # Code for undetermined script
SCRIPT_UNKNOWN = SCRIPT_UNCODED = ScriptSubtag("Zzzz")  # Code for uncoded script
REGION_UNKNOWN = RegionSubtag("ZZ")

###########################################################
# Legacy tags
###########################################################

GRANDFATHERED_TAGS = cast(Sequence[GrandfatheredKey], GrandfatheredKey.__args__)
GRANDFATHERED_CF: Mapping[str, GrandfatheredKey] = {
    k.casefold(): k for k in GRANDFATHERED_TAGS
}

REDUNDANT_TAGS = cast(Sequence[RedundantTag], RedundantTag.__args__)
# There is no need to casefold redundant tags

PRIVATE_USE_LANGUAGE = {
    "Description": "Private use",
    "Added": "2005-10-16",
    "Scope": "private-use",
}

PRIVATE_USE_SCRIPT_REGION = {"Description": "Private use", "Added": "2005-10-16"}


def is_private_language(subtag) -> LanguageSubtag | Literal[False]:
    lang = subtag.casefold()
    if "qaa" <= lang <= "qtz":
        return LanguageSubtag(lang)
    return False


def is_private_script(subtag) -> ScriptSubtag | Literal[False]:
    script = subtag.title()
    if "Qaaa" <= script <= "Qabx":
        return ScriptSubtag(script)
    return False


def is_private_region(subtag) -> RegionSubtag | Literal[False]:
    region = subtag.upper()
    return (
        RegionSubtag(region)
        if (
            region == "AA"
            or region == "ZZ"
            or "QM" <= region <= "QZ"
            or "XA" <= region <= "XZ"
        )
        else False
    )


def characterize(
    pos: int, subtag: str
) -> (
    tuple[Literal["language", "extlang"], LanguageSubtag]
    | tuple[Literal["script"], ScriptSubtag]
    | tuple[Literal["region"], RegionSubtag]
    | tuple[Literal["variant"], VariantSubtag]
    | tuple[Literal["extension"], ExtensionSubtag]
):
    """Lexically characterizes a subtag according to its position,
    and returns a 2-tuple (its type, case-formatted form)."""
    match pos == 0, len(subtag), subtag.isalpha(), subtag.isdecimal():
        case True, (2 | 3), True, False:
            # 2*3ALPHA
            return "language", LanguageSubtag(intern(subtag.casefold()))
        case False, 3, True, False:
            # 3ALPHA
            return "extlang", LanguageSubtag(intern(subtag.casefold()))
        case False, 4, True, False:
            # 4ALPHA
            return "script", ScriptSubtag(intern(subtag.title()))
        case False, 2, True, False:
            # 2ALPHA
            return "region", RegionSubtag(intern(subtag.upper()))
        case False, 3, False, True:
            # 3DIGIT
            return "region", RegionSubtag(intern(subtag.casefold()))
        case False, (5 | 6 | 7 | 8), _, _:
            # 5*8alphanum
            return "variant", VariantSubtag(intern(subtag.casefold()))
        case False, 4, False, _ if subtag[0].isdecimal():
            # DIGIT 3ALPHANUM
            return "variant", VariantSubtag(intern(subtag.casefold()))
        case True, 4, True, False if subtag.casefold() == "root":
            # Coerce "root" into "und"
            # https://www.unicode.org/reports/tr35/#bcp-47-conformance
            return "language", LANGUAGE_UNDETERMINED
        case True, _, _, _:
            raise WellFormednessError(
                f"The first subtag must be a primary language subtag or 'x': {subtag!r}"
            )
        case False, 1, _, _:
            if subtag == "X" or subtag == "x":
                raise WellFormednessError(
                    "x extension tags are reserved for private use"
                )
            return "extension", ExtensionSubtag(intern(subtag.casefold()))
        case _:
            raise WellFormednessError(
                f"Subtag does not match any of the productions: {subtag!r}"
            )


class GrandfatheredPartsDict(TypedDict):
    grandfathered: GrandfatheredKey


class RegularPartsDict(TypedDict):
    language: NotRequired[LanguageSubtag]
    extlang: NotRequired[LanguageSubtag]
    script: NotRequired[ScriptSubtag]
    region: NotRequired[RegionSubtag]
    variants: NotRequired[Sequence[VariantSubtag]]
    privateuse: NotRequired[Sequence[str]]
    extensions: NotRequired[Mapping[ExtensionSubtag, Sequence[str]]]


def tag_to_parts(
    tag: str | Sequence[str], *, allow_stars: bool = False
) -> RegularPartsDict | GrandfatheredPartsDict:
    """Syntactically tokenizes a tag into its constitutent parts.
    Except in the case of grandfathered tags, this function does not validate.
    NOTE: This function catches most common syntactic issues, but is not strict.

    This is also a common entry point for parsing language tags.
    """
    if isinstance(tag, str):
        # Unicode CLDR BCP 47 extension allows underscore, though hyphen is still preferred
        parts = tag.replace("_", "-").split("-")
        cf = tag.casefold()
    else:
        parts = tag
        cf = "-".join(tag).casefold()
    try:
        return {"grandfathered": GRANDFATHERED_CF[cf]}
    except KeyError:
        pass
    output = {}
    extensions = {}
    variants = []
    current_extension = ""
    privateuse = []

    for i, part in enumerate(parts):
        length = len(part)
        if length == 0 or length > 8:
            raise WellFormednessError(
                f"Subtag must be between 1 and 8 characters: {part!r}"
            )
        elif part == "*":
            if allow_stars:
                continue
            raise WellFormednessError("Star not allowed")
        elif not part.isascii() or not part.isalnum():
            raise WellFormednessError(f"Subtag must be alphanumeric: {part!r}")
        elif current_extension == "x":
            part = part.casefold()
            privateuse.append(part)
        elif length == 1:
            part = part.casefold()
            if part == "x":
                current_extension = "x"
            elif i == 0:
                if part == "i":
                    raise WellFormednessError(
                        f"Only grandfathered tags can start with i-: {cf!r}"
                    )
                raise WellFormednessError(
                    f"Tag cannot begin with extension singleton: {cf!r}"
                )
            elif "0" <= part <= "9" or "a" <= part <= "z":
                if part in extensions:
                    raise WellFormednessError(
                        f"Duplicate extension singleton: {part!r}"
                    )
                current_extension = part
                extensions[current_extension] = []
            else:
                raise WellFormednessError(
                    f"Extension subtag must be 0-9, a-w, y-z, got {part!r}"
                )
        elif current_extension:
            part = part.casefold()
            extensions[current_extension].append(part)
        else:
            t, st = characterize(i, part)
            match t:
                case "language":
                    output["language"] = st
                case "extlang":
                    if (
                        "extlang" in output
                        or "script" in output
                        or "region" in output
                        or "variants" in output
                    ):
                        raise WellFormednessError(
                            f"Misordered subtags: extlang {st!r} after extlang/script/region/variants"
                        )
                    output["extlang"] = st
                case "script":
                    if "script" in output or "region" in output or "variants" in output:
                        raise WellFormednessError(
                            f"Misordered subtags: script {st!r} after script/region/variants"
                        )
                    output["script"] = st
                case "region":
                    if "region" in output or "variants" in output:
                        raise WellFormednessError(
                            f"Misordered subtags: region {st!r} after region/variants"
                        )
                    output["region"] = st
                case "variant":
                    output["variants"] = variants
                    variants.append(st)
                case err:
                    raise WellFormednessError(
                        f"Unexpected subtag {st!r} of type {err!r}"
                    )

    if not allow_stars:
        for e, x in extensions.items():
            if not x:
                raise WellFormednessError(f"No extension subtag after singleton {e!r}")
    if extensions:
        output["extensions"] = extensions
    if current_extension == "x":
        if not allow_stars and not privateuse:
            raise WellFormednessError('No private-use subtag after "x"')
        output["privateuse"] = privateuse
    return cast(RegularPartsDict, output)


def match_parts(tag_range: RegularPartsDict, tag: RegularPartsDict) -> bool:
    output = {}
    """Expect two fully-expanded tags and ranges. 
    Return the subtags that have participated the match, or None if no match is found.
    """
    language = tag_range.get("language", None)
    if language is not None and language != tag.get("language", None):
        return False
    extlang = tag_range.get("extlang", None)
    if extlang is not None and extlang != tag.get("extlang", None):
        return False
    script = tag_range.get("script", None)
    if script is not None and script != tag.get("script", None):
        return False
    variants = tag_range.get("variants", ())
    if variants and set(variants) > set(tag.get("variants", ())):
        return False
    extensions = tag_range.get("extensions", {})
    if extensions:
        extensions_target = tag.get("extensions", {})
        if not extensions_target:
            return False
        for ext, tags in extensions.items():
            tags_target = extensions_target.get(ext, ())
            if ext not in tags_target:
                return False
            if set(tags) > set(tags_target):
                return False
    privateuse = tag_range.get("privateuse", ())
    if privateuse:
        if "privateuse" not in tag:
            return False
        if set(privateuse) > set(tag.get("privateuse", ())):
            return False
    return True
