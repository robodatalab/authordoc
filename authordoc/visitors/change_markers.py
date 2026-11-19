from __future__ import annotations

from typing import TYPE_CHECKING

from authordoc.author_doc_change_visitor import AuthorDocChangeVisitor
from authordoc.visitors.marker_attributes import FOLDED, TRUE, MarkerAttributes
from authordoc.written_attributes import written_attribute_value

if TYPE_CHECKING:
    from authordoc.cells.cell import Cell
    from authordoc.changes.cell_added import CellAdded
    from authordoc.changes.cell_header_changed import CellHeaderChanged
    from authordoc.changes.cell_removed import CellRemoved
    from authordoc.changes.cell_text_changed import CellTextChanged
    from authordoc.changes.cells_moved import CellsMoved

CELL_ADDED = "added"
CELL_REMOVED = "removed"
CELLS_MOVED = "moved"
CELL_HEADER_CHANGED = "header"
CELL_TEXT_CHANGED = "text"

AT = "at"
KIND = "kind"
TEXT = "text"
FROM = "from"
TEXT_REMOVED = "removed"
TEXT_WRITTEN = "written"
CELL_IDS_BEFORE = "before"
CELL_IDS_AFTER = "after"
BEFORE = "before-"
AFTER = "after-"

CELL_IDS_SEPARATOR = ","


def _prefixed(prefix: str, attributes: dict[str, str]) -> dict[str, str]:
    attributes_prefixed = {f"{prefix}{name}": value for name, value in attributes.items()}
    return attributes_prefixed


def _change_marker(change: str, attributes: dict[str, str]) -> str:
    said = "".join(f' {name}="{written_attribute_value(value)}"' for name, value in attributes.items())
    marker = f"<!-- change: {change}{said} -->"
    return marker


class ChangeMarkers(AuthorDocChangeVisitor[str]):
    def __init__(self) -> None:
        self._marker_attributes = MarkerAttributes()

    def visit_cell_added(self, cell_added: CellAdded) -> str:
        header = self._header_of(cell_added.cell)
        header_after = _prefixed(AFTER, header)
        cell_index = str(cell_added.cell_index)
        attributes = {AT: cell_index, KIND: cell_added.cell.kind, TEXT: cell_added.cell.source, **header_after}
        marker = _change_marker(CELL_ADDED, attributes)
        return marker

    def visit_cell_removed(self, cell_removed: CellRemoved) -> str:
        header = self._header_of(cell_removed.cell)
        header_before = _prefixed(BEFORE, header)
        cell_index = str(cell_removed.cell_index)
        attributes = {AT: cell_index, KIND: cell_removed.cell.kind, TEXT: cell_removed.cell.source, **header_before}
        marker = _change_marker(CELL_REMOVED, attributes)
        return marker

    def visit_cells_moved(self, cells_moved: CellsMoved) -> str:
        cell_ids_before = CELL_IDS_SEPARATOR.join(cells_moved.cell_ids_before)
        cell_ids_after = CELL_IDS_SEPARATOR.join(cells_moved.cell_ids_after)
        attributes = {CELL_IDS_BEFORE: cell_ids_before, CELL_IDS_AFTER: cell_ids_after}
        marker = _change_marker(CELLS_MOVED, attributes)
        return marker

    def visit_cell_header_changed(self, cell_header_changed: CellHeaderChanged) -> str:
        before = self._header_of(cell_header_changed.header_before)
        after = self._header_of(cell_header_changed.header_after)
        header_before = _prefixed(BEFORE, before)
        header_after = _prefixed(AFTER, after)
        attributes = {KIND: cell_header_changed.header_after.kind, **header_before, **header_after}
        marker = _change_marker(CELL_HEADER_CHANGED, attributes)
        return marker

    def visit_cell_text_changed(self, cell_text_changed: CellTextChanged) -> str:
        from_character = str(cell_text_changed.from_character)
        attributes = {
            FROM: from_character,
            TEXT_REMOVED: cell_text_changed.text_removed,
            TEXT_WRITTEN: cell_text_changed.text_written,
        }
        marker = _change_marker(CELL_TEXT_CHANGED, attributes)
        return marker

    def _header_of(self, cell: Cell) -> dict[str, str]:
        attributes_of_the_kind = cell.accept(self._marker_attributes)
        folded = {FOLDED: TRUE} if cell.folded else {}
        header = {**attributes_of_the_kind, **folded}
        return header
