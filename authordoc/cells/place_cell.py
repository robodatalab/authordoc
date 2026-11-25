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

    def ancestors(self, document: Document) -> list[PlaceCell]:
        ancestors: list[PlaceCell] = []
        parent = self.parent(document)
        while parent is not None:
            reached = parent
            is_a_cycle = reached.unique_id == self.unique_id or any(
                outer.unique_id == reached.unique_id for outer in ancestors
            )
            if is_a_cycle:
                return []
            ancestors.append(reached)
            parent = reached.parent(document)
        return ancestors

    def children(self, document: Document) -> list[PlaceCell]:
        places = [cell for cell in document.cells if isinstance(cell, PlaceCell)]
        children: list[PlaceCell] = []
        for place in places:
            ancestors = place.ancestors(document)
            if ancestors and ancestors[0].unique_id == self.unique_id:
                children.append(place)
        return children

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
