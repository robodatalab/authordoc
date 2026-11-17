from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, TypeVar
from uuid import uuid4

from authordoc.cells.cell import Cell

if TYPE_CHECKING:
    from authordoc.cells.cell_visitor import CellVisitor

CHARACTER = "character"

_Result = TypeVar("_Result")


@dataclass(frozen=True)
class CharacterCell(Cell):
    kind: str = field(default=CHARACTER, init=False)
    title: str = ""
    source: str = ""
    folded: bool = False
    at: tuple[int, int] | None = field(default=None, compare=False)
    _unique_id: str = field(default_factory=lambda: str(uuid4()))

    def with_source(self, source: str) -> CharacterCell:
        return replace(self, source=source)

    def with_folded(self, folded: bool) -> CharacterCell:
        return replace(self, folded=folded)

    def accept(self, visitor: CellVisitor[_Result]) -> _Result:
        return visitor.visit_character(self)
