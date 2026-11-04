from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, TypeVar
from uuid import uuid4

from authordoc.cells.cell import Cell
from authordoc.cells.story_word_range import StoryWordRange

if TYPE_CHECKING:
    from authordoc.cells.cell_visitor import CellVisitor

SALIENT_CONCEPT = "salient-concept"


@dataclass(frozen=True)
class SalientConceptReference:
    reference_id: str
    story_word_range: StoryWordRange

_Result = TypeVar("_Result")


@dataclass(frozen=True)
class SalientConceptCell(Cell):
    kind: str = field(default=SALIENT_CONCEPT, init=False)
    title: str = ""
    references: Sequence[SalientConceptReference] = ()
    source: str = ""
    folded: bool = False
    at: tuple[int, int] | None = field(default=None, compare=False)
    _unique_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        # Kept as a tuple, whatever sequence they come as, so that no one changes
        # them in place.
        object.__setattr__(self, "references", tuple(self.references))

    def with_source(self, source: str) -> SalientConceptCell:
        return replace(self, source=source)

    def with_folded(self, folded: bool) -> SalientConceptCell:
        return replace(self, folded=folded)

    def accept(self, visitor: CellVisitor[_Result]) -> _Result:
        return visitor.visit_salient_concept(self)
