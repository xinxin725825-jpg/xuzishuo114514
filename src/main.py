"""Command-line entry point for the mini-Scheme interpreter."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from standard_library import create_global_environment
from evaluator import evaluate
from lexer import tokenize
from parser import parse_program
from printer import scheme_repr

# Interpretation is recursive, so a deeply recursive Scheme program consumes
# several Python frames per Scheme call.  The default limit is low enough that
# a legitimate program could exhaust it, so give it room; the interpreter still
# reports a clean error instead of a traceback if a program goes even deeper.
RECURSION_LIMIT = 20000


def run_source(source: str, environment, output: TextIO) -> None:
    for expression in parse_program(tokenize(source)):
        result = evaluate(expression, environment)
        if result is not None:
            output.write(scheme_repr(result) + "\n")


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    if sys.getrecursionlimit() < RECURSION_LIMIT:
        sys.setrecursionlimit(RECURSION_LIMIT)
    environment = create_global_environment(sys.stdout)
    try:
        if arguments:
            for filename in arguments:
                run_source(Path(filename).read_text(encoding="utf-8"), environment, sys.stdout)
        else:
            run_source(sys.stdin.read(), environment, sys.stdout)
        return 0
    except RecursionError:
        print("error: maximum recursion depth exceeded", file=sys.stderr)
        return 1
    except OSError as error:
        # e.g. a file argument that does not exist or cannot be read.
        print(f"error: cannot read input: {error}", file=sys.stderr)
        return 1
    except (ValueError, TypeError, NameError, SyntaxError, ZeroDivisionError, ArithmeticError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
