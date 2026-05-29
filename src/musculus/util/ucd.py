from array import array
from collections.abc import (
    Callable,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
    Set,
)
from enum import StrEnum
from importlib.resources.abc import Traversable
from typing import cast, overload

from musculus.util.parse import (
    MAX_UNICODE,
    CodePoint,
    LooseMatchStrEnum,
    screaming_snake_case,
    to_code_point,
)
from ..resources.ucd import PVA_PATH


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


def from_pva(pva_lines: Iterable[str], prop: str) -> tuple[dict[str, str], str | None]:
    m = {}
    default = None
    for token_line in ucd_tokenize(
        pva_lines, keep_missing_lines=True, filter=lambda l: l.startswith(prop)
    ):
        p, principal_value, *aliases = token_line
        if p != prop:
            continue
        if isinstance(token_line, list):
            default = principal_value
        else:
            for alias in aliases:
                m[screaming_snake_case(alias)] = principal_value
    return m, default


class TwoStageTable(Mapping[int | str, int]):
    arrays: dict[int, array[int]]
    bits_per_plane: int
    plane_defaults: list[int]
    typecode: str

    def __init__(
        self, *, default: int, bits_per_plane: int = 16, typecode: str = "B"
    ) -> None:
        self.bits_per_plane = bits_per_plane
        self.arrays = {}
        self.plane_defaults = [default] * ((MAX_UNICODE >> bits_per_plane) + 1)
        self.typecode = typecode

    def insert(self, start_cp: int, end_cp: int, value: int):
        bpp = self.bits_per_plane
        pwr = 2**bpp
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
        index = cp & (2**bpp - 1)
        try:
            return self.arrays[plane][index]
        except LookupError:
            return self.plane_defaults[plane]

    def __iter__(self) -> Iterator[int]:
        yield from range(MAX_UNICODE + 1)

    def __len__(self) -> int:
        return MAX_UNICODE + 1


class OneStageTable(Mapping[int | str, int]):
    def __init__(self, *, default: int) -> None:
        self.default = default
        self.dict = {}

    def insert(self, start_cp: int, end_cp: int, value: int):
        if not 0 <= start_cp <= end_cp <= MAX_UNICODE:
            raise ValueError
        for i in range(start_cp, end_cp + 1):
            self.dict[i] = value

    def __getitem__(self, key: int | str) -> int:
        i = to_code_point(key)
        try:
            return self.dict[i]
        except KeyError:
            if not 0 <= i <= MAX_UNICODE:
                raise KeyError
            return self.default

    def __iter__(self) -> Iterator[int]:
        yield from range(MAX_UNICODE + 1)

    def __len__(self) -> int:
        return MAX_UNICODE + 1


@overload
def get_ucd_table[T: LooseMatchStrEnum](
    res: Traversable,
    prop: str,
    enum_name: str,
    *,
    bits_per_plane: int = 16,
    compress: Sequence[tuple[int, int]] = (),
) -> tuple[type[T], TwoStageTable, Callable[[str | int], T]]: ...


@overload
def get_ucd_table[T: LooseMatchStrEnum](
    res: Traversable, prop: str, enum_name: str, *, bits_per_plane: None
) -> tuple[type[T], OneStageTable, Callable[[str | int], T]]: ...


def get_ucd_table[T: LooseMatchStrEnum](
    res: Traversable,
    prop: str,
    enum_name: str,
    *,
    bits_per_plane: int | None = 16,
    compress: Sequence[tuple[int, int]] = (),
) -> tuple[type[T], OneStageTable | TwoStageTable, Callable[[str | int], T]]:
    with PVA_PATH.open("r", encoding="utf-8", errors="strict") as pva:
        d, default = from_pva(pva, prop)
    d = {screaming_snake_case(k): v for k, v in d.items()}
    EnumClass = cast(type[StrEnum], LooseMatchStrEnum(enum_name, d))

    prop_list = list(EnumClass)
    prop_list_inv = {v: i for i, v in enumerate(prop_list)}
    typecode = "B" if len(prop_list) <= 256 else "H"
    if default is not None:
        # The PVA contains a @missing line for this property
        default_index = prop_list_inv[EnumClass(default)]
    # Otherwise, we will later get the default from the particular property file
    table = None
    with res.open("r", encoding="utf-8", errors="strict") as txt:
        for token in ucd_tokenize(txt, keep_missing_lines=True):
            code_points, value = token
            pvalue = EnumClass(value)
            s, dots, e = code_points.partition("..")
            start_cp = int(s, base=16)
            if isinstance(token, list):
                default = pvalue
                default_index = prop_list_inv[EnumClass(default)]
            if dots:
                end_cp = int(e, base=16)
            else:
                end_cp = start_cp
            if table is None:
                if bits_per_plane is None:
                    table = OneStageTable(default=default_index)
                else:
                    table = TwoStageTable(
                        default=default_index,
                        bits_per_plane=bits_per_plane,
                        typecode=typecode,
                    )
            table.insert(start_cp, end_cp, prop_list_inv[pvalue])
    if table is None:
        if bits_per_plane is None:
            table = OneStageTable(default=default_index)
        else:
            table = TwoStageTable(
                default=default_index, bits_per_plane=bits_per_plane, typecode=typecode
            )
    if isinstance(table, TwoStageTable):
        for start, end in compress:
            table.compress_planes(start, end)

    def get(c: str | int, /) -> T:
        return prop_list[table[c]]  # type: ignore

    return EnumClass, table, get  # type: ignore

def get_boolean_property(res: Traversable) -> dict[str, Set[CodePoint]]:
    output = {}
    with res.open("r", encoding="utf-8", errors="strict") as txt:
        for token in ucd_tokenize(txt, keep_missing_lines=False):
            code_points, prop = token
            try:
                result = output[prop]
            except KeyError:
                result = output.setdefault(prop, set())
            s, dots, e = code_points.partition("..")
            start_cp = int(s, base=16)
            if dots:
                end_cp = int(e, base=16)
                result.update(range(start_cp, end_cp + 1))
            else:
                result.add(start_cp)
    return output