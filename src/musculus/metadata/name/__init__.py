from abc import ABC, abstractmethod
from collections.abc import Callable, Collection
from enum import StrEnum
from functools import lru_cache
from typing import NewType, Protocol, TypedDict

from musculus.unicode.util import CodePoint, collate

from ..langtag import LANGUAGE_TAG_UNDETERMINED, LanguageTag
from ..langtag.subtag import (
    LANGUAGE_UNDETERMINED,
    SCRIPT_COMMON,
    SCRIPT_INHERITED,
    SCRIPT_INHERITED_DEPRECATED,
    SCRIPT_UNKNOWN,
    LanguageSubtag,
    ScriptSubtag,
)


class FieldModifier(StrEnum):
    ALL_CAPS = "allCaps"
    CORE = "core"
    GENITIVE = "genitive"
    INFORMAL = "informal"
    INITIAL = "initial"
    INITIAL_CAP = "initialCap"
    MONOGRAM = "monogram"
    PREFIX = "prefix"
    RETAIN = "retain"
    VOCATIVE = "vocative"


class NameField(StrEnum):
    CREDENTIALS = "credentials"
    GENERATION = "generation"
    GIVEN = "given"
    GIVEN2 = "given2"
    SURNAME = "surname"
    SURNAME2 = "surname2"
    TITLE = "title"


class Order(StrEnum):
    GIVEN_FIRST = "givenFirst"
    SURNAME_FIRST = "surnamefirst"
    SORTING = "sorting"


class Length(StrEnum):
    LONG = "long"
    MEDIUM = "medium"
    SHORT = "short"


class Usage(StrEnum):
    ADDRESSING = "addressing"
    REFERRING = "referring"
    MONOGRAM = "monogram"

class Formality(StrEnum):
    FORMAL = "formal"
    INFORMAL = "informal"

_ALL_ABBR = {**Order.__members__, **Length.__members__, **Usage.__members__, **Formality.__members__}
_ALL_ABBR_COLL = {collate(v): v for v in _ALL_ABBR.values()}

class PersonNameAttributes(TypedDict):
    order: Order | None
    length: Length | None
    usage: Usage | None
    formality: Formality | None

@lru_cache(maxsize=4*4*4*3)
def attrs_from_abbr(attrs: str) -> PersonNameAttributes:
    output: PersonNameAttributes = {
        "order": None,
        "length": None,
        "usage": None,
        "formality": None
    }
    for attr in attrs.split("-"):
        attr = collate(attr)
        try:
            match _ALL_ABBR_COLL[attr]:
                case Order() as order:
                    output["order"] = order
                case Length() as length:
                    output["length"] = length
                case Usage() as usage:
                    output["usage"] = usage
                case Formality() as formality:
                    output["formality"] = formality
                case _:
                    pass
        except KeyError:
            pass
    return output


FieldKey = NewType("FieldKey", str)


def _join_von_last(von, last):
    if not von:
        return last
    if not last:
        return von
    return f"{von} {last}"



class PersonName(ABC):
    """This ABC does not inherit from `Parseable`, since subclasses
    may or may not be parseable from a simple string.
    """

    # Subclasses should comply with LDML (but we aren't enforcing this):
    # "There must be at least one field present: either a given or surname field.
    # Other fields are optional, and some of them can be constructed from other fields if necessary."

    __slots__ = ()
    name_locale: LanguageTag = LANGUAGE_TAG_UNDETERMINED
    preferred_order: Order | None = None

    @abstractmethod
    def get_field_value(
        self, name_field: NameField, *modifiers: FieldModifier
    ) -> tuple[str | None, Collection[FieldModifier]]:
        """Returns the field value or `None`, and the leftover modifiers NOT handled."""
        ...

    @abstractmethod
    def __getitem__(self, key: FieldKey) -> str:
        """Returns the field value for the field key, or raises `KeyError` if the exact key is not found."""
        ...

    def von(self) -> str:
        vons, mods = self.get_field_value(NameField.SURNAME, FieldModifier.PREFIX)
        if vons is None or mods:
            return ""
        return vons

    def last(self) -> str:
        last, mods = self.get_field_value(NameField.SURNAME, FieldModifier.CORE)
        return last or ""

    def junior(self) -> str:
        junior, mods = self.get_field_value(NameField.GENERATION)
        return junior or ""

    def first(self) -> str:
        first, mods = self.get_field_value(NameField.GIVEN)
        return first or ""

    def to_bibtex(self) -> str:
        von = " ".join(self.von()).replace(",", "\\,")
        last = " ".join(self.last()).replace(",", "\\,")
        junior = " ".join(self.junior()).replace(",", "\\,")
        first = " ".join(self.first()).replace(",", "\\,")
        if junior:
            return f"{_join_von_last(von, last)}, {junior}, {first}".strip()
        if first:
            return f"{_join_von_last(von, last)}, {first}".strip()
        return _join_von_last(von, last)
