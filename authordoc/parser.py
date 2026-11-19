from __future__ import annotations

import re
from collections.abc import Sequence
from uuid import uuid4

from authordoc.cells.cell import Cell
from authordoc.cells.about_cell import ABOUT, AboutCell
from authordoc.cells.blurb_cell import BLURB, BlurbCell
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
from authordoc.cells.table_of_contents_cell import (
    TABLE_OF_CONTENTS,
    TableOfContentsCell,
)
from authordoc.cells.title_page_cell import TITLE_PAGE, TitlePageCell
from authordoc.cells.story_word_range import StoryWordRange
from authordoc.cells.unknown_cell import UnknownCell
from authordoc.visitors.marker_attributes import (
    AUTHOR,
    COVER_DESIGNER,
    DATE,
    DOCUMENTS,
    FULL_PAGE,
    ISBN,
    KDP,
    LANGUAGE,
    NO,
    CHARACTER_CONCEPTS,
    PLACE_PARENT,
    PLOT_CHARACTERS,
    PLOT_CONCEPTS,
    PLOT_EDGES,
    PLOT_NODES,
    PORTRAIT,
    PUBLISHER,
    SALIENT_CONCEPT_REFERENCES,
    SRC,
    SUBSTACK,
    SUBTITLE,
    TITLE,
    VERSION,
    WEBSITE,
    MarkerAttributes,
)
from authordoc.written_attributes import attributes_in, written_attribute_value
from authordoc.author_doc_change import AuthorDocChange
from authordoc.changes.cell_added import CellAdded
from authordoc.changes.cell_header_changed import CellHeaderChanged
from authordoc.changes.cell_removed import CellRemoved
from authordoc.changes.cell_text_changed import CellTextChanged
from authordoc.changes.cells_moved import CellsMoved
from authordoc.suggestion import Suggestion
from authordoc.visitors.change_markers import (
    AFTER,
    AT,
    BEFORE,
    CELL_ADDED,
    CELL_HEADER_CHANGED,
    CELL_IDS_AFTER,
    CELL_IDS_BEFORE,
    CELL_IDS_SEPARATOR,
    CELL_REMOVED,
    CELL_TEXT_CHANGED,
    CELLS_MOVED,
    FROM,
    KIND,
    TEXT,
    TEXT_REMOVED,
    TEXT_WRITTEN,
    ChangeMarkers,
)

_UNIQUE_ID = "id"
FOLDED = "folded"
_TRUE = "true"

_MARKER = re.compile(r"^<!--\s*cell:\s*([A-Za-z0-9][A-Za-z0-9_-]*)\s*(.*?)\s*-->\s*$")

_SUGGESTION_MARKER = re.compile(r"^<!--\s*suggestion:\s*(.*?)\s*-->\s*$")

_CHANGE_MARKER = re.compile(r"^<!--\s*change:\s*([a-z]+)\s*(.*?)\s*-->\s*$")

_SALIENT_CONCEPT_REFERENCE = re.compile(r"^\s*(?:([^:\s]+):)?(\d+)-(\d+)\s*$")

_PLOT_NODE = re.compile(r"^\s*([^:\s]+):(\d+)-(\d+)\s*$")
_PLOT_EDGE = re.compile(r"^\s*([^:\s]+):([^>\s]+)>(\S+)\s*$")

_COMMENT_OPEN = "<!--"
_COMMENT_CLOSE = "-->"


def parse(text: str) -> list[Cell]:
    cells: list[Cell] = []
    kind, attrs, body, first, unique_id, folded = MARKDOWN, {}, [], 0, "", False
    opened = False

    def close() -> None:
        # `serialize` strips blank lines off both ends of a cell's text, so
        # the lines it occupies are the ones between the outermost non-blank ones.
        written = [i for i, line in enumerate(body) if line != ""]
        source = "\n".join(body).strip("\n")
        # A marker opens a cell, so the run of text above the first one belongs
        # to no cell and is dropped — as the editor's reader drops it.
        if opened:
            at = (first + written[0], first + written[-1]) if written else None
            cell = _cell_from_marker(kind, dict(attrs), source, folded, at, unique_id)
            cells.append(cell)

    # Split on "\n" alone, as the editor's reader does: a form feed or a
    # U+2028 is a character the author wrote, not a line the document has.
    for index, line in enumerate(text.split("\n")):
        if _SUGGESTION_MARKER.match(line):
            close()
            opened = False
            body = []
            continue
        marker = _MARKER.match(line)
        if not marker:
            body.append(line)
            continue
        close()
        opened = True
        kind = marker.group(1)
        attrs = attributes_in(marker.group(2))
        unique_id = attrs.pop(_UNIQUE_ID, "") or str(uuid4())
        folded = attrs.pop(FOLDED, "") == _TRUE
        body = []
        first = index + 1
    close()
    return cells


def parse_suggestions(text: str) -> list[Suggestion]:
    # The diff reads documents, so it is imported where it is used.
    from authordoc.diff import AuthorDocDiff

    suggestions: list[Suggestion] = []
    cell_id: str | None = None
    changes: list[AuthorDocChange] = []

    def close() -> None:
        nonlocal cell_id, changes
        if cell_id is not None:
            diff = AuthorDocDiff(changes)
            suggestion = Suggestion(cell_id, diff)
            suggestions.append(suggestion)
        cell_id = None
        changes = []

    for line in text.split("\n"):
        suggestion_marker = _SUGGESTION_MARKER.match(line)
        if suggestion_marker:
            close()
            suggestion_said = suggestion_marker.group(1)
            attrs = attributes_in(suggestion_said)
            cell_id = attrs.get(_UNIQUE_ID, "")
            continue
        change_marker = _CHANGE_MARKER.match(line)
        if change_marker and cell_id is not None:
            change_written = change_marker.group(1)
            change_said = change_marker.group(2)
            attrs = attributes_in(change_said)
            change = _change_from_marker(change_written, attrs, cell_id)
            changes.append(change)
            continue
        if line.strip():
            close()
    close()
    return suggestions


def _attributes_prefixed(prefix: str, attrs: dict[str, str]) -> dict[str, str]:
    attributes = {name[len(prefix) :]: value for name, value in attrs.items() if name.startswith(prefix)}
    return attributes


def _cell_of_the_change(kind: str, header: dict[str, str], source: str, cell_id: str) -> Cell:
    attrs = dict(header)
    folded = attrs.pop(FOLDED, "") == _TRUE
    cell = _cell_from_marker(kind, attrs, source, folded, None, cell_id)
    return cell


def _change_from_marker(change: str, attrs: dict[str, str], cell_id: str) -> AuthorDocChange:
    kind = attrs.get(KIND, MARKDOWN)
    text = attrs.get(TEXT, "")
    header_before = _attributes_prefixed(BEFORE, attrs)
    header_after = _attributes_prefixed(AFTER, attrs)
    if change == CELL_ADDED:
        cell_index = int(attrs[AT])
        cell = _cell_of_the_change(kind, header_after, text, cell_id)
        return CellAdded(cell_index, cell)
    if change == CELL_REMOVED:
        cell_index = int(attrs[AT])
        cell = _cell_of_the_change(kind, header_before, text, cell_id)
        return CellRemoved(cell_index, cell)
    if change == CELLS_MOVED:
        cell_ids_before = attrs.get(CELL_IDS_BEFORE, "").split(CELL_IDS_SEPARATOR)
        cell_ids_after = attrs.get(CELL_IDS_AFTER, "").split(CELL_IDS_SEPARATOR)
        return CellsMoved(cell_ids_before, cell_ids_after)
    if change == CELL_HEADER_CHANGED:
        before = _cell_of_the_change(kind, header_before, "", cell_id)
        after = _cell_of_the_change(kind, header_after, "", cell_id)
        return CellHeaderChanged(before, after)
    if change == CELL_TEXT_CHANGED:
        from_character = int(attrs[FROM])
        text_removed = attrs.get(TEXT_REMOVED, "")
        text_written = attrs.get(TEXT_WRITTEN, "")
        return CellTextChanged(cell_id, from_character, text_removed, text_written)
    raise ValueError(f'No change is written as "{change}"')


def serialize(cells: Sequence[Cell], suggestions: Sequence[Suggestion]) -> str:
    marker_attributes = MarkerAttributes()
    out: list[str] = []
    for cell in cells:
        marker = marker_for(cell, marker_attributes)
        out.append(marker)
        out.append("")
        if cell.source:
            out.append(cell.source)
            out.append("")
        suggestion = next((held for held in suggestions if held.cell_id == cell.unique_id), None)
        if suggestion is not None:
            suggestion_lines = _suggestion_written(suggestion)
            out.extend(suggestion_lines)
            out.append("")
    cell_ids = [cell.unique_id for cell in cells]
    suggestions_for_no_cell = [suggestion for suggestion in suggestions if suggestion.cell_id not in cell_ids]
    for suggestion in suggestions_for_no_cell:
        suggestion_lines = _suggestion_written(suggestion)
        out.extend(suggestion_lines)
        out.append("")
    serialized = "\n".join(out)
    return serialized


def _suggestion_written(suggestion: Suggestion) -> list[str]:
    cell_id_written = written_attribute_value(suggestion.cell_id)
    marker = f'<!-- suggestion: {_UNIQUE_ID}="{cell_id_written}" -->'
    change_markers = ChangeMarkers()
    diff = suggestion.diff()
    changes_written = [change.accept(change_markers) for change in diff.changes]
    written = [marker, *changes_written]
    return written


def cell_of_kind(kind: str) -> Cell:
    unique_id = str(uuid4())
    return _cell_from_marker(kind, {}, "", False, None, unique_id)


def _salient_concept_references_in(written: str) -> list[SalientConceptReference]:
    references: list[SalientConceptReference] = []
    for written_reference in written.split(","):
        read_reference = _SALIENT_CONCEPT_REFERENCE.match(written_reference)
        if read_reference is None:
            continue
        reference_id = read_reference.group(1) or str(uuid4())
        first_word = int(read_reference.group(2))
        last_word = int(read_reference.group(3))
        story_word_range = StoryWordRange(first_word, last_word)
        reference = SalientConceptReference(reference_id, story_word_range)
        references.append(reference)
    return references


def _plot_nodes_in(written: str) -> list[PlotNode]:
    nodes: list[PlotNode] = []
    for written_node in written.split(","):
        read_node = _PLOT_NODE.match(written_node)
        if read_node is None:
            continue
        first_word = int(read_node.group(2))
        last_word = int(read_node.group(3))
        story_word_range = StoryWordRange(first_word, last_word)
        node = PlotNode(read_node.group(1), story_word_range)
        nodes.append(node)
    return nodes


def _plot_edges_in(written: str) -> list[PlotEdge]:
    edges: list[PlotEdge] = []
    for written_edge in written.split(","):
        read_edge = _PLOT_EDGE.match(written_edge)
        if read_edge is None:
            continue
        edge = PlotEdge(read_edge.group(1), read_edge.group(2), read_edge.group(3))
        edges.append(edge)
    return edges


def _cell_ids_in(written: str) -> list[str]:
    parts = [written_concept.strip() for written_concept in written.split(",")]
    concepts = [concept_id for concept_id in parts if concept_id]
    return concepts


def _cell_from_marker(
    kind: str,
    attrs: dict[str, str],
    source: str,
    folded: bool,
    at: tuple[int, int] | None,
    unique_id: str,
) -> Cell:
    if kind == MARKDOWN:
        return MarkdownCell(source, folded, at, unique_id)
    if kind == CHAPTER:
        return ChapterCell(attrs.get(TITLE, ""), source, folded, at, unique_id)
    if kind == PART:
        return PartCell(attrs.get(TITLE, ""), source, folded, at, unique_id)
    if kind == DIVIDER:
        return DividerCell(source, folded, at, unique_id)
    if kind == TITLE_PAGE:
        return TitlePageCell(
            attrs.get(TITLE, ""),
            attrs.get(SUBTITLE, ""),
            attrs.get(AUTHOR, ""),
            attrs.get(PUBLISHER, ""),
            attrs.get(DATE, ""),
            attrs.get(VERSION, ""),
            attrs.get(ISBN, ""),
            attrs.get(COVER_DESIGNER, ""),
            attrs.get(LANGUAGE, ""),
            source,
            folded,
            at,
            unique_id,
        )
    if kind == IMAGE:
        return ImageCell(
            attrs.get(SRC, ""),
            attrs.get(FULL_PAGE) != NO,
            source,
            folded,
            at,
            unique_id,
        )
    if kind == TABLE_OF_CONTENTS:
        return TableOfContentsCell(source, folded, at, unique_id)
    if kind == DISCLAIMER:
        return DisclaimerCell(attrs.get(TITLE, ""), source, folded, at, unique_id)
    if kind == ABOUT:
        return AboutCell(
            attrs.get(KDP, ""),
            attrs.get(WEBSITE, ""),
            attrs.get(SUBSTACK, ""),
            attrs.get(PORTRAIT, ""),
            source,
            folded,
            at,
            unique_id,
        )
    if kind == BLURB:
        return BlurbCell(source, folded, at, unique_id)
    if kind == NOTE:
        return NoteCell(source, folded, at, unique_id)
    if kind == RECAP:
        return RecapCell(attrs.get(DOCUMENTS, ""), source, folded, at, unique_id)
    if kind == SALIENT_CONCEPT:
        references = _salient_concept_references_in(
            attrs.get(SALIENT_CONCEPT_REFERENCES, "")
        )
        return SalientConceptCell(
            attrs.get(TITLE, ""), references, source, folded, at, unique_id
        )
    if kind == PLOT:
        edges = _plot_edges_in(attrs.get(PLOT_EDGES, ""))
        concepts = _cell_ids_in(attrs.get(PLOT_CONCEPTS, ""))
        characters = _cell_ids_in(attrs.get(PLOT_CHARACTERS, ""))
        # A plot written before plots had events keeps its nodes in its marker
        # and its overview in its body; it is written back with events.
        if PLOT_NODES in attrs:
            nodes = _plot_nodes_in(attrs[PLOT_NODES])
            return PlotCell(
                attrs.get(TITLE, ""),
                nodes,
                edges,
                source,
                folded,
                at,
                unique_id,
                concepts,
                characters,
            )
        return PlotCell.from_body(
            attrs.get(TITLE, ""), edges, source, folded, at, unique_id, concepts, characters
        )
    if kind == CHARACTER:
        concepts = _cell_ids_in(attrs.get(CHARACTER_CONCEPTS, ""))
        return CharacterCell(attrs.get(TITLE, ""), source, folded, at, unique_id, concepts)
    if kind == PLACE:
        return PlaceCell(
            attrs.get(TITLE, ""), source, folded, at, unique_id, attrs.get(PLACE_PARENT, "")
        )
    return UnknownCell(kind, attrs, source, folded, at, unique_id)


def split_comments(lines: list[str], line_indices: list[int]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    kept_indices: list[int] = []
    inside = False

    for line, index in zip(lines, line_indices):
        # A comment may open on one line and close on another, and one never
        # closed runs to the end, so a line is only known by what came above it.
        commented = inside
        remainder: list[str] = []
        rest = line

        while rest:
            if inside:
                close = rest.find(_COMMENT_CLOSE)
                if close < 0:
                    break
                inside = False
                rest = rest[close + len(_COMMENT_CLOSE) :]
            else:
                opened = rest.find(_COMMENT_OPEN)
                if opened < 0:
                    remainder.append(rest)
                    break
                remainder.append(rest[:opened])
                commented = True
                inside = True
                rest = rest[opened + len(_COMMENT_OPEN) :]

        # Prose standing beside a comment is still prose; only a line the comment
        # left nothing of is a comment line. A blank line the author wrote is not.
        if commented and not "".join(remainder).strip():
            if kept_indices:
                ranges.append((kept_indices[0], kept_indices[-1]))
                kept_indices = []
        else:
            kept_indices.append(index)

    if kept_indices:
        ranges.append((kept_indices[0], kept_indices[-1]))

    return ranges


def marker_for(cell: Cell, marker_attributes: MarkerAttributes) -> str:
    attributes_of_the_kind = cell.accept(marker_attributes)
    folded = {FOLDED: _TRUE} if cell.folded else {}
    written_attrs = {_UNIQUE_ID: cell.unique_id, **attributes_of_the_kind, **folded}
    said = "".join(
        f' {name}="{written_attribute_value(value)}"'
        for name, value in written_attrs.items()
    )
    return f"<!-- cell: {cell.kind}{said} -->"

