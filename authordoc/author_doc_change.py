from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from authordoc.author_doc_change_visitor import AuthorDocChangeVisitor
    from authordoc.cells.cell import Cell

_Result = TypeVar("_Result")


class AuthorDocChange(ABC):
    @abstractmethod
    def accept(self, visitor: AuthorDocChangeVisitor[_Result]) -> _Result: ...

    @abstractmethod
    def invert(self) -> AuthorDocChange: ...

    @abstractmethod
    def apply_to(self, cells: Sequence[Cell]) -> list[Cell]: ...
