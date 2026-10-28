from __future__ import annotations

from dataclasses import dataclass

from authordoc.cells.about_cell import AboutCell
from authordoc.cells.blurb_cell import BlurbCell
from authordoc.cells.cell_visitor import CellVisitor
from authordoc.cells.chapter_cell import ChapterCell
from authordoc.cells.disclaimer_cell import DisclaimerCell
from authordoc.cells.divider_cell import DividerCell
from authordoc.cells.image_cell import ImageCell
from authordoc.cells.markdown_cell import MarkdownCell
from authordoc.cells.note_cell import NoteCell
from authordoc.cells.part_cell import PartCell
from authordoc.cells.plot_cell import PlotCell
from authordoc.cells.recap_cell import RecapCell
from authordoc.cells.salient_concept_cell import SalientConceptCell
from authordoc.cells.story_word_range import StoryWordRange
from authordoc.cells.table_of_contents_cell import TableOfContentsCell
from authordoc.cells.title_page_cell import TitlePageCell
from authordoc.cells.unknown_cell import UnknownCell


@dataclass(frozen=True)
class AnnotatedPassages:
    title: str
    story_word_ranges: list[StoryWordRange]


class AnnotatedPassagesOf(CellVisitor["AnnotatedPassages | None"]):
    def visit_salient_concept(self, cell: SalientConceptCell) -> AnnotatedPassages:
        story_word_ranges = [
            reference.story_word_range for reference in cell.references
        ]
        return AnnotatedPassages(cell.title, story_word_ranges)

    # Only an event that story text tells has a passage.
    def visit_plot(self, cell: PlotCell) -> AnnotatedPassages:
        story_word_ranges = [
            node.story_word_range
            for node in cell.nodes
            if node.story_word_range is not None
        ]
        return AnnotatedPassages(cell.title, story_word_ranges)

    def visit_markdown(self, cell: MarkdownCell) -> None:
        return None

    def visit_chapter(self, cell: ChapterCell) -> None:
        return None

    def visit_part(self, cell: PartCell) -> None:
        return None

    def visit_divider(self, cell: DividerCell) -> None:
        return None

    def visit_title_page(self, cell: TitlePageCell) -> None:
        return None

    def visit_image(self, cell: ImageCell) -> None:
        return None

    def visit_table_of_contents(self, cell: TableOfContentsCell) -> None:
        return None

    def visit_disclaimer(self, cell: DisclaimerCell) -> None:
        return None

    def visit_about(self, cell: AboutCell) -> None:
        return None

    def visit_blurb(self, cell: BlurbCell) -> None:
        return None

    def visit_note(self, cell: NoteCell) -> None:
        return None

    def visit_recap(self, cell: RecapCell) -> None:
        return None

    def visit_unknown(self, cell: UnknownCell) -> None:
        return None
