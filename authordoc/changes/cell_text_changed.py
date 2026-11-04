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
class CellTextChanged(AuthorDocChange):
    cell_id: str
    from_character: int
    text_removed: str
    text_written: str

    @classmethod
    def between(cls, cell_id: str, text_before: str, text_after: str) -> CellTextChanged:
        characters_same_at_the_start = 0
        while (
            characters_same_at_the_start < len(text_before)
            and characters_same_at_the_start < len(text_after)
            and text_before[characters_same_at_the_start] == text_after[characters_same_at_the_start]
        ):
            characters_same_at_the_start += 1
        characters_same_at_the_end = 0
        while (
            characters_same_at_the_end < len(text_before) - characters_same_at_the_start
            and characters_same_at_the_end < len(text_after) - characters_same_at_the_start
            and text_before[len(text_before) - 1 - characters_same_at_the_end]
            == text_after[len(text_after) - 1 - characters_same_at_the_end]
        ):
            characters_same_at_the_end += 1
        text_removed = text_before[characters_same_at_the_start : len(text_before) - characters_same_at_the_end]
        text_written = text_after[characters_same_at_the_start : len(text_after) - characters_same_at_the_end]
        changed = cls(cell_id, characters_same_at_the_start, text_removed, text_written)
        return changed

    def accept(self, visitor: AuthorDocChangeVisitor[_Result]) -> _Result:
        return visitor.visit_cell_text_changed(self)

    def invert(self) -> CellTextChanged:
        inverted = CellTextChanged(self.cell_id, self.from_character, self.text_written, self.text_removed)
        return inverted

    def text_after(self, text_before: str) -> str:
        text_ahead = text_before[: self.from_character]
        text_behind = text_before[self.from_character + len(self.text_removed) :]
        return text_ahead + self.text_written + text_behind

    def apply_to(self, cells: Sequence[Cell]) -> list[Cell]:
        changed: list[Cell] = []
        for cell in cells:
            if cell.unique_id != self.cell_id:
                changed.append(cell)
                continue
            text_after = self.text_after(cell.source)
            rewritten = cell.with_source(text_after)
            changed.append(rewritten)
        return changed
