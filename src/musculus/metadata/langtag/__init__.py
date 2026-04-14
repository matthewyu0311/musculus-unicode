"""
Partly implements RFC 5646.
"""

from collections.abc import Iterator, Mapping, Sequence
from string import ascii_lowercase, digits
from types import MappingProxyType
from typing import Self

from musculus.util.functions import (
    EMPTY_MAPPING,
    immutable,
    new_with_fields,
    repr_slots,
)
from musculus.util.parse import Parseable, ValidityError, WellFormednessError

from .registry import VENDORED_REGISTRY, RegistryMixin
from .subtag import (
    GRANDFATHERED_CF,
    LANGUAGE_UNDETERMINED,
    ExtensionSubtag,
    GrandfatheredKey,
    GrandfatheredPartsDict,
    LanguageSubtag,
    RegionSubtag,
    RegularPartsDict,
    ScriptSubtag,
    VariantSubtag,
    characterize,
    is_private_language,
    is_private_region,
    is_private_script,
    tag_to_parts,
)


class LanguageRange(Parseable):
    __slots__ = ()

    @classmethod
    def parse(
        cls, source: str, /, *, registry: RegistryMixin | None = VENDORED_REGISTRY
    ) -> LanguageTag | GrandfatheredTag:
        m = tag_to_parts(source, allow_stars=True)
        if "grandfathered" in m:
            o = GrandfatheredTag(m["grandfathered"])
        else:
            o = LanguageTag(**m)
        if registry is None:
            return o
        return o.canonicalize(registry)

    def to_dict(self) -> RegularPartsDict | GrandfatheredPartsDict: ...

    def canonicalize(
        self, registry: RegistryMixin = VENDORED_REGISTRY
    ) -> LanguageRange: ...

    def subtags(self) -> Sequence[str]: ...

    def __len__(self) -> int:
        return len(self.subtags())

    def __iter__(self) -> Iterator[str]:
        return iter(self.subtags())

    def __str__(self) -> str:
        return "-".join(self.subtags())

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, LanguageRange):
            return NotImplemented
        return self.subtags() == other.subtags()

    __repr__ = repr_slots

    def __hash__(self) -> int:
        return hash(self.subtags())

    def describe(self) -> str:
        return repr(self)


@immutable
class LanguageTag(LanguageRange):
    """A lightweight implementation that aims to implement RFC 5646 Language Tags in a manner
    compatible with Unicode Technical Standard #35 LDML locale identifiers.
    """

    __slots__ = (
        "language",
        "extlang",
        "script",
        "region",
        "variants",
        "extensions",
        "privateuse",
    )
    language: LanguageSubtag | None
    extlang: LanguageSubtag | None
    script: ScriptSubtag | None
    region: RegionSubtag | None
    variants: Sequence[VariantSubtag]
    extensions: Mapping[ExtensionSubtag, Sequence[str]]
    privateuse: Sequence[str]

    def __new__(
        cls,
        language: LanguageSubtag | None = None,
        extlang: LanguageSubtag | None = None,
        script: ScriptSubtag | None = None,
        region: RegionSubtag | None = None,
        variants: VariantSubtag | Sequence[VariantSubtag] = (),
        extensions: Mapping[ExtensionSubtag, Sequence[str]] = EMPTY_MAPPING,
        privateuse: Sequence[str] = (),
    ) -> Self:
        if language is not None:
            t, language = characterize(0, language)  # type: ignore
            if t != "language":
                raise WellFormednessError(f"Not a language: {language!r}")
        if extlang is not None:
            t, extlang = characterize(1, extlang)  # type: ignore
            if t != "extlang":
                raise WellFormednessError(f"Not a language: {extlang!r}")
        if script is not None:
            t, script = characterize(2, script)  # type: ignore
            if t != "script":
                raise WellFormednessError(f"Not a script: {script!r}")
        if region is not None:
            t, region = characterize(3, region)  # type: ignore
            if t != "region":
                raise WellFormednessError(f"Not a region: {region!r}")
        if variants:
            vs = []
            for variant in variants:
                t, v = characterize(4, variant)  # type: ignore
                if t != "variant":
                    raise WellFormednessError(f"Not a variant: {variant!r}")
                vs.append(v)
            variants = tuple(vs)
        if extensions:
            es = {}
            for k, v in extensions.items():
                k = k.casefold()
                if k == "x":
                    # Wrong argument name, but we allow this as long as it doesn't conflict
                    if privateuse:
                        raise TypeError(
                            'Private-use subtag should be passed in the "privateuse" argument'
                        )
                    privateuse = v
                    continue
                if len(k) != 1 or (k not in digits and k not in ascii_lowercase):
                    raise WellFormednessError(f"Not an extension singleton: {k!r}")
                l = []
                for item in v:
                    item = item.casefold()
                    if (
                        not item.isascii()
                        or not item.isalnum()
                        or not 2 <= len(item) <= 8
                    ):
                        raise WellFormednessError(f"Not an extension subtag: {item!r}")
                    l.append(item)
                if k in es:
                    # This can happen due to casefoldidng
                    raise WellFormednessError(f"Duplicate extension singleton: {k!r}")
                if l:
                    es[k] = tuple(l)
            extensions = MappingProxyType(es)
        if privateuse:
            pu = []
            for p in privateuse:
                p = p.casefold()
                if not p.isascii() or not p.isalnum() or not 1 <= len(p) <= 8:
                    raise WellFormednessError(f"Not a private-use subtag: {p!r}")
                pu.append(p)
            privateuse = tuple(pu)
        # if not language and not extlang and not script and not region and not variants:
        #     language = LANGUAGE_UNDETERMINED
        return new_with_fields(
            cls,
            language=language,
            extlang=extlang,
            script=script,
            region=region,
            variants=variants,
            extensions=extensions,
            privateuse=privateuse,
        )

    @classmethod
    def parse(cls, source: str, /) -> Self:
        o = LanguageRange.parse(source)
        if isinstance(o, cls):
            return o
        o = o.canonicalize()
        if isinstance(o, cls):
            return o
        raise ValidityError(f"Grandfathered tag: {o}")

    def to_dict(self) -> RegularPartsDict:
        output: RegularPartsDict = {}
        if self.language is not None:
            output["language"] = self.language
        if self.extlang is not None:
            output["extlang"] = self.extlang
        if self.script is not None:
            output["script"] = self.script
        if self.region is not None:
            output["region"] = self.region
        if self.variants:
            output["variants"] = self.variants
        if self.extensions:
            output["extensions"] = self.extensions
        if self.privateuse:
            output["privateuse"] = self.privateuse
        return output

    def to_expanded_dict(
        self,
        *,
        registry: RegistryMixin = VENDORED_REGISTRY,
        strict_extlang: bool = True,
    ) -> RegularPartsDict:
        return registry.expand(self.to_dict(), strict_extlang=strict_extlang)

    def canonicalize(self, registry: RegistryMixin = VENDORED_REGISTRY) -> Self:
        d = self.to_dict()
        canon = registry.canonicalize(d)
        if canon == d:
            return self
        return self.__class__(**canon)

    def subtags(self) -> Sequence[str]:
        output: list[str]
        if self.language is None:
            if (
                not self.extlang
                and not self.script
                and not self.region
                and not self.variants
                and not self.extensions
            ):
                output = []
            else:
                output = ["*"]
        else:
            output = [self.language]
        if self.extlang is not None:
            output.append(self.extlang)
        if self.script is not None:
            output.append(self.script)
        if self.region is not None:
            output.append(self.region)
        output.extend(self.variants)
        for k in sorted(self.extensions.keys()):
            output.append(k)
            output.extend(self.extensions[k])
        if self.privateuse:
            output.append("x")
            output.extend(self.privateuse)
        return output or ["*"]

    def __repr__(self) -> str:
        output = []
        output.append(f"{self.language!r}")
        output.append(f"{self.extlang!r}")
        output.append(f"{self.script!r}")
        output.append(f"{self.region!r}")
        if self.variants or self.privateuse or self.extensions:
            output.append(f"{tuple(self.variants)!r}")
            if self.privateuse or self.extensions:
                output.append(f"{dict(self.extensions)!r}")
                if self.privateuse:
                    output.append(f"{tuple(self.privateuse)!r}")
        s = ", ".join(output)
        return f"{self.__class__.__name__}({s})"

    def describe(self, registry: RegistryMixin = VENDORED_REGISTRY) -> str:
        try:
            if self.extlang is not None:
                lang_desc: str | list[str] = registry.languages[self.extlang][
                    "Description"
                ]
            elif self.language is not None:
                lang_desc = registry.languages[self.language]["Description"]
            else:
                lang_desc = "No language"
            if not isinstance(lang_desc, str):
                lang_desc = lang_desc[0]
        except LookupError:
            if self.extlang is not None:
                lang_desc = f"Language {self.extlang!r}"
            elif is_private_language(self.language):
                lang_desc = f"Private-use langauage {self.language!r}"
            else:
                lang_desc = f"Language {self.language!r}"
        try:
            if self.script is not None:
                script_desc = registry.scripts[self.script]["Description"]
                if not isinstance(script_desc, str):
                    script_desc = script_desc[0]
            else:
                script_desc = ""
        except LookupError:
            if is_private_script(self.script):
                script_desc = f"Private-use script {self.script!r}"
            else:
                script_desc = f"Script {self.script!r}"
        try:
            if self.region is not None:
                region_desc = registry.regions[self.region]["Description"]
                if not isinstance(region_desc, str):
                    region_desc = region_desc[0]
            else:
                region_desc = ""
        except LookupError:
            if is_private_region(self.region):
                region_desc = f"Private-use region {self.region!r}"
            else:
                region_desc = f"Region {self.region!r}"
        variants_desc = []
        for variant in self.variants:
            try:
                variant_desc = registry.variants[variant]["Description"]
                if not isinstance(variant_desc, str):
                    variant_desc = variant_desc[0]
            except LookupError:
                variant_desc = f"Variant {variant!r}"
            variants_desc.append(variant_desc)
        return ", ".join(
            filter(None, [lang_desc, script_desc, region_desc, *variants_desc])
        )

LANGUAGE_TAG_STAR = LanguageTag()
LANGUAGE_TAG_UNDETERMINED = LanguageTag(LANGUAGE_UNDETERMINED)

@immutable
class GrandfatheredTag(LanguageRange):
    """A lightweight implementation that aims to implement RFC 5646 Language Tags in a manner
    compatible with Unicode Technical Standard #35 LDML locale identifiers.
    """

    __slots__ = ("grandfathered",)

    grandfathered: GrandfatheredKey

    def __new__(cls, grandfathered: GrandfatheredKey) -> Self:
        try:
            cf = GRANDFATHERED_CF[grandfathered.casefold()]
        except KeyError:
            raise ValidityError(f"Not a grandfathered tag: {grandfathered!r}")
        return new_with_fields(cls, grandfathered=cf)

    def to_dict(self) -> GrandfatheredPartsDict:
        return {"grandfathered": self.grandfathered}

    def subtags(self) -> Sequence[str]:
        return self.grandfathered.split("-")

    def canonicalize(
        self, registry: RegistryMixin = VENDORED_REGISTRY
    ) -> Self | LanguageTag:
        d = self.to_dict()
        canon = registry.canonicalize(d)
        if "grandfathered" in canon:
            # We can't really canonicalize this one
            return self
        return LanguageTag(**canon)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.grandfathered!r})"

    def describe(self, registry: RegistryMixin = VENDORED_REGISTRY) -> str:
        try:
            d = registry.grandfathereds[self.grandfathered]["Description"]
            if isinstance(d, str):
                return d
            return d[0]
        except LookupError:
            return repr(self)

    def to_expanded_dict(self, registry: RegistryMixin = VENDORED_REGISTRY):
        canon = self.canonicalize()
        if canon is self:
            return self.to_dict()
        return canon.canonicalize(registry=registry).to_expanded_dict()
