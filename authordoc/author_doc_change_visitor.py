from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from authordoc.changes.cell_added import CellAdded
    from authordoc.changes.cell_header_changed import CellHeaderChanged
    from authordoc.changes.cell_removed import CellRemoved
    from authordoc.changes.cell_text_changed import CellTextChanged
    from authordoc.changes.cells_moved import CellsMoved

_Result = TypeVar("_Result")


class AuthorDocChangeVisitor(ABC, Generic[_Result]):
    @abstractmethod
    def visit_cell_added(self, cell_added: CellAdded) -> _Result: ...

    @abstractmethod
    def visit_cell_removed(self, cell_removed: CellRemoved) -> _Result: ...

    @abstractmethod
    def visit_cells_moved(self, cells_moved: CellsMoved) -> _Result: ...

    @abstractmethod
    def visit_cell_header_changed(self, cell_header_changed: CellHeaderChanged) -> _Result: ...

    @abstractmethod
    def visit_cell_text_changed(self, cell_text_changed: CellTextChanged) -> _Result: ...
