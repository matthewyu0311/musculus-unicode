from .invariants import PROP_EMOJI, PROP_EMOJI_PRESENTATION, PROP_EMOJI_MODIFIER_BASE, PROP_EXTENDED_PICTOGRAPHIC
from ..util.ucd import get_boolean_property
from ..resources.ucd import EMOJI_DATA_PATH
from musculus.util.parse import to_code_point

_emoji_data = get_boolean_property(EMOJI_DATA_PATH)
_EMOJI_SET = _emoji_data[PROP_EMOJI]
_EMOJI_PRESENTATION_SET = _emoji_data[PROP_EMOJI_PRESENTATION]
_EMOJI_MODIFIER_BASE_SET = _emoji_data[PROP_EMOJI_MODIFIER_BASE]
_EXT_PICT_SET = _emoji_data[PROP_EXTENDED_PICTOGRAPHIC]

def is_emoji(cp: int | str, /) -> bool:
    return to_code_point(cp) in _EMOJI_SET

def is_emoji_presentation(cp: int | str, /) -> bool:
    return to_code_point(cp) in _EMOJI_PRESENTATION_SET

def is_emoji_modifier_base(cp: int | str, /) -> bool:
    return to_code_point(cp) in _EMOJI_MODIFIER_BASE_SET

def is_extended_pictographic(cp: int | str, /) -> bool:
    return to_code_point(cp) in _EXT_PICT_SET
