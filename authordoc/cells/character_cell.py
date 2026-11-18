from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, TypeVar
from uuid import uuid4

from authordoc.cells.cell import Cell
from authordoc.cells.salient_concept_cell import SalientConceptCell

if TYPE_CHECKING:
    from authordoc.cells.cell_visitor import CellVisitor
    from authordoc.storydoc import Document

CHARACTER = "character"

_Result = TypeVar("_Result")


@dataclass(frozen=True)
class CharacterCell(Cell):
    kind: str = field(default=CHARACTER, init=False)
    title: str = ""
    source: str = ""
    folded: bool = False
    at: tuple[int, int] | None = field(default=None, compare=False)
    _unique_id: str = field(default_factory=lambda: str(uuid4()))
    _concepts: Sequence[str] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "_concepts", tuple(self._concepts))

    def concepts(self, document: Document) -> list[SalientConceptCell]:
        referenced = [document.cell_with_id(concept_id) for concept_id in self._concepts]
        concepts = [cell for cell in referenced if isinstance(cell, SalientConceptCell)]
        return concepts

    def with_concepts(self, concepts: Sequence[SalientConceptCell]) -> CharacterCell:
        concept_ids = [concept.unique_id for concept in concepts]
        supporting = replace(self, _concepts=concept_ids)
        return supporting

    def with_source(self, source: str) -> CharacterCell:
        return replace(self, source=source)

    def with_folded(self, folded: bool) -> CharacterCell:
        return replace(self, folded=folded)

    def accept(self, visitor: CellVisitor[_Result]) -> _Result:
        return visitor.visit_character(self)
