"""Evaluation and application for mini-Scheme expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from standard_library import BuiltinProcedure
from environment import Environment
from values import DottedList, NIL, SchemeString, Symbol, is_number, is_true, list_to_pairs


@dataclass
class Closure:
    parameters: list[Symbol]
    body: list[Any]
    environment: Environment


def evaluate(expression: Any, environment: Environment) -> Any:
    if expression is NIL or isinstance(expression, (bool, SchemeString)) or is_number(expression):
        return expression
    if isinstance(expression, Symbol):
        return environment.lookup(expression)
    if isinstance(expression, DottedList):
        raise SyntaxError("cannot evaluate an improper list as a call")
    if not isinstance(expression, list):
        raise TypeError(f"cannot evaluate {expression!r}")
    if not expression:
        return NIL

    operator = expression[0]
    if isinstance(operator, Symbol):
        special_forms = {
            "quote": _evaluate_quote,
            "if": _evaluate_if,
            "cond": _evaluate_cond,
            "and": _evaluate_and,
            "or": _evaluate_or,
            "define": _evaluate_define,
            "lambda": _evaluate_lambda,
            "let": _evaluate_let,
            "begin": _evaluate_begin,
        }
        special_form = special_forms.get(str(operator))
        if special_form is not None:
            return special_form(expression[1:], environment)

    procedure = evaluate(operator, environment)
    arguments = [evaluate(argument, environment) for argument in expression[1:]]
    return apply(procedure, arguments)


def apply(procedure: Any, arguments: list[Any]) -> Any:
    if isinstance(procedure, BuiltinProcedure):
        return procedure(*arguments)
    if isinstance(procedure, Closure):
        if len(arguments) != len(procedure.parameters):
            raise TypeError("procedure called with the wrong number of arguments")
        call_environment = Environment(procedure.environment)
        for parameter, argument in zip(procedure.parameters, arguments):
            call_environment.define(parameter, argument)
        return evaluate_sequence(procedure.body, call_environment)
    raise TypeError("attempted to call a non-procedure")


def evaluate_sequence(expressions: list[Any], environment: Environment) -> Any:
    result: Any = None
    for expression in expressions:
        result = evaluate(expression, environment)
    return result


def _require_count(arguments: list[Any], minimum: int, maximum: int | None, name: str) -> None:
    valid = len(arguments) >= minimum and (maximum is None or len(arguments) <= maximum)
    if not valid:
        raise SyntaxError(f"{name}: wrong number of parts")


def _evaluate_quote(arguments: list[Any], environment: Environment) -> Any:
    _require_count(arguments, 1, 1, "quote")
    return _quote_to_value(arguments[0])


def _quote_to_value(expression: Any) -> Any:
    if isinstance(expression, list):
        return list_to_pairs(_quote_to_value(item) for item in expression)
    if isinstance(expression, DottedList):
        tail = _quote_to_value(expression.tail)
        return list_to_pairs((_quote_to_value(item) for item in expression.items), tail)
    return expression


def _evaluate_if(arguments: list[Any], environment: Environment) -> Any:
    _require_count(arguments, 2, 3, "if")
    branch = arguments[1] if is_true(evaluate(arguments[0], environment)) else (arguments[2] if len(arguments) == 3 else None)
    return evaluate(branch, environment) if branch is not None else None


def _evaluate_cond(arguments: list[Any], environment: Environment) -> Any:
    for index, clause in enumerate(arguments):
        if not isinstance(clause, list) or not clause:
            raise SyntaxError("cond: each clause must be a non-empty list")
        test_expression, *body = clause
        if isinstance(test_expression, Symbol) and test_expression == Symbol("else"):
            if index != len(arguments) - 1:
                raise SyntaxError("cond: else must be the last clause")
            return evaluate_sequence(body, environment) if body else True
        test_value = evaluate(test_expression, environment)
        if is_true(test_value):
            return evaluate_sequence(body, environment) if body else test_value
    return None


def _evaluate_and(arguments: list[Any], environment: Environment) -> Any:
    result: Any = True
    for expression in arguments:
        result = evaluate(expression, environment)
        if result is False:
            return False
    return result


def _evaluate_or(arguments: list[Any], environment: Environment) -> Any:
    for expression in arguments:
        result = evaluate(expression, environment)
        if result is not False:
            return result
    return False


def _evaluate_define(arguments: list[Any], environment: Environment) -> Symbol:
    _require_count(arguments, 2, None, "define")
    target = arguments[0]
    if isinstance(target, Symbol):
        _require_count(arguments, 2, 2, "define")
        environment.define(target, evaluate(arguments[1], environment))
        return target
    if isinstance(target, list) and target and isinstance(target[0], Symbol):
        name = target[0]
        parameters = _validate_parameters(target[1:])
        closure = Closure(parameters, arguments[1:], environment)
        environment.define(name, closure)
        return name
    raise SyntaxError("define: expected a name or function signature")


def _evaluate_lambda(arguments: list[Any], environment: Environment) -> Closure:
    _require_count(arguments, 2, None, "lambda")
    if not isinstance(arguments[0], list):
        raise SyntaxError("lambda: parameter list must be a list")
    return Closure(_validate_parameters(arguments[0]), arguments[1:], environment)


def _validate_parameters(parameters: list[Any]) -> list[Symbol]:
    if not all(isinstance(parameter, Symbol) for parameter in parameters):
        raise SyntaxError("parameters must be symbols")
    if len(set(parameters)) != len(parameters):
        raise SyntaxError("parameter names must be unique")
    return parameters


def _evaluate_let(arguments: list[Any], environment: Environment) -> Any:
    _require_count(arguments, 2, None, "let")
    raw_bindings = arguments[0]
    if not isinstance(raw_bindings, list):
        raise SyntaxError("let: bindings must be a list")
    names: list[Symbol] = []
    values: list[Any] = []
    for binding in raw_bindings:
        if not isinstance(binding, list) or len(binding) != 2 or not isinstance(binding[0], Symbol):
            raise SyntaxError("let: each binding must contain a name and value")
        names.append(binding[0])
        # Evaluate all initializers in the outer environment: parallel binding.
        values.append(evaluate(binding[1], environment))
    local = Environment(environment)
    for name, value in zip(names, values):
        local.define(name, value)
    return evaluate_sequence(arguments[1:], local)


def _evaluate_begin(arguments: list[Any], environment: Environment) -> Any:
    return evaluate_sequence(arguments, environment)
