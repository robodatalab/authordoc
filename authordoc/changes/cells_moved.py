from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from authordoc.author_doc_change import AuthorDocChange

if TYPE_CHECKING:
    from authordoc.author_doc_change_visitor import AuthorDocChangeVisitor
    from authordoc.cells.cell import Cell

_Result = TypeVar("_Result")


@dataclass(frozen=True)
class CellsMoved(AuthorDocChange):
    cell_ids_before: list[str]
    cell_ids_after: list[str]

    def accept(self, visitor: AuthorDocChangeVisitor[_Result]) -> _Result:
        return visitor.visit_cells_moved(self)

    def invert(self) -> CellsMoved:
        inverted = CellsMoved(self.cell_ids_after, self.cell_ids_before)
        return inverted

    def apply_to(self, cells: Sequence[Cell]) -> list[Cell]:
        cell_of_id = {cell.unique_id: cell for cell in cells}
        moved = [cell_of_id[cell_id] for cell_id in self.cell_ids_after]
        return moved
