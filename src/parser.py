"""Turn mini-Scheme tokens into expression trees."""

from __future__ import annotations

import re
from typing import Any

from lexer import SchemeSyntaxError
from values import DottedList, SchemeString, Symbol


INTEGER = re.compile(r"^[+-]?\d+$")
FLOAT = re.compile(r"^[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?$")


def parse_program(tokens: list[object]) -> list[Any]:
    expressions: list[Any] = []
    position = 0
    while position < len(tokens):
        expression, position = _parse_expression(tokens, position)
        expressions.append(expression)
    return expressions


def _parse_expression(tokens: list[object], position: int) -> tuple[Any, int]:
    if position >= len(tokens):
        raise SchemeSyntaxError("unexpected end of input")
    token = tokens[position]
    if token == "(":
        return _parse_list(tokens, position + 1)
    if token == ")":
        raise SchemeSyntaxError("unexpected )")
    if token == "'":
        quoted, next_position = _parse_expression(tokens, position + 1)
        return [Symbol("quote"), quoted], next_position
    return _parse_atom(token), position + 1


def _parse_list(tokens: list[object], position: int) -> tuple[Any, int]:
    items: list[Any] = []
    while position < len(tokens):
        token = tokens[position]
        if token == ")":
            return items, position + 1
        if token == ".":
            if not items:
                raise SchemeSyntaxError("dot needs a preceding list item")
            tail, position = _parse_expression(tokens, position + 1)
            if position >= len(tokens) or tokens[position] != ")":
                raise SchemeSyntaxError("dotted list needs exactly one tail")
            # `(a b . (c d))` is just the proper list `(a b c d)`; only keep a
            # DottedList when the tail is not itself a proper list.
            if isinstance(tail, list):
                items.extend(tail)
                return items, position + 1
            return DottedList(items, tail), position + 1
        expression, position = _parse_expression(tokens, position)
        items.append(expression)
    raise SchemeSyntaxError("missing )")


def _parse_atom(token: object) -> Any:
    if isinstance(token, SchemeString):
        return token
    assert isinstance(token, str)
    if token == "#t":
        return True
    if token == "#f":
        return False
    if INTEGER.match(token):
        return int(token)
    if FLOAT.match(token):
        return float(token)
    return Symbol(token)
