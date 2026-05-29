from abc import ABC, abstractmethod
from collections.abc import Collection, Iterable, Mapping, Sequence
from enum import StrEnum
from functools import lru_cache
from itertools import chain
from typing import Self, NewType, TypedDict

from musculus.util.parse import collate
from musculus.util.functions import (
    immutable,
    new_with_fields,
)
from ..langtag import LANGUAGE_TAG_UNDETERMINED, LanguageTag

FieldKey = NewType("FieldKey", str)


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


_ALL_ABBR = {
    **Order.__members__,
    **Length.__members__,
    **Usage.__members__,
    **Formality.__members__,
}
_ALL_ABBR_COLL = {collate(v): v for v in _ALL_ABBR.values()}


class PersonNameAttributes(TypedDict):
    order: Order | None
    length: Length | None
    usage: Usage | None
    formality: Formality | None


@lru_cache(maxsize=4 * 4 * 4 * 3)
def _attrs_from_abbr(attrs: str) -> PersonNameAttributes:
    output: PersonNameAttributes = {
        "order": None,
        "length": None,
        "usage": None,
        "formality": None,
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


def _make_field_key(identifier: NameField, *modifiers: FieldModifier) -> FieldKey:
    mods = sorted(modifiers)
    if FieldModifier.PREFIX in mods and FieldModifier.CORE in mods:
        raise ValueError("-prefix and -core cannot be used together")
    if FieldModifier.ALL_CAPS in mods and FieldModifier.INITIAL_CAP in mods:
        raise ValueError("-allCaps and -initialCap cannot be used together")
    if FieldModifier.INITIAL in mods and FieldModifier.MONOGRAM in mods:
        raise ValueError("-initial and -monogram cannot be used together")
    return FieldKey("-".join((identifier, *mods)))


def _field_key_to_modifiers(field_name: str) -> tuple[NameField, list[FieldModifier]]:
    identifier, _, modifiers = field_name.partition("-")
    mods = [FieldModifier(x) for x in modifiers.split("-")]
    mods.sort()
    return NameField(identifier), mods


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

    def __str__(self) -> str:
        # TODO FIXME: use preferred order
        return self.to_bibtex()

    def __format__(self, format_spec: str) -> str:
        if not format_spec:
            return str(self)
        # TODO
        raise NotImplementedError


@immutable
class SimplePersonName(
    PersonName,
    # Parseable,
    # Parseable semantics requires robust __str__ / parse roundtripping which we can't do
):
    __slots__ = ("name_locale", "preferred_order", "_field_values")
    _field_values: dict[FieldKey, str]

    def __new__(
        cls,
        field_values: Mapping[FieldKey | str, str],
        *,
        name_locale: LanguageTag = LANGUAGE_TAG_UNDETERMINED,
        preferred_order: Order | None = None,
    ) -> Self:
        fd = {FieldKey(k): v for k, v in field_values.items()}
        # Special-casing of surname handling
        if "surname" not in fd:
            surname_prefix = fd.get(FieldKey("surname-prefix"), None)
            surname_core = fd.get(FieldKey("surname-core"), None)
            if surname_prefix and surname_core:
                fd[FieldKey("surname")] = surname_prefix + " " + surname_core
            elif surname_prefix:
                fd[FieldKey("surname")] = surname_prefix
            elif surname_core:
                fd[FieldKey("surname")] = surname_core
        if preferred_order == Order.SORTING:
            preferred_order = None
        return new_with_fields(
            cls,
            name_locale=name_locale,
            preferred_order=preferred_order,
            _field_values=fd,
        )

    def __getitem__(self, key: FieldKey) -> str:
        return self._field_values[key]

    def get_field_value(
        self, name_field: NameField, *modifiers: FieldModifier
    ) -> tuple[str | None, Collection[FieldModifier]]:
        key = _make_field_key(name_field, *modifiers)
        try:
            # If we can find an exact match, return it
            output = self._field_values[key]
            return output, ()
        except KeyError:
            pass
        key = _make_field_key(name_field)
        if key not in self._field_values:
            return None, modifiers
        if len(modifiers) == 1:
            return self._field_values[key], modifiers
        # If there are two or more identifiers, we need to try
        ms = set(modifiers)
        winning_key = None
        winning_score = 0
        for fk in self._field_values.keys():
            iden, mods = _field_key_to_modifiers(fk)
            if iden != name_field or not ms.issuperset(mods):
                continue
            score = len(mods)
            if score > winning_score or (
                score == winning_score and (winning_key is None or fk < winning_key)
            ):
                winning_key = fk
                winning_score = score
        if winning_key is None:
            return None, modifiers
        _, mods = _field_key_to_modifiers(winning_key)
        return self._field_values[winning_key], ms.difference(mods)

    @classmethod
    def from_bibtex(
        cls,
        von: str = "",
        last: str = "",
        junior: str = "",
        first: str = "",
        *,
        name_locale: LanguageTag = LANGUAGE_TAG_UNDETERMINED,
        preferred_order: Order | None = None,
    ) -> Self:
        """Constructs an instance based on standard BibTeX name parts."""
        fm = {}
        von = von.strip()
        last = last.strip()
        junior = junior.strip()
        first = first.strip()
        if von:
            # von maps to surname-prefix
            # last maps to surname-core
            fm[FieldKey("surname-prefix")] = von
            if last:
                fm[FieldKey("surname-core")] = last
        elif last:
            fm[FieldKey("surname")] = last
        if junior:
            fm[FieldKey("generation")] = junior
        if first:
            fm[FieldKey("given")] = first
        return cls(fm, name_locale=name_locale, preferred_order=preferred_order)

    @classmethod
    def parse_bibtex(
        cls,
        source: str,
        /,
        *,
        name_locale: LanguageTag = LANGUAGE_TAG_UNDETERMINED,
        preferred_order: Order | None = None,
    ) -> Self:
        """
        Parses a string name, splitting the name into parts according to the BibTeX heuristics.
        NOTE: the stringified form of the name does not necessarily roundtrip.
        This method is modeled after BibTeX name processing, but does not handle braces.
        From https://metacpan.org/pod/LaTeX::BibTeX::Name :

        How tokens are divided into parts depends on the form of the name.

        - If the name has no commas at brace-level zero (as in the second example),
        then it is assumed to be in either "first last" or "first von last" form.
        -- If there are no tokens that start with a lower-case letter, then "first last" form is assumed:
        the final token is the last name, and all other tokens form the first name.
        -- Otherwise, the earliest contiguous sequence of tokens with initial lower-case letters is taken as the 'von' part;
        if this sequence includes the final token, then a warning is printed and the final token is forced to be the 'last' part.

        - If a name has a single comma, then it is assumed to be in "von last, first" form.
        -- A leading sequence of tokens with initial lower-case letters, if any, forms the 'von' part;
        -- tokens between the 'von' and the comma form the 'last' part;
        -- tokens following the comma form the 'first' part.
        -- Again, if there are no tokens following a leading sequence of lowercase tokens, a warning is printed and
        the token immediately preceding the comma is taken to be the 'last' part.

        - If a name has more than two commas, a warning is printed and the name is treated as though only the first two commas were present.

        - Finally, if a name has two commas, it is assumed to be in "von last, jr, first" form.
        (This is the only way to represent a name with a 'jr' part.) The parsing of the name is the same as for a one-comma name,
        except that tokens between the two commas are taken to be the 'jr' part.
        """
        bin0 = []
        bin1 = []
        bin2 = []
        comma_count = 0
        for token in _tokenize_bibtex(source):
            match comma_count, token:
                case (0 | 1), ",":
                    comma_count += 1
                case 0, _:
                    bin0.append(token)
                case 1, _:
                    bin1.append(token)
                case _, _:
                    if token == ",":
                        comma_count += 1
                    bin2.append(token)
        if comma_count == 0:
            # First last / first von last
            first, von, last = _split_first_von_last(bin0)
            junior = ()
        elif comma_count == 1:
            von, last = _split_von_last(bin0)
            first = bin1
            junior = ()
        else:
            # von last, jr, first
            von, last = _split_von_last(bin0)
            junior = bin1
            first = bin2
        return cls.from_bibtex(
            von=" ".join(von),
            last=" ".join(last),
            junior=" ".join(junior),
            first=" ".join(first),
            name_locale=name_locale,
            preferred_order=preferred_order,
        )

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if not isinstance(other, PersonName):
            return NotImplemented
        # Unicode does not (?) provide an official equivalence algorithm...
        if isinstance(other, SimplePersonName):
            return self._field_values == other._field_values
        return (
            self.von() == other.von()
            and self.last() == other.last()
            and self.junior() == other.junior()
            and self.first() == other.first()
        )

    def __hash__(self) -> int:
        return hash(frozenset(map(tuple, self._field_values.items())))

    def __repr__(self) -> str:
        parts = [repr(self._field_values)]
        if self.preferred_order is not None:
            parts.append(f"preferred_order={self.preferred_order!r}")
        if self.name_locale != LANGUAGE_TAG_UNDETERMINED:
            parts.append(f"name_locale={self.name_locale!r}")
        return f"{self.__class__.__qualname__}({', '.join(parts)})"


def _split_first_von_last(
    tokens: Sequence[str],
) -> tuple[list[str], list[str], list[str]]:
    first = []
    von = []
    last = []
    target = first
    for token in filter(None, tokens):
        if token[0].islower():
            if target is first:
                target = von
        else:
            if target is von:
                target = last
        target.append(token)
    if not last:
        if von:
            last = von[-1:]
            von = von[:-1]
        else:
            last = first[-1:]
            first = first[:-1]
    return first, von, last


def _split_von_last(tokens: Sequence[str]) -> tuple[list[str], list[str]]:
    von = []
    last = []
    target = von
    for token in filter(None, tokens):
        if not token[0].islower():
            target = last
        target.append(token)
    return von, last


def _join_von_last(von: str, last: str) -> str:
    if not von:
        return last
    if not last:
        return von
    return f"{von} {last}"


def _tokenize_bibtex(source: str) -> Iterable[str]:
    buf = []
    brace_level = 0
    escape = False
    for s in chain(source, [None]):
        if s is None:
            if buf:
                yield "".join(buf)
                buf.clear()
        elif escape:
            buf.append(s)
            escape = False
        elif s == "\\":
            escape = True
        elif s == "{":
            # XXX: Braces shouldn't create new tokens by themselves:
            # "Tokens are separated by whitespace or commas at brace-level zero"
            # if brace_level == 0 and buf:
            #     yield "".join(buf)
            #     buf.clear()
            brace_level += 1
            buf.append("{")
        elif s == "}":
            if brace_level > 0:
                brace_level -= 1
            buf.append("}")
            # if brace_level == 0:
            #     yield "".join(buf)
            #     buf.clear()
        elif brace_level == 0 and s.isspace():
            if buf:
                yield "".join(buf)
                buf.clear()
        elif brace_level == 0 and s == ",":
            if buf:
                yield "".join(buf)
                buf.clear()
            yield ","
        else:
            buf.append(s)
