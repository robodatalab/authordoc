from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from authordoc.author_doc_change import AuthorDocChange
from authordoc.cells.cell import Cell
from authordoc.changes.cell_added import CellAdded
from authordoc.changes.cell_header_changed import CellHeaderChanged
from authordoc.changes.cell_removed import CellRemoved
from authordoc.changes.cell_text_changed import CellTextChanged
from authordoc.changes.cells_moved import CellsMoved
from authordoc.parser import marker_for
from authordoc.storydoc import Document
from authordoc.visitors.marker_attributes import MarkerAttributes


@dataclass(frozen=True)
class AuthorDocDiff:
    changes: list[AuthorDocChange]

    @classmethod
    def diff(cls, lhs: Document, rhs: Document) -> AuthorDocDiff:
        changes: list[AuthorDocChange] = []
        cell_ids_in_lhs = [cell.unique_id for cell in lhs.cells]
        cell_ids_in_rhs = [cell.unique_id for cell in rhs.cells]

        for cell_index in reversed(range(len(lhs.cells))):
            cell_in_lhs = lhs.cells[cell_index]
            if cell_in_lhs.unique_id not in cell_ids_in_rhs:
                removed = CellRemoved(cell_index, cell_in_lhs)
                changes.append(removed)

        cell_ids_before = [cell_id for cell_id in cell_ids_in_lhs if cell_id in cell_ids_in_rhs]
        cell_ids_after = [cell_id for cell_id in cell_ids_in_rhs if cell_id in cell_ids_in_lhs]
        if cell_ids_before != cell_ids_after:
            moved = CellsMoved(cell_ids_before, cell_ids_after)
            changes.append(moved)

        marker_attributes = MarkerAttributes()
        for cell_index, cell_in_rhs in enumerate(rhs.cells):
            cell_in_lhs = lhs.cell_with_id(cell_in_rhs.unique_id)
            if cell_in_lhs is None:
                added = CellAdded(cell_index, cell_in_rhs)
                changes.append(added)
                continue
            marker_in_lhs = marker_for(cell_in_lhs, marker_attributes)
            marker_in_rhs = marker_for(cell_in_rhs, marker_attributes)
            if marker_in_lhs != marker_in_rhs:
                header_before = cell_in_lhs.with_source("")
                header_after = cell_in_rhs.with_source("")
                header_changed = CellHeaderChanged(header_before, header_after)
                changes.append(header_changed)
            if cell_in_lhs.source != cell_in_rhs.source:
                text_changed = CellTextChanged.between(cell_in_rhs.unique_id, cell_in_lhs.source, cell_in_rhs.source)
                changes.append(text_changed)

        difference = cls(changes)
        return difference

    def empty(self) -> bool:
        return not self.changes

    def followed_by(self, diffs_after_it: Sequence[AuthorDocDiff]) -> AuthorDocDiff:
        changes_after_it = [change for diff in diffs_after_it for change in diff.changes]
        followed = AuthorDocDiff([*self.changes, *changes_after_it])
        return followed

    def invert(self) -> AuthorDocDiff:
        changes_in_reverse = reversed(self.changes)
        inverted_changes = [change.invert() for change in changes_in_reverse]
        inverted = AuthorDocDiff(inverted_changes)
        return inverted

    def apply_the_diff(self, document: Document) -> Document:
        cells: list[Cell] = document.cells
        for change in self.changes:
            cells = change.apply_to(cells)
        applied = Document.from_cells(cells, document.path)
        return applied
