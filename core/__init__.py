"""Core package.

``Bot`` and ``Player`` are re-exported here for convenience, but they are
resolved lazily (:pep:`562`).  Importing them eagerly made ``import model``
fail: ``model.*`` needs ``core.utils``, which ran this ``__init__``, which
pulled in ``Bot`` -> ``Command`` -> ``Player`` -> back into the still-loading
``model.inventory``.  Lazy resolution keeps ``from core import Bot`` working
while letting the model layer be imported on its own (tests, tooling).
"""
from typing import Any

__all__ = ["Bot", "Player"]


def __getattr__(name: str) -> Any:
    if name == "Bot":
        from .bot import Bot
        return Bot
    if name == "Player":
        from .player import Player
        return Player
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list:
    return sorted(list(globals()) + __all__)
