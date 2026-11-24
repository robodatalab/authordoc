import unittest
from pathlib import Path

import authordoc
from authordoc import cells
from authordoc.cells.about_cell import ABOUT, AboutCell
from authordoc.cells.blurb_cell import BLURB, BlurbCell
from authordoc.cells.cell import Cell
from authordoc.cells.cell_visitor import CellVisitor
from authordoc.cells.chapter_cell import CHAPTER, ChapterCell
from authordoc.cells.character_cell import CHARACTER, CharacterCell
from authordoc.cells.disclaimer_cell import DISCLAIMER, DisclaimerCell
from authordoc.cells.divider_cell import DIVIDER, DividerCell
from authordoc.cells.image_cell import IMAGE, ImageCell
from authordoc.cells.markdown_cell import MARKDOWN, MarkdownCell
from authordoc.cells.note_cell import NOTE, NoteCell
from authordoc.cells.part_cell import PART, PartCell
from authordoc.cells.place_cell import PLACE, PlaceCell
from authordoc.cells.plot_cell import PLOT, PlotCell, PlotEdge, PlotNode
from authordoc.cells.recap_cell import RECAP, RecapCell
from authordoc.cells.salient_concept_cell import (
    SALIENT_CONCEPT,
    SalientConceptCell,
    SalientConceptReference,
)
from authordoc.cells.story_word_range import StoryWordRange
from authordoc.cells.table_of_contents_cell import TABLE_OF_CONTENTS, TableOfContentsCell
from authordoc.cells.title_page_cell import TITLE_PAGE, TitlePageCell
from authordoc.cells.unknown_cell import UnknownCell


class CellsPackage(unittest.TestCase):
    def test_exports_every_cell_type(self) -> None:
        self.assertIs(cells.Cell, Cell)
        self.assertIs(cells.CellVisitor, CellVisitor)
        self.assertIs(cells.AboutCell, AboutCell)
        self.assertIs(cells.BlurbCell, BlurbCell)
        self.assertIs(cells.ChapterCell, ChapterCell)
        self.assertIs(cells.CharacterCell, CharacterCell)
        self.assertIs(cells.DisclaimerCell, DisclaimerCell)
        self.assertIs(cells.DividerCell, DividerCell)
        self.assertIs(cells.ImageCell, ImageCell)
        self.assertIs(cells.MarkdownCell, MarkdownCell)
        self.assertIs(cells.NoteCell, NoteCell)
        self.assertIs(cells.PartCell, PartCell)
        self.assertIs(cells.PlaceCell, PlaceCell)
        self.assertIs(cells.PlotCell, PlotCell)
        self.assertIs(cells.PlotNode, PlotNode)
        self.assertIs(cells.PlotEdge, PlotEdge)
        self.assertIs(cells.RecapCell, RecapCell)
        self.assertIs(cells.SalientConceptCell, SalientConceptCell)
        self.assertIs(cells.SalientConceptReference, SalientConceptReference)
        self.assertIs(cells.StoryWordRange, StoryWordRange)
        self.assertIs(cells.TableOfContentsCell, TableOfContentsCell)
        self.assertIs(cells.TitlePageCell, TitlePageCell)
        self.assertIs(cells.UnknownCell, UnknownCell)

    def test_exports_every_cell_kind(self) -> None:
        self.assertEqual(cells.ABOUT, ABOUT)
        self.assertEqual(cells.BLURB, BLURB)
        self.assertEqual(cells.CHAPTER, CHAPTER)
        self.assertEqual(cells.CHARACTER, CHARACTER)
        self.assertEqual(cells.DISCLAIMER, DISCLAIMER)
        self.assertEqual(cells.DIVIDER, DIVIDER)
        self.assertEqual(cells.IMAGE, IMAGE)
        self.assertEqual(cells.MARKDOWN, MARKDOWN)
        self.assertEqual(cells.NOTE, NOTE)
        self.assertEqual(cells.PART, PART)
        self.assertEqual(cells.PLACE, PLACE)
        self.assertEqual(cells.PLOT, PLOT)
        self.assertEqual(cells.RECAP, RECAP)
        self.assertEqual(cells.SALIENT_CONCEPT, SALIENT_CONCEPT)
        self.assertEqual(cells.TABLE_OF_CONTENTS, TABLE_OF_CONTENTS)
        self.assertEqual(cells.TITLE_PAGE, TITLE_PAGE)


class TypedPackage(unittest.TestCase):
    def test_the_package_declares_that_it_carries_type_hints(self) -> None:
        marker = Path(authordoc.__file__).parent / "py.typed"
        self.assertTrue(marker.is_file())


if __name__ == "__main__":
    unittest.main()
