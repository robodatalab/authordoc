"""A story and the layout it is published in, in one human-readable file.

The file is `<name>.author`, and it is markdown. What makes it a story document
is that the markdown is cut into cells, each opened by a marker that says what
the cell *is*:

    <!-- cell: chapter title="The First Night" -->

    The lantern had gone out again.

    <!-- cell: image src="art/cover.jpg" full-page="yes" -->

The marker is an HTML comment, so every reader that renders markdown renders the
document and shows none of the scaffolding, and every editor that opens text can
edit it. There is no custom editor a person is obliged to use — which is the
whole point of not being a notebook full of escaped JSON strings.

Two properties are load-bearing:

**The format is open.** A cell's type is any name, and this module knows nothing
about most of them. An unrecognised type is carried through parse and save
untouched, so a document written by a newer version — or by hand — survives a
round trip through an older one rather than losing the cells it could not name.

**Plain markdown is already a story document.** A file with no markers at all
parses as one `markdown` cell holding the lot. Nothing has to be converted, and a
document whose markers are all deleted is still the story.

The one ambiguity worth naming: a line inside a cell that itself looks like a
marker opens a new cell. Markdown has the same bargain with fences.
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from pathlib import Path
from typing import TypeVar

from authordoc.cells.cell import Cell
from authordoc.cells.plot_cell import PlotCell, PlotEdge, PlotNode
from authordoc.cells.salient_concept_cell import SalientConceptCell
from authordoc.cells.title_page_cell import TitlePageCell
from authordoc.parser import parse, parse_suggestions, serialize
from authordoc.suggestion import Suggestion

EXTENSION = ".author"

_Cell = TypeVar("_Cell", bound=Cell)


class Document:
    """An .author document"""

    def __init__(self, text: str, path: Path | None = None) -> None:
        self._path = path
        self._cells = parse(text)
        self._suggestions = parse_suggestions(text)
        suggestion_without_its_cell = next(
            (suggestion for suggestion in self._suggestions if self.cell_with_id(suggestion.cell_id) is None),
            None,
        )
        if suggestion_without_its_cell is not None:
            raise ValueError(
                f"The suggestion is for cell {suggestion_without_its_cell.cell_id}, which the document does not have"
            )

    @classmethod
    def from_cells(cls, cells: Sequence[Cell], path: Path | None = None, suggestions: Sequence[Suggestion] = ()) -> Document:
        """A new document made of `cells`, in their order. The cells are written
        out and read back, so every cell is as a fresh read of the file gives it,
        with the lines it is written on.

        Use it to build a document. To change one, use `with_cells` or
        `with_cell`, which keep what points at the story's words in step."""
        written = cls("", path)
        written._cells = list(cells)
        written._suggestions = list(suggestions)
        serialized = written.serialize()
        built = cls(serialized, path)
        return built

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def cells(self) -> list[Cell]:
        """The cells, in their order: a copy, so changing it changes no document."""
        cells = list(self._cells)
        return cells

    @property
    def text(self) -> str:
        """Deprecated: use `serialize()`."""
        warnings.warn("Document.text is deprecated; use Document.serialize()", DeprecationWarning, stacklevel=2)
        serialized = self.serialize()
        return serialized

    def serialize(self) -> str:
        """The document as text, such that `parse(text) == cells`."""
        serialized = serialize(self._cells, self._suggestions)
        return serialized

    @property
    def suggestions(self) -> list[Suggestion]:
        suggestions = list(self._suggestions)
        return suggestions

    def suggestion_for(self, cell_id: str) -> Suggestion | None:
        return next((suggestion for suggestion in self._suggestions if suggestion.cell_id == cell_id), None)

    @property
    def lines(self) -> list[str]:
        serialized = self.serialize()
        return serialized.splitlines()

    @classmethod
    def load(cls, path: Path) -> "Document":
        return cls(path.read_text(encoding="utf-8"), path)

    def save(self) -> None:
        assert self._path is not None
        serialized = self.serialize()
        self._path.write_text(serialized, encoding="utf-8")

    @property
    def title_page(self) -> TitlePageCell:
        """What the book says of itself, blank in a document that says nothing."""
        return next(
            (cell for cell in self._cells if isinstance(cell, TitlePageCell)),
            TitlePageCell(),
        )

    @property
    def title(self) -> str:
        return self.title_page.title or "Anonymous"

    def cell_with_id(self, cell_id: str) -> Cell | None:
        return next((cell for cell in self._cells if cell.unique_id == cell_id), None)

    def get_cell(self, cell_type: type[_Cell], kind: str) -> _Cell | None:
        """The first cell of `cell_type` whose kind is `kind`; None when the
        document has no such cell."""
        found = next(
            (cell for cell in self._cells if isinstance(cell, cell_type) and cell.kind == kind),
            None,
        )
        return found

    def with_cells(self, cells: Sequence[Cell]) -> Document:
        """A new document made of `cells`, in their order: a cell with a new id is
        added where it stands, and a cell left out is removed. Whatever points at
        the story's words keeps pointing at the same words. No document is
        changed: the one you hold stays as it is."""
        # The diff and the synchronizer read documents, so they are imported where
        # they are used.
        from authordoc.diff import AuthorDocDiff
        from authordoc.synchronizers.passages_synchronizer import PassagesSynchronizer

        cell_ids_kept = {cell.unique_id for cell in cells}
        suggestions_of_the_cells_kept = [suggestion for suggestion in self._suggestions if suggestion.cell_id in cell_ids_kept]
        written = Document.from_cells(cells, self._path, suggestions_of_the_cells_kept)
        change = AuthorDocDiff.diff(self, written)
        synchronizer = PassagesSynchronizer()
        passages_moved = synchronizer.synchronize(self, change)
        synchronized = passages_moved.apply_the_diff(written)
        return synchronized

    def with_cell(self, cell: Cell) -> Document:
        """A new document with `cell` in the place of the cell with its id, kept in
        step as `with_cells` keeps it."""
        replaced = [cell if held.unique_id == cell.unique_id else held for held in self._cells]
        with_the_cell = self.with_cells(replaced)
        return with_the_cell

    def with_suggestion(self, suggestion: Suggestion) -> Document:
        others = [held for held in self._suggestions if held.cell_id != suggestion.cell_id]
        with_the_suggestion = Document.from_cells(self._cells, self._path, [*others, suggestion])
        return with_the_suggestion

    def without_suggestion(self, cell_id: str) -> Document:
        others = [held for held in self._suggestions if held.cell_id != cell_id]
        without_the_suggestion = Document.from_cells(self._cells, self._path, others)
        return without_the_suggestion

    def salient_concepts(self) -> list[SalientConceptCell]:
        return [cell for cell in self._cells if isinstance(cell, SalientConceptCell)]

    def plots(self) -> list[PlotCell]:
        return [cell for cell in self._cells if isinstance(cell, PlotCell)]

    def get_plot_of_edge(self, edge: PlotEdge) -> PlotCell:
        plot = next(plot for plot in self.plots() if edge in plot.edges)
        return plot

    def get_plot_of_node(self, node: PlotNode) -> PlotCell:
        plot = next(plot for plot in self.plots() if node in plot.nodes)
        return plot

    def __str__(self) -> str:
        return self.serialize()

    def cell_at(self, line: int) -> Cell | None:
        """The cell `line` falls in."""
        for cell in self._cells:
            if cell.at and cell.at[0] <= line <= cell.at[1]:
                return cell
        return None
