import unittest

from parameterized import parameterized

from authordoc.diff import AuthorDocDiff
from authordoc.storydoc import Document

SHE_SAW = '<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n'
HE_HEARD = '<!-- cell: markdown id="c2" -->\n\nHe heard the bell.\n'
THE_CHAPTER = '<!-- cell: chapter id="c0" title="One" -->\n'
THE_STORY = THE_CHAPTER + "\n" + SHE_SAW + "\n" + HE_HEARD


class Diff(unittest.TestCase):
    def test_says_nothing_about_two_documents_written_the_same(self) -> None:
        lhs = Document(SHE_SAW)
        rhs = Document(SHE_SAW)

        difference = AuthorDocDiff.diff(lhs, rhs)

        self.assertTrue(difference.empty())


class InvertingADifference(unittest.TestCase):
    def test_leaves_a_difference_that_says_nothing_saying_nothing(self) -> None:
        lhs = Document(SHE_SAW)
        rhs = Document(SHE_SAW)
        difference = AuthorDocDiff.diff(lhs, rhs)

        inverted = difference.invert()

        self.assertTrue(inverted.empty())


class ApplyingADifference(unittest.TestCase):
    @parameterized.expand(
        [
            ("leaves_a_document_alone_when_the_difference_says_nothing", THE_STORY, THE_STORY),
            (
                "writes_a_word_one_document_has_in_place_of_the_word_the_other_has",
                SHE_SAW,
                '<!-- cell: markdown id="c1" -->\n\nShe opened the door.\n',
            ),
            (
                "writes_a_character_typed_at_the_end_of_a_cell",
                SHE_SAW,
                '<!-- cell: markdown id="c1" -->\n\nShe saw the door.!\n',
            ),
            ("puts_in_a_cell_one_document_has_and_the_other_has_not", SHE_SAW, SHE_SAW + "\n" + HE_HEARD),
            (
                "puts_a_cell_back_where_it_stood_not_at_the_end",
                SHE_SAW + "\n" + HE_HEARD,
                SHE_SAW + "\n" + THE_CHAPTER + "\n" + HE_HEARD,
            ),
            ("takes_out_a_cell_one_document_has_and_the_other_has_not", THE_STORY, THE_CHAPTER + "\n" + HE_HEARD),
            ("writes_back_a_cell_taken_out_with_the_attributes_it_was_written_with", THE_STORY, SHE_SAW + "\n" + HE_HEARD),
            ("empties_a_cell_of_its_text_without_taking_it_out_of_the_document", SHE_SAW, '<!-- cell: markdown id="c1" -->\n'),
            ("puts_cells_back_in_the_order_they_stood_in", THE_STORY, HE_HEARD + "\n" + THE_CHAPTER + "\n" + SHE_SAW),
            (
                "moves_one_cell_of_many_past_the_others",
                SHE_SAW + "\n" + HE_HEARD + "\n" + THE_CHAPTER,
                THE_CHAPTER + "\n" + SHE_SAW + "\n" + HE_HEARD,
            ),
            (
                "writes_changes_and_takes_away_attributes",
                '<!-- cell: chapter id="c1" title="One" folded="true" -->\n',
                '<!-- cell: chapter id="c1" title="Two" printed="no" -->\n',
            ),
            (
                "writes_a_cell_as_the_kind_the_other_document_has_it",
                SHE_SAW,
                '<!-- cell: note id="c1" -->\n\nShe saw the door.\n',
            ),
            ("writes_into_a_document_that_has_no_cells_at_all", "", SHE_SAW + "\n" + HE_HEARD),
            (
                "writes_every_kind_of_change_at_once",
                THE_STORY,
                '<!-- cell: chapter id="c0" title="Two" folded="true" -->\n'
                "\n"
                '<!-- cell: note id="c2" -->\n\nHe heard a bell.\n'
                "\n"
                '<!-- cell: markdown id="c3" -->\n\nShe waited.\n',
            ),
        ]
    )
    def test_turns_one_document_into_the_other_and_back(self, _, lhs_text: str, rhs_text: str) -> None:
        lhs = Document(lhs_text)
        rhs = Document(rhs_text)
        change = AuthorDocDiff.diff(lhs, rhs)

        turned = change.apply_the_diff(lhs)
        inverted = change.invert()
        turned_back = inverted.apply_the_diff(rhs)

        self.assertEqual(turned.text, rhs.text)
        self.assertEqual(turned_back.text, lhs.text)
