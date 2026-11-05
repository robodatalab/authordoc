import unittest

from parameterized import parameterized

from authordoc.cells.plot_cell import PlotEdge, PlotNode
from authordoc.cells.salient_concept_cell import SalientConceptReference
from authordoc.cells.story_word_range import StoryWordRange
from authordoc.diff import AuthorDocDiff
from authordoc.storydoc import Document
from authordoc.synchronizers.passages_synchronizer import PassagesSynchronizer

THE_CHAPTER = '<!-- cell: chapter title="One" id="c1" -->\n'
THE_NOTE = '<!-- cell: note id="n1" -->\n\n<!--\nNot a story word.\n-->\n'
HE_HEARD = '<!-- cell: markdown id="c3" -->\n\nHe heard the bell.\n'
IT_RANG = '<!-- cell: markdown id="c4" -->\n\nIt rang.\n'


def she_saw(door: str) -> str:
    return f'<!-- cell: markdown id="c2" -->\n\n{door}\n'


def the_concept(words: str) -> str:
    return f'<!-- cell: salient-concept title="Door" words="{words}" id="k1" -->\n\nWhat she saw.\n'


def the_plot(nodes: str, edges: str) -> str:
    return f'<!-- cell: plot title="The bell" nodes="{nodes}" edges="{edges}" id="p1" -->\n\nHe hears the bell.\n'


class SalientConceptPassages(unittest.TestCase):
    @parameterized.expand(
        [
            # As the author writes in a cell.
            (
                "move_on_when_a_word_is_written_before_them",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:6-7")],
                [she_saw("She saw the old door."), HE_HEARD, the_concept("r1:6-7")],
                (SalientConceptReference("r1", StoryWordRange(7, 8)),),
            ),
            (
                "take_in_a_word_written_among_them",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:1-3")],
                [she_saw("She saw the old door."), HE_HEARD, the_concept("r1:1-3")],
                (SalientConceptReference("r1", StoryWordRange(1, 4)),),
            ),
            (
                "leave_out_a_word_written_just_before_them",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:2-3")],
                [she_saw("She saw quietly the door."), HE_HEARD, the_concept("r1:2-3")],
                (SalientConceptReference("r1", StoryWordRange(3, 4)),),
            ),
            (
                "leave_out_a_word_written_just_after_them",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:1-2")],
                [she_saw("She saw the old door."), HE_HEARD, the_concept("r1:1-2")],
                (SalientConceptReference("r1", StoryWordRange(1, 2)),),
            ),
            (
                "keep_a_word_of_theirs_that_was_written_over",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:1-3")],
                [she_saw("She sees the door."), HE_HEARD, the_concept("r1:1-3")],
                (SalientConceptReference("r1", StoryWordRange(1, 3)),),
            ),
            (
                "lose_a_passage_whose_words_were_all_deleted",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:1-1, r2:2-3")],
                [she_saw("She saw"), HE_HEARD, the_concept("r1:1-1, r2:2-3")],
                (SalientConceptReference("r1", StoryWordRange(1, 1)),),
            ),
            (
                "are_gone_when_every_one_of_them_was_deleted",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:2-3")],
                [she_saw("She saw"), HE_HEARD, the_concept("r1:2-3")],
                (),
            ),
            (
                "count_no_words_of_a_cell_that_is_not_prose",
                [THE_CHAPTER, she_saw("She saw the door."), THE_NOTE, HE_HEARD, the_concept("r1:6-7")],
                [THE_CHAPTER, she_saw("She saw the old door."), THE_NOTE, HE_HEARD, the_concept("r1:6-7")],
                (SalientConceptReference("r1", StoryWordRange(7, 8)),),
            ),
            # As the author adds, takes out and moves cells.
            (
                "move_on_when_a_cell_is_written_before_them",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:6-7")],
                [she_saw("She saw the door."), IT_RANG, HE_HEARD, the_concept("r1:6-7")],
                (SalientConceptReference("r1", StoryWordRange(8, 9)),),
            ),
            (
                "move_back_when_a_cell_before_them_is_taken_out",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:6-7")],
                [HE_HEARD, the_concept("r1:6-7")],
                (SalientConceptReference("r1", StoryWordRange(2, 3)),),
            ),
            (
                "go_with_the_cell_they_stand_in_when_it_moves",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:6-7")],
                [HE_HEARD, she_saw("She saw the door."), the_concept("r1:6-7")],
                (SalientConceptReference("r1", StoryWordRange(2, 3)),),
            ),
            (
                "are_gone_with_the_cell_they_stand_in",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:2-3, r2:6-7")],
                [HE_HEARD, the_concept("r1:2-3, r2:6-7")],
                (SalientConceptReference("r2", StoryWordRange(2, 3)),),
            ),
            # That the change writes itself.
            (
                "are_left_as_the_change_writes_them",
                [she_saw("She saw the door."), HE_HEARD, the_concept("r1:6-7")],
                [she_saw("She saw the old door."), HE_HEARD, the_concept("r1:2-3")],
                (SalientConceptReference("r1", StoryWordRange(2, 3)),),
            ),
            (
                "are_left_as_they_come_when_the_concept_is_added",
                [she_saw("She saw the door."), HE_HEARD],
                [she_saw("She saw the old door."), HE_HEARD, the_concept("r1:6-7")],
                (SalientConceptReference("r1", StoryWordRange(6, 7)),),
            ),
        ]
    )
    def test_keep_to_the_words_they_point_at(
        self, _, cells_before: list[str], cells_after: list[str], expected: tuple[SalientConceptReference, ...]
    ) -> None:
        before_text = "\n".join(cells_before)
        after_text = "\n".join(cells_after)
        before = Document(before_text)
        after = Document(after_text)
        change = AuthorDocDiff.diff(before, after)
        synchronizer = PassagesSynchronizer()

        passages_moved = synchronizer.synchronize(before, change)

        story = passages_moved.apply_the_diff(after)
        (concept,) = story.salient_concepts()
        self.assertEqual(concept.references, expected)


class PlotNodes(unittest.TestCase):
    @parameterized.expand(
        [
            (
                "move_on_when_a_word_is_written_before_them",
                [she_saw("She saw the door."), HE_HEARD, the_plot("n-she:0-0, n-bell:6-7", "e-1:n-she>n-bell")],
                [she_saw("She saw the old door."), HE_HEARD, the_plot("n-she:0-0, n-bell:6-7", "e-1:n-she>n-bell")],
                (PlotNode("n-she", StoryWordRange(0, 0)), PlotNode("n-bell", StoryWordRange(7, 8))),
                (PlotEdge("e-1", "n-she", "n-bell"),),
            ),
            (
                "stay_in_the_plot_with_their_edges_told_by_no_words_when_all_their_words_are_deleted",
                [
                    she_saw("She saw the door."),
                    HE_HEARD,
                    the_plot("n-she:0-0, n-door:2-3, n-bell:6-7", "e-1:n-she>n-door, e-2:n-she>n-bell"),
                ],
                [
                    she_saw("She saw"),
                    HE_HEARD,
                    the_plot("n-she:0-0, n-door:2-3, n-bell:6-7", "e-1:n-she>n-door, e-2:n-she>n-bell"),
                ],
                (
                    PlotNode("n-she", StoryWordRange(0, 0)),
                    PlotNode("n-door", None),
                    PlotNode("n-bell", StoryWordRange(4, 5)),
                ),
                (PlotEdge("e-1", "n-she", "n-door"), PlotEdge("e-2", "n-she", "n-bell")),
            ),
        ]
    )
    def test_keep_to_the_words_that_tell_them(
        self,
        _,
        cells_before: list[str],
        cells_after: list[str],
        expected_nodes: tuple[PlotNode, ...],
        expected_edges: tuple[PlotEdge, ...],
    ) -> None:
        before_text = "\n".join(cells_before)
        after_text = "\n".join(cells_after)
        before = Document(before_text)
        after = Document(after_text)
        change = AuthorDocDiff.diff(before, after)
        synchronizer = PassagesSynchronizer()

        passages_moved = synchronizer.synchronize(before, change)

        story = passages_moved.apply_the_diff(after)
        (plot,) = story.plots()
        self.assertEqual(plot.nodes, expected_nodes)
        self.assertEqual(plot.edges, expected_edges)


class AChangeThatMovesNoPassage(unittest.TestCase):
    def test_asks_for_no_change_of_its_own(self) -> None:
        before_text = "\n".join([she_saw("She saw the door."), HE_HEARD, the_concept("2-3")])
        after_text = "\n".join(
            [
                she_saw("She saw the door."),
                '<!-- cell: markdown id="c3" -->\n\nHe heard the bells.\n',
                the_concept("2-3"),
            ]
        )
        before = Document(before_text)
        after = Document(after_text)
        change = AuthorDocDiff.diff(before, after)
        synchronizer = PassagesSynchronizer()

        passages_moved = synchronizer.synchronize(before, change)

        self.assertTrue(passages_moved.empty())
