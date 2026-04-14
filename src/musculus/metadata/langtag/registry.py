import datetime as dt
from collections.abc import Iterable, Mapping, Sequence, Set
from graphlib import TopologicalSorter
from importlib.resources.abc import Traversable
from pathlib import Path
from sys import intern
from typing import TYPE_CHECKING, Self, cast, overload

from musculus.util.functions import immutable
from musculus.util.iana import RecordDict, iter_records
from musculus.util.parse import ValidityError

from ...resources.langtag import EXTENSIONS_PATH, SUBTAG_PATH
from .subtag import (
    PRIVATE_USE_LANGUAGE,
    PRIVATE_USE_SCRIPT_REGION,
    REGION_UNKNOWN,
    SCRIPT_INHERITED,
    SCRIPT_INHERITED_DEPRECATED,
    SCRIPT_UNKNOWN,
    ExtensionSubtag,
    GrandfatheredKey,
    GrandfatheredPartsDict,
    LanguageSubtag,
    RedundantTag,
    RegionSubtag,
    RegularPartsDict,
    ScopeField,
    ScriptSubtag,
    VariantSubtag,
    is_private_language,
    is_private_region,
    is_private_script,
    tag_to_parts,
)


class RegistryMixin:
    __slots__ = ()
    date: dt.date | None
    # The exact requirements of the mapping are too complex to be specified in type hints
    languages: Mapping[LanguageSubtag, Mapping]
    macrolanguages: Mapping[LanguageSubtag, Set[LanguageSubtag]]
    scripts: Mapping[ScriptSubtag, Mapping]
    regions: Mapping[RegionSubtag, Mapping]
    variants: Mapping[VariantSubtag, Mapping]
    extensions: Mapping[ExtensionSubtag, Mapping]
    grandfathereds: Mapping[GrandfatheredKey, Mapping]
    redundants: Mapping[RedundantTag, Mapping]

    def __repr__(self) -> str:
        output = ["<Language subtag registry"]
        if self.date:
            output.append(f"date: {self.date.isoformat()}")
        output.append(
            f"languages: {len(self.languages)} (macrolanguages: {len(self.macrolanguages)})"
        )
        output.append(f"scripts: {len(self.scripts)}")
        output.append(f"regions: {len(self.regions)}")
        output.append(f"variants: {len(self.variants)}")
        output.append(f"redundant: {len(self.redundants)}")
        output.append(f"grandfathered: {len(self.grandfathereds)}")
        output.append(f"extensions: {len(self.extensions)}>")
        return ", ".join(output)

    def is_valid_subtag(self, subtag: str) -> bool:
        return bool(
            subtag in self.languages
            or subtag in self.scripts
            or subtag in self.regions
            or subtag in self.variants
            or is_private_language(subtag)
            or is_private_region(subtag)
            or is_private_script(subtag)
        )

    def entry(
        self,
        item: (
            LanguageSubtag
            | ScriptSubtag
            | RegionSubtag
            | VariantSubtag
            | ExtensionSubtag
            | GrandfatheredKey
            | RedundantTag
        ),
    ) -> Mapping:
        try:
            return self.languages[item]  # type: ignore
        except KeyError:
            pass
        try:
            return self.scripts[item]  # type: ignore
        except KeyError:
            pass
        try:
            return self.regions[item]  # type: ignore
        except KeyError:
            pass
        try:
            return self.variants[item]  # type: ignore
        except KeyError:
            pass
        try:
            return self.extensions[item]  # type: ignore
        except KeyError:
            pass
        try:
            return self.grandfathereds[item]  # type: ignore
        except KeyError:
            pass
        try:
            return self.redundants[item]  # type: ignore
        except KeyError:
            pass
        length = len(item)
        if length == 2 and is_private_region(item):
            return PRIVATE_USE_SCRIPT_REGION
        elif length == 3 and is_private_language(item):
            return PRIVATE_USE_LANGUAGE
        elif length == 4 and is_private_script(item):
            return PRIVATE_USE_SCRIPT_REGION
        raise ValidityError(f"Not a tag or subtag in the registry: {item!r}")

    def language_preferred(self, lang: LanguageSubtag) -> LanguageSubtag:
        try:
            return self.languages[lang].get("Preferred-Value", lang)
        except KeyError:
            if l := is_private_language(lang):
                return l
            raise

    def script_preferred(self, script: ScriptSubtag) -> ScriptSubtag:
        try:
            return self.scripts[script].get("Preferred-Value", script)
        except KeyError:
            if s := is_private_script(script):
                return s
            raise

    def region_preferred(self, region: RegionSubtag) -> RegionSubtag:
        try:
            return self.regions[region].get("Preferred-Value", region)
        except KeyError:
            if r := is_private_region(region):
                return r
            raise

    def variant_preferred(self, variant: VariantSubtag) -> VariantSubtag:
        return self.variants[variant].get("Preferred-Value", variant)

    def variant_preferred_tag(self, variant: VariantSubtag) -> str | None:
        return self.variants[variant].get("_preferred_tag", None)

    def variant_prefixes(self, variant: VariantSubtag) -> list[str] | None:
        pfx = self.variants[variant].get("Prefix", None)
        if isinstance(pfx, str):
            return [pfx]
        return pfx

    def extlang_prefix(self, extlang: LanguageSubtag) -> LanguageSubtag | None:
        """Return `None` if the language can only be used as a primary language."""
        try:
            return self.languages[extlang].get("Prefix", None)
        except KeyError:
            if is_private_language(extlang):
                return None
            raise

    def language_macrolanguage(self, lang: LanguageSubtag) -> LanguageSubtag | None:
        try:
            return self.languages[lang].get("Macrolanguage", None)
        except KeyError:
            if is_private_language(lang):
                return None
            raise

    def language_prefix_or_macrolanguage(
        self, lang: LanguageSubtag
    ) -> LanguageSubtag | None:
        """Return the Prefix of the language, falling back to the macrolanguage."""
        try:
            return self.languages[lang].get(
                "Prefix", self.languages[lang].get("Macrolanguage", None)
            )
        except KeyError:
            if is_private_language(lang):
                return None
            raise

    def language_encompassed(self, lang: LanguageSubtag) -> Set[LanguageSubtag] | None:
        try:
            return self.macrolanguages[lang]
        except KeyError:
            return None

    def language_scope(self, lang: LanguageSubtag) -> ScopeField:
        try:
            return self.languages[lang].get("Scope", "individual")
        except KeyError:
            if is_private_language(lang):
                return "private-use"
            raise

    def language_suppressed_script(self, lang: LanguageSubtag) -> ScriptSubtag | None:
        # extlangs don't contain a suppress-script in the file,
        # but their prefixes do
        # For example, "aao" itself doesn't have a Suppress-Script,
        # but it has a prefix "ar", which does contain a Suppress-Script of "Arab"
        # Thus, "aao" can be written as "ar-aao", which implies the script "Arab"
        if is_private_language(lang):
            return None
        l = self.languages[lang]
        ss = l.get("Suppress-Script", None)
        if ss is None and "Prefix" in l:
            return self.languages[l["Prefix"]].get("Suppress-Script", None)
        else:
            return ss

    def variants_sort(self, variants: Sequence[VariantSubtag]) -> list[VariantSubtag]:
        prefixed_sorter: TopologicalSorter[VariantSubtag] = TopologicalSorter()
        general_purpose: list[VariantSubtag] = []
        for variant in sorted(variants):
            prefixes = self.variant_prefixes(variant)
            if prefixes:
                # Prefixed variants are sorted based on a graph
                prefix_variants: set[VariantSubtag] = set()
                for prefix in prefixes:
                    ttpp = tag_to_parts(prefix).get("variants", None)
                    if ttpp:
                        prefix_variants.update(ttpp)
                prefixed_sorter.add(variant, *prefix_variants)
            else:
                # General-purpose variants are sorted alphabetically and attached to the end
                general_purpose.append(variant)
        prefixed_variants = prefixed_sorter.static_order()
        return list(
            filter(set(variants).__contains__, (*prefixed_variants, *general_purpose))
        )

    def expand(
        self, tag: RegularPartsDict, *, strict_extlang: bool = True
    ) -> RegularPartsDict:
        """Expand a tag into the extended language form, or the "macrolanguage-language" form.
        If `strict_extlang` is false, treat primary language with macrolanguage as if it had a prefix.
        Such tags are invalid but are useful for semantic matching.
        """
        if strict_extlang:
            prefix_func = self.extlang_prefix
        else:
            prefix_func = self.language_prefix_or_macrolanguage
        output: RegularPartsDict = tag.copy()
        script = tag.get("script", None)
        try:
            match tag.get("language", None), tag.get("extlang", None):
                case None, None:
                    pass
                case language, None:
                    pfx = prefix_func(language)
                    if pfx is not None:
                        # Language is an extlang or has macrolanguage
                        output["language"] = pfx
                        output["extlang"] = language
                    if script is None:
                        script = self.languages[language].get("Suppress-Script", script)
                    if script is None and pfx is not None:
                        script = self.languages[pfx].get("Suppress-Script", None)
                case language, extlang:
                    pfx = prefix_func(extlang)
                    if pfx is None:
                        raise ValidityError(f"Not an extlang: {extlang}")
                    if language is None:
                        output["language"] = pfx
                    elif pfx != language:
                        raise ValidityError(
                            f"Extended language tag {extlang!r} is incompatible "
                            f"with the primary language tag {language!r}"
                        )
                    if script is None:
                        script = self.languages[extlang].get("Suppress-Script", script)
                    if script is None:
                        script = self.languages[pfx].get("Suppress-Script", None)
        except KeyError:
            raise ValidityError
        if script is not None:
            output["script"] = script
        return output

    @overload
    def canonicalize(
        self,
        tag: RegularPartsDict,
    ) -> RegularPartsDict: ...

    @overload
    def canonicalize(
        self,
        tag: str | Sequence[str] | RegularPartsDict | GrandfatheredPartsDict,
    ) -> RegularPartsDict | GrandfatheredPartsDict: ...

    def canonicalize(
        self,
        tag,
    ):
        """
        NOTE: This slightly differs from Unicode CLDR canonicalization
        https://cldr.unicode.org/index/cldr-spec/picking-the-right-language-code#canonical-form
        
        """
        prefix_func = self.language_prefix_or_macrolanguage
        if not isinstance(tag, Mapping):
            tag = tag_to_parts(tag, allow_stars=True)
        grandfathered = tag.get("grandfathered", None)
        if grandfathered:
            tag = cast(GrandfatheredPartsDict, tag)
            try:
                # Replace with preferred value
                tag = tag_to_parts(
                    self.grandfathereds[grandfathered]["Preferred-Value"]
                )
            except KeyError:
                # No preferred value
                return tag
        tag = cast(RegularPartsDict, tag)
        language = tag.get("language", None)
        extlang = tag.get("extlang", None)
        script = tag.get("script", None)
        region = tag.get("region", None)
        variants = tag.get("variants", [])
        try:
            # If there is an extended language, check its prefix
            if extlang:
                extlang_prefix = prefix_func(extlang)
                if language is not None and extlang_prefix != language:
                    raise ValidityError(
                        f"Extended language tag {extlang!r} is incompatible "
                        f"with the primary language tag {language!r}"
                    )
                language = extlang
                extlang = None
            # If no language can be determined, set it to "und"
            if language is None:
                subtags: list = ["*"]
            else:
                # Convert the primary language into its preferred form
                language = self.language_preferred(language)
                if language == "sgn" and region is not None:
                    # Redundant tags:
                    # If we get a sign language-region combo, replace it with a preferred value
                    t = f"sgn-{region}"
                    if t in self.redundants:
                        pv = self.redundants[cast(RedundantTag, t)].get(
                            "Preferred-Value", None
                        )
                        if pv is not None:
                            repl = tag_to_parts(pv)
                            language = repl.get("language", language)
                            region = None
                if extlang_prefix := prefix_func(language):
                    # we need to check prefix of variants with the longest form of the tag
                    subtags: list = [extlang_prefix, language]
                else:
                    subtags: list = [language]

            if script == SCRIPT_INHERITED_DEPRECATED:  # Qaai -> Zinh
                script = SCRIPT_INHERITED
            if script:
                script = self.script_preferred(script)
                subtags.append(script)
                # Also check its prefix for Suppress-Script
                if language is not None and script == self.language_suppressed_script(
                    language
                ):
                    # Suppress it, but still keep it in subtags for matches
                    script = None

            # Convert the region into its preferred form
            if region:
                region = self.region_preferred(region)
                subtags.append(region)

            need_replace = -1
            replacement = None
            if variants:
                matching_prefixes = set()
                # Sort the variants first
                variants = self.variants_sort(variants)
                seen_variants = []
                for iv, variant in enumerate(variants):
                    prefixes = self.variant_prefixes(variant)
                    sts = [*subtags, *seen_variants]
                    if prefixes is None:
                        # General-purpose variants
                        seen_variants.append(variant)
                        continue
                    prefixes = [p.split("-") for p in prefixes]
                    # Longest match wins
                    prefixes.sort(key=list.__len__, reverse=True)
                    matching_prefix = None
                    for prefix in prefixes:
                        if set(prefix) <= set(sts):
                            matching_prefix = tuple(prefix)
                            break
                    if matching_prefix is None:
                        raise ValidityError(
                            f"Variant {variant!r} does not have a matching prefix"
                        )
                    if matching_prefix in matching_prefixes:
                        raise ValidityError(
                            "Variants that share a prefix are mutually exclusive."
                        )
                    matching_prefixes.add(matching_prefix)
                    if vpt := self.variant_preferred_tag(variant):
                        need_replace = iv
                        replacement = vpt
                    seen_variants.append(variant)
                if need_replace != -1 and replacement is not None:
                    variants = variants[need_replace + 1 :]
                    ttp = tag_to_parts(replacement)

                    language = ttp.get("language", language)
                    script = ttp.get("script", script)
                    region = ttp.get("region", region)
                    variants = (*ttp.get("variants", ()), *variants)

                    new_parts: RegularPartsDict = {}
                    if language:
                        new_parts["language"] = language
                    if script and (script != SCRIPT_UNKNOWN):
                        new_parts["script"] = script
                    if region and (region != REGION_UNKNOWN):
                        new_parts["region"] = region
                    if variants:
                        new_parts["variants"] = variants
                    if "privateuse" in tag:
                        pu = tag["privateuse"]
                        new_parts["privateuse"] = pu
                    if "extensions" in tag:
                        new_parts["extensions"] = tag["extensions"]
                    return self.canonicalize(new_parts)
                variants = list(map(self.variant_preferred, variants)) or []
            new_parts: RegularPartsDict = {}
            if language:
                new_parts["language"] = language
            if script and (script != SCRIPT_UNKNOWN):
                new_parts["script"] = script
            if region and (region != REGION_UNKNOWN):
                new_parts["region"] = region
            if variants:
                new_parts["variants"] = variants
            if "privateuse" in tag:
                pu = tag["privateuse"]
                new_parts["privateuse"] = pu
            if "extensions" in tag:
                for extension in tag["extensions"]:
                    if extension not in self.extensions:
                        raise ValidityError(f"Unknown extension: {extension!r}")
                new_parts["extensions"] = tag["extensions"]
            return new_parts
        except KeyError as ke:
            raise ValidityError from ke


class Registry(RegistryMixin):

    @classmethod
    def load_file(
        cls,
        file: Path | Traversable = SUBTAG_PATH,
        extensions_file: Path | Traversable | None = EXTENSIONS_PATH,
    ) -> Self:
        with file.open(mode="r", encoding="utf-8", errors="strict") as f:
            records = iter_records(f)
            try:
                first = next(records)
            except StopIteration:
                raise ValueError
            try:
                date = dt.date.fromisoformat(cast(str, first["File-Date"]))
            except LookupError, ValueError:
                date = None

            if extensions_file is not None:
                with extensions_file.open(mode="r", encoding="utf-8", errors="strict") as fx:
                    recordx = iter_records(fx)
                    try:
                        next(recordx)
                    except StopIteration:
                        pass
                    return cls(records, recordx, date=date, copy_dicts=False)
            else:
                return cls(records, date=date, copy_dicts=False)

    def __init__(
        self,
        records: Iterable[RecordDict],
        extension_records: Iterable[RecordDict] | None = None,
        *,
        date: dt.date | None = None,
        copy_dicts: bool = True,
    ) -> None:
        extensions = {}
        macrolanguages = {}
        languages = {}
        languages_inverse = {}
        scripts = {}
        scripts_inverse = {}
        regions = {}
        regions_inverse = {}
        variants = {}
        variants_inverse = {}
        grandfathereds = {}
        grandfathereds_inverse = {}
        redundants = {}
        redundants_inverse = {}
        for item in records:
            if copy_dicts:
                # Make a copy and don't mutate incoming dicts in-place
                item = dict(item)
            item.pop("Added", None)
            match item.pop("Type"):
                case "language" | "extlang" as t:
                    tag = intern(cast(str, item.pop("Subtag")))
                    if is_private_language(tag):
                        continue
                    if t == "extlang":
                        # In practice the PV is always the primary language of the same tag
                        # even if the primary language tag itself has another PV (see "ajp")
                        # Thus, extlang PV provides no information
                        del item["Preferred-Value"]
                    try:
                        languages[tag].update(item)
                    except KeyError:
                        languages[tag] = item
                        desc = item["Description"]
                        if isinstance(desc, str):
                            languages_inverse[desc] = tag
                        else:
                            for d in desc:
                                languages_inverse[d] = tag
                        try:
                            scope = item["Scope"]
                            if scope == "macrolanguage":
                                macrolanguages.setdefault(tag, set())
                        except KeyError:
                            pass
                        try:
                            ml = item["Macrolanguage"]
                            try:
                                macrolanguages[ml].add(tag)
                            except KeyError:
                                macrolanguages[ml] = {tag}
                        except KeyError:
                            pass
                case "region":
                    tag = intern(cast(str, item.pop("Subtag")))
                    if is_private_region(tag):
                        continue
                    regions[tag] = item
                    desc = item["Description"]
                    if isinstance(desc, str):
                        regions_inverse[desc] = tag
                    else:
                        for d in desc:
                            regions_inverse[d] = tag
                case "script":
                    tag = intern(cast(str, item.pop("Subtag")))
                    if is_private_script(tag):
                        continue
                    scripts[tag] = item
                    desc = item["Description"]
                    if isinstance(desc, str):
                        scripts_inverse[desc] = tag
                    else:
                        for d in desc:
                            scripts_inverse[d] = tag
                case "variant":
                    tag = intern(cast(str, item.pop("Subtag")))
                    variants[tag] = item
                    desc = item["Description"]
                    if isinstance(desc, str):
                        variants_inverse[desc] = tag
                    else:
                        for d in desc:
                            variants_inverse[d] = tag
                    try:
                        comments = item["Comments"]
                        if isinstance(comments, str):
                            comments = [comments]
                        for comment in comments:
                            if comment.startswith("Preferred tag is "):
                                item["_preferred_tag"] = comment.removeprefix(
                                    "Preferred tag is "
                                )
                    except KeyError:
                        pass
                case "grandfathered":
                    tag = intern(cast(str, item.pop("Tag")))
                    grandfathereds[tag] = item
                    desc = item["Description"]
                    if isinstance(desc, str):
                        grandfathereds_inverse[desc] = tag
                    else:
                        for d in desc:
                            grandfathereds_inverse[d] = tag
                case "redundant":
                    tag = intern(cast(str, item.pop("Tag")))
                    redundants[tag] = item
                    desc = item["Description"]
                    if isinstance(desc, str):
                        redundants_inverse[desc] = tag
                    else:
                        for d in desc:
                            redundants_inverse[d] = tag
                case _:
                    pass
        if extension_records is not None:
            for item in extension_records:
                if copy_dicts:
                    item = dict(item)
                tag = intern(cast(str, item.pop("Identifier")))
                extensions[tag] = item

        self.date = date
        self.extensions: dict[ExtensionSubtag, dict] = extensions
        self.macrolanguages: dict[LanguageSubtag, set[LanguageSubtag]] = macrolanguages
        self.languages: dict[LanguageSubtag, dict] = languages
        self.languages_inverse: dict[str, LanguageSubtag] = languages_inverse
        self.scripts: dict[ScriptSubtag, dict] = scripts
        self.scripts_inverse: dict[str, ScriptSubtag] = scripts_inverse
        self.regions: dict[RegionSubtag, dict] = regions
        self.regions_inverse: dict[str, RegionSubtag] = regions_inverse
        self.variants: dict[VariantSubtag, dict] = variants
        self.variants_inverse: dict[str, VariantSubtag] = variants_inverse
        self.grandfathereds: dict[GrandfatheredKey, dict] = grandfathereds
        self.grandfathereds_inverse: dict[str, GrandfatheredKey] = (
            grandfathereds_inverse
        )
        self.redundants: dict[RedundantTag, dict] = redundants
        self.redundants_inverse: dict[str, RedundantTag] = redundants_inverse


def _export(reg: RegistryMixin):
    output = []
    if reg.date is not None:
        output.append(f"date = {reg.date.isoformat()!r}")
    else:
        output.append("date = None")
    for name in (
        "extensions",
        "macrolanguages",
        "languages",
        "languages_inverse",
        "scripts",
        "scripts_inverse",
        "regions",
        "regions_inverse",
        "variants",
        "variants_inverse",
        "grandfathereds",
        "grandfathereds_inverse",
        "redundants",
        "redundants_inverse",
    ):
        output.append(f"{name} = {dict(getattr(reg, name))!r}")

    return [f"{s}\n" for s in output]


if TYPE_CHECKING:

    @immutable
    class _VendoredRegistry(RegistryMixin):
        __slots__ = ()
        date = None
        extensions = {}  # type: ignore
        macrolanguages = {}  # type: ignore
        languages = {}  # type: ignore
        languages_invers = {}  # type: ignore
        scripts = {}  # type: ignore
        scripts_inverse = {}  # type: ignore
        regions = {}  # type: ignore
        regions_inverse = {}  # type: ignore
        variants = {}  # type: ignore
        variants_inverse = {}  # type: ignore
        grandfathereds = {}  # type: ignore
        grandfathereds_inverse = {}  # type: ignore
        redundants = {}  # type: ignore
        redundants_inverse = {}  # type: ignore

else:
    # Type checkers, please don't try to analyze the _vendored.py file
    from . import _vendored

    @immutable
    class _VendoredRegistry(RegistryMixin):
        __slots__ = ()
        date = dt.date.fromisoformat(_vendored.date) if _vendored.date else None
        extensions = _vendored.extensions
        macrolanguages = _vendored.macrolanguages
        languages = _vendored.languages
        languages_inverse = _vendored.languages_inverse
        scripts = _vendored.scripts
        scripts_inverse = _vendored.scripts_inverse
        regions = _vendored.regions
        regions_inverse = _vendored.regions_inverse
        variants = _vendored.variants
        variants_inverse = _vendored.variants_inverse
        grandfathereds = _vendored.grandfathereds
        grandfathereds_inverse = _vendored.grandfathereds_inverse
        redundants = _vendored.redundants
        redundants_inverse = _vendored.redundants_inverse


VENDORED_REGISTRY = _VendoredRegistry()
