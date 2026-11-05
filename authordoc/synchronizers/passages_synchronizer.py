from __future__ import annotations

from dataclasses import dataclass, replace

from authordoc.author_doc_synchronizer import AuthorDocSynchronizer
from authordoc.cells.about_cell import AboutCell
from authordoc.cells.blurb_cell import BlurbCell
from authordoc.cells.cell import Cell
from authordoc.cells.cell_visitor import CellVisitor
from authordoc.cells.chapter_cell import ChapterCell
from authordoc.cells.disclaimer_cell import DisclaimerCell
from authordoc.cells.divider_cell import DividerCell
from authordoc.cells.image_cell import ImageCell
from authordoc.cells.markdown_cell import MarkdownCell
from authordoc.cells.note_cell import NoteCell
from authordoc.cells.part_cell import PartCell
from authordoc.cells.plot_cell import PlotCell, PlotNode
from authordoc.cells.recap_cell import RecapCell
from authordoc.cells.salient_concept_cell import SalientConceptCell, SalientConceptReference
from authordoc.cells.story_word_range import StoryWordRange
from authordoc.cells.table_of_contents_cell import TableOfContentsCell
from authordoc.cells.title_page_cell import TitlePageCell
from authordoc.cells.unknown_cell import UnknownCell
from authordoc.diff import AuthorDocDiff
from authordoc.iterators.story_words_iterator import StoryWord, StoryWordsIterator
from authordoc.storydoc import Document


@dataclass(frozen=True)
class _WordsAnEditReplaced:
    first_old_word: int
    end_of_old_words: int
    first_new_word: int
    end_of_new_words: int

    def falls_within(self, story_word_range: StoryWordRange) -> bool:
        if self.first_old_word == self.end_of_old_words:
            return story_word_range.first_word < self.first_old_word <= story_word_range.last_word
        return self.first_old_word <= story_word_range.last_word and self.end_of_old_words > story_word_range.first_word


class _WhereTheStoryWordsWent:
    def __init__(
        self,
        new_number_of_each_old_word: dict[int, int],
        words_the_edits_replaced: list[_WordsAnEditReplaced],
    ) -> None:
        self._new_number_of_each_old_word = new_number_of_each_old_word
        self._words_the_edits_replaced = words_the_edits_replaced

    def range_kept_in_step(self, story_word_range: StoryWordRange) -> StoryWordRange | None:
        words_it_covers: list[int] = []
        for word in range(story_word_range.first_word, story_word_range.last_word + 1):
            new_number = self._new_number_of_each_old_word.get(word)
            if new_number is not None:
                words_it_covers.append(new_number)
        for edit in self._words_the_edits_replaced:
            if edit.first_new_word < edit.end_of_new_words and edit.falls_within(story_word_range):
                words_it_covers.extend((edit.first_new_word, edit.end_of_new_words - 1))
        if not words_it_covers:
            return None
        first_word = min(words_it_covers)
        last_word = max(words_it_covers)
        kept_in_step = StoryWordRange(first_word, last_word)
        return kept_in_step


def _story_words_of_each_cell(document: Document) -> dict[str, list[StoryWord]]:
    story_words_of_each_cell: dict[str, list[StoryWord]] = {}
    story_words = StoryWordsIterator(document)
    for word in story_words:
        words_of_the_cell = story_words_of_each_cell.setdefault(word.cell_id, [])
        words_of_the_cell.append(word)
    return story_words_of_each_cell


def _words_both_ends_of_the_cell_share(old_words: list[StoryWord], new_words: list[StoryWord]) -> tuple[int, int]:
    words_in_the_shorter = min(len(old_words), len(new_words))
    words_at_the_start = 0
    while words_at_the_start < words_in_the_shorter and old_words[words_at_the_start].text == new_words[words_at_the_start].text:
        words_at_the_start += 1
    words_at_the_end = 0
    while (
        words_at_the_end < words_in_the_shorter - words_at_the_start
        and old_words[len(old_words) - 1 - words_at_the_end].text == new_words[len(new_words) - 1 - words_at_the_end].text
    ):
        words_at_the_end += 1
    return (words_at_the_start, words_at_the_end)


def _where_the_story_words_went(before: Document, after: Document) -> _WhereTheStoryWordsWent:
    new_number_of_each_old_word: dict[int, int] = {}
    words_the_edits_replaced: list[_WordsAnEditReplaced] = []
    story_words_before = _story_words_of_each_cell(before)
    story_words_after = _story_words_of_each_cell(after)
    for cell_id, old_words in story_words_before.items():
        new_words = story_words_after.get(cell_id)
        if new_words is None:
            continue
        words_at_the_start, words_at_the_end = _words_both_ends_of_the_cell_share(old_words, new_words)
        for word in range(words_at_the_start):
            new_number_of_each_old_word[old_words[word].number] = new_words[word].number
        for word in range(words_at_the_end):
            old_word = old_words[len(old_words) - 1 - word]
            new_word = new_words[len(new_words) - 1 - word]
            new_number_of_each_old_word[old_word.number] = new_word.number
        if words_at_the_start + words_at_the_end < max(len(old_words), len(new_words)):
            first_old_word = old_words[0].number
            first_new_word = new_words[0].number
            words_the_edit_replaced = _WordsAnEditReplaced(
                first_old_word + words_at_the_start,
                first_old_word + len(old_words) - words_at_the_end,
                first_new_word + words_at_the_start,
                first_new_word + len(new_words) - words_at_the_end,
            )
            words_the_edits_replaced.append(words_the_edit_replaced)
    where_the_words_went = _WhereTheStoryWordsWent(new_number_of_each_old_word, words_the_edits_replaced)
    return where_the_words_went


class _PassagesKeptInStep(CellVisitor[Cell]):
    """A range the change leaves as it was counts the story's words as they stood
    before it, and moves with them; a range the change sets, new or different,
    counts them as they stand after it, and is kept as the change writes it. So
    the order the change writes its cells in makes no difference."""

    def __init__(self, before: Document, where_the_words_went: _WhereTheStoryWordsWent) -> None:
        self._before = before
        self._where_the_words_went = where_the_words_went

    def visit_salient_concept(self, cell: SalientConceptCell) -> SalientConceptCell:
        held = self._before.cell_with_id(cell.unique_id)
        references_before = held.references if isinstance(held, SalientConceptCell) else ()
        ranges_before = {reference.reference_id: reference.story_word_range for reference in references_before}
        references_kept_in_step: list[SalientConceptReference] = []
        for reference in cell.references:
            if ranges_before.get(reference.reference_id) != reference.story_word_range:
                references_kept_in_step.append(reference)
                continue
            range_kept_in_step = self._where_the_words_went.range_kept_in_step(reference.story_word_range)
            if range_kept_in_step is not None:
                reference_kept_in_step = SalientConceptReference(reference.reference_id, range_kept_in_step)
                references_kept_in_step.append(reference_kept_in_step)
        kept_in_step = replace(cell, references=references_kept_in_step)
        return kept_in_step

    # An event outlives the words that told it: when they are gone, it is simply
    # told by none.
    def visit_plot(self, cell: PlotCell) -> PlotCell:
        held = self._before.cell_with_id(cell.unique_id)
        nodes_before = held.nodes if isinstance(held, PlotCell) else ()
        ranges_before = {node.node_id: node.story_word_range for node in nodes_before}
        nodes_kept_in_step: list[PlotNode] = []
        for node in cell.nodes:
            if node.story_word_range is None or ranges_before.get(node.node_id) != node.story_word_range:
                nodes_kept_in_step.append(node)
                continue
            range_kept_in_step = self._where_the_words_went.range_kept_in_step(node.story_word_range)
            node_kept_in_step = node.with_story_word_range(range_kept_in_step)
            nodes_kept_in_step.append(node_kept_in_step)
        kept_in_step = cell.with_nodes(nodes_kept_in_step)
        return kept_in_step

    def visit_markdown(self, cell: MarkdownCell) -> MarkdownCell:
        return cell

    def visit_chapter(self, cell: ChapterCell) -> ChapterCell:
        return cell

    def visit_part(self, cell: PartCell) -> PartCell:
        return cell

    def visit_divider(self, cell: DividerCell) -> DividerCell:
        return cell

    def visit_title_page(self, cell: TitlePageCell) -> TitlePageCell:
        return cell

    def visit_image(self, cell: ImageCell) -> ImageCell:
        return cell

    def visit_table_of_contents(self, cell: TableOfContentsCell) -> TableOfContentsCell:
        return cell

    def visit_disclaimer(self, cell: DisclaimerCell) -> DisclaimerCell:
        return cell

    def visit_about(self, cell: AboutCell) -> AboutCell:
        return cell

    def visit_blurb(self, cell: BlurbCell) -> BlurbCell:
        return cell

    def visit_note(self, cell: NoteCell) -> NoteCell:
        return cell

    def visit_recap(self, cell: RecapCell) -> RecapCell:
        return cell

    def visit_unknown(self, cell: UnknownCell) -> UnknownCell:
        return cell


class PassagesSynchronizer(AuthorDocSynchronizer):
    def synchronize(self, before: Document, change: AuthorDocDiff) -> AuthorDocDiff:
        after = change.apply_the_diff(before)
        where_the_words_went = _where_the_story_words_went(before, after)
        passages_kept_in_step = _PassagesKeptInStep(before, where_the_words_went)
        cells_with_their_passages_in_step = [cell.accept(passages_kept_in_step) for cell in after.cells]
        document_with_its_passages_in_step = Document.from_cells(cells_with_their_passages_in_step, after.path)
        passages_moved = AuthorDocDiff.diff(after, document_with_its_passages_in_step)
        return passages_moved
