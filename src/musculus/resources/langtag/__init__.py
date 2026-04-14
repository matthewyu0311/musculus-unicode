import importlib.resources
from importlib.resources.abc import Traversable

if __package__ is None:
    raise ImportError("This shall not be used as a top-level module.")

LANGTAG_PATH: Traversable = importlib.resources.files(__package__)
SUBTAG_PATH: Traversable = LANGTAG_PATH.joinpath("language-subtag-registry.txt")
EXTENSIONS_PATH: Traversable = LANGTAG_PATH.joinpath("language-tag-extensions-registry.txt")
