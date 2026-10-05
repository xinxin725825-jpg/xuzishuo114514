"""Scheme value formatting, shared by the REPL-style runner and display."""

from __future__ import annotations

from typing import Any

from values import NIL, Pair, SchemeString, Symbol


def scheme_repr(value: Any) -> str:
    if value is None:
        # The no-value result (e.g. `(if #f 1)` or `display`) is never printed by
        # the top-level runner; if it somehow reaches a printer nested inside a
        # structure, say so rather than emitting a blank hole.
        raise TypeError("cannot print a value that has no representation")
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if value is NIL:
        return "()"
    if isinstance(value, SchemeString):
        return '"' + _escape_string(value) + '"'
    if isinstance(value, Symbol):
        return str(value)
    if isinstance(value, Pair):
        return _pair_repr(value)
    if isinstance(value, float):
        return _float_repr(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value
    # Built-ins and closures deliberately share the unspecified procedure form.
    if type(value).__name__ in ("BuiltinProcedure", "Closure"):
        return "#<procedure>"
    # Anything else is not a mini-Scheme value; say so instead of pretending it
    # is a procedure, which would silently hide an internal error.
    raise TypeError(f"cannot print value of type {type(value).__name__}")


def _float_repr(value: float) -> str:
    if value != value or value in (float("inf"), float("-inf")):
        raise TypeError("cannot print a non-finite number")
    # `repr` keeps the ".0" marker, so floating point results stay visibly
    # distinct from integers (e.g. 2.0 rather than 2).
    return repr(value)


def display_repr(value: Any) -> str:
    """Format a value the way `display` writes it: strings lose their quotes."""
    if value is None:
        raise TypeError("cannot print a value that has no representation")
    if isinstance(value, SchemeString):
        return str(value)
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if value is NIL:
        return "()"
    if isinstance(value, Pair):
        return _pair_display(value)
    return scheme_repr(value)


def _escape_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def _pair_repr(pair: Pair) -> str:
    return _pair_text(pair, scheme_repr)


def _pair_display(pair: Pair) -> str:
    return _pair_text(pair, display_repr)


def _pair_text(pair: Pair, render) -> str:
    items: list[str] = []
    current: Any = pair
    while isinstance(current, Pair):
        items.append(render(current.first))
        current = current.rest
    if current is NIL:
        return "(" + " ".join(items) + ")"
    return "(" + " ".join(items) + " . " + render(current) + ")"
