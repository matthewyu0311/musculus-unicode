import importlib.resources
from importlib.resources.abc import Traversable

if __package__ is None:
    raise ImportError("This shall not be used as a top-level module.")

UCD_PATH: Traversable = importlib.resources.files(__package__)
PVA_PATH: Traversable = UCD_PATH.joinpath("PropertyValueAliases.txt")
SCRIPTS_PATH: Traversable = UCD_PATH.joinpath("Scripts.txt")
SCRIPT_EXTENSIONS_PATH: Traversable = UCD_PATH.joinpath("ScriptExtensions.txt")
EMOJI_DATA_PATH: Traversable = UCD_PATH.joinpath("emoji").joinpath("emoji-data.txt")
