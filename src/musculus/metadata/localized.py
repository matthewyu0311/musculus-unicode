from typing import Self
from re import Pattern
from .langtag import LANGUAGE_TAG_STAR, LanguageRange
from musculus.util.functions import (
    Itemizable,
    itemize,
    SlottedImmutableMixin,
    new_with_fields,
    repr_slots,
)


class LocalizedMetadata:
    __slots__ = ()
    language: LanguageRange


class Title(SlottedImmutableMixin, LocalizedMetadata):
    __slots__ = ("main", "separator", "subtitle", "language")
    __match_args__ = ("main", "separator", "subtitle")

    main: str
    separator: str
    subtitle: str

    def __new__(
        cls,
        main: str,
        separator: str = "",
        subtitle: str = "",
        *,
        language: LanguageRange = LANGUAGE_TAG_STAR,
    ) -> Self:
        return new_with_fields(
            cls,
            main=main,
            separator=separator,
            subtitle=subtitle,
            language=language,
        )

    __repr__ = repr_slots

    def __str__(self) -> str:
        return f"{self.main}{self.separator}{self.subtitle}"

    @classmethod
    def parse(
        cls, source: str, /, *, patterns: Itemizable[LanguageRange, Pattern[str]] = ()
    ) -> Self:
        for language, pattern in itemize(patterns):
            m = pattern.fullmatch(source)
            if m is None:
                continue
            gd = m.groupdict()
            maintitle = gd["main"]
            separator = gd.get("separator", "")
            subtitle = gd.get("subtitle", "")
            return cls(maintitle, separator, subtitle, language=language)
        return cls(source, "", "", language=LANGUAGE_TAG_STAR)



# A common pattern for English book titles is
# R"(?P<main>[^:]*)(?P<separator>:\W*)?(?P<subtitle>.*)"
