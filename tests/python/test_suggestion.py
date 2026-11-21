import unittest

from authordoc.diff import AuthorDocDiff
from authordoc.storydoc import Document
from authordoc.suggestion import Suggestion

WITH_A_SUGGESTION = (
    '<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n\n'
    '<!-- suggestion: id="c1" -->\n'
    '<!-- change: text from="16" removed="" written=" at last" -->\n\n'
    '<!-- cell: markdown id="c2" -->\n\nHe heard the bell.\n'
)

THE_CHAPTER_BEFORE = '<!-- cell: chapter id="h1" title="Bell" -->\n\nThe bell rings.\n'

THE_CHAPTER_AFTER = '<!-- cell: chapter id="h1" title="The bell tolls" folded="true" -->\n\nThe bell tolls at night.\n'


class SuggestionInADocument(unittest.TestCase):
    def test_is_read_after_the_cell_it_patches_leaving_the_cells_as_they_are(self) -> None:
        document = Document(WITH_A_SUGGESTION)

        [suggestion] = document.suggestions

        self.assertEqual(
            [[cell.source for cell in document.cells], suggestion.cell_id],
            [["She saw the door.", "He heard the bell."], "c1"],
        )

    def test_carries_a_diff_that_patches_its_cell(self) -> None:
        document = Document(WITH_A_SUGGESTION)
        suggestion = document.suggestion_for("c1")
        assert suggestion is not None

        patched = suggestion.diff().apply_the_diff(document)

        patched_cell = patched.cell_with_id("c1")
        assert patched_cell is not None
        self.assertEqual(patched_cell.source, "She saw the door at last.")

    def test_is_written_back_as_it_was_read(self) -> None:
        document = Document(WITH_A_SUGGESTION)

        self.assertEqual(document.serialize(), WITH_A_SUGGESTION)

    def test_is_written_back_by_the_deprecated_text_too_until_it_is_retired(self) -> None:
        document = Document(WITH_A_SUGGESTION)

        with self.assertWarns(DeprecationWarning):
            text = document.text

        self.assertEqual(text, WITH_A_SUGGESTION)

    def test_keeps_every_change_of_the_diff_the_diff_tool_gives_through_writing_and_reading_back(self) -> None:
        before = Document(THE_CHAPTER_BEFORE)
        after = Document(THE_CHAPTER_AFTER)
        diff = AuthorDocDiff.diff(before, after)
        suggestion_made = Suggestion("h1", diff)
        suggested = before.with_suggestion(suggestion_made)

        read_back = Document(suggested.serialize())
        suggestion = read_back.suggestion_for("h1")
        assert suggestion is not None
        patched = suggestion.diff().apply_the_diff(read_back)
        patched_written = Document.from_cells(patched.cells).serialize()

        self.assertEqual(patched_written, THE_CHAPTER_AFTER)

    def test_is_refused_for_a_cell_the_document_does_not_have_when_added_to_it(self) -> None:
        document = Document('<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n')
        empty_diff = AuthorDocDiff([])
        suggestion = Suggestion("c9", empty_diff)

        with self.assertRaises(ValueError) as refused:
            document.with_suggestion(suggestion)

        self.assertEqual(str(refused.exception), "The suggestion is for cell c9, which the document does not have")

    def test_is_refused_for_a_cell_the_document_does_not_have_when_the_document_is_built_with_it(self) -> None:
        document = Document('<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n')
        empty_diff = AuthorDocDiff([])
        suggestion = Suggestion("c9", empty_diff)

        with self.assertRaises(ValueError) as refused:
            Document.from_cells(document.cells, None, [suggestion])

        self.assertEqual(str(refused.exception), "The suggestion is for cell c9, which the document does not have")

    def test_is_refused_for_a_cell_the_document_does_not_have_when_read(self) -> None:
        text = (
            '<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n\n'
            '<!-- suggestion: id="c9" -->\n'
            '<!-- change: text from="0" removed="" written="He heard the bell." -->\n'
        )

        with self.assertRaises(ValueError) as refused:
            Document(text)

        self.assertEqual(str(refused.exception), "The suggestion is for cell c9, which the document does not have")

    def test_is_one_per_cell_a_new_one_for_a_cell_taking_the_place_of_the_one_before(self) -> None:
        document = Document(WITH_A_SUGGESTION)
        empty_diff = AuthorDocDiff([])

        suggestion = Suggestion("c1", empty_diff)

        resuggested = document.with_suggestion(suggestion)

        self.assertEqual(resuggested.suggestions, [Suggestion("c1", empty_diff)])

    def test_can_be_taken_off_its_cell(self) -> None:
        document = Document(WITH_A_SUGGESTION)

        without_it = document.without_suggestion("c1")

        self.assertEqual(
            [without_it.suggestions, without_it.serialize()],
            [
                [],
                '<!-- cell: markdown id="c1" -->\n\nShe saw the door.\n\n'
                '<!-- cell: markdown id="c2" -->\n\nHe heard the bell.\n',
            ],
        )

    def test_stays_with_the_document_while_its_cells_change(self) -> None:
        document = Document(WITH_A_SUGGESTION)
        _, he_heard = document.cells

        he_heard_twice = he_heard.with_source("He heard the bell twice.")

        changed = document.with_cell(he_heard_twice)

        self.assertEqual(changed.suggestion_for("c1"), document.suggestion_for("c1"))


class SuggestionsDiff(unittest.TestCase):
    def test_gives_its_diff_and_a_suggestion_with_another_diff_in_its_place(self) -> None:
        diff = AuthorDocDiff([])
        other_diff = AuthorDocDiff([])
        suggestion = Suggestion("c1", diff)

        updated = suggestion.with_the_diff(other_diff)

        self.assertEqual([suggestion.diff(), updated.cell_id], [diff, "c1"])
        self.assertIs(updated.diff(), other_diff)
