"""The standard procedures listed in the mini-Scheme specification."""

from __future__ import annotations

import math
from functools import reduce
from operator import mul
from typing import Any, Callable, TextIO

from environment import Environment
from printer import display_repr
from values import NIL, Pair, SchemeString, Symbol, is_number, list_to_pairs, pairs_to_list


class BuiltinProcedure:
    def __init__(self, function: Callable[..., Any], name: str) -> None:
        self.function = function
        self.name = name

    def __call__(self, *arguments: Any) -> Any:
        return self.function(*arguments)


def _require_count(arguments: tuple[Any, ...], count: int, name: str) -> None:
    if len(arguments) != count:
        raise TypeError(f"{name}: expected {count} arguments")


def _require_min_count(arguments: tuple[Any, ...], count: int, name: str) -> None:
    if len(arguments) < count:
        raise TypeError(f"{name}: expected at least {count} arguments")


def _require_numbers(arguments: tuple[Any, ...], name: str) -> None:
    if not all(is_number(value) for value in arguments):
        raise TypeError(f"{name}: expected numbers")


def _require_integers(arguments: tuple[Any, ...], name: str) -> None:
    _require_numbers(arguments, name)
    if not all(isinstance(value, int) for value in arguments):
        raise TypeError(f"{name}: expected integers")


def _truncating_quotient(left: int, right: int) -> int:
    if right == 0:
        raise ZeroDivisionError("division by zero")
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient


def _add(*arguments: Any) -> Any:
    _require_numbers(arguments, "+")
    return sum(arguments)


def _subtract(*arguments: Any) -> Any:
    _require_min_count(arguments, 1, "-")
    _require_numbers(arguments, "-")
    return -arguments[0] if len(arguments) == 1 else arguments[0] - sum(arguments[1:])


def _multiply(*arguments: Any) -> Any:
    _require_numbers(arguments, "*")
    return reduce(mul, arguments, 1)


def _divide(*arguments: Any) -> Any:
    _require_min_count(arguments, 1, "/")
    _require_numbers(arguments, "/")
    if len(arguments) == 1:
        return 1 / arguments[0]
    result = arguments[0]
    for divisor in arguments[1:]:
        if isinstance(result, int) and isinstance(divisor, int):
            result = _truncating_quotient(result, divisor)
        else:
            result /= divisor
    return result


def _abs(*arguments: Any) -> Any:
    _require_count(arguments, 1, "abs")
    _require_numbers(arguments, "abs")
    return abs(arguments[0])


def _expt(*arguments: Any) -> Any:
    """`expt` takes exactly two numbers and must return a real number."""
    _require_count(arguments, 2, "expt")
    _require_numbers(arguments, "expt")
    base, exponent = arguments
    try:
        result = base ** exponent
    except OverflowError:
        # e.g. `(expt 2.0 1024)`: the real result is too large for a float.
        raise OverflowError("expt: result is too large to represent") from None
    if isinstance(result, complex):
        # e.g. `(expt -1 0.5)`: no real result exists.
        raise TypeError("expt: result is not a real number")
    if isinstance(result, float) and (result != result or result in (float("inf"), float("-inf"))):
        raise OverflowError("expt: result is too large to represent")
    return result


def _modulo(*arguments: Any) -> Any:
    _require_count(arguments, 2, "modulo")
    left, right = arguments
    _require_integers(arguments, "modulo")
    if right == 0:
        raise ZeroDivisionError("division by zero")
    return left % right


def _quotient(*arguments: Any) -> Any:
    _require_count(arguments, 2, "quotient")
    left, right = arguments
    _require_numbers(arguments, "quotient")
    if isinstance(left, int) and isinstance(right, int):
        return _truncating_quotient(left, right)
    return math.trunc(left / right)


def _make_comparison(name: str) -> Callable[..., bool]:
    """Build a chained comparison.  spec §5: operands are numbers or symbols."""
    if name == "=":
        ordered = False
        compare = lambda a, b: a == b  # noqa: E731
    else:
        ordered = name != "="
        compare = {
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
        }[name]

    def chained(*arguments: Any) -> bool:
        for left, right in zip(arguments, arguments[1:]):
            both_numbers = is_number(left) and is_number(right)
            both_symbols = isinstance(left, Symbol) and isinstance(right, Symbol)
            if not (both_numbers or both_symbols):
                raise TypeError(f"{name}: arguments must be two numbers or two symbols")
            if ordered and both_symbols:
                compare_values = (str(left), str(right))
            else:
                compare_values = (left, right)
            if not compare(compare_values[0], compare_values[1]):
                return False
        return True

    return chained


def _not(*arguments: Any) -> bool:
    _require_count(arguments, 1, "not")
    # spec §4.4: only #f is false.
    return arguments[0] is False


def _cons(*arguments: Any) -> Pair:
    _require_count(arguments, 2, "cons")
    return Pair(arguments[0], arguments[1])


def _car(*arguments: Any) -> Any:
    _require_count(arguments, 1, "car")
    pair = arguments[0]
    if not isinstance(pair, Pair):
        raise TypeError("car: expected a pair")
    return pair.first


def _cdr(*arguments: Any) -> Any:
    _require_count(arguments, 1, "cdr")
    pair = arguments[0]
    if not isinstance(pair, Pair):
        raise TypeError("cdr: expected a pair")
    return pair.rest


def _list(*values: Any) -> Any:
    return list_to_pairs(values)


def _length(*arguments: Any) -> int:
    _require_count(arguments, 1, "length")
    return len(pairs_to_list(arguments[0]))


def _append(*lists: Any) -> Any:
    if not lists:
        return NIL
    # Every argument except the last must be a proper list; the last one may be
    # any value, and the result is consed onto it (so the result can be a dotted
    # pair, e.g. `(append '(1 2) 3)` -> `(1 2 . 3)`).
    values: list[Any] = []
    for value in lists[:-1]:
        values.extend(pairs_to_list(value))
    return list_to_pairs(values, lists[-1])


def _null(*arguments: Any) -> bool:
    _require_count(arguments, 1, "null?")
    return arguments[0] is NIL


def _pair(*arguments: Any) -> bool:
    _require_count(arguments, 1, "pair?")
    return isinstance(arguments[0], Pair)


def _symbol(*arguments: Any) -> bool:
    _require_count(arguments, 1, "symbol?")
    return isinstance(arguments[0], Symbol)


def _string(*arguments: Any) -> bool:
    _require_count(arguments, 1, "string?")
    return isinstance(arguments[0], SchemeString)


def _boolean(*arguments: Any) -> bool:
    _require_count(arguments, 1, "boolean?")
    return isinstance(arguments[0], bool)


def _procedure(*arguments: Any) -> bool:
    _require_count(arguments, 1, "procedure?")
    value = arguments[0]
    return isinstance(value, BuiltinProcedure) or type(value).__name__ == "Closure"


def _number(*arguments: Any) -> bool:
    _require_count(arguments, 1, "number?")
    return is_number(arguments[0])


def _zero(*arguments: Any) -> bool:
    _require_count(arguments, 1, "zero?")
    _require_numbers(arguments, "zero?")
    return arguments[0] == 0


def _even(*arguments: Any) -> bool:
    _require_count(arguments, 1, "even?")
    _require_integers(arguments, "even?")
    return arguments[0] % 2 == 0


def _odd(*arguments: Any) -> bool:
    _require_count(arguments, 1, "odd?")
    _require_integers(arguments, "odd?")
    return arguments[0] % 2 != 0


def _is_proper_list(*arguments: Any) -> bool:
    _require_count(arguments, 1, "list?")
    value = arguments[0]
    seen: set[int] = set()
    while isinstance(value, Pair):
        identity = id(value)
        if identity in seen:
            return False
        seen.add(identity)
        value = value.rest
    return value is NIL


def _eq(left: Any, right: Any) -> bool:
    if left is NIL and right is NIL:
        return True
    if is_number(left) and is_number(right):
        # Compare by value, but keep the type consistent with `equal?` so that
        # `eq?` never implies `equal?` for the same pair of values.  The type
        # check also stops Python's `True == 1` rule leaking into Scheme.
        return type(left) is type(right) and left == right
    if isinstance(left, (Symbol, bool)) and isinstance(right, type(left)):
        return left == right
    return left is right


def _equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, Pair):
        return _equal(left.first, right.first) and _equal(left.rest, right.rest)
    if left is NIL:
        return True
    return left == right


def create_global_environment(output: TextIO) -> Environment:
    """Create an initial environment with every required built-in procedure."""
    environment = Environment()

    def display(value: Any) -> None:
        output.write(display_repr(value))
        output.flush()

    def newline() -> None:
        output.write("\n")
        output.flush()

    def guarded_display(*arguments: Any) -> None:
        _require_count(arguments, 1, "display")
        display(arguments[0])

    def guarded_newline(*arguments: Any) -> None:
        _require_count(arguments, 0, "newline")
        newline()

    procedures: dict[str, Callable[..., Any]] = {
        "+": _add,
        "-": _subtract,
        "*": _multiply,
        "/": _divide,
        "modulo": _modulo,
        "quotient": _quotient,
        "expt": _expt,
        "abs": _abs,
        "=": _make_comparison("="),
        "<": _make_comparison("<"),
        ">": _make_comparison(">"),
        "<=": _make_comparison("<="),
        ">=": _make_comparison(">="),
        "not": _not,
        "cons": _cons,
        "car": _car,
        "cdr": _cdr,
        "list": _list,
        "length": _length,
        "append": _append,
        "null?": _null,
        "pair?": _pair,
        "list?": _is_proper_list,
        "number?": _number,
        "boolean?": _boolean,
        "symbol?": _symbol,
        "string?": _string,
        # Closure lives in evaluator, which imports this module.  Checking its
        # stable runtime class name avoids a circular import while keeping the
        # predicate limited to the interpreter's two procedure representations.
        "procedure?": _procedure,
        "zero?": _zero,
        "even?": _even,
        "odd?": _odd,
        "eq?": _eq,
        "equal?": _equal,
        "display": guarded_display,
        "newline": guarded_newline,
    }
    for name, procedure in procedures.items():
        environment.define(Symbol(name), BuiltinProcedure(procedure, name))
    return environment
