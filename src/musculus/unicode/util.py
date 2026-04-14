"""Helper classes and functions for the rest of the unicode package.
Most of the functions make sense only in UCD contexts and are not designed to be useful standalone.
This file must not import any non-stdlib modules."""

import unicodedata
from array import array
from collections import ChainMap, deque
from collections.abc import (
    Callable,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from enum import StrEnum
from fractions import Fraction
from string import ascii_letters, digits
from types import NotImplementedType
from typing import ClassVar, Literal, NewType, Self, cast

type ReturnValue = bool | int | Fraction | str | tuple | NotImplementedType | None
PropNameXML = NewType("PropNameXML", str)
Collated = NewType("Collated", str)
CollatedName = NewType("CollatedName", str)
CodePoint = NewType("CodePoint", int)
type NormalizationForm = Literal["NFC", "NFD", "NFKC", "NFKD"]

MAX_UNICODE = CodePoint(0x10FFFF)
BITS = 21
MAX_ASCII = CodePoint(0x007F)

ASCII_CAPITAL_A = CodePoint(0x0041)
ASCII_CAPITAL_Z = CodePoint(0x005A)
ASCII_SMALL_A = CodePoint(0x0061)
ASCII_SMALL_Z = CodePoint(0x007A)

MILLION_RANGE = cast(Sequence[CodePoint], range(MAX_UNICODE + 1))
MILLION_RANGE_REVERSED = cast(Sequence[CodePoint], range(MAX_UNICODE, -1, -1))

# These functions operate on code points, not strings


def ascii_casefold(cp: CodePoint) -> CodePoint:
    if ASCII_CAPITAL_A <= cp <= ASCII_CAPITAL_Z:
        return CodePoint(cp + 0x0020)
    return cp


def pascal_case(s: str, check_identifier: bool = True) -> str:
    """PascalCase a string such that it is suitable for use as a class name.
    This is designed to process long property names (second column and beyond in PropertyAliases.txt).
    The result loose-matches the input.

    For example, "kRSUnicode" becomes "KRSUnicode".
    """
    if not s:
        return ""
    output = "".join(
        w[0].upper() + w[1:] for w in s.replace(" ", "").replace("-", "_").split("_")
    )

    if output.isidentifier() or not check_identifier:
        return output
    return output + "_"


def screaming_snake_case(s: str, check_identifier: bool = True) -> str:
    """SCREAMING_SNAKE_CASE a string such that it is suitable for use as a name for constants.
    This is designed to process long value aliases (third column and beyond in PropertyValueAliases.txt).

    The result loose-matches the input, despite how it looks!

    For example, "Arabic_Presentation_Forms-A" becomes "ARABIC_PRESENTATION_FORMS_A".
    """
    if not s:
        return ""
    output = s.strip().upper().replace(" ", "_").replace("-", "_")

    if output.isidentifier() or not check_identifier:
        return output
    return output + "_"


def to_code_point(cp: str | int, /) -> CodePoint:
    if isinstance(cp, str):
        return CodePoint(ord(cp))
    if not 0 <= cp <= MAX_UNICODE:
        raise UnicodeError(f"Code point ouside of 0..U+10FFFF: {cp}")
    return CodePoint(cp)


def from_code_point(cp: str | int, /) -> str:
    if isinstance(cp, int):
        return chr(cp)
    if len(cp) != 1:
        raise ValueError(f"String of length != 1")
    return cp


def collate(prop: str, /) -> Collated:
    return Collated(
        "".join(
            c.casefold()
            for c in prop
            if c != "_" and not c.isspace() and unicodedata.category(c) != "Pd"
        )
    )


def collate_uax44_lm2(name: str, /) -> CollatedName:
    output = []
    name = f" {name} "
    for i, c in enumerate(name):
        match c:
            case " " | "_":
                continue
            case alpha if alpha in ascii_letters:
                output.append(alpha.lower())
            case digit if digit in digits:
                output.append(digit)
            case "-":
                if name[i - 1] in "_ " or name[i + 1] in "_ ":
                    # Non-medial hyphen
                    output.append("-")
            case _:
                raise UnicodeError(f"Invalid name: {name.strip()!r}")
    n = "".join(output)
    # Special case U+1180 HANGUL JUNGSEONG O-E
    if n == "hanguljungseongoe" and "o-e" in name.lower():
        return CollatedName("hanguljungseongo-e")
    return CollatedName(n)


def remove_prefix(collated: Collated) -> Collated:
    # UAX44-LM3: remove the "is" prefix
    if collated.startswith("is") and len(collated) > 2:
        return Collated(collated[2:])
    return collated


class LooseMatchStrEnum(StrEnum):
    __collated__: ClassVar[bool] = False

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._precollate()

    @classmethod
    def _precollate(cls):
        if cls.__collated__:
            return
        existing = dict(cls.__members__)
        for k, v in existing.items():
            kc = collate(k)
            if kc not in existing:
                try:
                    v._add_alias_(kc)  # type: ignore
                except NameError:
                    pass  # Already assigned
            no_prefix = remove_prefix(kc)
            if no_prefix != kc and no_prefix not in existing:
                try:
                    v._add_alias_(no_prefix)  # type: ignore
                except NameError:
                    pass  # No-prefix form has already been assigned
            vv = v.value
            vc = collate(vv)
            if vc != vv:
                try:
                    v._add_value_alias_(vc)  # type: ignore
                except ValueError:
                    pass
            vnp = remove_prefix(vc)
            if vnp != vc:
                try:
                    v._add_value_alias_(vnp)  # type: ignore
                except ValueError:
                    pass
        cls.__collated__ = True

    @classmethod
    def _missing_(cls, value: str, /) -> Self:
        try:
            return cls.__members__[value]
        except KeyError:
            pass

        collated = remove_prefix(collate(value))
        if collated != value:
            try:
                return cls.__members__[collated]
            except KeyError:
                try:
                    return cls(collated)
                except ValueError as ve:
                    raise ve
        raise ValueError(value)


def loose_match_boolean(v: str) -> bool:
    if v in {"", "Y", "Yes", "True", "T"}:
        return True
    return collate(v) in {"y", "yes", "true", "t"}


def ucd_tokenize(
    lines: Iterable[str],
    *,
    keep_missing_lines: bool = False,
    filter: Callable[[str], bool] | None = None,
) -> Iterable[list[str] | tuple[str, ...]]:
    # All ";"-separated .txt property files share a similar format
    for line in lines:
        line = line.lstrip()
        if not line:
            continue
        if filter is not None and not filter(line):
            continue
        is_missing = False
        if line[0] == "#":
            if keep_missing_lines and line.startswith("# @missing:"):
                is_missing = True
                line = line[11:]
            else:
                continue
        line, _, _ = line.partition("#")
        tokens = map(str.strip, line.split(";"))

        if is_missing:
            yield list(tokens)
        else:
            yield tuple(tokens)


def dict_from_pva(pva_lines: Iterable[str], prop: str):
    m = {}
    for token_line in ucd_tokenize(
        pva_lines, keep_missing_lines=False, filter=lambda l: l.startswith(prop)
    ):
        p, name, *aliases = token_line
        if p != prop:
            continue
        for alias in aliases:
            m[screaming_snake_case(alias)] = name
    return m

class TwoStageTable(Mapping[int | str, int]):
    arrays: dict[int, array[int]]
    bits_per_plane: int
    plane_defaults: list[int]
    typecode: str

    def __init__(self, *, default: int, bits_per_plane: int = 16, typecode: str = "B") -> None:
        self.bits_per_plane = bits_per_plane
        self.arrays = {}
        self.plane_defaults = [default] * ((MAX_UNICODE >> bits_per_plane) + 1)
        self.typecode = typecode

    def insert(self, start_cp: int, end_cp: int, value: int):
        bpp = self.bits_per_plane
        pwr = 2 ** bpp
        pwrm1 = pwr - 1
        if start_cp > end_cp:
            raise ValueError
        start_plane = start_cp >> bpp
        end_plane = end_cp >> bpp
        if start_plane != end_plane:
            # This is very rare (perhaps never happens) in the case of script
            # but in case it does, we recur each plane
            for plane in range(start_plane, end_plane + 1):
                s = start_cp if plane == start_plane else plane << bpp
                e = end_cp if plane == end_plane else (s | pwrm1)
                self.insert(s, e, value)
        start_index = start_cp & pwrm1
        end_index = end_cp & pwrm1
        try:
            arr = self.arrays[start_plane]
        except LookupError:
            arr = array(self.typecode, [self.plane_defaults[start_plane]] * pwr)
            self.arrays[start_plane] = arr
        if start_cp == end_cp:
            arr[start_index] = value
        else:
            arr[start_index : end_index + 1] = array(
                self.typecode, [value] * (end_index - start_index + 1)
            )

    def _compress_plane(self, plane: int) -> None:
        try:
            arr = self.arrays[plane]
        except KeyError:
            return
        s = set(arr)
        if len(s) == 1:
            # If the plane is homogeneous, drop the array
            v = s.pop()
            self.plane_defaults[plane] = v
            del self.arrays[plane]

    def compress_planes(self, start_cp: int = 0, end_cp: int = MAX_UNICODE) -> None:
        start_plane = start_cp >> self.bits_per_plane
        end_plane = end_cp >> self.bits_per_plane
        for plane in range(start_plane, end_plane + 1):
            self._compress_plane(plane)

    def __getitem__(self, key: int | str) -> int:
        bpp = self.bits_per_plane
        cp = to_code_point(key)
        plane = cp >> bpp
        index = cp & (2 ** bpp - 1)
        try:
            return self.arrays[plane][index]
        except LookupError:
            return self.plane_defaults[plane]
    
    def __iter__(self) -> Iterator[int]:
        yield from range(MAX_UNICODE + 1)

    def __len__(self) -> int:
        return MAX_UNICODE + 1