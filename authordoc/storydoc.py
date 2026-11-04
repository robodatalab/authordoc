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

from pathlib import Path
from typing import TypeVar

from authordoc.cells.cell import Cell
from authordoc.cells.plot_cell import PlotCell, PlotEdge, PlotNode
from authordoc.cells.salient_concept_cell import SalientConceptCell
from authordoc.cells.title_page_cell import TitlePageCell
from authordoc.parser import marker_for, parse
from authordoc.visitors.marker_attributes import MarkerAttributes

EXTENSION = ".author"

_Cell = TypeVar("_Cell", bound=Cell)


class Document:
    """An .author document"""

    def __init__(self, text: str, path: Path | None = None) -> None:
        self.path = path
        self.cells = parse(text)

    @classmethod
    def from_cells(cls, cells: list[Cell], path: Path | None = None) -> Document:
        """A new document made of `cells`, in their order. The cells are written
        out and read back, so every cell is as a fresh read of the file gives it,
        with the lines it is written on.

        Use it to build a document, or to add, remove or reorder cells. To replace
        one cell, every other cell staying where it is, use `with_cell`. No
        document is changed: the one you hold stays as it is."""
        written = cls("", path)
        written.cells = list(cells)
        return cls(written.text, path)

    @property
    def text(self) -> str:
        """The document as text, such that `parse(text) == cells`."""
        marker_attributes = MarkerAttributes()
        out: list[str] = []
        for cell in self.cells:
            marker = marker_for(cell, marker_attributes)
            out.append(marker)
            out.append("")
            if cell.source:
                out.append(cell.source)
                out.append("")
        return "\n".join(out)

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    @classmethod
    def load(cls, path: Path) -> "Document":
        return cls(path.read_text(encoding="utf-8"), path)

    def save(self) -> None:
        assert self.path is not None
        self.path.write_text(self.text, encoding="utf-8")

    @property
    def title_page(self) -> TitlePageCell:
        """What the book says of itself, blank in a document that says nothing."""
        return next(
            (cell for cell in self.cells if isinstance(cell, TitlePageCell)),
            TitlePageCell(),
        )

    @property
    def title(self) -> str:
        return self.title_page.title or "Anonymous"

    def cell_with_id(self, cell_id: str) -> Cell | None:
        return next((cell for cell in self.cells if cell.unique_id == cell_id), None)

    def get_cell(self, cell_type: type[_Cell], kind: str) -> _Cell | None:
        """The first cell of `cell_type` whose kind is `kind`; None when the
        document has no such cell."""
        found = next(
            (cell for cell in self.cells if isinstance(cell, cell_type) and cell.kind == kind),
            None,
        )
        return found

    def with_cell(self, cell: Cell) -> Document:
        """A new document with `cell` in the place of the cell with its id; one with
        the same cells when this document has no cell with that id. Like every
        document `from_cells` makes, every cell is as a fresh read of the file
        gives it, with the lines it is written on.

        Use it to replace one cell, every other cell staying where it is. To add,
        remove or reorder cells, use `from_cells`. No document is changed: the one
        you hold stays as it is."""
        cells = [cell if held.unique_id == cell.unique_id else held for held in self.cells]
        with_the_cell = Document.from_cells(cells, self.path)
        return with_the_cell

    def salient_concepts(self) -> list[SalientConceptCell]:
        return [cell for cell in self.cells if isinstance(cell, SalientConceptCell)]

    def plots(self) -> list[PlotCell]:
        return [cell for cell in self.cells if isinstance(cell, PlotCell)]

    def get_plot_of_edge(self, edge: PlotEdge) -> PlotCell:
        plot = next(plot for plot in self.plots() if edge in plot.edges)
        return plot

    def get_plot_of_node(self, node: PlotNode) -> PlotCell:
        plot = next(plot for plot in self.plots() if node in plot.nodes)
        return plot

    def __str__(self) -> str:
        return self.text

    def cell_at(self, line: int) -> Cell | None:
        """The cell `line` falls in."""
        for cell in self.cells:
            if cell.at and cell.at[0] <= line <= cell.at[1]:
                return cell
        return None
