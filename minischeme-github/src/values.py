"""Runtime values used by the mini-Scheme interpreter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


class Symbol(str):
    """A Scheme identifier, kept distinct from a string literal."""


class SchemeString(str):
    """A Scheme string literal, kept distinct from a Symbol."""


class Nil:
    """The singleton empty list."""

    def __repr__(self) -> str:
        return "NIL"


NIL = Nil()


@dataclass
class Pair:
    first: Any
    rest: Any


@dataclass
class DottedList:
    """Parser-only representation of source such as ``(a b . c)``."""

    items: list[Any]
    tail: Any


def list_to_pairs(items: Iterable[Any], tail: Any = NIL) -> Any:
    """Make the linked-pair representation used for Scheme lists."""
    result = tail
    for item in reversed(list(items)):
        result = Pair(item, result)
    return result


def pairs_to_list(value: Any) -> list[Any]:
    """Return a Python list for a proper Scheme list, or raise ValueError."""
    result: list[Any] = []
    while isinstance(value, Pair):
        result.append(value.first)
        value = value.rest
    if value is not NIL:
        raise ValueError("expected a proper list")
    return result


def is_number(value: Any) -> bool:
    # bool is an int subclass in Python, but not a number in Scheme.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_true(value: Any) -> bool:
    """Scheme's only false value is #f."""
    return value is not False
