from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, TypeVar
from uuid import uuid4

from authordoc.cells.cell import Cell

if TYPE_CHECKING:
    from authordoc.cells.cell_visitor import CellVisitor
    from authordoc.storydoc import Document

PLACE = "place"

_Result = TypeVar("_Result")


@dataclass(frozen=True)
class PlaceCell(Cell):
    kind: str = field(default=PLACE, init=False)
    title: str = ""
    source: str = ""
    folded: bool = False
    at: tuple[int, int] | None = field(default=None, compare=False)
    _unique_id: str = field(default_factory=lambda: str(uuid4()))
    _parent: str = ""

    def parent(self, document: Document) -> PlaceCell | None:
        referenced = document.cell_with_id(self._parent)
        parent = referenced if isinstance(referenced, PlaceCell) else None
        return parent

    def with_parent(self, parent: PlaceCell | None) -> PlaceCell:
        parent_id = "" if parent is None else parent.unique_id
        placed = replace(self, _parent=parent_id)
        return placed

    def with_source(self, source: str) -> PlaceCell:
        return replace(self, source=source)

    def with_folded(self, folded: bool) -> PlaceCell:
        return replace(self, folded=folded)

    def accept(self, visitor: CellVisitor[_Result]) -> _Result:
        return visitor.visit_place(self)
