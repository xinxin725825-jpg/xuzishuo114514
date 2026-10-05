"""Lexically scoped variable environments."""

from __future__ import annotations

from typing import Any

from values import Symbol


class Environment:
    def __init__(self, parent: "Environment | None" = None) -> None:
        self.parent = parent
        self.bindings: dict[Symbol, Any] = {}

    def define(self, name: Symbol, value: Any) -> None:
        self.bindings[name] = value

    def lookup(self, name: Symbol) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        raise NameError(f"unknown symbol: {name}")
