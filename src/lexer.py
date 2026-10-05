"""Tokenisation for the small Scheme surface syntax."""

from __future__ import annotations

from values import SchemeString


class SchemeSyntaxError(ValueError):
    pass


def tokenize(source: str) -> list[object]:
    """Split source into parentheses, quote marks, words, and string values."""
    tokens: list[object] = []
    index = 0
    length = len(source)

    while index < length:
        char = source[index]
        if char.isspace():
            index += 1
        elif char == ";":
            newline = source.find("\n", index)
            index = length if newline == -1 else newline + 1
        elif char in "()'":
            tokens.append(char)
            index += 1
        elif char == '"':
            index += 1
            pieces: list[str] = []
            while index < length:
                char = source[index]
                if char == '"':
                    index += 1
                    break
                if char == "\\":
                    index += 1
                    if index == length:
                        raise SchemeSyntaxError("unfinished string escape")
                    escaped = source[index]
                    pieces.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(escaped, escaped))
                    index += 1
                else:
                    pieces.append(char)
                    index += 1
            else:
                raise SchemeSyntaxError("unterminated string")
            tokens.append(SchemeString("".join(pieces)))
        else:
            start = index
            while index < length and not source[index].isspace() and source[index] not in "();'\"":
                index += 1
            tokens.append(source[start:index])
    return tokens
