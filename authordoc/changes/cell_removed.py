from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from authordoc.author_doc_change import AuthorDocChange
from authordoc.changes import cell_added

if TYPE_CHECKING:
    from authordoc.author_doc_change_visitor import AuthorDocChangeVisitor
    from authordoc.cells.cell import Cell

_Result = TypeVar("_Result")


@dataclass(frozen=True)
class CellRemoved(AuthorDocChange):
    cell_index: int
    cell: Cell

    def accept(self, visitor: AuthorDocChangeVisitor[_Result]) -> _Result:
        return visitor.visit_cell_removed(self)

    def invert(self) -> cell_added.CellAdded:
        inverted = cell_added.CellAdded(self.cell_index, self.cell)
        return inverted

    def apply_to(self, cells: Sequence[Cell]) -> list[Cell]:
        cells_above = cells[: self.cell_index]
        cells_below = cells[self.cell_index + 1 :]
        return [*cells_above, *cells_below]
