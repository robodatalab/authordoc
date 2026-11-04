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
class CellHeaderChanged(AuthorDocChange):
    header_before: Cell
    header_after: Cell

    def accept(self, visitor: AuthorDocChangeVisitor[_Result]) -> _Result:
        return visitor.visit_cell_header_changed(self)

    def invert(self) -> CellHeaderChanged:
        inverted = CellHeaderChanged(self.header_after, self.header_before)
        return inverted

    def apply_to(self, cells: Sequence[Cell]) -> list[Cell]:
        changed = [
            self.header_after.with_source(cell.source) if cell.unique_id == self.header_after.unique_id else cell
            for cell in cells
        ]
        return changed
