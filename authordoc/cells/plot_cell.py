from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, TypeVar
from uuid import uuid4

from authordoc.cells.cell import Cell
from authordoc.cells.character_cell import CharacterCell
from authordoc.cells.place_cell import PlaceCell
from authordoc.cells.salient_concept_cell import SalientConceptCell
from authordoc.cells.story_word_range import StoryWordRange
from authordoc.written_attributes import attributes_in, written_attribute_value

if TYPE_CHECKING:
    from authordoc.cells.cell_visitor import CellVisitor
    from authordoc.storydoc import Document

PLOT = "plot"

# A plot's body is its overview and its events, written to a rigid schema, one
# element to a line:
#
#     <ol title="How Captain Varn gave her life to buy her daughter time.">
#     <li id="e1" timestamp="1.1" place="h1" characters="v1, d1" words="412-468">Captain Varn watches the news with her daughter.</li>
#     <li id="e2" timestamp="1.2" place="c1" characters="v1">Varn is given command of the corvette.</li>
#     </ol>
#
# The attributes are written as a cell marker's are, and an event's summary is
# the rest of its line, up to the closing tag. The timestamps are a clock the
# whole manuscript shares, so a plot skips the moments nothing happens in it;
# `place` and `characters` are the ids of the place the event happens in and of
# the characters in it; and `words`
# are the story's words that tell the event, once there are any.
_ATTRIBUTES = r'((?:\s+[A-Za-z0-9][A-Za-z0-9_-]*\s*=\s*"(?:[^"\\]|\\.)*")*)\s*'
_EVENTS_OPENED = re.compile(rf"^<ol{_ATTRIBUTES}>$")
_EVENT = re.compile(rf"^<li{_ATTRIBUTES}>(.*)</li>$")
_EVENTS_CLOSED = "</ol>"
_EVENT_WORDS = re.compile(r"^(\d+)-(\d+)$")

_OVERVIEW = "title"
_EVENT_ID = "id"
_TIMESTAMP = "timestamp"
_PLACE = "place"
_CHARACTERS = "characters"
_WORDS = "words"


@dataclass(frozen=True)
class PlotNode:
    node_id: str
    story_word_range: StoryWordRange | None
    timestamp: str = ""
    place_id: str = ""
    character_ids: Sequence[str] = ()
    summary: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "character_ids", tuple(self.character_ids))

    def place(self, document: Document) -> PlaceCell | None:
        referenced = document.cell_with_id(self.place_id)
        place = referenced if isinstance(referenced, PlaceCell) else None
        return place

    def characters(self, document: Document) -> list[CharacterCell]:
        referenced = [document.cell_with_id(character_id) for character_id in self.character_ids]
        characters = [cell for cell in referenced if isinstance(cell, CharacterCell)]
        return characters

    def with_story_word_range(self, story_word_range: StoryWordRange | None) -> PlotNode:
        with_the_words = replace(self, story_word_range=story_word_range)
        return with_the_words

    def with_timestamp(self, timestamp: str) -> PlotNode:
        with_the_timestamp = replace(self, timestamp=timestamp)
        return with_the_timestamp

    def with_place(self, place: PlaceCell | None) -> PlotNode:
        place_id = "" if place is None else place.unique_id
        with_the_place = replace(self, place_id=place_id)
        return with_the_place

    def with_characters(self, characters: Sequence[CharacterCell]) -> PlotNode:
        character_ids = [character.unique_id for character in characters]
        with_the_characters = replace(self, character_ids=character_ids)
        return with_the_characters

    def with_summary(self, summary: str) -> PlotNode:
        with_the_summary = replace(self, summary=summary)
        return with_the_summary


@dataclass(frozen=True)
class PlotEdge:
    edge_id: str
    from_node_id: str
    to_node_id: str

_Result = TypeVar("_Result")


@dataclass(frozen=True)
class PlotCell(Cell):
    kind: str = field(default=PLOT, init=False)
    title: str = ""
    nodes: Sequence[PlotNode] = ()
    edges: Sequence[PlotEdge] = ()
    overview: str = ""
    folded: bool = False
    at: tuple[int, int] | None = field(default=None, compare=False)
    _unique_id: str = field(default_factory=lambda: str(uuid4()))
    # The ids of the salient concepts the plot references.
    _concepts: Sequence[str] = ()
    _characters: Sequence[str] = ()

    def __post_init__(self) -> None:
        # Kept as tuples, whatever sequences they come as, so that no one changes
        # them in place.
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "edges", tuple(self.edges))
        object.__setattr__(self, "_concepts", tuple(self._concepts))
        object.__setattr__(self, "_characters", tuple(self._characters))

    @property
    def source(self) -> str:  # type: ignore[override]
        return written_plot_body(self.overview, self.nodes)

    @classmethod
    def from_body(
        cls,
        title: str,
        edges: list[PlotEdge],
        body: str,
        folded: bool,
        at: tuple[int, int] | None,
        unique_id: str,
        concepts: list[str],
        characters: list[str],
    ) -> PlotCell:
        """The plot whose body is `body`: its overview and events read from it."""
        overview, nodes = plot_body_read(body)
        return cls(title, nodes, edges, overview, folded, at, unique_id, concepts, characters)

    def get_node_by_id(self, node_id: str) -> PlotNode:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(node_id)

    def inbound_edges(self, node: PlotNode) -> list[PlotEdge]:
        """The plot's edges that lead to `node`, in the plot's order."""
        inbound = [edge for edge in self.edges if edge.to_node_id == node.node_id]
        return inbound

    def outbound_edges(self, node: PlotNode) -> list[PlotEdge]:
        """The plot's edges that leave `node`, in the plot's order."""
        outbound = [edge for edge in self.edges if edge.from_node_id == node.node_id]
        return outbound

    def concepts(self, document: Document) -> list[SalientConceptCell]:
        """The salient concepts of `document` the plot references, in the order it
        references them; a concept the document no longer has is left out."""
        referenced = [document.cell_with_id(concept_id) for concept_id in self._concepts]
        concepts = [cell for cell in referenced if isinstance(cell, SalientConceptCell)]
        return concepts

    def with_source(self, source: str) -> PlotCell:
        overview, nodes = plot_body_read(source)
        return replace(self, overview=overview, nodes=nodes)

    def with_folded(self, folded: bool) -> PlotCell:
        return replace(self, folded=folded)

    def with_overview(self, overview: str) -> PlotCell:
        return replace(self, overview=overview)

    def with_title(self, title: str) -> PlotCell:
        retitled = replace(self, title=title)
        return retitled

    def with_nodes(self, nodes: Sequence[PlotNode]) -> PlotCell:
        with_the_nodes = replace(self, nodes=nodes)
        return with_the_nodes

    def with_node(self, node: PlotNode) -> PlotCell:
        """The plot with `node` in place of its event of the same id."""
        nodes = [node if held.node_id == node.node_id else held for held in self.nodes]
        with_the_node = replace(self, nodes=nodes)
        return with_the_node

    def with_edges(self, edges: Sequence[PlotEdge]) -> PlotCell:
        with_the_edges = replace(self, edges=edges)
        return with_the_edges

    def with_concepts(self, concepts: Sequence[SalientConceptCell]) -> PlotCell:
        """The plot referencing `concepts`, in their order."""
        concept_ids = [concept.unique_id for concept in concepts]
        referencing = replace(self, _concepts=concept_ids)
        return referencing

    def characters(self, document: Document) -> list[CharacterCell]:
        referenced = [document.cell_with_id(character_id) for character_id in self._characters]
        characters = [cell for cell in referenced if isinstance(cell, CharacterCell)]
        return characters

    def with_characters(self, characters: Sequence[CharacterCell]) -> PlotCell:
        character_ids = [character.unique_id for character in characters]
        following = replace(self, _characters=character_ids)
        return following

    def accept(self, visitor: CellVisitor[_Result]) -> _Result:
        return visitor.visit_plot(self)


def written_plot_body(overview: str, nodes: list[PlotNode]) -> str:
    """A plot's body as the schema writes it; nothing at all for a plot with
    neither an overview nor events."""
    if overview == "" and not nodes:
        return ""
    opened = f"<ol{_written_attributes([(_OVERVIEW, overview)])}>"
    events = [_written_plot_event(node) for node in nodes]
    return "\n".join([opened, *events, _EVENTS_CLOSED])


def plot_body_read(body: str) -> tuple[str, list[PlotNode]]:
    """The overview and the events a plot's body holds. A body that is not a list
    of events — one written before plots had events, or one never given any — is
    all overview."""
    lines = [line.strip() for line in body.split("\n")]
    lines = [line for line in lines if line != ""]
    opened = _EVENTS_OPENED.match(lines[0]) if lines else None
    if opened is None:
        return body, []
    overview = attributes_in(opened.group(1)).get(_OVERVIEW, "")
    nodes: list[PlotNode] = []
    for line in lines[1:]:
        if line == _EVENTS_CLOSED:
            break
        event = _EVENT.match(line)
        if event is None:
            continue
        node = _plot_event_read(event.group(1), event.group(2))
        nodes.append(node)
    return overview, nodes


def _plot_event_read(written_attributes: str, summary: str) -> PlotNode:
    attributes = attributes_in(written_attributes)
    node_id = attributes.get(_EVENT_ID) or str(uuid4())
    words = _EVENT_WORDS.match(attributes.get(_WORDS, ""))
    story_word_range = (
        None if words is None else StoryWordRange(int(words.group(1)), int(words.group(2)))
    )
    written_character_ids = [
        character_id.strip() for character_id in attributes.get(_CHARACTERS, "").split(",")
    ]
    character_ids = [character_id for character_id in written_character_ids if character_id]
    return PlotNode(
        node_id,
        story_word_range,
        attributes.get(_TIMESTAMP, ""),
        attributes.get(_PLACE, ""),
        character_ids,
        summary.strip(),
    )


def _written_plot_event(node: PlotNode) -> str:
    words = (
        ""
        if node.story_word_range is None
        else f"{node.story_word_range.first_word}-{node.story_word_range.last_word}"
    )
    character_ids = ", ".join(node.character_ids)
    attributes = _written_attributes(
        [
            (_EVENT_ID, node.node_id),
            (_TIMESTAMP, node.timestamp),
            (_PLACE, node.place_id),
            (_CHARACTERS, character_ids),
            (_WORDS, words),
        ]
    )
    # An event is one line, so a summary is too.
    summary = re.sub(r"\s*\n\s*", " ", node.summary)
    return f"<li{attributes}>{summary}</li>"


def _written_attributes(attributes: list[tuple[str, str]]) -> str:
    return "".join(
        f' {name}="{written_attribute_value(value)}"'
        for name, value in attributes
        if value != ""
    )
